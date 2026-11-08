"""Orchestrator agent: plans the review and compiles the final report.

Planning and summarising use the LLM when available. Everything that decides
an outcome (dedupe, suppression, scoring, verdict, escalation) is plain code,
so the verdict is reproducible and cannot be talked out of by a model.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from codesentinel.agents.prompts import PLANNER_PROMPT, SUMMARY_PROMPT
from codesentinel.config import Settings
from codesentinel.llm import get_models, structured_call
from codesentinel.memory import get_memory
from codesentinel.models import SEVERITY_ORDER, SEVERITY_WEIGHT, CodeFile, Finding, ReviewPlan
from pydantic import BaseModel

RISKY_HINTS = re.compile(r"(password|token|secret|sql|execute|subprocess|payment|refund|auth|login|pickle|eval|admin)", re.I)


class Summary(BaseModel):
    summary: str


def heuristic_plan(files: list[CodeFile]) -> ReviewPlan:
    text = "\n".join(f.content for f in files)
    hits = sorted({m.lower() for m in RISKY_HINTS.findall(text)})
    only_tests = all(f.is_test for f in files)
    agents = ["bugs", "security"] if only_tests else ["bugs", "security", "tests"]
    focus = [f"Check how `{h}` related code handles untrusted input and failures" for h in hits[:4]] or [
        "General correctness and maintainability"]
    risk = "high" if len(hits) >= 3 else "medium" if hits else "low"
    return ReviewPlan(agents=agents, focus_areas=focus, risk_level=risk,
                      rationale=f"Rule based plan. Sensitive keywords found: {', '.join(hits) or 'none'}.")


def make_plan(files: list[CodeFile], settings: Settings) -> tuple[ReviewPlan, str]:
    base = heuristic_plan(files)
    models = get_models(settings)
    if not models:
        return base, "rules"
    inventory = [{"path": f.path, "language": f.language, "lines": len(f.content.splitlines()), "is_test": f.is_test,
                  "preview": f.content[:1200]} for f in files]
    try:
        plan, model = structured_call(models, PLANNER_PROMPT, json.dumps(inventory), ReviewPlan)
        if not plan.agents:
            plan.agents = base.agents
        return plan, model
    except Exception:  # noqa: BLE001  planning is never allowed to block a review
        return base, "rules (LLM planner failed)"


def _dedupe(findings: list[Finding]) -> list[Finding]:
    best: dict[tuple, Finding] = {}
    for f in findings:
        key = (f.file, f.line, f.rule_id if f.rule_id != "LLM" else f.title.lower()[:40])
        cur = best.get(key)
        if cur is None or SEVERITY_ORDER[f.severity] < SEVERITY_ORDER[cur.severity] or f.confidence > cur.confidence:
            best[key] = f
    return list(best.values())


def score_and_verdict(findings: list[Finding]) -> tuple[int, str, dict]:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for f in findings:
        counts[f.severity] += 1
    penalty = sum(SEVERITY_WEIGHT[f.severity] * (0.5 if f.confidence < 0.5 else 1) for f in findings)
    # Halves every 50 penalty points: one high issue is about 85, four criticals about 25. Never negative.
    score = round(100 * 0.5 ** (penalty / 50))
    if counts["critical"]:
        verdict = "block"
    elif counts["high"] or score < 70:
        verdict = "request_changes"
    else:
        verdict = "approve_with_comments" if findings else "approve"
    return score, verdict, counts


def compile_report(state: dict, settings: Settings) -> dict:
    namespace = state.get("namespace", "local")
    memory = get_memory()
    raw = [Finding(**f) for f in state.get("findings", [])]
    findings, suppressed = [], []
    for f in _dedupe(raw):
        hit = memory.is_suppressed(namespace, f.model_dump())
        if hit:
            suppressed.append({**f.model_dump(), "suppressed_reason": hit["text"]})
        else:
            findings.append(f)
    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], -f.confidence, f.file, f.line))
    score, verdict, counts = score_and_verdict(findings)
    runs = state.get("agent_runs", [])

    escalations = []
    if counts["critical"]:
        escalations.append(f"{counts['critical']} critical issue(s) found. A senior reviewer must acknowledge them before anything is posted.")
    degraded = [r["agent"] for r in runs if r.get("status") == "degraded"]
    if degraded:
        escalations.append(f"These agents fell back to static analysis because the LLM failed: {', '.join(degraded)}.")
    dropped = sum(r.get("ungrounded_dropped", 0) for r in runs)
    if dropped >= 3:
        escalations.append(f"{dropped} LLM findings were dropped because they did not match the code. Treat LLM output with care.")
    slow = [r["agent"] for r in runs if r.get("duration_s", 0) > settings.slow_agent_seconds]
    if slow:
        escalations.append(f"Slow agents (over {settings.slow_agent_seconds:.0f}s): {', '.join(slow)}.")

    summary = _summary(findings, counts, verdict, state, settings)
    history = memory.review_history(namespace)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "namespace": namespace,
        "source": state.get("source", {}),
        "files": [f["path"] for f in state.get("files", [])],
        "plan": state.get("plan", {}),
        "score": score,
        "verdict": verdict,
        "counts": counts,
        "summary": summary,
        "findings": [f.model_dump() for f in findings],
        "suppressed": suppressed,
        "agent_runs": runs,
        "escalations": escalations,
        "previous_score": history[-1]["metadata"].get("score") if history else None,
    }


def _summary(findings: list[Finding], counts: dict, verdict: str, state: dict, settings: Settings) -> str:
    top = findings[:6]
    fallback = (f"The review found {len(findings)} issue(s): "
                + ", ".join(f"{n} {s}" for s, n in counts.items() if n) + ". " if findings else
                "No issues were found by any agent. ") + (
        f"The most important one is \"{top[0].title}\" in {top[0].file} at line {top[0].line}. " if top else "") + {
        "block": "Do not merge until the critical issues are fixed.",
        "request_changes": "Fix the high severity issues before merging.",
        "approve_with_comments": "The change can merge once the comments are considered.",
        "approve": "The change looks safe to merge.",
    }[verdict]
    models = get_models(settings)
    if not models or not findings:
        return fallback
    payload = {"verdict": verdict, "counts": counts,
               "top_findings": [{"severity": f.severity, "title": f.title, "file": f.file, "line": f.line,
                                 "why": f.explanation[:300]} for f in top]}
    try:
        result, _ = structured_call(models, SUMMARY_PROMPT, json.dumps(payload), Summary)
        return result.summary.strip() or fallback
    except Exception:  # noqa: BLE001
        return fallback
