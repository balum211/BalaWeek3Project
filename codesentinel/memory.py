"""Long term memory for the review agents.

What the agent remembers, per project namespace (for example `owner/repo`):

  convention   Team coding rules ("we use Decimal for money", "SQLAlchemy only").
               Retrieved by relevance and injected into every specialist prompt.
  dismissal    A finding a human marked as a false positive, with the reason.
               Enforced in code: matching findings are suppressed next time.
  review       A short record of each approved review (score, counts, verdict),
               used for week over week trend lines.

Storage
  Local SQLite is always the system of record, so suppression rules are
  deterministic and auditable. When MEM0_API_KEY is set, conventions and
  review summaries are mirrored to Mem0 and semantic search goes through Mem0,
  following the Mem0 handout's add / search pattern scoped by user_id.

Access is scoped by namespace so one project never sees another's memories.
"""

from __future__ import annotations

import fnmatch
import json
import re
import sqlite3
import threading
import time
import uuid
from typing import Any

from codesentinel.config import DATA_DIR, get_settings

_LOCK = threading.Lock()
_WORD = re.compile(r"[a-z0-9_]+")
STOP = {"the", "a", "an", "and", "or", "to", "of", "in", "for", "is", "we", "use", "on", "with", "be", "it", "this", "that"}


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in STOP and len(w) > 2}


class MemoryStore:
    def __init__(self, path=None):
        self.path = str(path or DATA_DIR / "memory.sqlite")
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS memories (id TEXT PRIMARY KEY, namespace TEXT, kind TEXT, text TEXT,"
                      " metadata TEXT, created REAL)")
        self._mem0 = None
        key = get_settings().mem0_api_key
        if key:
            try:
                from mem0 import MemoryClient  # type: ignore

                self._mem0 = MemoryClient(api_key=key)
            except Exception:  # mem0 not installed or bad key: stay local
                self._mem0 = None

    @property
    def backend(self) -> str:
        return "Mem0 platform + local SQLite" if self._mem0 else "Local SQLite"

    def _conn(self):
        return sqlite3.connect(self.path, timeout=10, check_same_thread=False)

    # ------------------------------------------------------------------ writes
    def add(self, namespace: str, kind: str, text: str, metadata: dict | None = None) -> str:
        mid = uuid.uuid4().hex[:12]
        with _LOCK, self._conn() as c:
            c.execute("INSERT INTO memories VALUES(?, ?, ?, ?, ?, ?)",
                      (mid, namespace, kind, text, json.dumps(metadata or {}), time.time()))
        if self._mem0 and kind in {"convention", "review"}:
            try:
                self._mem0.add([{"role": "user", "content": text}], user_id=namespace,
                               metadata={"kind": kind, **(metadata or {})})
            except Exception:
                pass  # the local copy is authoritative; a mirror failure must not break the review
        return mid

    def delete(self, memory_id: str) -> None:
        with _LOCK, self._conn() as c:
            c.execute("DELETE FROM memories WHERE id=?", (memory_id,))

    # ------------------------------------------------------------------ reads
    def list(self, namespace: str, kind: str | None = None) -> list[dict[str, Any]]:
        q = "SELECT id, namespace, kind, text, metadata, created FROM memories WHERE namespace=?"
        args: list = [namespace]
        if kind:
            q += " AND kind=?"
            args.append(kind)
        with _LOCK, self._conn() as c:
            rows = c.execute(q + " ORDER BY created DESC", args).fetchall()
        return [{"id": r[0], "namespace": r[1], "kind": r[2], "text": r[3], "metadata": json.loads(r[4]),
                 "created": r[5]} for r in rows]

    def namespaces(self) -> list[str]:
        with _LOCK, self._conn() as c:
            return [r[0] for r in c.execute("SELECT DISTINCT namespace FROM memories ORDER BY namespace").fetchall()]

    def search(self, namespace: str, query: str, kind: str = "convention", limit: int = 5) -> list[dict]:
        if self._mem0 and kind == "convention":
            try:
                res = self._mem0.search(query, filters={"user_id": namespace}, top_k=limit)
                items = res.get("results", res) if isinstance(res, dict) else res
                hits = [{"text": m.get("memory", ""), "score": m.get("score", 0)} for m in items]
                if hits:
                    return hits
            except Exception:
                pass
        q = _tokens(query)
        scored = []
        for m in self.list(namespace, kind):
            overlap = len(q & _tokens(m["text"]))
            scored.append({**m, "score": overlap})
        scored.sort(key=lambda m: (-m["score"], -m["created"]))
        # conventions are short and few: always return the best ones even with zero overlap
        return scored[:limit]

    # ------------------------------------------------------------------ domain helpers
    def dismissals(self, namespace: str) -> list[dict]:
        return self.list(namespace, "dismissal")

    def is_suppressed(self, namespace: str, finding: dict) -> dict | None:
        for d in self.dismissals(namespace):
            md = d["metadata"]
            if md.get("rule_id") != finding.get("rule_id"):
                continue
            pattern = md.get("file_pattern") or "*"
            if fnmatch.fnmatch(finding.get("file", ""), pattern) or fnmatch.fnmatch(finding.get("file", "").split("/")[-1], pattern):
                if not md.get("evidence") or md["evidence"].strip() == (finding.get("evidence") or "").strip():
                    return d
        return None

    def review_history(self, namespace: str) -> list[dict]:
        return sorted(self.list(namespace, "review"), key=lambda m: m["created"])


_store: MemoryStore | None = None


def get_memory() -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store
