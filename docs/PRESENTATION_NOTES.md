# CodeSentinel: presenter notes

**Presenter:** Bala · **Program:** Mastering Agentic AI, Week 3 · **Use case:** 3E, Code Review Agent (multi agent, code track)

**Live app:** https://balaweek3project-codesentinel.streamlit.app/
**Code:** https://github.com/balum211/BalaWeek3Project

## 1. The 30 second pitch

> Code review takes 30 to 45 minutes per pull request, and under pressure the security and test checks are what get skipped. CodeSentinel is a multi agent reviewer built on LangGraph. An orchestrator plans the review, three specialist agents check bugs, security and tests in parallel, and every finding quotes the exact line it refers to. A human approves the plan before the agents run and approves every write before anything is saved, posted or remembered. On my seeded test code it found 31 of 31 issues with 100% precision.

## 2. Talk flow

### 5 minute version (matches the demo video)

| Time | Section | What to show | Key message |
|---|---|---|---|
| 0:00 to 0:30 | Problem and pitch | Live app hero | Reviews are slow and skip security and tests. |
| 0:30 to 1:15 | Architecture | Pipeline strip on the landing page, Architecture tab | One LangGraph graph, three parallel ReAct agents, two human checkpoints. |
| 1:15 to 2:45 | Live review | Review tab with the Loyalty portal sample | Plan approval, ranked findings, quoted evidence, critical acknowledgement. |
| 2:45 to 3:30 | Memory and monitoring | Team memory and Monitor tabs | Dismissals are remembered and enforced; the human on the loop sees fallbacks and cache hits. |
| 3:30 to 4:15 | Real code, MCP, evals | GitHub link mode, `evals/results.md`, `mcp_server.py` | Works on real repositories, is measurable, and plugs into other tools. |
| 4:15 to 4:50 | How I built it and learnings | Documentation section 4 and 5 | Built with Claude Code; control flow and human checkpoints are the product. |

### 10 minute version

Use the same order. Add these sections:

* **Failure handling (1 min):** walk through retry, then the backup provider, then JSON repair, then the rule based fallback. Show the Monitor tab flag.
* **Design (1 min):** explain how the UI makes the human in the loop design visible.
* **Questions (2 min).**

## 3. Live demo click path

Open the live app before you start presenting. Streamlit Cloud apps go to sleep, and the first load can take about 30 seconds.

1. **Hero.** Point at the 3D report preview. The scan line sweeps the code and flags two critical lines. Then point at the sidebar: **LLM agents on**, Nebius Llama 3.3 70B.
2. **How it works.** Scroll to the three cards and the pipeline strip: Intake, Plan, You approve, Bugs / Security / Tests, Report, You approve, Actions.
3. **Workspace.** Keep "Pause for plan approval" on. Choose **Sample code**, then **Loyalty portal API (Flask)**. Open the preview to show the file. Click **Run review**.
4. **Step 1, approve the plan.** The pipeline shows Intake and Plan done, and "You approve" glowing.
   * Say: "The orchestrator rated this high risk because of words like password, eval and pickle."
   * Add a focus line, for example "check authorization on every route", then click **Approve plan**.
5. **Step 2, review the report.**
   * **Score ring and verdict:** Blocked, about 20 findings, 5 critical.
   * **Agent cards:** each shows its status, mode (LLM agent or rule based) and duration.
   * **Escalation callout:** critical findings need acknowledgement.
   * **Agent pills:** filter the findings by agent.
   * **A finding card:** severity, file and line, CWE, quoted evidence and explanation.
   * **Fix, suggested test and dismiss:** shows the fix and a generated pytest.
6. **Dismiss one low finding** with a reason, for example "None comparison style is accepted in this team".
7. **Approve actions.**
   * Tick save, outbox comment and remember feedback.
   * Notice that the critical acknowledgement box is required before posting.
   * Enter your name and click **Approve and run actions**. The pipeline is now fully done and the actions log lists each step.
8. **Team memory tab.** The dismissal is stored with its reason. Add a convention, for example "money values must use Decimal".
9. **Run the same sample again** with plan approval off. Point at "1 finding suppressed by team memory" and "previous review" under the score.
10. **Monitor tab.** Show the agent runs table (model, tool calls, ungrounded findings dropped, seconds), the cache hit rates and the event timeline.
11. **GitHub link.** Paste `https://github.com/we45/Vulnerable-Flask-App/blob/master/app/app.py` and run it. It is blocked for hardcoded secrets, an unverified JWT and SQL injection.

## 4. Architecture in plain words

* **One graph.** A LangGraph `StateGraph` with typed state and reducers (`operator.add` for findings and events).
* **Nodes in order:**
  1. **intake:** checks file count (15 max), size (120 KB max), binary and empty files, and picks the memory namespace.
  2. **plan:** the orchestrator, an LLM with a heuristic fallback, picks the agents, focus areas and risk level.
  3. **plan_review:** `interrupt()`, the first human checkpoint.
  4. **dispatch:** fans out with `Send` so the three specialists run in parallel.
  5. **specialist:** each is a `create_agent` ReAct loop with read only tools.
  6. **aggregate:**
     * deduplicates the findings
     * runs the grounding guard, which drops LLM findings whose quoted code is not in the file
     * applies the team memory suppressions
     * scores the review and sets the verdict, in code.
  7. **human_review:** `interrupt()`, the second human checkpoint.
  8. **execute_actions:** the only node that writes (save report, post or outbox comment, remember feedback).
* **Checkpoints:** `SqliteSaver`, one thread per review, with the thread id in the URL. You can close the tab at an approval step and come back later.
* **Agent tools (all read only):** `run_static_checks`, `read_code`, `list_functions`, `search_team_memory`, `lookup_rule`. A GitHub fetch tool loads pull requests and files.
* **Static rules:** 29 deterministic rules:
  * bugs B001 to B013
  * security S001 to S013
  * tests T001 to T003
  * plus B000 for syntax errors

  The rules give the LLM evidence, and they are the fallback when the LLM fails.
* **Scoring:**
  * Weights: critical 25, high 12, medium 5, low 2, info 0. Findings with confidence below 0.5 count half.
  * Score = `round(100 × 0.5 ^ (penalty / 50))`, so the score halves every 50 penalty points.
  * Verdicts:
    * any critical: **block**
    * any high or a score below 70: **request changes**
    * other findings: **approve with comments**
    * no findings: **approve**
* **Models:** OpenAI compatible `ChatOpenAI`. Provider priority is Nebius, then Fireworks, then OpenAI, with automatic fallback. `CS_PROVIDER=static` turns the LLM off.

## 5. Week 3 concepts, and where each shows up

| Week 3 concept | Where it is in CodeSentinel |
|---|---|
| Multi agent system | Orchestrator plus 3 specialist ReAct agents fanned out in parallel with `Send` |
| Tools | 5 read only agent tools, a GitHub fetch tool, and 3 write actions behind approval |
| State and reducers | Typed graph state; findings and events merge with `operator.add` |
| Checkpointing | `SqliteSaver` per thread; reviews survive a server restart |
| Human in the loop (HITL) | Two `interrupt()` points: plan approval and report approval. Posting criticals needs explicit acknowledgement, enforced in code |
| Human on the loop (HOTL) | Monitor tab: agent status, fallbacks, slow agents (over 45 s), dropped ungrounded findings, cache hit rates, event timeline |
| Long term memory | Per project namespace: conventions (injected into prompts), dismissals (enforced in code), review score history. SQLite by default, Mem0 optional |
| Caching | L1 stable prompt prefix ordering; L2 LLM response cache; L3 tool result cache (short TTL for GitHub, long TTL for static analysis). Keys include prompt version, model and code hash |
| Failure handling | Retries with timeout, then the backup provider, then JSON repair, then the static fallback per agent; a grounding guard against hallucinated lines |
| MCP | `mcp_server.py` over stdio: tools `review_code`, `review_github`, `scan_security` and `get_team_conventions`, resource `rules://catalog`, prompt `review_request` |
| A2A | `a2a/agent-card.json` describes the agent's skills for other agents |
| Evals | `evals/run_evals.py` with line level ground truth: 31/31 recall and 100% precision in static mode, plus 3 real repositories |

## 6. Numbers to remember

* **31 / 31** seeded issues found, **100%** precision, under **1 second** per sample in static mode
* **3** specialist agents, **5** read only agent tools, **29** static rules
* **2** human approval points; **3** write actions, all behind approval
* **20** automated tests, including scripted fake LLM tests (no network needed)
* **3** real open source projects reviewed live from GitHub: vulpy, dvpwa and Vulnerable Flask App
* Limits: **15** files and **120 KB** per file per review; a slow agent warning at **45 s**

## 7. The design story (if asked about the UI)

* It follows the `elayadesign/ai-design-skills` landing page system:
  * Geist type, a fixed spacing scale, Phosphor icons and one easing curve
  * skeleton loaders, composed empty states and reduced motion support
* It also borrows the glass and 3D layer from our Team 24 LaneRoom app: a navy base with aurora light, a grid floor, floating spheres and glass panels.
* **The pipeline strip is the point.** It reads the checkpoint and shows which nodes finished, where the graph is waiting for a human, and which agents were skipped. The HITL design becomes visible to the reviewer.
* **Teal accent, not orange,** because orange already means "high" severity in the reports.

## 8. Likely questions and answers

**Why multi agent and not one big prompt?**
Each specialist has a narrow job, its own prompt and the right tools, and they run in parallel. One prompt that covers bugs, security and tests misses things and is harder to debug. The orchestrator can also skip agents a change doesn't need, and you can remove an agent at the plan approval step.

**How do you stop hallucinations?**
Three layers:
1. The agents must call `read_code` to see the real lines.
2. Every finding has to quote its evidence, and the grounding guard drops any finding whose quote isn't in the file. The Monitor tab counts those drops.
3. The static rules give the agents real evidence to start from.

**What if the LLM is down or returns garbage?**
The steps run in this order:
1. Retry with a timeout.
2. Switch to the backup provider.
3. Repair malformed JSON.
4. If all of that fails, the agent falls back to its static rules.

The review still finishes, and the Monitor tab flags the fallback. Tests with a scripted fake model cover each of these paths.

**Why are some rules in code instead of the prompt?**
A text instruction is a request, not a guarantee. Rules like "never post critical findings without acknowledgement", "dismissed findings stay dismissed" and the score and verdict are enforced in Python.

**What does memory actually store?**
Three narrow things per project:
* conventions, which are injected into the agent prompts
* dismissed false positives with their reasons, which are suppressed automatically next time
* review scores, for the trend line.

**Can it change my code or post on its own?**
No. The agents only have read tools. Saving, posting and remembering happen only in `execute_actions`, after a human approves. MCP and eval runs can't do external writes at all.

**How did you evaluate it?**
I built ground truth at line level for three seeded services, split into issues static rules can detect and issues only an LLM can find. In static mode it found 31 of 31 with 100% precision. I also reviewed three real, intentionally vulnerable open source projects fetched live from GitHub.

**What's the difference between HITL and HOTL here?**
HITL means the graph stops and waits for you: plan approval and report approval. HOTL means it runs on its own while you watch and step in when needed: the Monitor tab with fallbacks, slow agents and dropped findings.

**How does caching help?**
It saves cost and time on repeat reviews. The LLM response cache and the tool caches use keys built from the prompt version, model and code hash, so a prompt change automatically invalidates old answers. GitHub data has a short TTL because it changes.

**Which languages does it support?**
Python gets full syntax tree analysis. JavaScript, TypeScript, Java, Go, Ruby, PHP and C# get pattern based security checks, and the LLM agents can read any language.

**How did you use AI coding tools?**
I built it with Claude Code as a pair programmer. I gave it all the Week 3 materials, then reviewed and steered each iteration:
* rebuilding the specialists as ReAct agents
* adding the grounding guard
* fixing duplicate findings and a JWT rule that double counted
* changing the scoring curve
* the UI redesign and the public deployment

**What would you do next?**
* line level pull request comments
* an LLM as judge eval tracked in LangSmith
* a running A2A endpoint
* deeper analysis for languages other than Python

## 9. Backup plan if the live demo fails

* **App asleep or slow:** open it 5 minutes early. If it's still loading, talk through the architecture section first.
* **LLM provider error:** keep going. The review completes in rule based mode, and that is itself the failure handling story: "this is the fallback working".
* **No internet:** run it locally with `uv run streamlit run app.py`. Without a key it runs in rule based mode.
* **Last resort:** show the saved reports in `sample_outputs/` and the eval table in `evals/results.md`.

## 10. Closing line

> The prompts were the easy part. The real work was deciding what is code and what is model, where the graph pauses for a human, and making every claim verifiable. CodeSentinel reads every line, and you stay in charge of every write. Thank you.
