"""Visual system for the Streamlit app.

Derived from the elayadesign/ai-design-skills `landing-page-design` skill, Part B:
  B1 typography   Geist (Geist Mono for code only), named text styles on the Tailwind scale,
                  no italics, weights capped at semibold
  B2 spacing      only 2/4/8/12/16/24/32/40/48/64 px tokens; main buttons 8px by 12px padding
  B3 radius       Tailwind radii with the nested radius rule (inner = outer minus gap)
  B4 surfaces     flat dark backgrounds from the allowed list, full borders only, no gradients
  B5 hero         heading gradient text #FFFFFF to #9B9B9B, max width 680px
  B6 icons        Phosphor
  B7 motion       cubic-bezier(0.22,1,0.36,1); transform and opacity only; reduced motion respected
  B9 states       hover, active, focus ring, skeleton loading, composed empty states, inline errors
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap');
@import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css');

:root {
  --bg: #181818; --surface: #1F1F1F; --raised: #272727; --line: #313131; --deep: #131209;
  --text: #EDEDED; --muted: #9B9B9B; --accent: #8BD3B0;
  --critical: #F87171; --high: #FB923C; --medium: #FACC15; --low: #60A5FA; --info: #A3A3A3;
  --s-50: 4px; --s-75: 8px; --s-100: 12px; --s-200: 16px; --s-300: 24px; --s-400: 32px; --s-600: 48px;
  --ease: cubic-bezier(0.22, 1, 0.36, 1);
}

html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {
  font-family: 'Geist', ui-sans-serif, system-ui, sans-serif !important;
  font-style: normal !important;
}
code, pre, .stCode, kbd { font-family: 'Geist Mono', ui-monospace, monospace !important; }
.stApp { background: var(--bg); }
.block-container { padding-top: var(--s-400); padding-bottom: var(--s-600); max-width: 1180px; }
h1, h2, h3, h4 { font-weight: 600 !important; letter-spacing: -0.01em; text-wrap: balance; }
p, li { text-wrap: pretty; }

/* B5 hero */
.cs-hero { margin: var(--s-200) 0 var(--s-400) 0; }
.cs-eyebrow { font-size: 12px; line-height: 16px; font-weight: 500; color: var(--accent);
  display: inline-flex; gap: var(--s-75); align-items: center; padding: var(--s-50) var(--s-100);
  border: 1px solid var(--line); border-radius: 9999px; background: var(--surface); }
.cs-h1 { font-size: 48px; line-height: 48px; font-weight: 600; max-width: 680px; margin: var(--s-200) 0 var(--s-100) 0;
  background: linear-gradient(90deg, #FFFFFF, #9B9B9B); -webkit-background-clip: text; background-clip: text; color: transparent; }
.cs-sub { font-size: 18px; line-height: 28px; font-weight: 400; color: var(--muted); max-width: 680px; }

/* cards and text styles */
.cs-card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: var(--s-200);
  transition: transform 500ms var(--ease), opacity 300ms var(--ease); }
.cs-card + .cs-card { margin-top: var(--s-100); }
.cs-inner { background: var(--raised); border-radius: 8px; padding: var(--s-75) var(--s-100); }
.title-3 { font-size: 16px; line-height: 24px; font-weight: 500; color: var(--text); }
.body-6 { font-size: 14px; line-height: 20px; font-weight: 400; color: var(--muted); }
.caption-4 { font-size: 12px; line-height: 16px; font-weight: 500; color: var(--muted); }
.heading-5 { font-size: 24px; line-height: 32px; font-weight: 600; }

.cs-metric { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: var(--s-200); }
.cs-metric .label { font-size: 12px; line-height: 16px; font-weight: 500; color: var(--muted); display: flex; gap: var(--s-50); align-items: center; }
.cs-metric .value { font-size: 30px; line-height: 36px; font-weight: 600; margin-top: var(--s-50); font-variant-numeric: tabular-nums; }

.cs-badge { display: inline-flex; align-items: center; gap: var(--s-50); font-size: 12px; line-height: 16px; font-weight: 600;
  padding: 2px var(--s-75); border-radius: 9999px; border: 1px solid currentColor; }
.sev-critical { color: var(--critical); } .sev-high { color: var(--high); } .sev-medium { color: var(--medium); }
.sev-low { color: var(--low); } .sev-info { color: var(--info); }
.verdict-block { color: var(--critical); } .verdict-request_changes { color: var(--high); }
.verdict-approve_with_comments { color: var(--medium); } .verdict-approve { color: var(--accent); }

.cs-callout { border: 1px solid var(--high); background: #272727; border-radius: 12px; padding: var(--s-100) var(--s-200);
  font-size: 14px; line-height: 20px; color: var(--text); display: flex; gap: var(--s-75); }
.cs-callout + .cs-callout { margin-top: var(--s-75); }

.cs-step { display: flex; align-items: center; gap: var(--s-75); font-size: 14px; line-height: 20px; color: var(--text);
  padding: var(--s-75) 0; animation: cs-rise 500ms var(--ease) both; }
.cs-step i { color: var(--accent); font-size: 16px; }
@keyframes cs-rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

/* B9 skeleton loader shaped like the report */
.cs-skel { background: var(--raised); border-radius: 8px; height: 16px; margin: var(--s-75) 0; animation: cs-pulse 1400ms var(--ease) infinite; }
.cs-skel.w60 { width: 60%; } .cs-skel.w40 { width: 40%; } .cs-skel.w80 { width: 80%; } .cs-skel.tall { height: 72px; }
@keyframes cs-pulse { 0%, 100% { opacity: 0.45; } 50% { opacity: 1; } }

/* B9 empty state */
.cs-empty { text-align: center; padding: var(--s-600) var(--s-300); border: 1px solid var(--line); border-radius: 16px; background: var(--surface); }
.cs-empty i { font-size: 32px; color: var(--accent); }

/* buttons: B2 padding, B7 motion, B9 states */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  padding: 8px 12px !important; border-radius: 12px !important; font-weight: 600 !important; font-size: 16px; line-height: 24px;
  border: 1px solid var(--line) !important;
  transition: transform 300ms var(--ease), opacity 300ms var(--ease), background-color 300ms var(--ease) !important; }
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-1px); }
.stButton > button:active, .stDownloadButton > button:active { transform: scale(0.98); }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible { outline: 2px solid var(--accent) !important; outline-offset: 2px; }
.stButton > button[kind="primary"] { background: var(--accent) !important; color: #131209 !important; border-color: var(--accent) !important; }

[data-testid="stSidebar"] { background: var(--deep); border-right: 1px solid var(--line); }
[data-testid="stExpander"] details { border-radius: 12px !important; border: 1px solid var(--line) !important; background: var(--surface); }
.stTabs [data-baseweb="tab-list"] { gap: var(--s-75); }
.stTabs [data-baseweb="tab"] { font-weight: 500; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: opacity 200ms linear !important; transform: none !important; }
}
</style>
"""

SEV_ICON = {"critical": "ph-warning-octagon", "high": "ph-warning", "medium": "ph-warning-circle", "low": "ph-info", "info": "ph-note"}
VERDICT_ICON = {"block": "ph-prohibit", "request_changes": "ph-arrow-u-up-left", "approve_with_comments": "ph-chat-circle-text",
                "approve": "ph-check-circle"}
VERDICT_LABEL = {"block": "Blocked", "request_changes": "Changes requested", "approve_with_comments": "Approved with comments",
                 "approve": "Approved"}


def badge(severity: str) -> str:
    return f'<span class="cs-badge sev-{severity}"><i class="ph {SEV_ICON[severity]}"></i>{severity.title()}</span>'


def metric(label: str, value: str, icon: str, cls: str = "") -> str:
    return (f'<div class="cs-metric"><div class="label"><i class="ph {icon}"></i>{label}</div>'
            f'<div class="value {cls}">{value}</div></div>')


SKELETON = """
<div class="cs-card">
  <div class="cs-skel w40"></div><div class="cs-skel w80"></div><div class="cs-skel w60"></div>
  <div class="cs-skel tall"></div><div class="cs-skel w80"></div><div class="cs-skel w60"></div>
</div>
"""
