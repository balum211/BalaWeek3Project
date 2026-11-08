# Week 3 submission checklist

Submission form: https://forms.gle/waBYFkkf5xxmcouV9 · Final certification deadline: **November 11, 2026**

| Deliverable | What to submit | Where it is |
|---|---|---|
| Code base | GitHub link | https://github.com/balum211/BalaWeek3Project |
| Live app | Public Streamlit link | https://balaweek3project-codesentinel.streamlit.app/ |
| Project documentation (Google Doc) | Upload `docs/CodeSentinel_Week3_Project_Documentation.docx` to Google Drive, open it with Google Docs, set sharing to "Anyone with the link can view", paste the link | `docs/CodeSentinel_Week3_Project_Documentation.docx` (Markdown source: `docs/PROJECT_DOCUMENTATION.md`) |
| Video demo (5 minutes or less) | Record with Loom following the script, paste the share link | `docs/DEMO_VIDEO_SCRIPT.md` |
| Sample output | Included in the repo | `sample_outputs/`, `evals/results.md` |

## Form answers you can reuse (links)

* GitHub: https://github.com/balum211/BalaWeek3Project
* Live app: https://balaweek3project-codesentinel.streamlit.app/
* Google Doc: upload `CodeSentinel_Week3_Project_Documentation.docx`, open with Google Docs, share as "Anyone with the link can view"
* Video: your Loom link (5 minutes or less)

## Before recording the demo

1. `uv sync`
2. Optional but recommended: copy `.env.example` to `.env` and add your `NEBIUS_API_KEY` so the specialists run as LLM ReAct agents.
3. With the key set, run `uv run python evals/run_evals.py` once and commit the refreshed `evals/results.md` and `sample_outputs/`, so the "LLM only issues" column has real numbers.
4. Delete the `data/` folder so memory and caches start empty, then `uv run streamlit run app.py`.

## Form answers you can reuse

**Use case:** 3E, Code Review Agent (multi agent)
**Track:** Code track, LangChain + LangGraph, Streamlit UI
**One liner:** CodeSentinel helps a software engineer or tech lead review a pull request in a web app, replacing 30 to 45 minutes of manual review per PR. Three specialist ReAct agents (bugs, security, tests) run in parallel with 6 read only tools, a human approves the plan and every write, and it caught 31 of 31 seeded issues with 100% precision in under a second per sample in static mode.
