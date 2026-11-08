"""End to end graph tests: interrupts, resume, write gating, memory suppression."""

import uuid

from langgraph.types import Command

from codesentinel import graph as graph_mod
from codesentinel.graph import build_graph, review_once


def _cfg():
    return {"configurable": {"thread_id": uuid.uuid4().hex}}


def _start(g, cfg, files, ns, plan_approval=True):
    return g.invoke({"files": files, "source": {"label": "test"}, "namespace": ns,
                     "options": {"require_plan_approval": plan_approval}}, cfg)


def test_plan_interrupt_then_report_interrupt(samples):
    g, cfg = build_graph(), _cfg()
    _start(g, cfg, samples("payments_service"), "t/one")
    snap = g.get_state(cfg)
    assert snap.next == ("plan_review",)
    assert snap.tasks[0].interrupts[0].value["type"] == "plan_review"

    g.invoke(Command(resume={"approved": True, "agents": ["security"]}), cfg)
    snap = g.get_state(cfg)
    assert snap.next == ("human_review",)
    report = snap.values["report"]
    assert {f["agent"] for f in report["findings"]} == {"security"}  # human edited the plan
    assert report["verdict"] == "block"
    assert report["escalations"]


def test_cancel_at_plan_runs_nothing(samples):
    g, cfg = build_graph(), _cfg()
    _start(g, cfg, samples("payments_service"), "t/cancel")
    g.invoke(Command(resume={"approved": False}), cfg)
    snap = g.get_state(cfg)
    assert snap.next == ()
    assert snap.values["status"] == "cancelled"
    assert not snap.values.get("findings")


def test_reject_writes_nothing(samples, tmp_path, monkeypatch):
    monkeypatch.setattr(graph_mod, "REPORTS_DIR", tmp_path / "reports")
    g, cfg = build_graph(), _cfg()
    _start(g, cfg, samples("inventory_pipeline"), "t/reject", plan_approval=False)
    g.invoke(Command(resume={"decision": "reject"}), cfg)
    values = g.get_state(cfg).values
    assert values["status"] == "rejected"
    assert not (tmp_path / "reports").exists()


def test_critical_post_requires_acknowledgement(samples, tmp_path, monkeypatch):
    monkeypatch.setattr(graph_mod, "OUTBOX_DIR", tmp_path / "outbox")
    g, cfg = build_graph(), _cfg()
    _start(g, cfg, samples("flask_user_api"), "t/ack", plan_approval=False)
    g.invoke(Command(resume={"decision": "approve", "actions": ["post_github"], "acknowledge_critical": False}), cfg)
    log = g.get_state(cfg).values["actions_log"]
    assert log[0]["status"] == "blocked"
    assert not (tmp_path / "outbox").exists()


def test_dismissal_is_remembered_and_suppressed_next_time(samples, monkeypatch, tmp_path):
    monkeypatch.setattr(graph_mod, "REPORTS_DIR", tmp_path / "reports")
    ns = "t/memory"
    g, cfg = build_graph(), _cfg()
    _start(g, cfg, samples("inventory_pipeline"), ns, plan_approval=False)
    report = g.get_state(cfg).values["report"]
    todo = next(f for f in report["findings"] if f["rule_id"] == "B010")
    g.invoke(Command(resume={"decision": "approve", "actions": ["remember_feedback", "save_report"],
                             "dismissed": {todo["id"]: "tracked in JIRA INV-412"}}), cfg)
    final = g.get_state(cfg).values
    assert all(f["id"] != todo["id"] for f in final["report"]["findings"])
    assert any(l["action"] == "save_report" and l["status"] == "done" for l in final["actions_log"])

    cfg2 = _cfg()
    _start(g, cfg2, samples("inventory_pipeline"), ns, plan_approval=False)
    report2 = g.get_state(cfg2).values["report"]
    assert any(s["rule_id"] == "B010" for s in report2["suppressed"])
    assert all(f["rule_id"] != "B010" for f in report2["findings"])
    assert report2["previous_score"] is not None  # review history from memory


def test_auto_mode_never_performs_external_writes(samples, tmp_path, monkeypatch):
    monkeypatch.setattr(graph_mod, "OUTBOX_DIR", tmp_path / "outbox")
    g, cfg = build_graph(), _cfg()
    g.invoke({"files": samples("payments_service"), "source": {"label": "t"}, "namespace": "t/auto",
              "options": {"auto_approve": True, "auto_actions": ["post_github", "remember_feedback"]}}, cfg)
    values = g.get_state(cfg).values
    assert values["review"]["actions"] == []
    assert not (tmp_path / "outbox").exists()


def test_empty_input_stops_cleanly():
    state = review_once([{"path": "empty.py", "content": "   "}])
    assert state["status"] == "failed"
    assert "No reviewable code" in state["errors"][0]


def test_review_once_returns_markdown(samples):
    state = review_once(samples("payments_service"), namespace="t/once")
    assert state["status"] == "completed"
    assert "# CodeSentinel review report" in state["report"]["markdown"]
