"""Typed data contracts shared by every agent.

Agents never pass free text to each other: every finding is validated against
the `Finding` schema before it enters graph state. That keeps the hand-offs
between agents explicit (the same idea A2A formalises with typed artifacts).
"""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Severity = Literal["critical", "high", "medium", "low", "info"]
AgentName = Literal["bugs", "security", "tests"]

SEVERITY_ORDER: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
SEVERITY_WEIGHT: dict[str, int] = {"critical": 25, "high": 12, "medium": 5, "low": 2, "info": 0}

AGENT_TITLES = {
    "bugs": "Bug and anti pattern agent",
    "security": "Security agent",
    "tests": "Test coverage agent",
}


class Finding(BaseModel):
    agent: AgentName
    rule_id: str = Field(description="Stable rule identifier, e.g. S004 or LLM")
    title: str
    severity: Severity
    file: str
    line: int = Field(ge=0)
    end_line: int | None = None
    evidence: str = ""
    explanation: str = ""
    recommendation: str = ""
    confidence: float = Field(default=0.8, ge=0, le=1)
    source: Literal["static", "llm", "static+llm"] = "static"
    cwe: str | None = None
    suggested_test: str | None = None
    id: str = ""

    @field_validator("severity", mode="before")
    @classmethod
    def _norm_severity(cls, v: str) -> str:
        v = str(v).strip().lower()
        return {"blocker": "critical", "major": "high", "minor": "low", "moderate": "medium"}.get(v, v)

    def model_post_init(self, __context) -> None:  # noqa: D401
        if not self.id:
            raw = f"{self.agent}|{self.rule_id}|{self.file}|{self.line}|{self.title}"
            self.id = hashlib.sha1(raw.encode()).hexdigest()[:10]


class FindingList(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
    summary: str = ""


class ReviewPlan(BaseModel):
    agents: list[AgentName] = Field(default_factory=lambda: ["bugs", "security", "tests"])
    focus_areas: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "medium"
    rationale: str = ""


class CodeFile(BaseModel):
    path: str
    content: str
    language: str = "python"

    @property
    def is_test(self) -> bool:
        name = self.path.replace("\\", "/").split("/")[-1].lower()
        return name.startswith("test_") or name.endswith("_test.py") or "/tests/" in f"/{self.path.lower()}"


def detect_language(path: str) -> str:
    ext = path.lower().rsplit(".", 1)[-1] if "." in path else ""
    return {
        "py": "python",
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "java": "java",
        "go": "go",
        "rb": "ruby",
        "php": "php",
        "cs": "csharp",
    }.get(ext, "text")
