"""GitHub integration.

Read tools (autonomous): fetch a pull request's changed files, or a single file
from a blob URL. Results go through the L3 tool cache with a short TTL.

Write tool (human approval required): post the review as a PR comment. The
graph only calls it after the human approves in the review step, and it is
idempotent: a hidden marker in the comment body prevents duplicate posts when
a step is retried.
"""

from __future__ import annotations

import re
import time

import requests

from codesentinel.cache import content_hash, get_cache
from codesentinel.config import get_settings
from codesentinel.models import CodeFile, detect_language

API = "https://api.github.com"
PR_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")
BLOB_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)")
REVIEWABLE = (".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php", ".cs")


class GitHubError(RuntimeError):
    """Raised with a message that is safe to show to the user."""


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "codesentinel-review-agent"}
    token = get_settings().github_token
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(url: str, *, raw: bool = False, attempts: int = 3):
    """GET with retry and backoff on timeouts and 5xx. 4xx errors fail fast with a clear message."""
    cache = get_cache()
    key = content_hash(url, raw)
    cached = cache.get("github", key)
    if cached is not None:
        return cached
    last = None
    for i in range(attempts):
        try:
            r = requests.get(url, headers=_headers() if not raw else {"User-Agent": "codesentinel-review-agent"}, timeout=15)
            if r.status_code == 404:
                raise GitHubError("GitHub returned 404. Check the URL, or set GITHUB_TOKEN for private repositories.")
            if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
                raise GitHubError("GitHub rate limit reached. Set GITHUB_TOKEN in .env or try again later.")
            if r.status_code >= 500:
                raise requests.HTTPError(f"GitHub {r.status_code}")
            r.raise_for_status()
            value = r.text if raw else r.json()
            cache.set("github", key, value, get_settings().github_cache_ttl)
            return value
        except GitHubError:
            raise
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            last = exc
            time.sleep(0.6 * (2 ** i))
    raise GitHubError(f"GitHub could not be reached after {attempts} attempts ({last}).")


def parse_source_url(url: str) -> dict:
    url = url.strip()
    if m := PR_RE.search(url):
        return {"kind": "pr", "owner": m[1], "repo": m[2], "number": int(m[3]), "namespace": f"{m[1]}/{m[2]}"}
    if m := BLOB_RE.search(url):
        return {"kind": "blob", "owner": m[1], "repo": m[2], "ref": m[3], "path": m[4], "namespace": f"{m[1]}/{m[2]}"}
    raise GitHubError("That link is not a GitHub pull request or file URL.")


def fetch_files(url: str, max_files: int = 15) -> tuple[list[CodeFile], dict]:
    src = parse_source_url(url)
    if src["kind"] == "blob":
        raw = _get(f"https://raw.githubusercontent.com/{src['owner']}/{src['repo']}/{src['ref']}/{src['path']}", raw=True)
        return [CodeFile(path=src["path"], content=raw, language=detect_language(src["path"]))], {**src, "title": src["path"]}

    pr = _get(f"{API}/repos/{src['owner']}/{src['repo']}/pulls/{src['number']}")
    files = _get(f"{API}/repos/{src['owner']}/{src['repo']}/pulls/{src['number']}/files?per_page=100")
    out: list[CodeFile] = []
    skipped = 0
    for f in files:
        name = f["filename"]
        if f.get("status") == "removed" or not name.endswith(REVIEWABLE):
            continue
        if len(out) >= max_files:
            skipped += 1
            continue
        try:
            content = _get(f["raw_url"], raw=True)
        except GitHubError:
            continue
        out.append(CodeFile(path=name, content=content, language=detect_language(name)))
    meta = {**src, "title": pr.get("title", ""), "author": (pr.get("user") or {}).get("login", ""),
            "head_sha": (pr.get("head") or {}).get("sha", ""), "skipped_files": skipped,
            "changed_lines": {f["filename"]: _changed_lines(f.get("patch", "")) for f in files}}
    if not out:
        raise GitHubError("The pull request has no reviewable source files.")
    return out, meta


def _changed_lines(patch: str) -> list[int]:
    lines, cur = [], 0
    for row in patch.splitlines():
        if row.startswith("@@"):
            m = re.search(r"\+(\d+)", row)
            cur = int(m[1]) if m else 0
        elif row.startswith("+") and not row.startswith("+++"):
            lines.append(cur)
            cur += 1
        elif not row.startswith("-"):
            cur += 1
    return lines


def post_pr_comment(owner: str, repo: str, number: int, body: str, idempotency_key: str) -> dict:
    """WRITE action. Only called after human approval."""
    token = get_settings().github_token
    if not token:
        raise GitHubError("GITHUB_TOKEN is not set, so the comment cannot be posted.")
    marker = f"<!-- codesentinel:{idempotency_key} -->"
    existing = requests.get(f"{API}/repos/{owner}/{repo}/issues/{number}/comments?per_page=100", headers=_headers(), timeout=15)
    if existing.ok and any(marker in (c.get("body") or "") for c in existing.json()):
        return {"status": "skipped", "detail": "This review was already posted (idempotency key matched)."}
    r = requests.post(f"{API}/repos/{owner}/{repo}/issues/{number}/comments", headers=_headers(),
                      json={"body": f"{body}\n\n{marker}"}, timeout=20)
    if not r.ok:
        raise GitHubError(f"GitHub rejected the comment ({r.status_code}): {r.text[:200]}")
    return {"status": "posted", "url": r.json().get("html_url", "")}
