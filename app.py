"""CodeSentinel Streamlit app.

Run:  uv run streamlit run app.py
"""

from __future__ import annotations

import html
import json
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from langgraph.types import Command

from codesentinel import ui_style as ui
from codesentinel.cache import get_cache
from codesentinel.config import get_settings, provider_label
from codesentinel.graph import build_graph, sqlite_checkpointer
from codesentinel.memory import get_memory
from codesentinel.models import AGENT_TITLES
from codesentinel.tools.github_tools import GitHubError, fetch_files, parse_source_url

ROOT = Path(__file__).resolve().parent
REPO_URL = "https://github.com/balum211/BalaWeek3Project"
SAMPLES = {
    "Loyalty portal API (Flask)": "flask_user_api",
    "Inventory sync pipeline": "inventory_pipeline",
    "Checkout refunds with tests": "payments_service",
}
NODE_LABELS = {
    "intake": ("ph-tray-arrow-down", "Intake checked the files"),
    "plan": ("ph-strategy", "Orchestrator wrote the review plan"),
    "plan_review": ("ph-user-check", "Plan approval step"),
    "specialist": ("ph-robot", "Specialist agent finished"),
    "aggregate": ("ph-stack", "Orchestrator compiled the report"),
    "human_review": ("ph-hand", "Human review step"),
    "execute_actions": ("ph-lightning", "Approved actions ran"),
}
FAQ = [
    ("Does it change my code or post anything on its own?",
     "No. The agents only read. Saving the report, posting a pull request comment and updating team memory each run only after "
     "you approve them in the review step, and critical findings need an explicit acknowledgement first."),
    ("What happens if the language model fails or is slow?",
     "Each call retries with a timeout, then switches to the backup provider, then repairs malformed output. If all of that fails "
     "the agent falls back to its rule based checks, the review still completes, and the Monitor tab flags the fallback."),
    ("How do I know a finding is real?",
     "Every finding quotes the exact line it refers to. Model findings whose quoted code is not in the file are dropped, and the "
     "count of dropped findings is shown on the Monitor tab."),
    ("What does it remember between reviews?",
     "Per project: coding conventions you add, findings you dismissed as false positives (suppressed automatically next time), "
     "and the score of each approved review for trend lines."),
    ("Which languages does it support?",
     "Python gets full syntax tree analysis. JavaScript, TypeScript, Java, Go, Ruby, PHP and C# get pattern based security checks, "
     "and the model agents read any language."),
    ("Can other tools or agents use it?",
     "Yes. The same graph runs as an MCP server for Claude Desktop, Claude Code or Cursor, and an A2A agent card describes its "
     "skills. Those callers get read only reviews."),
]

st.set_page_config(page_title="CodeSentinel · multi agent code review", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="auto")
st.markdown(ui.CSS, unsafe_allow_html=True)
st.markdown(ui.BACKGROUND, unsafe_allow_html=True)


@st.cache_resource
def get_graph():
    return build_graph(sqlite_checkpointer())


graph = get_graph()
settings = get_settings()
memory = get_memory()
mode_label = "LLM agents on" if settings.llm_enabled else "Rule based mode"


# ------------------------------------------------------------------ session state
def thread_config() -> dict:
    return {"configurable": {"thread_id": st.session_state.thread_id}}


if "thread_id" not in st.session_state:
    st.session_state.thread_id = st.query_params.get("thread") or ""


def new_thread() -> None:
    st.session_state.thread_id = uuid.uuid4().hex[:12]
    st.query_params["thread"] = st.session_state.thread_id


def reset_thread() -> None:
    st.session_state.thread_id = ""
    st.query_params.clear()


def snapshot():
    if not st.session_state.thread_id:
        return None
    snap = graph.get_state(thread_config())
    return snap if snap and snap.values else None


def pending_interrupt(snap) -> dict | None:
    if not snap or not snap.next:
        return None
    for task in snap.tasks:
        for intr in task.interrupts:
            return intr.value
    return None


def run_stream(payload) -> None:
    """Stream graph updates into a live timeline with a skeleton report underneath."""
    steps = st.empty()
    skeleton = st.empty()
    skeleton.markdown(ui.SKELETON, unsafe_allow_html=True)
    rows: list[str] = []
    try:
        for update in graph.stream(payload, thread_config(), stream_mode="updates"):
            for node, out in update.items():
                if node == "__interrupt__":
                    rows.append('<div class="cs-step"><i class="ph ph-pause-circle"></i><b>Paused for your review</b></div>')
                    continue
                icon, label = NODE_LABELS.get(node, ("ph-dot", node))
                detail = html.escape(out["events"][-1]["detail"]) if isinstance(out, dict) and out.get("events") else ""
                rows.append(f'<div class="cs-step"><i class="ph {icon}"></i><span><b>{label}</b>'
                            f'<span class="body-6"> · {detail}</span></span></div>')
                steps.markdown('<div class="cs-timeline">' + "".join(rows) + "</div>", unsafe_allow_html=True)
    except Exception as exc:  # noqa: BLE001  surface the failure inline, keep the checkpoint
        skeleton.empty()
        st.error(f"The review stopped: {type(exc).__name__}: {exc}. Your progress is saved; press resume to retry.")
        return
    skeleton.empty()
    st.rerun()


# ------------------------------------------------------------------ sidebar (system status)
with st.sidebar:
    st.markdown(ui.brand(), unsafe_allow_html=True)
    st.markdown(f'<span class="cs-chip {"ok" if settings.llm_enabled else "warn"}"><i class="ph-fill ph-circle"></i>'
                f'{html.escape(mode_label)}</span>', unsafe_allow_html=True)
    rows = [("ph-cpu", "Model", provider_label(settings.provider))]
    if settings.fallback_provider:
        rows.append(("ph-arrows-clockwise", "Fallback model", provider_label(settings.fallback_provider)))
    rows += [("ph-brain", "Memory", memory.backend),
             ("ph-github-logo", "GitHub posting", "Token found" if settings.github_token else "No token, comments go to the outbox folder"),
             ("ph-database", "Checkpoints", "SQLite, one thread per review")]
    if st.session_state.thread_id:
        rows.append(("ph-git-branch", "Current thread", st.session_state.thread_id))
    st.markdown(ui.side_status(rows), unsafe_allow_html=True)
    st.markdown(ui.side_links(REPO_URL), unsafe_allow_html=True)


# ------------------------------------------------------------------ landing
st.markdown(ui.nav(mode_label, settings.llm_enabled), unsafe_allow_html=True)
st.markdown(ui.hero(), unsafe_allow_html=True)
st.markdown(ui.how_it_works(), unsafe_allow_html=True)
st.markdown(ui.section_head("workspace", "ph-terminal-window", "Workspace", "Run a review",
                            "Pick a sample, paste code, upload files or link a public GitHub pull request."),
            unsafe_allow_html=True)


# ------------------------------------------------------------------ review helpers
def collect_input() -> tuple[list[dict], dict] | None:
    mode = st.segmented_control("Source", ["Sample code", "Paste code", "Upload files", "GitHub link"],
                                default="Sample code", label_visibility="collapsed")
    files: list[dict] = []
    source: dict = {}
    if mode == "Sample code":
        choice = st.selectbox("Sample", list(SAMPLES))
        folder = ROOT / "samples" / SAMPLES[choice]
        files = [{"path": p.name, "content": p.read_text(encoding="utf-8")} for p in sorted(folder.glob("*.py"))]
        source = {"kind": "sample", "label": f"Sample: {choice}", "namespace": f"samples/{SAMPLES[choice]}"}
        with st.expander(f"Preview {len(files)} file(s)"):
            for f in files:
                st.caption(f["path"])
                st.code(f["content"], language="python", line_numbers=True)
    elif mode == "Paste code":
        name = st.text_input("File name", value="snippet.py")
        code = st.text_area("Code", height=280, placeholder="Paste a function, a module or a diff")
        if code.strip():
            files = [{"path": name or "snippet.py", "content": code}]
        source = {"kind": "paste", "label": f"Pasted code ({name})", "namespace": "local/playground"}
    elif mode == "Upload files":
        uploads = st.file_uploader("Source files", accept_multiple_files=True,
                                   type=["py", "js", "jsx", "ts", "tsx", "java", "go", "rb", "php", "cs"])
        for u in uploads or []:
            files.append({"path": u.name, "content": u.getvalue().decode("utf-8", errors="replace")})
        source = {"kind": "upload", "label": f"Uploaded files ({len(files)})", "namespace": "local/playground"}
    else:
        url = st.text_input("Pull request or file link", placeholder="https://github.com/owner/repo/pull/123")
        st.caption("Try https://github.com/we45/Vulnerable-Flask-App/blob/master/app/app.py")
        if url.strip():
            try:
                parse_source_url(url)
                source = {"kind": "github_pending", "url": url.strip()}
            except GitHubError as exc:
                st.error(str(exc))
    if not files and source.get("kind") != "github_pending":
        return None
    return files, source


def start_review(files: list[dict], source: dict, require_plan: bool, namespace_input: str) -> None:
    if source.get("kind") == "github_pending":
        try:
            gh_files, meta = fetch_files(source["url"], settings.max_files)
        except GitHubError as exc:
            st.error(f"{exc}")
            return
        files = [f.model_dump() for f in gh_files]
        label = f"{meta['namespace']} PR #{meta['number']}: {meta.get('title', '')}" if meta["kind"] == "pr" else \
            f"{meta['namespace']}: {meta['path']}"
        source = {**meta, "label": label, "url": source["url"]}
        source.pop("changed_lines", None)
    new_thread()
    namespace = namespace_input.strip() or source.get("namespace") or "local/playground"
    run_stream({"files": files, "source": source, "namespace": namespace,
                "options": {"require_plan_approval": require_plan}})


def render_finding(f: dict, review_mode: bool) -> tuple[bool, str]:
    st.markdown(ui.finding_card(f, AGENT_TITLES[f["agent"]]), unsafe_allow_html=True)
    dismissed, reason = False, ""
    with st.expander("Fix, suggested test" + (" and dismiss" if review_mode else "")):
        st.markdown(f"**Fix.** {f['recommendation']}")
        if f.get("suggested_test"):
            st.markdown("**Suggested test**")
            st.code(f["suggested_test"], language="python")
        if review_mode:
            dismissed = st.checkbox("Dismiss as a false positive", key=f"dis_{f['id']}")
            if dismissed:
                reason = st.text_input("Reason (saved to team memory if you choose to remember feedback)",
                                       key=f"why_{f['id']}", placeholder="For example: this endpoint is internal only")
    return dismissed, reason


def render_report_body(report: dict, review_mode: bool) -> dict[str, str]:
    st.markdown(ui.scoreboard(report), unsafe_allow_html=True)
    st.markdown(ui.agent_cards(report.get("agent_runs", []), AGENT_TITLES), unsafe_allow_html=True)
    st.markdown(f'<div class="cs-card" style="margin-top:12px"><div class="caption-3">Summary</div>'
                f'<div class="body-3" style="margin-top:8px;color:var(--text)">'
                f'{html.escape(report["summary"]).replace(chr(10), "<br>")}</div></div>', unsafe_allow_html=True)
    for e in report.get("escalations", []):
        st.markdown(f'<div class="cs-callout" style="margin-top:12px"><i class="ph ph-siren"></i>{html.escape(e)}</div>',
                    unsafe_allow_html=True)
    st.markdown('<div class="heading-6" style="margin:32px 0 8px 0">Findings, highest priority first</div>', unsafe_allow_html=True)
    agent_filter = st.pills("Agent", list(AGENT_TITLES), selection_mode="multi", default=list(AGENT_TITLES),
                            format_func=lambda a: AGENT_TITLES[a], key=f"pills_{review_mode}", label_visibility="collapsed")
    dismissed: dict[str, str] = {}
    shown = [f for f in report["findings"] if f["agent"] in (agent_filter or [])]
    if not shown:
        st.markdown(ui.empty("ph-sparkle", "No findings here", "Nothing to fix for the selected agents."), unsafe_allow_html=True)
    for f in shown:
        is_dismissed, reason = render_finding(f, review_mode)
        if is_dismissed:
            dismissed[f["id"]] = reason
    if report.get("suppressed"):
        with st.expander(f"{len(report['suppressed'])} finding(s) suppressed by team memory"):
            for s in report["suppressed"]:
                st.markdown(f"- `{s['file']}:{s['line']}` {s['title']} ({s['rule_id']}): {s['suppressed_reason']}")
    return dismissed


# ------------------------------------------------------------------ workspace
tab_review, tab_memory, tab_monitor, tab_arch = st.tabs(["Review", "Team memory", "Monitor", "Architecture"])
snap = snapshot()

def pipeline_state(snap, intr) -> str | None:
    """Light up the pipeline strip from the checkpoint: what ran, what waits on you, what was skipped."""
    if snap is None:
        return None
    v = snap.values
    agents = set(AGENT_TITLES)
    ran = {r["agent"] for r in v.get("agent_runs", [])}
    if intr and intr["type"] == "plan_review":
        return ui.pipeline({"intake", "plan"}, "gate1")
    if intr and intr["type"] == "report_review":
        return ui.pipeline({"intake", "plan", "gate1", "aggregate"} | ran, "gate2", agents - ran)
    status = v.get("status")
    if status == "cancelled":
        return ui.pipeline({"intake", "plan"}, None, agents | {"gate1", "aggregate", "gate2", "actions"})
    if snap.next or status == "failed" or not v.get("report"):
        return None
    skipped = (agents - ran) | ({"actions"} if status != "completed" else set())
    return ui.pipeline(({"intake", "plan", "gate1", "aggregate", "gate2", "actions"} | ran) - skipped, None, skipped)


with tab_review:
    intr = pending_interrupt(snap)
    strip = pipeline_state(snap, intr)
    if strip:
        st.markdown(strip, unsafe_allow_html=True)

    if snap is None:
        c1, c2 = st.columns([1, 1.4])
        require_plan = c1.toggle("Pause for plan approval", value=True,
                                 help="Human in the loop checkpoint 1: approve or edit the plan before agents run.")
        namespace_input = c2.text_input("Project memory namespace", value="", label_visibility="collapsed",
                                        placeholder="Memory namespace (optional, detected from the source)")
        picked = collect_input()
        if picked is None:
            st.markdown(ui.empty("ph-code", "Add some code to begin",
                                 "Pick a sample, paste code, upload files or link a GitHub pull request."), unsafe_allow_html=True)
        if st.button("Run review", type="primary", disabled=picked is None, icon=":material/play_arrow:"):
            start_review(*picked, require_plan, namespace_input)

    elif intr and intr["type"] == "plan_review":
        plan = intr["plan"]
        st.markdown(f'<div class="cs-card"><div class="caption-3">Step 1 of 2 · Approve the plan</div>'
                    f'<div class="heading-6" style="margin-top:8px"><i class="ph ph-strategy" style="color:var(--accent)"></i> '
                    f'Risk {plan["risk_level"]} · planned by {html.escape(str(intr.get("planner")))}</div>'
                    f'<div class="body-6" style="margin-top:4px">{html.escape(plan["rationale"])}</div>'
                    f'<div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:12px">'
                    + "".join(f'<span class="cs-chip"><i class="ph ph-file-code"></i>{html.escape(p)}</span>' for p in intr["files"])
                    + "</div></div>", unsafe_allow_html=True)
        agents = st.multiselect("Agents to run", list(AGENT_TITLES), default=plan["agents"], format_func=lambda a: AGENT_TITLES[a])
        focus = st.text_area("Focus areas, one per line", value="\n".join(plan.get("focus_areas", [])), height=120)
        c1, c2, _ = st.columns([1, 1, 4])
        if c1.button("Approve plan", type="primary", disabled=not agents, icon=":material/check:"):
            run_stream(Command(resume={"approved": True, "agents": agents,
                                       "focus_areas": [x.strip() for x in focus.splitlines() if x.strip()]}))
        if c2.button("Cancel run"):
            run_stream(Command(resume={"approved": False}))

    elif intr and intr["type"] == "report_review":
        report = intr["report"]
        st.markdown('<div class="caption-3" style="margin-bottom:12px">Step 2 of 2 · Review the report</div>', unsafe_allow_html=True)
        dismissed = render_report_body(report, review_mode=True)
        st.markdown('<div class="cs-card" style="margin-top:32px"><div class="heading-6">'
                    '<i class="ph ph-lock-key" style="color:var(--accent)"></i> Approve actions</div>'
                    '<div class="body-6" style="margin-top:4px">These are the only steps that change anything. '
                    'Each one runs only if you tick it.</div></div>', unsafe_allow_html=True)
        a1 = st.checkbox("Save the report to the reports folder", value=True)
        post_label = "Post the report as a pull request comment" if intr.get("can_post") else \
            "Write the pull request comment to the outbox folder (source is not a pull request)"
        a2 = st.checkbox(post_label, value=False)
        a3 = st.checkbox("Remember my feedback (dismissed findings and the review score) in team memory", value=True)
        ack = True
        if report["counts"]["critical"]:
            ack = st.checkbox(f"I have read the {report['counts']['critical']} critical finding(s) and accept "
                              "responsibility for sharing them", value=False)
        c1, c2 = st.columns(2)
        reviewer = c1.text_input("Your name", value="", placeholder="Shown on the report")
        note = c2.text_input("Note for the author (optional)")
        b1, b2, _ = st.columns([1.4, 1, 3])
        if b1.button("Approve and run actions", type="primary", icon=":material/task_alt:"):
            actions = [a for a, on in (("save_report", a1), ("post_github", a2), ("remember_feedback", a3)) if on]
            run_stream(Command(resume={"decision": "approve", "actions": actions, "dismissed": dismissed,
                                       "acknowledge_critical": ack, "reviewer": reviewer, "note": note}))
        if b2.button("Reject report"):
            run_stream(Command(resume={"decision": "reject"}))

    elif snap.next:
        st.warning("This review was interrupted before it finished. Its state is saved in the checkpoint.")
        if st.button("Resume review", type="primary"):
            run_stream(None)

    else:
        values = snap.values
        if values.get("status") == "failed":
            st.error(" ".join(values.get("errors", [])) or "The review could not start.")
        elif values.get("status") == "cancelled":
            st.info("The run was cancelled at the plan step. No agents ran and nothing was written.")
        else:
            report = values["report"]
            status = values.get("status")
            icon_map = {"done": "ph-check-circle", "posted": "ph-check-circle", "outbox": "ph-tray", "skipped": "ph-minus-circle",
                        "blocked": "ph-prohibit", "failed": "ph-x-circle"}
            log_rows = "".join(f'<div class="cs-step"><i class="ph {icon_map.get(i["status"], "ph-dot")}"></i><span><b>{i["action"]}</b>'
                               f'<span class="body-6"> · {i["status"]} · {html.escape(str(i["detail"]))}</span></span></div>'
                               for i in values.get("actions_log", []))
            st.markdown(f'<div class="caption-3" style="margin-bottom:8px">{"Review complete" if status == "completed" else "Report rejected"}'
                        f'</div><div class="cs-timeline" style="margin-bottom:16px">{log_rows}</div>', unsafe_allow_html=True)
            render_report_body(report, review_mode=False)
            d1, d2, _ = st.columns([1, 1, 3])
            d1.download_button("Download Markdown", report["markdown"], file_name="codesentinel_report.md", icon=":material/download:")
            d2.download_button("Download JSON", json.dumps(report, indent=2, default=str), file_name="codesentinel_report.json")
        if values.get("errors"):
            with st.expander("Intake notes"):
                for err in values["errors"]:
                    st.markdown(f"- {err}")
        if st.button("Start a new review", icon=":material/restart_alt:"):
            reset_thread()
            st.rerun()


# ------------------------------------------------------------------ memory tab
with tab_memory:
    st.markdown('<div class="body-6" style="margin-bottom:16px">Long term memory scoped per project. Conventions are injected into '
                'every agent prompt. Dismissals are enforced in code, so a false positive you dismiss stays dismissed.</div>',
                unsafe_allow_html=True)
    known = sorted(set(memory.namespaces()) | {"local/playground"} | {f"samples/{v}" for v in SAMPLES.values()})
    current_ns = (snap.values.get("namespace") if snap else None) or "local/playground"
    if current_ns not in known:
        known.append(current_ns)
    ns = st.selectbox("Namespace", known, index=known.index(current_ns))
    with st.form("add_convention", clear_on_submit=True):
        text = st.text_area("Add a team convention", placeholder="For example: money values must use Decimal, never float")
        if st.form_submit_button("Save convention"):
            if text.strip():
                memory.add(ns, "convention", text.strip(), {"author": "ui"})
                st.success(f"Convention saved to {ns}.")
            else:
                st.error("Write the convention before saving.")
    cols = st.columns(2)
    for col, kind, title, icon, empty_text in ((cols[0], "convention", "Conventions", "ph-book-open", "No conventions yet."),
                                               (cols[1], "dismissal", "Dismissed findings", "ph-eye-slash", "Nothing dismissed yet.")):
        with col:
            st.markdown(f'<div class="title-3" style="margin:16px 0 8px 0">{title}</div>', unsafe_allow_html=True)
            items = memory.list(ns, kind)
            if not items:
                st.markdown(ui.empty(icon, empty_text, ""), unsafe_allow_html=True)
            for m in items:
                c1, c2 = st.columns([6, 1])
                c1.markdown(f'<div class="cs-inner body-6">{html.escape(m["text"])}</div>', unsafe_allow_html=True)
                if c2.button("Delete", key=f"del_{m['id']}"):
                    memory.delete(m["id"])
                    st.rerun()
    st.markdown('<div class="title-3" style="margin:24px 0 8px 0">Review history</div>', unsafe_allow_html=True)
    hist = memory.review_history(ns)
    if hist:
        df = pd.DataFrame([{"reviewed": datetime.fromtimestamp(h["created"]), "score": h["metadata"].get("score"),
                            "verdict": h["metadata"].get("verdict")} for h in hist])
        st.line_chart(df, x="reviewed", y="score", height=220, color="#2DD4BF")
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.markdown('<div class="body-6">Approve a review with "Remember my feedback" to start the trend line.</div>',
                    unsafe_allow_html=True)


# ------------------------------------------------------------------ monitor tab (human on the loop)
with tab_monitor:
    st.markdown('<div class="body-6" style="margin-bottom:16px">Human on the loop view: what each agent did, how long it took, '
                'whether it fell back, and how much work the cache saved.</div>', unsafe_allow_html=True)
    stats = get_cache().stats()
    cards = []
    for ns_name, label in (("llm", "LLM response cache"), ("static", "Static result cache"), ("github", "GitHub tool cache")):
        s = stats.get(ns_name, {"hits": 0, "misses": 0, "hit_rate": 0.0, "entries": 0})
        cards.append(f'<div class="cs-stat"><div class="caption-3"><i class="ph ph-database"></i> {label}</div>'
                     f'<div class="num" style="margin-top:8px">{s["hit_rate"] * 100:.0f}%</div>'
                     f'<div class="caption-5">{s["hits"]} hits · {s["misses"]} misses · {s["entries"]} entries</div></div>')
    st.markdown(f'<div class="cs-grid-3" style="margin-top:0">{"".join(cards)}</div>', unsafe_allow_html=True)
    if st.button("Clear caches"):
        get_cache().clear()
        st.rerun()
    if snap is None:
        st.markdown(ui.empty("ph-pulse", "No run yet", "Start a review to see agent activity here."), unsafe_allow_html=True)
    else:
        v = snap.values
        runs = v.get("agent_runs", [])
        if runs:
            st.markdown('<div class="title-3" style="margin:24px 0 8px 0">Agent runs</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([{"agent": AGENT_TITLES[r["agent"]], "mode": r["mode"], "model": r.get("model") or "none",
                                        "status": r["status"], "tool calls": r.get("tool_calls", 0), "cache": r.get("cache"),
                                        "ungrounded dropped": r.get("ungrounded_dropped", 0), "seconds": r.get("duration_s"),
                                        "error": r.get("error") or ""} for r in runs]), hide_index=True, use_container_width=True)
            for r in [r for r in runs if r["status"] != "ok" or r.get("duration_s", 0) > settings.slow_agent_seconds]:
                st.markdown(f'<div class="cs-callout" style="margin-top:8px"><i class="ph ph-siren"></i>{AGENT_TITLES[r["agent"]]} '
                            f'status {r["status"]}: {html.escape(r.get("error") or "slow run")}</div>', unsafe_allow_html=True)
        ev = v.get("events", [])
        if ev:
            st.markdown('<div class="title-3" style="margin:24px 0 8px 0">Event timeline</div>', unsafe_allow_html=True)
            t0 = ev[0]["ts"]
            st.dataframe(pd.DataFrame([{"t plus seconds": round(e["ts"] - t0, 2), "node": e["node"], "detail": e["detail"]}
                                       for e in ev]), hide_index=True, use_container_width=True)


# ------------------------------------------------------------------ architecture tab
with tab_arch:
    img = ROOT / "docs" / "architecture.png"
    if img.exists():
        st.image(str(img), use_container_width=True)
    st.markdown("""
| Layer | What CodeSentinel does |
|---|---|
| Control flow | LangGraph `StateGraph`: intake, plan, plan approval, parallel specialists via `Send`, aggregate, human review, actions |
| Agents | Orchestrator plus three ReAct specialists built with `create_agent` (bugs, security, tests) |
| Tools | Read only: static checks, read code, list functions, search team memory, rule lookup, GitHub fetch. Write: save report, post PR comment, update memory |
| State | Typed graph state with reducers, checkpointed to SQLite per thread so reviews survive restarts |
| Memory | Per project conventions, enforced dismissals and score history (local SQLite, optional Mem0) |
| Human in the loop | `interrupt()` before agents run (plan) and before every write (report). Critical findings need explicit acknowledgement |
| Human on the loop | Monitor tab: agent status, fallbacks, durations, cache hit rates, escalations |
| Failure handling | Retries with backoff, model fallback, JSON repair, hallucination guard on line numbers, static fallback per agent |
| Caching | L1 prompt ordering, L2 LLM response cache, L3 tool result cache with TTLs |
| Interop | MCP server exposes the reviewer to Claude Desktop or any MCP host; an A2A agent card describes its skills |
""")
    with st.expander("Graph definition (Mermaid)"):
        st.code(graph.get_graph().draw_mermaid(), language="text")


# ------------------------------------------------------------------ closing sections
st.markdown(ui.tagline(), unsafe_allow_html=True)
st.markdown(ui.benefits(), unsafe_allow_html=True)
st.markdown(ui.section_head("faq", "ph-question", "FAQ", "Questions reviewers ask first"), unsafe_allow_html=True)
for q, a in FAQ:
    with st.expander(q):
        st.markdown(a)
st.markdown("""
<section class="cs-section cs-reveal" style="text-align:center">
  <h2 class="title" style="margin:0 auto 8px auto">Run your first review in under a minute</h2>
  <div class="body-3" style="margin:0 auto;max-width:680px">Start with a sample service, then try your own code or a public pull request.</div>
  <div class="cs-actions" style="justify-content:center"><a class="cs-btn primary" href="#workspace"><i class="ph ph-play"></i>Run a free review</a></div>
</section>""", unsafe_allow_html=True)
st.markdown(ui.footer(REPO_URL), unsafe_allow_html=True)
