"""The CodeSentinel LangGraph.

    START
      │
    intake ──(no files)──► END            validate input, size guards, load memory namespace
      │
    plan                                  orchestrator decides agents, focus and risk
      │
    plan_review   ⏸ interrupt (optional)  human approves or edits the plan, or cancels
      │
      ├──Send──► specialist[bugs]     ┐
      ├──Send──► specialist[security] ├  parallel ReAct agents (read only tools)
      └──Send──► specialist[tests]    ┘
      │
    aggregate                             dedupe, memory suppression, score, verdict, escalations
      │
    human_review  ⏸ interrupt            approve or reject, dismiss false positives, choose write actions
      │
    execute_actions                       the only node that writes: save, post to GitHub, update memory
      │
     END

State is checkpointed (SQLite) per thread_id, so a review can pause at either
interrupt, survive a browser refresh or app restart, and resume exactly there.
"""

from __future__ import annotations

import json
import operator
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send, interrupt

from codesentinel.agents.orchestrator import compile_report, make_plan
from codesentinel.agents.specialists import run_specialist
from codesentinel.cache import content_hash
from codesentinel.config import DATA_DIR, ROOT_DIR, get_settings
from codesentinel.memory import get_memory
from codesentinel.models import CodeFile, ReviewPlan, detect_language
from codesentinel.report import to_markdown
from codesentinel.tools.github_tools import GitHubError, post_pr_comment

WRITE_ACTIONS = {"save_report", "post_github", "remember_feedback"}
AUTONOMOUS_SAFE_ACTIONS = {"save_report"}  # local file only; nothing leaves the machine
REPORTS_DIR = ROOT_DIR / "reports"
OUTBOX_DIR = ROOT_DIR / "outbox"


class ReviewState(TypedDict, total=False):
    source: dict
    namespace: str
    files: list[dict]
    options: dict
    plan: dict
    planner: str
    status: str
    findings: Annotated[list[dict], operator.add]
    agent_runs: Annotated[list[dict], operator.add]
    events: Annotated[list[dict], operator.add]
    errors: Annotated[list[str], operator.add]
    report: dict
    review: dict
    actions_log: Annotated[list[dict], operator.add]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def _event(node: str, detail: str, **extra) -> dict:
    return {"ts": time.time(), "node": node, "detail": detail, **extra}


# --------------------------------------------------------------------------- nodes

def intake(state: ReviewState) -> dict:
    s = get_settings()
    files, notes = [], []
    for raw in state.get("files", [])[: s.max_files]:
        content = raw.get("content", "")
        if "\x00" in content:
            notes.append(f"Skipped {raw.get('path')}: binary file.")
            continue
        if not content.strip():
            notes.append(f"Skipped {raw.get('path')}: empty file.")
            continue
        if len(content.encode()) > s.max_file_bytes:
            content = content.encode()[: s.max_file_bytes].decode(errors="ignore")
            notes.append(f"Truncated {raw.get('path')} to {s.max_file_bytes // 1000} KB.")
        path = raw.get("path") or "snippet.py"
        files.append(CodeFile(path=path, content=content, language=raw.get("language") or detect_language(path)).model_dump())
    if len(state.get("files", [])) > s.max_files:
        notes.append(f"Only the first {s.max_files} files are reviewed.")
    namespace = state.get("namespace") or state.get("source", {}).get("namespace") or "local/playground"
    if not files:
        return {"files": [], "status": "failed", "errors": ["No reviewable code was provided."] + notes,
                "events": [_event("intake", "Stopped: nothing to review")]}
    return {"files": files, "namespace": namespace, "status": "planning", "errors": notes,
            "events": [_event("intake", f"Accepted {len(files)} file(s) for {namespace}")]}


def plan_node(state: ReviewState) -> dict:
    files = [CodeFile(**f) for f in state["files"]]
    plan, planner = make_plan(files, get_settings())
    return {"plan": plan.model_dump(), "planner": planner, "status": "planned",
            "events": [_event("plan", f"Plan by {planner}: {', '.join(plan.agents)} · risk {plan.risk_level}")]}


def plan_review(state: ReviewState) -> dict:
    if not state.get("options", {}).get("require_plan_approval"):
        return {"events": [_event("plan_review", "Plan approval not required; continuing")]}
    answer = interrupt({"type": "plan_review", "plan": state["plan"], "planner": state.get("planner"),
                        "files": [f["path"] for f in state["files"]]})
    if not answer or not answer.get("approved"):
        return {"status": "cancelled", "events": [_event("plan_review", "Reviewer cancelled the run")]}
    plan = ReviewPlan(**{**state["plan"], **{k: v for k, v in answer.items() if k in {"agents", "focus_areas"}}})
    if not plan.agents:
        return {"status": "cancelled", "events": [_event("plan_review", "No agents selected; run cancelled")]}
    return {"plan": plan.model_dump(), "status": "reviewing",
            "events": [_event("plan_review", f"Reviewer approved plan: {', '.join(plan.agents)}")]}


def dispatch(state: ReviewState):
    if state.get("status") == "cancelled":
        return END
    return [Send("specialist", {"agent": a, "files": state["files"], "plan": state["plan"], "namespace": state["namespace"]})
            for a in state["plan"]["agents"]]


def specialist(payload: dict) -> dict:
    files = [CodeFile(**f) for f in payload["files"]]
    out = run_specialist(payload["agent"], files, payload["plan"], payload["namespace"], get_settings())
    run = out["run"]
    detail = f"{payload['agent']} agent: {len(out['findings'])} findings · {run['mode']} · {run['status']} · {run['duration_s']}s"
    return {"findings": [f.model_dump() for f in out["findings"]], "agent_runs": [run],
            "events": [_event("specialist", detail, agent=payload["agent"], status=run["status"])]}


def aggregate(state: ReviewState) -> dict:
    report = compile_report(state, get_settings())
    report["markdown"] = to_markdown(report)
    return {"report": report, "status": "awaiting_review",
            "events": [_event("aggregate", f"Report compiled: score {report['score']}, verdict {report['verdict']}, "
                                           f"{len(report['findings'])} findings, {len(report['suppressed'])} suppressed")]}


def human_review(state: ReviewState) -> dict:
    options = state.get("options", {})
    if options.get("auto_approve"):
        # Non interactive callers (MCP, evals) may only take local, reversible actions.
        actions = [a for a in options.get("auto_actions", []) if a in AUTONOMOUS_SAFE_ACTIONS]
        return {"review": {"decision": "approve", "actions": actions, "dismissed": {}, "reviewer": "auto",
                           "note": "Auto approved: read only run"},
                "events": [_event("human_review", "Auto approved (no external writes allowed)")]}
    report = state["report"]
    answer = interrupt({"type": "report_review", "report": report,
                        "available_actions": sorted(WRITE_ACTIONS),
                        "can_post": state.get("source", {}).get("kind") == "pr"})
    answer = answer or {"decision": "reject"}
    return {"review": answer, "events": [_event("human_review", f"Reviewer decision: {answer.get('decision')}")]}


def execute_actions(state: ReviewState) -> dict:
    review = state.get("review", {})
    report = dict(state["report"])
    log: list[dict] = []
    if review.get("decision") != "approve":
        return {"status": "rejected", "actions_log": [{"action": "none", "status": "skipped",
                                                       "detail": "Reviewer rejected the report. Nothing was written."}],
                "events": [_event("execute_actions", "No actions: report rejected")]}

    dismissed: dict[str, str] = review.get("dismissed", {})
    if dismissed:
        report["dismissed"] = [dict(f, dismiss_reason=dismissed[f["id"]]) for f in report["findings"] if f["id"] in dismissed]
        report["findings"] = [f for f in report["findings"] if f["id"] not in dismissed]
        from codesentinel.agents.orchestrator import score_and_verdict
        from codesentinel.models import Finding
        report["score"], report["verdict"], report["counts"] = score_and_verdict([Finding(**f) for f in report["findings"]])
        report["summary"] += (f"\n\nThe reviewer dismissed {len(dismissed)} finding(s) as false positives; "
                              f"{len(report['findings'])} remain.")
    report["approved_by"] = review.get("reviewer") or "a human reviewer"
    if review.get("note") and review.get("reviewer") != "auto":
        report["summary"] = f"{report['summary']}\n\nReviewer note ({review.get('reviewer') or 'reviewer'}): {review['note']}"
    report["markdown"] = to_markdown(report)
    key = content_hash(report["namespace"], report["source"], report["markdown"])[:16]
    memory = get_memory()

    for action in review.get("actions", []):
        try:
            if action == "save_report":
                folder = REPORTS_DIR / re.sub(r"[^\w.-]+", "_", report["namespace"])
                folder.mkdir(parents=True, exist_ok=True)
                stem = f"{datetime.now():%Y%m%d_%H%M%S}_{key[:8]}"
                (folder / f"{stem}.md").write_text(report["markdown"], encoding="utf-8")
                (folder / f"{stem}.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
                log.append({"action": action, "status": "done", "detail": _rel(folder / f"{stem}.md")})
            elif action == "post_github":
                if report["counts"]["critical"] and not review.get("acknowledge_critical"):
                    log.append({"action": action, "status": "blocked",
                                "detail": "Critical findings were not acknowledged, so nothing was posted."})
                    continue
                src = state.get("source", {})
                if src.get("kind") == "pr" and get_settings().github_token:
                    res = post_pr_comment(src["owner"], src["repo"], src["number"], report["markdown"], key)
                    log.append({"action": action, "status": res["status"], "detail": res.get("url") or res.get("detail")})
                else:
                    OUTBOX_DIR.mkdir(exist_ok=True)
                    path = OUTBOX_DIR / f"pr_comment_{key[:8]}.md"
                    path.write_text(report["markdown"], encoding="utf-8")
                    why = "no GITHUB_TOKEN set" if src.get("kind") == "pr" else "source is not a pull request"
                    log.append({"action": action, "status": "outbox",
                                "detail": f"Saved to {_rel(path)} instead of posting ({why})."})
            elif action == "remember_feedback":
                for f in report.get("dismissed", []):
                    memory.add(report["namespace"], "dismissal",
                               f"{f['rule_id']} in {f['file']} is a false positive: {f['dismiss_reason'] or 'no reason given'}",
                               {"rule_id": f["rule_id"], "file_pattern": f["file"], "evidence": f.get("evidence", ""),
                                "reason": f["dismiss_reason"]})
                memory.add(report["namespace"], "review",
                           f"Review of {report['source'].get('label', 'code')}: score {report['score']}, verdict "
                           f"{report['verdict']}, {sum(report['counts'].values())} findings.",
                           {"score": report["score"], "verdict": report["verdict"], "counts": report["counts"]})
                log.append({"action": action, "status": "done",
                            "detail": f"Stored {len(report.get('dismissed', []))} dismissal(s) and the review summary."})
        except GitHubError as exc:
            log.append({"action": action, "status": "failed", "detail": str(exc)})
        except Exception as exc:  # noqa: BLE001  one failed write must not undo the others
            log.append({"action": action, "status": "failed", "detail": f"{type(exc).__name__}: {exc}"})
    if not log:
        log.append({"action": "none", "status": "done", "detail": "Approved with no write actions selected."})
    return {"report": report, "status": "completed", "actions_log": log,
            "events": [_event("execute_actions", "; ".join(f"{l['action']}: {l['status']}" for l in log))]}


# --------------------------------------------------------------------------- build

def build_graph(checkpointer: Any | None = None):
    g = StateGraph(ReviewState)
    g.add_node("intake", intake)
    g.add_node("plan", plan_node)
    g.add_node("plan_review", plan_review)
    g.add_node("specialist", specialist)
    g.add_node("aggregate", aggregate)
    g.add_node("human_review", human_review)
    g.add_node("execute_actions", execute_actions)
    g.add_edge(START, "intake")
    g.add_conditional_edges("intake", lambda s: "plan" if s.get("files") else END, ["plan", END])
    g.add_edge("plan", "plan_review")
    g.add_conditional_edges("plan_review", dispatch, ["specialist", END])
    g.add_edge("specialist", "aggregate")
    g.add_edge("aggregate", "human_review")
    g.add_edge("human_review", "execute_actions")
    g.add_edge("execute_actions", END)
    return g.compile(checkpointer=checkpointer or InMemorySaver())


def sqlite_checkpointer(path: Path | None = None):
    from langgraph.checkpoint.sqlite import SqliteSaver

    conn = sqlite3.connect(str(path or DATA_DIR / "checkpoints.sqlite"), check_same_thread=False)
    return SqliteSaver(conn)


def review_once(files: list[dict], source: dict | None = None, namespace: str | None = None,
                save: bool = False) -> dict:
    """Run a full review without human interaction (used by MCP and evals). Read only."""
    graph = build_graph()
    config = {"configurable": {"thread_id": content_hash(time.time(), files)[:12]}}
    state = graph.invoke({"files": files, "source": source or {"label": "pasted code"}, "namespace": namespace,
                          "options": {"auto_approve": True, "auto_actions": ["save_report"] if save else []}}, config)
    return state
