"""The three specialist agents: bugs, security, tests.

Each specialist is a ReAct agent (LangChain `create_agent`, which is a
prebuilt LangGraph loop) with five tools. Four are read only lookups over the
code under review and the rule catalog; one reads team memory. None of them
can change anything, so the specialists run autonomously. All write actions
live in the parent graph behind a human approval step.

    run_static_checks   deterministic analyzer results for this specialty
    read_code           numbered source lines for a file range
    list_functions      function inventory (params, raises, branches, complexity)
    search_team_memory  team conventions from long term memory
    lookup_rule         rule catalog entry, with CWE where relevant
"""

from __future__ import annotations

import json
import time
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from codesentinel.agents.prompts import PROMPT_VERSION, SPECIALIST_PROMPTS
from codesentinel.cache import content_hash, get_cache
from codesentinel.config import Settings
from codesentinel.llm import get_models, message_text, model_name, parse_or_repair
from codesentinel.memory import get_memory
from codesentinel.models import SEVERITY_ORDER, AgentName, CodeFile, Finding, FindingList
from codesentinel.tools.static_analysis import RULES, numbered, public_functions, run_static_analysis

INLINE_CODE_LIMIT = 14000  # characters of numbered code placed directly in the prompt


class LLMFinding(Finding):
    agent: AgentName = "bugs"  # the model does not need to repeat its own name; we set it after parsing


class LLMFindings(FindingList):
    findings: list[LLMFinding] = []
    disputed_static_ids: dict[str, str] = {}


def _build_tools(files: list[CodeFile], static: list[Finding], namespace: str):
    by_path = {f.path: f for f in files}

    def _resolve(path: str) -> CodeFile | None:
        if path in by_path:
            return by_path[path]
        for p, f in by_path.items():
            if p.endswith(path) or path.endswith(p):
                return f
        return None

    @tool
    def run_static_checks(file_path: str = "") -> str:
        """Return the deterministic static analysis findings for your specialty, optionally for one file."""
        items = [f for f in static if not file_path or f.file == file_path or f.file.endswith(file_path)]
        return json.dumps([{"id": f.id, "rule_id": f.rule_id, "severity": f.severity, "file": f.file,
                            "line": f.line, "title": f.title, "evidence": f.evidence} for f in items][:60])

    @tool
    def read_code(file_path: str, start_line: int = 1, end_line: int = 200) -> str:
        """Read numbered source lines from a file under review. Use it to verify line numbers before reporting."""
        f = _resolve(file_path)
        if f is None:
            return f"No file named {file_path}. Files: {', '.join(by_path)}"
        end_line = min(end_line, start_line + 300)
        return numbered(f.content, start_line, end_line)

    @tool
    def list_functions(file_path: str) -> str:
        """List public functions in a Python file with parameters, raised exceptions, branch count and complexity."""
        f = _resolve(file_path)
        if f is None:
            return f"No file named {file_path}."
        return json.dumps(public_functions(f))

    @tool
    def search_team_memory(query: str) -> str:
        """Search this project's team conventions and past review decisions."""
        hits = get_memory().search(namespace, query, kind="convention", limit=5)
        return json.dumps([h["text"] for h in hits]) if hits else "No team conventions stored for this project."

    @tool
    def lookup_rule(rule_id: str) -> str:
        """Look up a rule from the static rule catalog (title, default severity, CWE)."""
        rule = RULES.get(rule_id.upper())
        return json.dumps(rule) if rule else f"Unknown rule {rule_id}. Known: {', '.join(RULES)}"

    return [run_static_checks, read_code, list_functions, search_team_memory, lookup_rule]


def _user_message(agent: str, files: list[CodeFile], plan: dict, static: list[Finding], conventions: list[str]) -> str:
    inventory = "\n".join(f"- {f.path} ({f.language}, {len(f.content.splitlines())} lines{', test file' if f.is_test else ''})"
                          for f in files)
    code_blob = "\n\n".join(f"### {f.path}\n{numbered(f.content)}" for f in files)
    code_section = (f"Code under review (line numbers on the left):\n{code_blob}" if len(code_blob) <= INLINE_CODE_LIMIT
                    else "The code is large. Use read_code and list_functions to inspect the parts you need.")
    static_json = json.dumps([{"id": f.id, "rule_id": f.rule_id, "severity": f.severity, "file": f.file, "line": f.line,
                               "title": f.title} for f in static][:40])
    return (f"Specialty: {agent}\n"
            f"Orchestrator focus areas: {json.dumps(plan.get('focus_areas', []))}\n"
            f"Team conventions: {json.dumps(conventions) if conventions else 'none stored'}\n\n"
            f"Files:\n{inventory}\n\nStatic findings for your specialty:\n{static_json}\n\n{code_section}\n\n"
            "Investigate, then reply with the JSON object described in your instructions.")


def ground_findings(raw: list[Finding], files: list[CodeFile]) -> tuple[list[Finding], int]:
    """Reject or correct LLM findings that do not point at real code (hallucination guard)."""
    by_path = {f.path: f for f in files}
    kept, dropped = [], 0
    for fd in raw:
        file = by_path.get(fd.file) or next((f for p, f in by_path.items() if p.endswith(fd.file) or fd.file.endswith(p)), None)
        if file is None:
            dropped += 1
            continue
        lines = file.content.splitlines()
        ev = (fd.evidence or "").strip()
        line = fd.line
        if ev:
            window = range(max(1, line - 3), min(len(lines), line + 3) + 1)
            near = next((i for i in window if ev[:60] and ev[:60] in lines[i - 1]), None)
            if near is None:
                near = next((i for i, t in enumerate(lines, 1) if ev[:60] and ev[:60] in t), None)
            if near is None:
                dropped += 1
                continue
            line = near
        elif not (1 <= line <= len(lines)):
            dropped += 1
            continue
        kept.append(fd.model_copy(update={"file": file.path, "line": line,
                                          "evidence": lines[line - 1].strip()[:240], "id": ""}))
    # recompute ids after correction
    return [Finding(**f.model_dump()) for f in kept], dropped


def merge_findings(static: list[Finding], llm: list[Finding], disputed: dict[str, str]) -> list[Finding]:
    merged: list[Finding] = []
    for s in static:
        if s.id in disputed:
            s = s.model_copy(update={"confidence": round(s.confidence * 0.5, 2),
                                     "explanation": f"{s.explanation} (Disputed by the LLM agent: {disputed[s.id]})"})
        merged.append(s)
    for f in llm:
        match = next((m for m in merged if m.file == f.file and abs(m.line - f.line) <= 1 and m.agent == f.agent
                      and (m.rule_id == f.rule_id or m.source == "static")), None)
        if match:
            idx = merged.index(match)
            sev = min(match.severity, f.severity, key=lambda s: SEVERITY_ORDER[s])
            merged[idx] = match.model_copy(update={
                "source": "static+llm", "severity": sev,
                "explanation": f.explanation if len(f.explanation) > len(match.explanation) else match.explanation,
                "recommendation": f.recommendation or match.recommendation,
                "suggested_test": f.suggested_test or match.suggested_test,
                "confidence": max(match.confidence, f.confidence)})
        else:
            merged.append(f)
    return merged


def run_specialist(agent: str, files: list[CodeFile], plan: dict, namespace: str, settings: Settings) -> dict[str, Any]:
    """Run one specialist. Never raises: failures degrade to static results and are reported."""
    started = time.time()
    cache = get_cache()
    run = {"agent": agent, "mode": "static", "status": "ok", "model": None, "tool_calls": 0, "cache": "miss",
           "ungrounded_dropped": 0, "error": None, "summary": ""}

    static_key = content_hash("static", agent, sorted(RULES), [f.model_dump() for f in files])
    cached_static = cache.get("static", static_key)
    if cached_static is not None:
        static = [Finding(**d) for d in cached_static]
    else:
        static = run_static_analysis(files, agent)
        cache.set("static", static_key, [f.model_dump() for f in static], ttl=7 * 24 * 3600)

    models = get_models(settings)
    if not models:
        run["duration_s"] = round(time.time() - started, 2)
        return {"findings": static, "run": run}

    conventions = [h["text"] for h in get_memory().search(namespace, " ".join(plan.get("focus_areas", [])) + " " + agent,
                                                         kind="convention", limit=5)]
    key = content_hash("llm", agent, PROMPT_VERSION, [model_name(m) for m in models], [f.model_dump() for f in files],
                       plan.get("focus_areas"), conventions)
    cached = cache.get("llm", key)
    if cached is not None:
        run.update(mode="llm", cache="hit", model=cached.get("model"), summary=cached.get("summary", ""))
        llm_findings = [Finding(**d) for d in cached["findings"]]
        merged = merge_findings(static, llm_findings, cached.get("disputed", {}))
        run["duration_s"] = round(time.time() - started, 2)
        return {"findings": merged, "run": run}

    tools = _build_tools(files, static, namespace)
    prompt = _user_message(agent, files, plan, static, conventions)
    errors = []
    for model in models:
        try:
            graph = create_agent(model, tools=tools, system_prompt=SPECIALIST_PROMPTS[agent], name=f"{agent}_agent")
            result = graph.invoke({"messages": [HumanMessage(content=prompt)]},
                                  config={"recursion_limit": settings.agent_step_limit * 2 + 1})
            messages = result["messages"]
            final = next((m for m in reversed(messages) if isinstance(m, AIMessage) and not m.tool_calls), messages[-1])
            parsed = parse_or_repair(model, message_text(final), LLMFindings)
            raw = [Finding(**{**f.model_dump(), "agent": agent, "source": "llm", "id": ""}) for f in parsed.findings]
            grounded, dropped = ground_findings(raw, files)
            run.update(mode="llm", model=model_name(model), summary=parsed.summary, ungrounded_dropped=dropped,
                       tool_calls=sum(len(m.tool_calls) for m in messages if isinstance(m, AIMessage)),
                       tool_errors=sum(1 for m in messages if isinstance(m, ToolMessage) and m.status == "error"))
            cache.set("llm", key, {"findings": [f.model_dump() for f in grounded], "disputed": parsed.disputed_static_ids,
                                   "summary": parsed.summary, "model": run["model"]}, settings.llm_cache_ttl)
            merged = merge_findings(static, grounded, parsed.disputed_static_ids)
            if errors:
                run["status"] = "recovered"
                run["error"] = " | ".join(errors)
            run["duration_s"] = round(time.time() - started, 2)
            return {"findings": merged, "run": run}
        except Exception as exc:  # noqa: BLE001  fall through to the next model, then degrade
            errors.append(f"{model_name(model)}: {type(exc).__name__}: {str(exc)[:240]}")

    run.update(status="degraded", error=" | ".join(errors), mode="static")
    run["duration_s"] = round(time.time() - started, 2)
    return {"findings": static, "run": run}
