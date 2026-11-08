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

from codesentinel.cache import get_cache
from codesentinel.config import get_settings, provider_label
from codesentinel.graph import build_graph, sqlite_checkpointer
from codesentinel.memory import get_memory
from codesentinel.models import AGENT_TITLES, detect_language
from codesentinel.tools.github_tools import GitHubError, fetch_files, parse_source_url
from codesentinel.ui_style import CSS, SKELETON, VERDICT_ICON, VERDICT_LABEL, badge, metric

ROOT = Path(__file__).resolve().parent
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

st.set_page_config(page_title="CodeSentinel · multi agent code review", page_icon="🛡️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def get_graph():
    return build_graph(sqlite_checkpointer())


graph = get_graph()
settings = get_settings()
memory = get_memory()


# ------------------------------------------------------------------ session state
def thread_config() -> dict:
    return {"configurable": {"thread_id": st.session_state.thread_id}}


if "thread_id" not in st.session_state:
    st.session_state.thread_id = st.query_params.get("thread") or ""


def new_thread() -> None:
    st.session_state.thread_id = uuid.uuid4().hex[:12]
    st.query_params["thread"] = st.session_state.thread_id


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
    """Stream graph updates into a live step list with a skeleton report underneath."""
    steps = st.empty()
    skeleton = st.empty()
    skeleton.markdown(SKELETON, unsafe_allow_html=True)
    rows: list[str] = []
    try:
        for update in graph.stream(payload, thread_config(), stream_mode="updates"):
            for node, out in update.items():
                if node == "__interrupt__":
                    rows.append('<div class="cs-step"><i class="ph ph-pause-circle"></i>Paused for your review</div>')
                    continue
                icon, label = NODE_LABELS.get(node, ("ph-dot", node))
                detail = ""
                if isinstance(out, dict) and out.get("events"):
                    detail = html.escape(out["events"][-1]["detail"])
                rows.append(f'<div class="cs-step"><i class="ph {icon}"></i><span><b>{label}</b>'
                            f'<span class="body-6"> · {detail}</span></span></div>')
                steps.markdown('<div class="cs-card">' + "".join(rows) + "</div>", unsafe_allow_html=True)
    except Exception as exc:  # noqa: BLE001  surface the failure inline, keep the checkpoint
        st.error(f"The review stopped: {type(exc).__name__}: {exc}. Your progress is saved; press resume to retry.")
        return
    finally:
        skeleton.empty()
    st.rerun()


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown('<div class="title-3"><i class="ph ph-shield-check"></i> CodeSentinel</div>'
                '<div class="body-6">LangGraph multi agent code review</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown(f'<div class="caption-4">Model</div><div class="body-6">{html.escape(provider_label(settings.provider))}</div>'
                + (f'<div class="caption-4" style="margin-top:8px">Fallback model</div><div class="body-6">'
                   f'{html.escape(provider_label(settings.fallback_provider))}</div>' if settings.fallback_provider else "")
                + f'<div class="caption-4" style="margin-top:8px">Memory</div><div class="body-6">{memory.backend}</div>'
                + f'<div class="caption-4" style="margin-top:8px">GitHub posting</div><div class="body-6">'
                  f'{"Token found" if settings.github_token else "No token, comments go to the outbox folder"}</div>',
                unsafe_allow_html=True)
    st.divider()
    require_plan = st.toggle("Pause for plan approval", value=True,
                             help="Human in the loop checkpoint 1: approve or edit the orchestrator plan before agents run.")
    namespace_input = st.text_input("Project memory namespace", value="",
                                    placeholder="Detected from the GitHub link, or local/playground",
                                    help="Team conventions, dismissed findings and review history are stored per namespace.")
    if st.button("Start a new review", use_container_width=True):
        st.session_state.thread_id = ""
        st.query_params.clear()
        st.rerun()
    if st.session_state.thread_id:
        st.markdown(f'<div class="caption-4">Thread {st.session_state.thread_id} · checkpointed in SQLite</div>',
                    unsafe_allow_html=True)


# ------------------------------------------------------------------ hero
st.markdown("""
<div class="cs-hero">
  <span class="cs-eyebrow"><i class="ph ph-shield-check"></i>Week 3 project · Code review agent</span>
  <div class="cs-h1">Three specialist agents<br>review your code.<br>You approve what ships.</div>
  <div class="cs-sub">A bug agent, a security agent and a test coverage agent work in parallel. An orchestrator ranks
  their findings, and nothing is posted or remembered until you approve it.</div>
</div>
""", unsafe_allow_html=True)

tab_review, tab_memory, tab_monitor, tab_how = st.tabs(["Review", "Team memory", "Monitor", "How it works"])


# ------------------------------------------------------------------ review tab helpers
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
        if url.strip():
            try:
                parse_source_url(url)
                source = {"kind": "github_pending", "url": url.strip()}
            except GitHubError as exc:
                st.error(str(exc))
    if not files and source.get("kind") != "github_pending":
        return None
    return files, source


def start_review(files: list[dict], source: dict) -> None:
    if source.get("kind") == "github_pending":
        try:
            with st.spinner("Fetching files from GitHub"):
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


def render_metrics(report: dict) -> None:
    c = report["counts"]
    cols = st.columns(4)
    v = report["verdict"]
    prev = report.get("previous_score")
    delta = f' <span class="caption-4">was {prev}</span>' if prev is not None else ""
    cols[0].markdown(metric("Quality score", f"{report['score']}{delta}", "ph-gauge"), unsafe_allow_html=True)
    cols[1].markdown(metric("Verdict", VERDICT_LABEL[v], VERDICT_ICON[v], f"verdict-{v}"), unsafe_allow_html=True)
    cols[2].markdown(metric("Critical and high", f"{c['critical']} · {c['high']}", "ph-warning-octagon"), unsafe_allow_html=True)
    cols[3].markdown(metric("All findings", str(len(report["findings"])), "ph-list-checks"), unsafe_allow_html=True)


def render_finding(f: dict, review_mode: bool) -> tuple[bool, str]:
    head = f"{f['severity'].upper()} · {f['title']} · {f['file']}:{f['line']}"
    dismissed, reason = False, ""
    with st.expander(head, expanded=f["severity"] in {"critical"} and review_mode):
        st.markdown(f"{badge(f['severity'])} &nbsp; <span class='caption-4'>{AGENT_TITLES[f['agent']]} · rule {f['rule_id']}"
                    f"{' · ' + f['cwe'] if f.get('cwe') else ''} · source {f['source']} · confidence {f['confidence']:.2f}</span>",
                    unsafe_allow_html=True)
        if f.get("evidence"):
            st.code(f["evidence"], language="python")
        st.markdown(f"**Why it matters.** {f['explanation']}")
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
    render_metrics(report)
    st.markdown(f'<div class="cs-card" style="margin-top:16px"><div class="title-3">Summary</div>'
                f'<div class="body-6" style="margin-top:4px">{html.escape(report["summary"]).replace(chr(10), "<br>")}</div></div>',
                unsafe_allow_html=True)
    for e in report.get("escalations", []):
        st.markdown(f'<div class="cs-callout" style="margin-top:12px"><i class="ph ph-siren"></i>{html.escape(e)}</div>',
                    unsafe_allow_html=True)
    st.markdown("#### Findings, highest priority first")
    agent_filter = st.pills("Agent", list(AGENT_TITLES), selection_mode="multi", default=list(AGENT_TITLES),
                            format_func=lambda a: AGENT_TITLES[a], key=f"pills_{review_mode}")
    dismissed: dict[str, str] = {}
    shown = [f for f in report["findings"] if f["agent"] in (agent_filter or [])]
    if not shown:
        st.markdown('<div class="cs-empty"><i class="ph ph-sparkle"></i><div class="title-3">No findings here</div>'
                    '<div class="body-6">Nothing to fix for the selected agents.</div></div>', unsafe_allow_html=True)
    for f in shown:
        is_dismissed, reason = render_finding(f, review_mode)
        if is_dismissed:
            dismissed[f["id"]] = reason
    if report.get("suppressed"):
        with st.expander(f"{len(report['suppressed'])} finding(s) suppressed by team memory"):
            for s in report["suppressed"]:
                st.markdown(f"- `{s['file']}:{s['line']}` {s['title']} ({s['rule_id']}): {s['suppressed_reason']}")
    return dismissed


# ------------------------------------------------------------------ review tab
with tab_review:
    snap = snapshot()
    intr = pending_interrupt(snap)

    if snap is None:
        st.markdown("#### Choose code to review")
        picked = collect_input()
        if picked is None:
            st.markdown('<div class="cs-empty"><i class="ph ph-code"></i><div class="title-3">Add some code to begin</div>'
                        '<div class="body-6">Pick a sample, paste code, upload files or link a GitHub pull request.</div></div>',
                        unsafe_allow_html=True)
        if st.button("Run review", type="primary", disabled=picked is None):
            start_review(*picked)

    elif intr and intr["type"] == "plan_review":
        plan = intr["plan"]
        st.markdown("#### Approve the review plan")
        st.markdown(f'<div class="cs-card"><div class="title-3"><i class="ph ph-strategy"></i> Plan from {html.escape(str(intr.get("planner")))}'
                    f' · risk {plan["risk_level"]}</div><div class="body-6" style="margin-top:4px">{html.escape(plan["rationale"])}</div>'
                    f'<div class="caption-4" style="margin-top:8px">Files: {html.escape(", ".join(intr["files"]))}</div></div>',
                    unsafe_allow_html=True)
        agents = st.multiselect("Agents to run", list(AGENT_TITLES), default=plan["agents"], format_func=lambda a: AGENT_TITLES[a])
        focus = st.text_area("Focus areas, one per line", value="\n".join(plan.get("focus_areas", [])), height=120)
        c1, c2, _ = st.columns([1, 1, 4])
        if c1.button("Approve plan", type="primary", disabled=not agents):
            run_stream(Command(resume={"approved": True, "agents": agents,
                                       "focus_areas": [x.strip() for x in focus.splitlines() if x.strip()]}))
        if c2.button("Cancel run"):
            run_stream(Command(resume={"approved": False}))

    elif intr and intr["type"] == "report_review":
        report = intr["report"]
        st.markdown(f"#### Review the report · {html.escape(report['source'].get('label', ''))}")
        dismissed = render_report_body(report, review_mode=True)
        st.markdown("#### Approve actions")
        st.markdown('<div class="body-6">These are the only steps that change anything. Each one runs only if you tick it.</div>',
                    unsafe_allow_html=True)
        a1 = st.checkbox("Save the report to the reports folder", value=True)
        post_label = "Post the report as a pull request comment" if intr.get("can_post") else \
            "Write the pull request comment to the outbox folder (source is not a pull request)"
        a2 = st.checkbox(post_label, value=False)
        a3 = st.checkbox("Remember my feedback (dismissed findings and the review score) in team memory", value=True)
        ack = True
        if report["counts"]["critical"]:
            ack = st.checkbox(f"I have read the {report['counts']['critical']} critical finding(s) and accept responsibility for sharing them",
                              value=False)
        reviewer = st.text_input("Your name", value="", placeholder="Shown on the report")
        note = st.text_input("Note for the author (optional)")
        c1, c2, _ = st.columns([1.4, 1, 3])
        if c1.button("Approve and run actions", type="primary"):
            actions = [a for a, on in (("save_report", a1), ("post_github", a2), ("remember_feedback", a3)) if on]
            run_stream(Command(resume={"decision": "approve", "actions": actions, "dismissed": dismissed,
                                       "acknowledge_critical": ack, "reviewer": reviewer, "note": note}))
        if c2.button("Reject report"):
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
            st.markdown(f"#### {'Review complete' if status == 'completed' else 'Report rejected'} · "
                        f"{html.escape(report['source'].get('label', ''))}")
            for item in values.get("actions_log", []):
                icon = {"done": "ph-check-circle", "posted": "ph-check-circle", "outbox": "ph-tray", "skipped": "ph-minus-circle",
                        "blocked": "ph-prohibit", "failed": "ph-x-circle"}.get(item["status"], "ph-dot")
                st.markdown(f'<div class="cs-step"><i class="ph {icon}"></i><b>{item["action"]}</b>'
                            f'<span class="body-6"> · {item["status"]} · {html.escape(str(item["detail"]))}</span></div>',
                            unsafe_allow_html=True)
            render_report_body(report, review_mode=False)
            d1, d2, _ = st.columns([1, 1, 3])
            d1.download_button("Download Markdown", report["markdown"], file_name="codesentinel_report.md")
            d2.download_button("Download JSON", json.dumps(report, indent=2, default=str), file_name="codesentinel_report.json")
        if values.get("errors"):
            with st.expander("Intake notes"):
                for e in values["errors"]:
                    st.markdown(f"- {e}")


# ------------------------------------------------------------------ memory tab
with tab_memory:
    st.markdown("#### Team memory")
    st.markdown('<div class="body-6">Long term memory scoped per project. Conventions are injected into every agent prompt. '
                'Dismissals are enforced in code, so a false positive you dismiss stays dismissed.</div>', unsafe_allow_html=True)
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
    with cols[0]:
        st.markdown("##### Conventions")
        conv = memory.list(ns, "convention")
        if not conv:
            st.markdown('<div class="cs-empty"><i class="ph ph-book-open"></i><div class="body-6">No conventions yet.</div></div>',
                        unsafe_allow_html=True)
        for m in conv:
            c1, c2 = st.columns([6, 1])
            c1.markdown(f'<div class="cs-inner body-6">{html.escape(m["text"])}</div>', unsafe_allow_html=True)
            if c2.button("Delete", key=f"del_{m['id']}"):
                memory.delete(m["id"])
                st.rerun()
    with cols[1]:
        st.markdown("##### Dismissed findings")
        dis = memory.dismissals(ns)
        if not dis:
            st.markdown('<div class="cs-empty"><i class="ph ph-eye-slash"></i><div class="body-6">Nothing dismissed yet.</div></div>',
                        unsafe_allow_html=True)
        for m in dis:
            c1, c2 = st.columns([6, 1])
            c1.markdown(f'<div class="cs-inner body-6">{html.escape(m["text"])}</div>', unsafe_allow_html=True)
            if c2.button("Delete", key=f"del_{m['id']}"):
                memory.delete(m["id"])
                st.rerun()
    st.markdown("##### Review history")
    hist = memory.review_history(ns)
    if hist:
        df = pd.DataFrame([{"reviewed": datetime.fromtimestamp(h["created"]), "score": h["metadata"].get("score"),
                            "verdict": h["metadata"].get("verdict")} for h in hist])
        st.line_chart(df, x="reviewed", y="score", height=220)
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.markdown('<div class="body-6">Approve a review with "Remember my feedback" to start the trend line.</div>',
                    unsafe_allow_html=True)


# ------------------------------------------------------------------ monitor tab (human on the loop)
with tab_monitor:
    st.markdown("#### Live monitor")
    st.markdown('<div class="body-6">Human on the loop view: what each agent did, how long it took, whether it fell back, '
                'and how much work the cache saved.</div>', unsafe_allow_html=True)
    stats = get_cache().stats()
    cols = st.columns(3)
    for col, ns_name, label in zip(cols, ["llm", "static", "github"], ["LLM response cache", "Static result cache", "GitHub tool cache"]):
        s = stats.get(ns_name, {"hits": 0, "misses": 0, "hit_rate": 0.0, "entries": 0})
        col.markdown(metric(label, f"{s['hit_rate'] * 100:.0f}%", "ph-database") +
                     f'<div class="caption-4" style="margin-top:4px">{s["hits"]} hits · {s["misses"]} misses · {s["entries"]} entries</div>',
                     unsafe_allow_html=True)
    if st.button("Clear caches"):
        get_cache().clear()
        st.rerun()
    if snap is None:
        st.markdown('<div class="cs-empty" style="margin-top:16px"><i class="ph ph-pulse"></i><div class="title-3">No run yet</div>'
                    '<div class="body-6">Start a review to see agent activity here.</div></div>', unsafe_allow_html=True)
    else:
        v = snap.values
        runs = v.get("agent_runs", [])
        if runs:
            st.markdown("##### Agent runs")
            st.dataframe(pd.DataFrame([{"agent": AGENT_TITLES[r["agent"]], "mode": r["mode"], "model": r.get("model") or "none",
                                        "status": r["status"], "tool calls": r.get("tool_calls", 0), "cache": r.get("cache"),
                                        "ungrounded dropped": r.get("ungrounded_dropped", 0), "seconds": r.get("duration_s"),
                                        "error": r.get("error") or ""} for r in runs]), hide_index=True, use_container_width=True)
            alerts = [r for r in runs if r["status"] != "ok" or r.get("duration_s", 0) > settings.slow_agent_seconds]
            for r in alerts:
                st.markdown(f'<div class="cs-callout" style="margin-top:8px"><i class="ph ph-siren"></i>{AGENT_TITLES[r["agent"]]} '
                            f'status {r["status"]}: {html.escape(r.get("error") or "slow run")}</div>', unsafe_allow_html=True)
        st.markdown("##### Event timeline")
        ev = v.get("events", [])
        if ev:
            t0 = ev[0]["ts"]
            st.dataframe(pd.DataFrame([{"t plus seconds": round(e["ts"] - t0, 2), "node": e["node"], "detail": e["detail"]} for e in ev]),
                         hide_index=True, use_container_width=True)


# ------------------------------------------------------------------ how it works tab
with tab_how:
    st.markdown("#### How it works")
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
