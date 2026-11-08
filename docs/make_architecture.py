"""Draw docs/architecture.png (run: uv run python docs/make_architecture.py)."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

BG, SURFACE, LINE, TEXT, MUTED = "#181818", "#1F1F1F", "#313131", "#EDEDED", "#9B9B9B"
ACCENT, HUMAN, WRITE, STORE = "#8BD3B0", "#FB923C", "#F87171", "#60A5FA"

fig, ax = plt.subplots(figsize=(16, 10), dpi=150)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 160)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, title, sub="", color=LINE, fill=SURFACE, title_color=TEXT):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.6", linewidth=1.6,
                                edgecolor=color, facecolor=fill))
    ax.text(x + w / 2, y + h / 2 + (1.6 if sub else 0), title, ha="center", va="center", color=title_color,
            fontsize=11.5, fontweight="semibold")
    if sub:
        ax.text(x + w / 2, y + h / 2 - 2.2, sub, ha="center", va="center", color=MUTED, fontsize=8.6, linespacing=1.3)


def arrow(x1, y1, x2, y2, color=MUTED, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14, color=color, linewidth=1.4,
                                 linestyle=ls, shrinkA=2, shrinkB=2))


ax.text(4, 96, "CodeSentinel architecture", color=TEXT, fontsize=18, fontweight="semibold")
ax.text(4, 92.3, "LangGraph StateGraph · SQLite checkpointer per thread · two human in the loop interrupts · read only agents, gated writes",
        color=MUTED, fontsize=10)

# inputs
box(4, 74, 26, 10, "Inputs", "Streamlit UI · MCP host\nsample, paste, upload, GitHub PR", color=LINE)
# main spine
box(38, 76, 20, 8, "intake", "validate, size guards")
box(64, 76, 20, 8, "plan", "orchestrator agent")
box(90, 76, 24, 8, "plan_review (pause)", "human approves or edits", color=HUMAN, title_color=HUMAN)
arrow(30, 79, 38, 80)
arrow(58, 80, 64, 80)
arrow(84, 80, 90, 80)

# specialists
box(40, 50, 30, 12, "Bug agent", "ReAct · create_agent\nlogic, leaks, anti patterns", color=ACCENT)
box(76, 50, 30, 12, "Security agent", "ReAct · create_agent\ninjection, secrets, crypto, CWE", color=ACCENT)
box(112, 50, 30, 12, "Test agent", "ReAct · create_agent\ngaps, error paths, pytest code", color=ACCENT)
ax.text(66, 70, "Send() fan out, parallel", color=ACCENT, fontsize=9, ha="center")
for x in (55, 91, 127):
    arrow(102, 76, x, 62, color=ACCENT)

# tools
box(40, 33, 102, 9, "Read only tools", "run_static_checks · read_code · list_functions · search_team_memory · lookup_rule · GitHub fetch (cached)",
    color=LINE)
for x in (55, 91, 127):
    arrow(x, 50, x, 42, style="<|-|>", color=MUTED)

# aggregate and review
box(4, 50, 30, 12, "aggregate", "dedupe, hallucination guard,\nmemory suppression, score, verdict")
arrow(40, 56, 34, 56, color=ACCENT)
ax.text(28, 44.5,"findings from all\nthree agents\n(state reducers)", color=ACCENT, fontsize=7.8, ha="center")
box(4, 26, 30, 12, "human_review (pause)", "approve or reject, dismiss false\npositives, ack criticals, pick actions",
    color=HUMAN, title_color=HUMAN)
arrow(19, 50, 19, 38)
box(4, 6, 30, 12, "execute_actions", "the only node that writes\nidempotent, per action errors", color=WRITE, title_color=WRITE)
arrow(19, 26, 19, 18)

# stores and side effects
box(44, 6, 30, 12, "Team memory", "conventions · dismissals · history\nSQLite, optional Mem0", color=STORE, title_color=STORE)
box(80, 6, 30, 12, "Cache", "L2 LLM responses · L3 tool results\nTTL + hit rate stats", color=STORE, title_color=STORE)
box(116, 6, 40, 12, "Outputs", "report .md/.json · PR comment (token)\nor outbox file · MCP response")
arrow(34, 12, 44, 12, color=WRITE)
ax.plot([19, 19, 136], [6, 2.2, 2.2], color=WRITE, linewidth=1.4)
arrow(136, 2.2, 136, 6, color=WRITE)
arrow(59, 18, 59, 33, color=STORE, ls="--")
arrow(95, 18, 95, 33, color=STORE, ls="--")

# monitor
box(122, 74, 34, 10, "Monitor (human on the loop)", "agent status, fallbacks, durations,\ncache hits, escalation alerts", color=HUMAN, title_color=HUMAN)
box(146, 50, 10, 12, "LLM", "Nebius\nFireworks\nOpenAI", color=LINE)
arrow(142, 56, 146, 56, style="<|-|>")

legend = [(ACCENT, "agent"), (HUMAN, "human checkpoint / oversight"), (WRITE, "write action"), (STORE, "persistent store")]
for y, (c, label) in zip((29.5, 26.5, 23.5, 20.5), legend):
    x = 118
    ax.add_patch(FancyBboxPatch((x, y), 2.0, 2.0, boxstyle="round,pad=0.1", facecolor=c, edgecolor=c))
    ax.text(x + 3.6, y + 1.0, label, color=MUTED, fontsize=9, va="center")

out = Path(__file__).resolve().parent / "architecture.png"
fig.savefig(out, facecolor=BG, bbox_inches="tight")
print(out)
