"""CodeSentinel as an MCP server.

Lets any MCP host (Claude Desktop, Claude Code, Cursor, a LangChain MCPAdapter
client) call the review team as tools. Runs over stdio.

Only read only capabilities are exposed. MCP callers get the report back; they
cannot post to GitHub or change team memory, because those writes require the
human approval step in the Streamlit app. Run reviews use auto_approve with
external writes disabled (enforced in graph.human_review).

    uv run python mcp_server.py                    # stdio server
    npx @modelcontextprotocol/inspector uv run python mcp_server.py
"""

from __future__ import annotations

import json

from mcp.server.mcpserver import MCPServer

from codesentinel.graph import review_once
from codesentinel.memory import get_memory
from codesentinel.models import CodeFile, detect_language
from codesentinel.tools.github_tools import GitHubError, fetch_files
from codesentinel.tools.static_analysis import RULES, run_static_analysis

mcp = MCPServer("CodeSentinel", version="1.0.0")


@mcp.tool()
def review_code(code: str, filename: str = "snippet.py", project: str = "mcp/clients") -> str:
    """Run the full multi agent review (bugs, security, tests) on one file and return a Markdown report."""
    state = review_once([{"path": filename, "content": code}], source={"kind": "mcp", "label": f"MCP: {filename}"},
                        namespace=project)
    if state.get("status") == "failed":
        return "Review failed: " + " ".join(state.get("errors", []))
    return state["report"]["markdown"]


@mcp.tool()
def review_github(url: str) -> str:
    """Review a public GitHub pull request or file URL and return a Markdown report."""
    try:
        files, meta = fetch_files(url)
    except GitHubError as exc:
        return f"Could not fetch from GitHub: {exc}"
    meta.pop("changed_lines", None)
    label = f"{meta['namespace']} PR #{meta['number']}" if meta["kind"] == "pr" else f"{meta['namespace']}: {meta['path']}"
    state = review_once([f.model_dump() for f in files], source={**meta, "label": label}, namespace=meta["namespace"])
    return state["report"]["markdown"]


@mcp.tool()
def scan_security(code: str, filename: str = "snippet.py") -> str:
    """Fast deterministic security scan (no LLM). Returns JSON findings with CWE ids."""
    f = CodeFile(path=filename, content=code, language=detect_language(filename))
    return json.dumps([x.model_dump(include={"rule_id", "title", "severity", "line", "evidence", "cwe", "recommendation"})
                       for x in run_static_analysis([f], "security")], indent=2)


@mcp.tool()
def get_team_conventions(project: str) -> str:
    """List the coding conventions stored in team memory for a project namespace."""
    items = get_memory().list(project, "convention")
    return "\n".join(f"- {m['text']}" for m in items) or "No conventions stored for this project."


@mcp.resource("rules://catalog")
def rule_catalog() -> str:
    """The static rule catalog used by the specialist agents."""
    return json.dumps(RULES, indent=2)


@mcp.prompt()
def review_request(code: str) -> str:
    """Template asking an assistant to review code with CodeSentinel and explain the top risks."""
    return ("Use the review_code tool on the code below. Then explain the three most important findings in plain "
            f"language and propose the fixes.\n\n```\n{code}\n```")


if __name__ == "__main__":
    mcp.run(transport="stdio")
