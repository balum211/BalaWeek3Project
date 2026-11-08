"""LLM path tests with a scripted fake chat model (no network, no keys).

They prove the ReAct specialist really calls tools, that hallucinated findings
are dropped, that model fallback works, and that a total LLM outage degrades
to static analysis instead of failing the review.
"""

import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from codesentinel.agents.specialists import run_specialist
from codesentinel.cache import get_cache
from codesentinel.config import Settings
from codesentinel.llm import extract_json, set_model_override
from codesentinel.models import CodeFile


class ScriptedModel(BaseChatModel):
    """Returns pre scripted messages in order. Raises if `fail` is set."""

    script: list[Any] = []
    fail: bool = False
    name_: str = "scripted"
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    @property
    def model_name(self) -> str:
        return self.name_

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        self.calls += 1
        if self.fail:
            raise TimeoutError("provider timed out")
        msg = self.script.pop(0) if self.script else AIMessage(content='{"findings": []}')
        return ChatResult(generations=[ChatGeneration(message=msg)])


SETTINGS = Settings(provider="openai")


def _files(samples):
    return [CodeFile(**f) for f in samples("payments_service")]


def _final_json():
    return json.dumps({
        "findings": [
            {"rule_id": "LLM", "title": "Float equality decides refund status", "severity": "high",
             "file": "payments.py", "line": 44, "evidence": "if sum(order.refunds) == order.amount:",
             "explanation": "Float sums rarely equal exactly, so fully refunded orders stay 'paid'.",
             "recommendation": "Use Decimal and compare with a tolerance or integer cents.", "confidence": 0.85},
            {"rule_id": "LLM", "title": "Invented issue", "severity": "critical", "file": "payments.py", "line": 7,
             "evidence": "os.system(user_input)", "explanation": "x", "recommendation": "y", "confidence": 0.9},
        ],
        "disputed_static_ids": {},
        "summary": "Refund logic compares floats.",
    })


def test_react_specialist_calls_tools_and_grounds_findings(samples):
    get_cache().clear()
    tool_call = AIMessage(content="", tool_calls=[{"name": "read_code", "args": {"file_path": "payments.py",
                                                                                   "start_line": 30, "end_line": 50},
                                                   "id": "call_1", "type": "tool_call"}])
    model = ScriptedModel(script=[tool_call, AIMessage(content=_final_json())])
    set_model_override([model])
    out = run_specialist("bugs", _files(samples), {"focus_areas": ["refunds"]}, "t/llm", SETTINGS)
    run = out["run"]
    assert run["mode"] == "llm" and run["status"] == "ok"
    assert run["tool_calls"] == 1
    assert run["ungrounded_dropped"] == 1  # the invented os.system finding
    titles = [f.title for f in out["findings"]]
    assert "Float equality decides refund status" in titles
    assert "Invented issue" not in titles

    # Second identical run is served from the L2 response cache: no model calls.
    model2 = ScriptedModel(script=[])
    set_model_override([model2])
    out2 = run_specialist("bugs", _files(samples), {"focus_areas": ["refunds"]}, "t/llm", SETTINGS)
    assert out2["run"]["cache"] == "hit" and model2.calls == 0


def test_fallback_model_recovers(samples):
    get_cache().clear()
    broken = ScriptedModel(fail=True, name_="primary")
    backup = ScriptedModel(script=[AIMessage(content=_final_json())], name_="backup")
    set_model_override([broken, backup])
    out = run_specialist("security", _files(samples), {}, "t/llm2", SETTINGS)
    assert out["run"]["status"] == "recovered"
    assert out["run"]["model"] == "backup"
    assert "primary" in out["run"]["error"]


def test_total_llm_outage_degrades_to_static(samples):
    get_cache().clear()
    set_model_override([ScriptedModel(fail=True), ScriptedModel(fail=True)])
    out = run_specialist("security", _files(samples), {}, "t/llm3", SETTINGS)
    assert out["run"]["status"] == "degraded"
    assert out["run"]["mode"] == "static"
    assert {f.rule_id for f in out["findings"]} >= {"S001", "S002", "S003", "S012"}


def test_malformed_json_is_repaired(samples):
    get_cache().clear()
    bad = AIMessage(content="Here you go: {findings: [oops")
    repaired = AIMessage(content=_final_json())
    set_model_override([ScriptedModel(script=[bad, repaired])])
    out = run_specialist("bugs", _files(samples), {}, "t/llm4", SETTINGS)
    assert out["run"]["status"] == "ok"
    assert any(f.source in {"llm", "static+llm"} for f in out["findings"])


def test_extract_json_handles_fences_and_prose():
    assert extract_json('Sure.\n```json\n{"a": {"b": "}"}}\n```') == {"a": {"b": "}"}}
    assert extract_json('prefix {"x": 1} suffix') == {"x": 1}
