"""Visual system and HTML components for the Streamlit app.

Derived from elayadesign/ai-design-skills `landing-page-design`:
  Part A  page structure: floating nav, hero (outcome headline, subheadline, one primary action,
          proof line, hero visual), proof strip, how it works in three steps, the working product,
          tagline reveal, benefits, FAQ, final call to action, footer
  B1      Geist only (Geist Mono for code), named text styles on the Tailwind scale, no italics,
          weights capped at semibold, no hyphens in copy, balanced headings
  B2      spacing tokens only: 2 4 8 12 16 24 32 40 48 64 80 96 px; buttons 8 by 12 px padding
  B3      Tailwind radii with the nested radius rule (inner = outer minus gap)
  B4      flat dark surfaces from the allowed list, full borders only, no background gradients
  B5      hero heading gradient text #FFFFFF to #9B9B9B, heading and subheading max 680px
  B6      Phosphor icons
  B7      cubic-bezier(0.22,1,0.36,1), transform and opacity only, scroll reveals without
          scroll listeners (CSS scroll driven timelines), reduced motion respected
  B9      hover, active, focus ring, skeleton loading, composed empty states, inline errors
  B11     tagline reveal: words go from muted to full one at a time as the section scrolls in
"""

from __future__ import annotations

import html
import re

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap');
@import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css');
@import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/fill/style.css');

:root {
  --black: #000000; --bg: #131209; --surface: #181818; --card: #1F1F1F; --raised: #272727; --line: #313131;
  --text: #EDEDED; --muted: #9B9B9B; --dim: #6B6B6B; --accent: #8BD3B0;
  --critical: #F87171; --high: #FB923C; --medium: #FACC15; --low: #60A5FA; --info: #A3A3A3;
  --ease: cubic-bezier(0.22, 1, 0.36, 1);
}

html, body, .stApp, .stMarkdown, button, input, textarea, select, label, p, li, h1, h2, h3, h4, h5, h6 {
  font-family: 'Geist', ui-sans-serif, system-ui, sans-serif !important; font-style: normal !important;
}
code, pre, .stCode, kbd, .mono { font-family: 'Geist Mono', ui-monospace, monospace !important; }
.stApp { background: var(--bg); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 96px; padding-bottom: 64px; max-width: 1180px; }
h1, h2, h3, h4 { font-weight: 600 !important; text-wrap: balance; letter-spacing: -0.01em; }
p, li { text-wrap: pretty; }
a, a:hover, a:visited, [data-testid="stMarkdownContainer"] a, [data-testid="stMarkdownContainer"] a:hover { text-decoration: none !important; }
.cs-hero a, .cs-footer a, .cs-nav a, .cs-section a { text-decoration: none !important; }

/* ---------- named text styles (B1) ---------- */
.heading-2 { font-size: 48px; line-height: 48px; font-weight: 600; }
.heading-3 { font-size: 36px; line-height: 40px; font-weight: 600; }
.heading-4 { font-size: 30px; line-height: 36px; font-weight: 600; }
.heading-5 { font-size: 24px; line-height: 32px; font-weight: 600; }
.heading-6 { font-size: 20px; line-height: 28px; font-weight: 600; }
.title-2 { font-size: 18px; line-height: 28px; font-weight: 500; color: var(--text); }
.title-3 { font-size: 16px; line-height: 24px; font-weight: 500; color: var(--text); }
.title-4 { font-size: 14px; line-height: 20px; font-weight: 500; color: var(--text); }
.body-3 { font-size: 16px; line-height: 24px; font-weight: 400; color: var(--muted); }
.body-6 { font-size: 14px; line-height: 20px; font-weight: 400; color: var(--muted); }
.caption-3 { font-size: 12px; line-height: 16px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.caption-4 { font-size: 12px; line-height: 16px; font-weight: 500; color: var(--muted); }
.caption-5 { font-size: 12px; line-height: 16px; font-weight: 400; color: var(--dim); }

/* ---------- floating nav (B7 navigation) ---------- */
.cs-nav { position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 999990;
  display: flex; align-items: center; gap: 24px; padding: 8px 8px 8px 16px; border-radius: 9999px;
  background: rgba(24, 24, 24, 0.72); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--line); white-space: nowrap; }
.cs-nav .brand { display: flex; gap: 8px; align-items: center; font-size: 14px; line-height: 20px; font-weight: 600; color: var(--text); }
.cs-nav .brand i { color: var(--accent); font-size: 20px; }
.cs-nav .links { display: flex; gap: 16px; }
.cs-nav .links a { font-size: 14px; line-height: 20px; font-weight: 500; color: var(--muted); transition: opacity 300ms var(--ease); }
.cs-nav .links a:hover { color: var(--text); }
.cs-nav .links a.current { color: var(--text); }
.cs-nav .cta { font-size: 14px; line-height: 20px; font-weight: 600; color: #131209 !important; background: var(--accent);
  padding: 8px 12px; border-radius: 9999px; transition: transform 300ms var(--ease); display: inline-flex; gap: 4px; align-items: center; }
.cs-nav .cta:hover { transform: translateY(-1px); }
.cs-nav .cta:active { transform: scale(0.98); }

/* ---------- hero (B5) ---------- */
.cs-hero { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: 48px; align-items: center; margin: 32px 0 48px 0; }
.cs-eyebrow { display: inline-flex; gap: 8px; align-items: center; padding: 4px 12px; border-radius: 9999px;
  font-size: 12px; line-height: 16px; font-weight: 500; color: var(--accent); border: 1px solid var(--line); background: var(--surface); }
.cs-eyebrow .dot { width: 8px; height: 8px; border-radius: 9999px; background: var(--accent); animation: cs-pulse 1800ms var(--ease) infinite; }
.cs-h1 { font-size: 48px; line-height: 48px; font-weight: 600; letter-spacing: -0.02em; max-width: 680px; margin: 24px 0 16px 0;
  background: linear-gradient(90deg, #FFFFFF, #9B9B9B); -webkit-background-clip: text; background-clip: text; color: transparent; }
.cs-sub { font-size: 18px; line-height: 28px; font-weight: 400; color: var(--muted); max-width: 680px; }
.cs-actions { display: flex; gap: 12px; align-items: center; margin-top: 32px; flex-wrap: wrap; }
.cs-btn { display: inline-flex; gap: 8px; align-items: center; padding: 8px 12px; border-radius: 12px; font-size: 16px; line-height: 24px;
  font-weight: 600; transition: transform 300ms var(--ease), opacity 300ms var(--ease); border: 1px solid var(--line); }
.cs-btn.primary { background: var(--accent); color: #131209 !important; border-color: var(--accent); }
.cs-btn.ghost { color: var(--text) !important; background: var(--surface); }
.cs-btn:hover { transform: translateY(-1px); }
.cs-btn:active { transform: scale(0.98); }
.cs-btn:focus-visible, .cs-nav a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.cs-proofline { display: flex; gap: 8px; align-items: center; margin-top: 24px; font-size: 14px; line-height: 20px; color: var(--muted); }
.cs-proofline i { color: var(--accent); font-size: 16px; }

/* hero visual: a real looking report preview */
.cs-preview { background: var(--surface); border: 1px solid var(--line); border-radius: 24px; padding: 16px;
  animation: cs-rise 800ms var(--ease) both; }
.cs-preview .chrome { display: flex; gap: 8px; align-items: center; padding: 0 4px 12px 4px; }
.cs-preview .chrome span { width: 12px; height: 12px; border-radius: 9999px; background: var(--raised); }
.cs-preview .chrome .path { width: auto; height: auto; background: none; margin-left: 8px; }
.cs-preview .pane { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }
.cs-preview .pane + .pane { margin-top: 8px; }
.cs-preview .row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.cs-preview .finding { display: flex; gap: 12px; align-items: flex-start; padding: 8px 0; }
.cs-preview .finding + .finding { border-top: 1px solid var(--line); }
.cs-preview .agents { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.cs-preview .agent { background: var(--raised); border-radius: 8px; padding: 8px 12px; }

/* ---------- section scaffolding ---------- */
.cs-section { margin: 80px 0 32px 0; }
.cs-section .kicker { display: flex; gap: 8px; align-items: center; color: var(--accent); }
.cs-section h2.title { font-size: 36px; line-height: 40px; font-weight: 600; margin: 12px 0 8px 0; max-width: 680px; color: var(--text); padding: 0; }
.cs-grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 32px; }
.cs-grid-4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.cs-stat { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 24px; }
.cs-stat .num { font-size: 36px; line-height: 40px; font-weight: 600; color: var(--text); font-variant-numeric: tabular-nums; }
.cs-step-card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 24px;
  transition: transform 500ms var(--ease); }
.cs-step-card:hover { transform: translateY(-4px); }
.cs-step-card .icon { width: 40px; height: 40px; border-radius: 12px; background: var(--raised); display: flex; align-items: center;
  justify-content: center; color: var(--accent); font-size: 20px; margin-bottom: 16px; }
.cs-step-card .n { float: right; }

/* scroll reveal for sections (B7) using scroll driven animations, no scroll listeners */
@supports (animation-timeline: view()) {
  .cs-reveal { animation: cs-rise linear both; animation-timeline: view(); animation-range: entry 0% entry 40%; }
}

/* ---------- tagline reveal (B11) ---------- */
.cs-tagline { margin: 96px 0; view-timeline-name: --tagline; }
.cs-tagline p { font-size: 48px; line-height: 48px; font-weight: 600; letter-spacing: -0.02em; max-width: 680px; color: var(--text); }
.cs-tagline .w { opacity: 1; }
@supports (animation-timeline: view()) {
  .cs-tagline .w { opacity: 0.3; animation: cs-word var(--ease) both; animation-timeline: --tagline;
    animation-range: cover var(--s) cover var(--e); }
}
@keyframes cs-word { from { opacity: 0.3; } to { opacity: 1; } }

/* ---------- product UI ---------- */
.cs-workspace-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap; }
.cs-chip { display: inline-flex; gap: 4px; align-items: center; padding: 2px 8px; border-radius: 9999px; font-size: 12px; line-height: 16px;
  font-weight: 500; color: var(--muted); background: var(--raised); border: 1px solid var(--line); }
.cs-chip.ok { color: var(--accent); }
.cs-chip.warn { color: var(--high); }
.cs-card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px; }
.cs-card + .cs-card { margin-top: 12px; }
.cs-inner { background: var(--raised); border-radius: 8px; padding: 8px 12px; }
.cs-badge { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; line-height: 16px; font-weight: 600;
  padding: 2px 8px; border-radius: 9999px; border: 1px solid currentColor; }
.sev-critical { color: var(--critical); } .sev-high { color: var(--high); } .sev-medium { color: var(--medium); }
.sev-low { color: var(--low); } .sev-info { color: var(--info); }
.verdict-block { color: var(--critical); } .verdict-request_changes { color: var(--high); }
.verdict-approve_with_comments { color: var(--medium); } .verdict-approve { color: var(--accent); }

.cs-scoreboard { display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 16px; }
.cs-ring { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px; display: flex;
  flex-direction: column; align-items: center; justify-content: center; gap: 8px; }
.cs-ring svg circle.track { stroke: var(--raised); }
.cs-ring svg circle.val { transition: stroke-dashoffset 800ms var(--ease); }
.cs-board { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 24px; }
.cs-sevbar { display: flex; height: 12px; border-radius: 9999px; overflow: hidden; background: var(--raised); margin: 16px 0 12px 0; gap: 2px; }
.cs-sevbar span { display: block; height: 100%; }
.cs-legend { display: flex; gap: 16px; flex-wrap: wrap; }
.cs-legend span { display: inline-flex; gap: 4px; align-items: center; font-size: 12px; line-height: 16px; color: var(--muted); }
.cs-legend b { font-weight: 600; color: var(--text); }
.cs-legend i.sq { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }

.cs-agents { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 12px; }
.cs-agent { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px; display: flex; gap: 12px; }
.cs-agent .icon { width: 40px; height: 40px; flex: none; border-radius: 12px; background: var(--raised); display: flex;
  align-items: center; justify-content: center; font-size: 20px; color: var(--accent); }

.cs-finding { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px 16px 12px 16px; margin-top: 12px;
  transition: transform 300ms var(--ease); }
.cs-finding:hover { transform: translateY(-2px); }
.cs-finding.sev-critical-b { border-color: rgba(248,113,113,0.55); }
.cs-finding .top { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.cs-finding .loc { font-family: 'Geist Mono', monospace !important; font-size: 12px; line-height: 16px; color: var(--muted);
  background: var(--raised); padding: 2px 8px; border-radius: 8px; }
.cs-finding .ev { margin-top: 12px; background: var(--black); border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px;
  font-family: 'Geist Mono', monospace !important; font-size: 12px; line-height: 16px; color: var(--text); overflow-x: auto; white-space: pre; }

.cs-callout { border: 1px solid var(--high); background: var(--card); border-radius: 12px; padding: 12px 16px;
  font-size: 14px; line-height: 20px; color: var(--text); display: flex; gap: 8px; align-items: flex-start; }
.cs-callout i { color: var(--high); font-size: 16px; margin-top: 2px; }
.cs-callout + .cs-callout { margin-top: 8px; }

.cs-timeline { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 8px 16px; }
.cs-step { display: flex; align-items: center; gap: 12px; font-size: 14px; line-height: 20px; color: var(--text);
  padding: 8px 0; animation: cs-rise 500ms var(--ease) both; }
.cs-step + .cs-step { border-top: 1px solid var(--line); }
.cs-step i { color: var(--accent); font-size: 16px; }

.cs-skel { background: var(--raised); border-radius: 8px; height: 16px; margin: 8px 0; animation: cs-pulse 1400ms var(--ease) infinite; }
.cs-skel.w60 { width: 60%; } .cs-skel.w40 { width: 40%; } .cs-skel.w80 { width: 80%; } .cs-skel.tall { height: 64px; }
.cs-empty { text-align: center; padding: 48px 24px; border: 1px solid var(--line); border-radius: 16px; background: var(--surface); }
.cs-empty .icon { width: 48px; height: 48px; margin: 0 auto 16px auto; border-radius: 12px; background: var(--raised); display: flex;
  align-items: center; justify-content: center; font-size: 24px; color: var(--accent); }

.cs-footer { margin-top: 96px; padding: 32px 0; border-top: 1px solid var(--line); display: flex; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; }
.cs-footer a { color: var(--muted); font-size: 14px; line-height: 20px; }
.cs-footer a:hover { color: var(--text); }

@keyframes cs-rise { from { opacity: 0; transform: translateY(32px); } to { opacity: 1; transform: none; } }
@keyframes cs-pulse { 0%, 100% { opacity: 0.45; } 50% { opacity: 1; } }

.cs-code { font-family: 'Geist Mono', monospace !important; font-size: 12px; line-height: 16px; color: var(--accent);
  background: var(--raised); padding: 2px 4px; border-radius: 4px; }

/* ---------- Streamlit widgets ---------- */
[data-baseweb="tab"] p, [data-testid="stPills"] button, [data-testid="stPills"] button p, [data-testid="stSegmentedControl"] button p,
[data-testid="stExpander"] summary p, [data-testid="stWidgetLabel"] p, .stCheckbox p, .stToggle p {
  font-family: 'Geist', ui-sans-serif, system-ui, sans-serif !important; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  padding: 8px 12px !important; border-radius: 12px !important; font-weight: 600 !important; min-height: 0 !important;
  border: 1px solid var(--line) !important; background: var(--surface);
  transition: transform 300ms var(--ease), opacity 300ms var(--ease) !important; }
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover { transform: translateY(-1px); border-color: var(--muted) !important; }
.stButton > button:active, .stDownloadButton > button:active { transform: scale(0.98); }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible { outline: 2px solid var(--accent) !important; outline-offset: 2px; }
.stButton > button[kind="primary"] { background: var(--accent) !important; color: #131209 !important; border-color: var(--accent) !important; }
[data-testid="stSidebar"] { background: var(--black); border-right: 1px solid var(--line); }
[data-testid="stExpander"] details { border-radius: 12px !important; border: 1px solid var(--line) !important; background: var(--surface); }
[data-testid="stExpander"] summary { font-weight: 500; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 4px; width: fit-content; }
.stTabs [data-baseweb="tab"] { font-weight: 500; padding: 4px 12px; border-radius: 8px; height: auto; }
.stTabs [aria-selected="true"] { background: var(--raised); }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-baseweb="select"] > div { border-radius: 12px !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }

/* ---------- responsive (390px check) ---------- */
@media (max-width: 900px) {
  .cs-hero { grid-template-columns: minmax(0, 1fr); gap: 32px; }
  .cs-grid-3, .cs-agents { grid-template-columns: minmax(0, 1fr); }
  .cs-grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .cs-scoreboard { grid-template-columns: minmax(0, 1fr); }
  .cs-h1 { font-size: 36px; line-height: 40px; }
  .cs-tagline p { font-size: 30px; line-height: 36px; }
  .cs-section h2.title { font-size: 30px; line-height: 36px; }
  .cs-nav .links, .cs-nav .cs-chip { display: none; }
  .cs-nav { max-width: calc(100% - 32px); }
  .cs-nav { gap: 16px; }
  .block-container { padding-top: 80px; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: opacity 200ms linear !important; }
  .cs-tagline .w { opacity: 1 !important; }
  .cs-reveal { opacity: 1 !important; transform: none !important; }
}
</style>
"""

SEV_ORDER = ["critical", "high", "medium", "low", "info"]
SEV_COLOR = {"critical": "#F87171", "high": "#FB923C", "medium": "#FACC15", "low": "#60A5FA", "info": "#A3A3A3"}
SEV_ICON = {"critical": "ph-warning-octagon", "high": "ph-warning", "medium": "ph-warning-circle", "low": "ph-info", "info": "ph-note"}
VERDICT_ICON = {"block": "ph-prohibit", "request_changes": "ph-arrow-u-up-left", "approve_with_comments": "ph-chat-circle-text",
                "approve": "ph-check-circle"}
VERDICT_LABEL = {"block": "Blocked", "request_changes": "Changes requested", "approve_with_comments": "Approved with comments",
                 "approve": "Approved"}
AGENT_ICON = {"bugs": "ph-bug-beetle", "security": "ph-shield-warning", "tests": "ph-flask"}
e = html.escape


def inline_code(text: str) -> str:
    """Escape text, then turn `code` spans into styled code elements."""
    return re.sub(r"`([^`]+)`", lambda m: f'<code class="cs-code">{m.group(1)}</code>', e(text))


def badge(severity: str) -> str:
    return f'<span class="cs-badge sev-{severity}"><i class="ph {SEV_ICON[severity]}"></i>{severity.title()}</span>'


def nav(mode_label: str, llm: bool) -> str:
    chip = f'<span class="cs-chip {"ok" if llm else "warn"}"><i class="ph-fill ph-circle"></i>{e(mode_label)}</span>'
    return f"""
<nav class="cs-nav" aria-label="Primary">
  <span class="brand"><i class="ph-fill ph-shield-check"></i>CodeSentinel</span>
  <span class="links">
    <a href="#how-it-works">How it works</a>
    <a class="current" href="#workspace" aria-current="page">Workspace</a>
    <a href="#faq">FAQ</a>
  </span>
  {chip}
  <a class="cta" href="#workspace"><i class="ph ph-play"></i>Run a review</a>
</nav>"""


def hero() -> str:
    return """
<section class="cs-hero" aria-label="Introduction">
  <div>
    <span class="cs-eyebrow"><span class="dot"></span>Week 3 project · Multi agent code review</span>
    <div class="cs-h1">Catch the bugs your<br>reviewers miss,<br>before you merge.</div>
    <div class="cs-sub">Three specialist agents check every change for bugs, security holes and missing tests
    at the same time. You approve the plan, you approve the report, and nothing ships without you.</div>
    <div class="cs-actions">
      <a class="cs-btn primary" href="#workspace"><i class="ph ph-play"></i>Run a free review</a>
      <a class="cs-btn ghost" href="#how-it-works"><i class="ph ph-graph"></i>See how it works</a>
    </div>
    <div class="cs-proofline"><i class="ph-fill ph-seal-check"></i>Found 31 of 31 seeded issues with 100% precision in our evals</div>
  </div>
  <div class="cs-preview" role="img" aria-label="Preview of a CodeSentinel review report">
    <div class="chrome"><span></span><span></span><span></span><span class="path caption-5 mono">payments.py · review report</span></div>
    <div class="pane">
      <div class="row">
        <div><div class="caption-3">Verdict</div><div class="heading-6 verdict-block" style="margin-top:4px">Blocked</div></div>
        <div style="text-align:right"><div class="caption-3">Quality score</div><div class="heading-6" style="margin-top:4px">22 <span class="caption-5">/ 100</span></div></div>
      </div>
      <div class="cs-sevbar" style="margin:12px 0 0 0"><span style="width:44%;background:#F87171"></span><span style="width:12%;background:#FACC15"></span><span style="width:44%;background:#60A5FA"></span></div>
    </div>
    <div class="pane">
      <div class="finding"><span class="cs-badge sev-critical"><i class="ph ph-warning-octagon"></i>Critical</span>
        <div><div class="title-4">JWT signature not verified</div><div class="caption-5 mono">payments.py:33 · CWE 347</div></div></div>
      <div class="finding"><span class="cs-badge sev-critical"><i class="ph ph-warning-octagon"></i>Critical</span>
        <div><div class="title-4">Shell command injection risk</div><div class="caption-5 mono">payments.py:50 · CWE 78</div></div></div>
      <div class="finding"><span class="cs-badge sev-medium"><i class="ph ph-warning-circle"></i>Medium</span>
        <div><div class="title-4">refund has five untested error paths</div><div class="caption-5 mono">payments.py:32 · pytest included</div></div></div>
    </div>
    <div class="pane agents">
      <div class="agent"><div class="caption-4"><i class="ph ph-bug-beetle"></i> Bugs</div><div class="title-4">done</div></div>
      <div class="agent"><div class="caption-4"><i class="ph ph-shield-warning"></i> Security</div><div class="title-4">done</div></div>
      <div class="agent"><div class="caption-4"><i class="ph ph-flask"></i> Tests</div><div class="title-4">done</div></div>
    </div>
  </div>
</section>
<section class="cs-grid-4 cs-reveal" aria-label="Results">
  <div class="cs-stat"><div class="num">31 / 31</div><div class="body-6">seeded issues found across three sample services</div></div>
  <div class="cs-stat"><div class="num">100%</div><div class="body-6">precision on bug and security findings</div></div>
  <div class="cs-stat"><div class="num">29</div><div class="body-6">grounded rules the agents use as evidence</div></div>
  <div class="cs-stat"><div class="num">2</div><div class="body-6">human approval points before anything is written</div></div>
</section>"""


def how_it_works() -> str:
    steps = [
        ("ph-strategy", "01", "The orchestrator plans", "It reads the change, rates the risk and decides which specialists run. You approve or edit the plan."),
        ("ph-users-three", "02", "Three agents work in parallel", "Bug, security and test agents each run a reasoning loop with read only tools and quote the exact line for every claim."),
        ("ph-user-check", "03", "You decide what ships", "Findings arrive ranked with a score and verdict. Dismiss false positives, then approve saving, posting and remembering."),
    ]
    cards = "".join(
        f'<div class="cs-step-card"><span class="caption-5 n mono">{n}</span><div class="icon"><i class="ph {i}"></i></div>'
        f'<div class="title-2">{t}</div><div class="body-6" style="margin-top:8px">{d}</div></div>' for i, n, t, d in steps)
    return f"""
<section class="cs-section cs-reveal" id="how-it-works">
  <div class="kicker caption-3"><i class="ph ph-graph"></i>How it works</div>
  <h2 class="title">A review team that never skips the checklist</h2>
  <div class="body-3" style="max-width:680px">Built as a LangGraph state machine with checkpoints, so a review can pause for you and resume exactly where it stopped.</div>
  <div class="cs-grid-3">{cards}</div>
</section>"""


def tagline() -> str:
    text = "Agents read every line. You stay in charge of every write."
    words = text.split()
    n = len(words)
    spans = []
    for i, w in enumerate(words):
        start = 25 + i * 30 / n
        spans.append(f'<span class="w" style="--s:{start:.1f}%;--e:{start + 6:.1f}%">{w}</span>')
    first, second = " ".join(spans[:4]), " ".join(spans[4:])
    return f'<section class="cs-tagline" aria-label="{e(text)}"><p>{first}<br>{second}</p></section>'


def benefits() -> str:
    items = [
        ("ph-crosshair", "Grounded, not guessed", "Every finding quotes the real line. Claims that do not match the code are dropped and counted."),
        ("ph-brain", "Remembers your team", "Dismiss a false positive once and it stays dismissed. Conventions feed every agent prompt."),
        ("ph-lifebuoy", "Works when the model fails", "Retries, a backup model and rule based fallbacks keep the review running, and the monitor shows it."),
    ]
    cards = "".join(f'<div class="cs-step-card"><div class="icon"><i class="ph {i}"></i></div><div class="title-2">{t}</div>'
                    f'<div class="body-6" style="margin-top:8px">{d}</div></div>' for i, t, d in items)
    return f'<section class="cs-section cs-reveal"><div class="cs-grid-3" style="margin-top:0">{cards}</div></section>'


def section_head(anchor: str, icon: str, kicker: str, title: str, body: str = "") -> str:
    return (f'<section class="cs-section" id="{anchor}" style="margin-bottom:24px"><div class="kicker caption-3"><i class="ph {icon}"></i>{kicker}</div>'
            f'<h2 class="title">{title}</h2>' + (f'<div class="body-3" style="max-width:680px">{body}</div>' if body else "") + "</section>")


def footer(repo_url: str) -> str:
    return f"""
<footer class="cs-footer">
  <div><div class="title-4"><i class="ph-fill ph-shield-check" style="color:var(--accent)"></i> CodeSentinel</div>
  <div class="caption-5" style="margin-top:4px">Week 3 project by Bala · Mastering Agentic AI, The Gen Academy</div></div>
  <div style="display:flex;gap:24px;flex-wrap:wrap">
    <a href="{repo_url}" target="_blank" rel="noopener"><i class="ph ph-github-logo"></i> Source code</a>
    <a href="{repo_url}/blob/main/docs/PROJECT_DOCUMENTATION.md" target="_blank" rel="noopener"><i class="ph ph-file-text"></i> Documentation</a>
    <a href="{repo_url}/blob/main/evals/results.md" target="_blank" rel="noopener"><i class="ph ph-chart-bar"></i> Eval results</a>
    <a href="#workspace"><i class="ph ph-arrow-up"></i> Back to workspace</a>
  </div>
</footer>"""


def score_ring(score: int, verdict: str, previous: int | None) -> str:
    r, c = 52, 2 * 3.14159 * 52
    color = {"block": "#F87171", "request_changes": "#FB923C", "approve_with_comments": "#FACC15", "approve": "#8BD3B0"}[verdict]
    off = c * (1 - score / 100)
    prev = f'<div class="caption-5">previous review {previous}</div>' if previous is not None else '<div class="caption-5">first review</div>'
    return f"""
<div class="cs-ring">
  <svg width="128" height="128" viewBox="0 0 128 128" aria-label="Quality score {score} of 100">
    <circle class="track" cx="64" cy="64" r="{r}" fill="none" stroke-width="10"/>
    <circle class="val" cx="64" cy="64" r="{r}" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"
      stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}" transform="rotate(-90 64 64)"/>
    <text x="64" y="62" text-anchor="middle" fill="#EDEDED" font-family="Geist" font-size="30" font-weight="600">{score}</text>
    <text x="64" y="82" text-anchor="middle" fill="#9B9B9B" font-family="Geist" font-size="12">of 100</text>
  </svg>
  {prev}
</div>"""


def scoreboard(report: dict) -> str:
    counts = report["counts"]
    total = sum(counts.values()) or 1
    bar = "".join(f'<span style="width:{counts[s] / total * 100:.2f}%;background:{SEV_COLOR[s]}"></span>' for s in SEV_ORDER if counts[s])
    legend = "".join(f'<span><i class="sq" style="background:{SEV_COLOR[s]}"></i>{s.title()} <b>{counts[s]}</b></span>' for s in SEV_ORDER)
    v = report["verdict"]
    src = report.get("source", {}).get("label", "")
    return f"""
<div class="cs-scoreboard">
  {score_ring(report["score"], v, report.get("previous_score"))}
  <div class="cs-board">
    <div style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">
      <div><div class="caption-3">Verdict</div>
        <div class="heading-4 verdict-{v}" style="margin-top:4px"><i class="ph {VERDICT_ICON[v]}"></i> {VERDICT_LABEL[v]}</div></div>
      <div style="text-align:right"><div class="caption-3">Findings</div><div class="heading-4" style="margin-top:4px">{len(report["findings"])}</div></div>
    </div>
    <div class="cs-sevbar">{bar}</div>
    <div class="cs-legend">{legend}</div>
    <div class="caption-5" style="margin-top:12px">{e(src)} · {e(report["generated_at"])} · project {e(report["namespace"])}</div>
  </div>
</div>"""


def agent_cards(runs: list[dict], titles: dict) -> str:
    out = []
    for r in runs:
        status_cls = "ok" if r["status"] == "ok" else "warn"
        mode = "LLM agent" if r["mode"] == "llm" else "Rule based"
        out.append(f"""<div class="cs-agent"><div class="icon"><i class="ph {AGENT_ICON[r['agent']]}"></i></div>
<div><div class="title-4">{titles[r['agent']]}</div>
<div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:4px"><span class="cs-chip {status_cls}">{e(r['status'])}</span>
<span class="cs-chip">{mode}</span><span class="cs-chip">{r.get('duration_s', 0)}s</span>
{'<span class="cs-chip ok">cache hit</span>' if r.get('cache') == 'hit' else ''}</div></div></div>""")
    return f'<div class="cs-agents">{"".join(out)}</div>'


def finding_card(f: dict, agent_title: str) -> str:
    cwe = f'<span class="cs-chip">{e(f["cwe"].replace("-", " "))}</span>' if f.get("cwe") else ""
    ev = f'<div class="ev">{e(f["evidence"])}</div>' if f.get("evidence") else ""
    crit = " sev-critical-b" if f["severity"] == "critical" else ""
    return f"""
<div class="cs-finding{crit}">
  <div class="top">{badge(f['severity'])}<span class="title-3">{e(f['title'])}</span></div>
  <div class="top" style="margin-top:8px"><span class="loc">{e(f['file'])}:{f['line']}</span>
    <span class="cs-chip"><i class="ph {AGENT_ICON[f['agent']]}"></i>{agent_title}</span>{cwe}
    <span class="cs-chip">{e(f['source'])} · {f['confidence']:.2f}</span></div>
  {ev}
  <div class="body-6" style="margin-top:12px">{inline_code(f['explanation'])}</div>
</div>"""


def empty(icon: str, title: str, body: str) -> str:
    return (f'<div class="cs-empty"><div class="icon"><i class="ph {icon}"></i></div><div class="title-3">{title}</div>'
            f'<div class="body-6" style="margin-top:4px">{body}</div></div>')


SKELETON = """
<div class="cs-scoreboard" style="margin-top:12px">
  <div class="cs-ring"><div class="cs-skel" style="width:112px;height:112px;border-radius:9999px"></div></div>
  <div class="cs-board"><div class="cs-skel w40"></div><div class="cs-skel w80"></div><div class="cs-skel w60"></div></div>
</div>
<div class="cs-card" style="margin-top:12px"><div class="cs-skel w40"></div><div class="cs-skel tall"></div><div class="cs-skel w80"></div></div>
"""
