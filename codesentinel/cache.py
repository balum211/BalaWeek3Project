"""SQLite backed cache with TTLs and hit/miss accounting.

Implements three of the five layers from the Week 3 caching handout:

  L2  response cache   namespace "llm"     exact key: agent + prompt version + model + code hash
  L3  tool result      namespace "github"  short TTL (live data), "static" long TTL (pure functions)
  L1  prompt prefix    not a store: prompts are ordered static first, dynamic last (see prompts.py)
                       so provider side prefix caching can apply.

Personal data is never cached: the only things stored are code review results
keyed by content hashes, and public GitHub API responses.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from typing import Any

from codesentinel.config import DATA_DIR

_LOCK = threading.Lock()


def content_hash(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(json.dumps(p, sort_keys=True, default=str).encode())
        h.update(b"\x00")
    return h.hexdigest()


class Cache:
    def __init__(self, path=None):
        self.path = str(path or DATA_DIR / "cache.sqlite")
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS cache (namespace TEXT, key TEXT, value TEXT, created REAL, ttl REAL,"
                      " PRIMARY KEY(namespace, key))")
            c.execute("CREATE TABLE IF NOT EXISTS stats (namespace TEXT PRIMARY KEY, hits INTEGER, misses INTEGER)")

    def _conn(self):
        return sqlite3.connect(self.path, timeout=10, check_same_thread=False)

    def _bump(self, c, namespace: str, hit: bool):
        c.execute("INSERT INTO stats(namespace, hits, misses) VALUES(?, 0, 0) ON CONFLICT(namespace) DO NOTHING", (namespace,))
        c.execute(f"UPDATE stats SET {'hits' if hit else 'misses'} = {'hits' if hit else 'misses'} + 1 WHERE namespace = ?",
                  (namespace,))

    def get(self, namespace: str, key: str) -> Any | None:
        with _LOCK, self._conn() as c:
            row = c.execute("SELECT value, created, ttl FROM cache WHERE namespace=? AND key=?", (namespace, key)).fetchone()
            if row and (row[2] <= 0 or time.time() - row[1] < row[2]):
                self._bump(c, namespace, True)
                return json.loads(row[0])
            if row:
                c.execute("DELETE FROM cache WHERE namespace=? AND key=?", (namespace, key))
            self._bump(c, namespace, False)
            return None

    def set(self, namespace: str, key: str, value: Any, ttl: float) -> None:
        with _LOCK, self._conn() as c:
            c.execute("INSERT OR REPLACE INTO cache VALUES(?, ?, ?, ?, ?)",
                      (namespace, key, json.dumps(value, default=str), time.time(), ttl))

    def stats(self) -> dict[str, dict]:
        with _LOCK, self._conn() as c:
            rows = c.execute("SELECT namespace, hits, misses FROM stats").fetchall()
            sizes = dict(c.execute("SELECT namespace, COUNT(*) FROM cache GROUP BY namespace").fetchall())
        out = {}
        for ns, hits, misses in rows:
            total = hits + misses
            out[ns] = {"hits": hits, "misses": misses, "hit_rate": round(hits / total, 3) if total else 0.0,
                       "entries": sizes.get(ns, 0)}
        return out

    def clear(self, namespace: str | None = None) -> None:
        with _LOCK, self._conn() as c:
            if namespace:
                c.execute("DELETE FROM cache WHERE namespace=?", (namespace,))
                c.execute("DELETE FROM stats WHERE namespace=?", (namespace,))
            else:
                c.execute("DELETE FROM cache")
                c.execute("DELETE FROM stats")


_cache: Cache | None = None


def get_cache() -> Cache:
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache
