# Demo video script (under 5 minutes)

Record the screen with Loom (already installed) at 1080p. Use the live app at https://balaweek3project-codesentinel.streamlit.app/ (LLM agents on), or run it locally with `uv run streamlit run app.py` and your Nebius key in `.env`. Keep VS Code open on the repository.

Before recording: delete `data/` once so the memory and cache start empty, and run one review in advance so you know the timings.

---

## 0:00 to 0:30 · Intro and the problem

**Show:** the live app's hero: the 3D tilted report preview with the scan line, then the sidebar showing **LLM agents on**.

**Say:** "Hi, I'm Bala. For Week 3 I built CodeSentinel, use case 3E, a multi agent code review system on the LangGraph code track. Code review takes 30 to 45 minutes per pull request, and security and test gaps are what get skipped under pressure. CodeSentinel runs three specialist agents in parallel, and nothing is posted or remembered until a human approves it."

## 0:30 to 1:15 · Architecture

**Show:** the How it works tab (architecture diagram), then `codesentinel/graph.py` briefly.

**Say:** "It is one LangGraph StateGraph. Intake validates the files. The orchestrator plans which agents to run. The graph then pauses with interrupt for my approval. The bug, security and test agents fan out in parallel with Send. Each is a ReAct agent built with create_agent and five read only tools. Aggregate dedupes, drops any LLM finding that does not match the real code, applies team memory, and computes the score and verdict in code. Then it pauses again for my review, and only the execute actions node can write. State is checkpointed to SQLite per thread."

## 1:15 to 2:45 · Live review with human in the loop

**Show:** Review tab, pick "Loyalty portal API (Flask)", click Run review.

**Say while it runs:** "Watch the steps stream in, and the pipeline strip above lights up each graph node as it finishes. The first pause is plan approval. I can remove an agent or add a focus area. I'll add 'check authorization on every route' and approve."

**Show:** the report: score, Blocked verdict, the critical callout, expand the SQL injection finding (evidence, CWE, fix), expand a test finding (suggested pytest).

**Say:** "Five critical issues, ranked first. Every finding quotes the exact line. The test agent even writes the pytest for me. This low severity None comparison is a style choice in our team, so I dismiss it with a reason."

**Show:** tick dismiss, type a reason, tick "Remember my feedback", tick the outbox comment, notice the critical acknowledgement checkbox, tick it, approve.

**Say:** "Posting is blocked in code until I acknowledge the criticals. I approve. The report is saved, the PR comment goes to the outbox because there is no GitHub token here, and my dismissal is stored in team memory."

## 2:45 to 3:30 · Memory, monitor, and failure handling

**Show:** run the same sample again (plan approval off in the sidebar to save time). Point at "1 finding suppressed by team memory" and "previous score".

**Say:** "Second run: the dismissed finding is suppressed automatically, and the report shows the previous score. That's long term memory, scoped per project."

**Show:** Monitor tab: agent runs table, cache hit rates, event timeline.

**Say:** "This is the human on the loop view: which model each agent used, tool calls, how many hallucinated findings were dropped, cache hits. If the LLM provider fails, the agent retries, falls back to the second provider, then degrades to static analysis, and this table flags it in orange. The tests cover each of those paths with a scripted fake model."

## 3:30 to 4:15 · Real code, MCP and evals

**Show:** GitHub link mode, paste `https://github.com/we45/Vulnerable-Flask-App/blob/master/app/app.py`, run (plan approval off). Then `evals/results.md`.

**Say:** "It also reviews real open source code straight from GitHub: here a deliberately vulnerable Flask app with hardcoded secrets and an unverified JWT. The eval harness has ground truth for my three samples: 31 of 31 seeded issues found with 100% precision, plus three real repositories."

**Show:** `mcp_server.py` and `a2a/agent-card.json`.

**Say:** "The same graph is exposed as an MCP server, so Claude Desktop can call review_code, and an A2A agent card advertises its skills. MCP callers get read only reviews; writes stay behind the human step."

## 4:15 to 4:50 · How I used AI coding tools and wrap up

**Show:** `docs/PROJECT_DOCUMENTATION.md` section 4 and 5.

**Say:** "I built this with Claude Code. I gave it all the Week 3 materials, and we iterated: turning single prompt agents into ReAct agents, adding the grounding guard, fixing duplicate findings and a JWT rule that double counted, and changing the scoring curve. The UI follows the ai-design-skills design system with the glass and 3D layer from our team's LaneRoom app, and it is deployed publicly on Streamlit Cloud. The biggest lesson: control flow and human checkpoints are the product, and important rules belong in code. Thanks for watching."
