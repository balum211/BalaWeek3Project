"""Visual system and HTML components for the Streamlit app.

Derived from elayadesign/ai-design-skills `landing-page-design`, with the glass and 3D layer used by the
Team 24 LaneRoom app:
  Part A  page structure: floating nav, hero (outcome headline, subheadline, one primary action,
          proof line, chips, hero visual), proof strip, how it works, the working product,
          tagline reveal, benefits, FAQ, final call to action, footer
  B1      Geist only (Geist Mono for code and figures), named text styles on the Tailwind scale, no italics,
          weights capped at semibold, no hyphens in copy, balanced headings
  B2      spacing tokens only: 2 4 8 12 16 24 32 40 48 64 80 96 px; buttons 8 by 12 px padding
  B3      Tailwind radii with the nested radius rule (inner = outer minus gap)
  B4      deep navy base with translucent glass surfaces over a fixed 3D background
          (aurora light, perspective grid floor, floating shaded spheres, tilted ring)
  B5      hero heading gradient text, heading and subheading max 680px
  B6      Phosphor icons
  B7      cubic-bezier(0.22,1,0.36,1), transform and opacity only, rise entrances, scroll reveals without
          scroll listeners (CSS scroll driven timelines), reduced motion respected
  B9      hover, active, focus ring, skeleton loading, composed empty states, inline errors
  B11     tagline reveal: words go from muted to full one at a time as the section scrolls in
"""

from __future__ import annotations

import html
import re

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap');
@import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css');
@import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/fill/style.css');

:root {
  /* deep navy base, teal accent, translucent glass surfaces over a 3D background */
  --bg: #050D1A; --side: rgba(6, 16, 30, 0.74); --panel: rgba(14, 34, 56, 0.55); --panel2: rgba(22, 48, 74, 0.58);
  --raise: rgba(40, 82, 116, 0.6); --line: rgba(125, 211, 252, 0.16); --deep: rgba(2, 8, 16, 0.72);
  --text: #EAF6FF; --muted: #9DBBCB; --dim: #64818F; --accent: #2DD4BF; --accent2: #5EEAD4; --warm: #FDBA74;
  --critical: #F87171; --high: #FB923C; --medium: #FACC15; --low: #60A5FA; --info: #A3A3A3;
  /* aliases kept for older markup */
  --surface: var(--panel); --card: var(--panel2); --raised: var(--raise); --black: var(--deep);
  --glass: blur(10px);
  --shadow: 0 10px 40px rgba(1, 8, 18, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  --ease: cubic-bezier(0.22, 1, 0.36, 1);
  --mono: 'Geist Mono', ui-monospace, monospace;
}

html, body, .stApp, .stMarkdown, button, input, textarea, select, label, p, li, h1, h2, h3, h4, h5, h6 {
  font-family: 'Geist', ui-sans-serif, system-ui, sans-serif !important; font-style: normal !important;
}
code, pre, .stCode, kbd, .mono { font-family: var(--mono) !important; }
[class^="ph"], [class*=" ph"] { font-family: 'Phosphor', 'Phosphor-Fill' !important; }
.ph-fill { font-family: 'Phosphor-Fill' !important; }
[data-testid="stHeader"] { background: transparent; }
.stAppDeployButton, [data-testid="stAppDeployButton"] { display: none; }
.block-container { padding-top: 96px; padding-bottom: 64px; max-width: 1180px; }
h1, h2, h3, h4 { font-weight: 600 !important; text-wrap: balance; letter-spacing: -0.01em; }
p, li { text-wrap: pretty; }
a, a:hover, a:visited, [data-testid="stMarkdownContainer"] a, [data-testid="stMarkdownContainer"] a:hover { text-decoration: none !important; }

/* ---------- 3D background: aurora light, perspective grid floor, floating shaded spheres ---------- */
.stApp { background: radial-gradient(1200px 700px at 15% -10%, #0B2A46 0%, transparent 60%),
  radial-gradient(900px 600px at 100% 10%, #0A3438 0%, transparent 55%), var(--bg); }
[data-testid="stMain"], [data-testid="stSidebar"], [data-testid="stHeader"] { position: relative; z-index: 1; }
.cs-bg3d { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; }
.cs-bg3d .aurora { position: absolute; width: 70vmax; height: 70vmax; border-radius: 50%; filter: blur(90px); opacity: 0.42;
  animation: cs-drift 26s ease-in-out infinite alternate; }
.cs-bg3d .a1 { left: -20vmax; top: -25vmax; background: radial-gradient(circle, #0EA5E9 0%, transparent 65%); }
.cs-bg3d .a2 { right: -25vmax; top: 10vh; background: radial-gradient(circle, #14B8A6 0%, transparent 65%); animation-delay: -9s; opacity: 0.3; }
.cs-bg3d .a3 { left: 30vw; bottom: -40vmax; background: radial-gradient(circle, #8B5CF6 0%, transparent 60%); animation-delay: -16s; opacity: 0.2; }
.cs-bg3d .floor { position: absolute; left: -50%; right: -50%; bottom: -8vh; height: 58vh; transform-origin: 50% 100%;
  transform: perspective(520px) rotateX(64deg);
  background-image: linear-gradient(rgba(56, 189, 248, 0.28) 1px, transparent 1px), linear-gradient(90deg, rgba(56, 189, 248, 0.28) 1px, transparent 1px);
  background-size: 64px 64px; animation: cs-floor 6s linear infinite;
  -webkit-mask-image: linear-gradient(to top, #000 10%, transparent 90%); mask-image: linear-gradient(to top, #000 10%, transparent 90%); }
.cs-bg3d .orb { position: absolute; border-radius: 50%; animation: cs-float 14s ease-in-out infinite;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.45), inset -14px -18px 40px rgba(0, 0, 0, 0.45); }
.cs-bg3d .o1 { width: 180px; height: 180px; right: 5vw; top: 18vh; background: radial-gradient(circle at 32% 28%, #FFFFFF 0%, #A5F3FC 12%, #0E7490 48%, #082F49 100%); }
.cs-bg3d .o2 { width: 96px; height: 96px; right: 2vw; top: 80vh; background: radial-gradient(circle at 32% 28%, #FFFFFF 0%, #99F6E4 12%, #0D9488 50%, #042F2E 100%); animation-delay: -5s; }
.cs-bg3d .o3 { width: 56px; height: 56px; right: 3vw; top: 7vh; background: radial-gradient(circle at 32% 28%, #FFFFFF 0%, #FED7AA 14%, #F97316 52%, #7C2D12 100%); animation-delay: -9s; }
.cs-bg3d .o4 { width: 72px; height: 72px; left: 46vw; top: 88vh; background: radial-gradient(circle at 32% 28%, #FFFFFF 0%, #DDD6FE 12%, #7C3AED 50%, #2E1065 100%); animation-delay: -3s; opacity: 0.8; }
.cs-bg3d .ring { position: absolute; right: 9vw; top: 56vh; width: 220px; height: 220px; border-radius: 50%; border: 10px solid rgba(56, 189, 248, 0.2);
  box-shadow: 0 0 40px rgba(56, 189, 248, 0.25), inset 0 0 30px rgba(56, 189, 248, 0.2); transform: rotateX(70deg) rotateZ(20deg);
  animation: cs-spin 30s linear infinite; }
@keyframes cs-drift { from { transform: translate3d(0, 0, 0) scale(1); } to { transform: translate3d(6vw, 4vh, 0) scale(1.12); } }
@keyframes cs-floor { to { background-position: 0 64px, 0 0; } }
@keyframes cs-float { 0%, 100% { transform: translate3d(0, 0, 0); } 50% { transform: translate3d(0, -26px, 0); } }
@keyframes cs-spin { to { transform: rotateX(70deg) rotateZ(380deg); } }

/* ---------- glass surfaces ---------- */
.cs-nav, .cs-hero, .cs-preview, .cs-stat, .cs-step-card, .cs-ring, .cs-board, .cs-agent, .cs-finding, .cs-card, .cs-timeline,
.cs-empty, .cs-callout, .cs-pipe, [data-testid="stExpander"] details, .stTabs [data-baseweb="tab-list"] {
  -webkit-backdrop-filter: var(--glass); backdrop-filter: var(--glass); box-shadow: var(--shadow); }

/* ---------- named text styles (B1) ---------- */
.heading-2 { font-size: 48px; line-height: 48px; font-weight: 600; }
.heading-3 { font-size: 36px; line-height: 40px; font-weight: 600; }
.heading-4 { font-size: 30px; line-height: 36px; font-weight: 600; }
.heading-5 { font-size: 24px; line-height: 32px; font-weight: 600; }
.heading-6 { font-size: 20px; line-height: 28px; font-weight: 600; color: #fff; }
.title-2 { font-size: 18px; line-height: 28px; font-weight: 500; color: #fff; }
.title-3 { font-size: 16px; line-height: 24px; font-weight: 500; color: #fff; }
.title-4 { font-size: 14px; line-height: 20px; font-weight: 500; color: var(--text); }
.body-3 { font-size: 16px; line-height: 24px; font-weight: 400; color: var(--muted); }
.body-6 { font-size: 14px; line-height: 20px; font-weight: 400; color: var(--muted); }
.caption-3 { font-size: 12px; line-height: 16px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
.caption-4 { font-size: 12px; line-height: 16px; font-weight: 500; color: var(--muted); }
.caption-5 { font-size: 12px; line-height: 16px; font-weight: 400; color: var(--dim); }

/* ---------- floating nav ---------- */
.cs-nav { position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 999990;
  display: flex; align-items: center; gap: 24px; padding: 8px 8px 8px 16px; border-radius: 9999px;
  background: rgba(6, 18, 32, 0.72); border: 1px solid var(--line); white-space: nowrap;
  transition: left 300ms var(--ease); }
.stApp:has([data-testid="stSidebar"][data-collapsed="false"]) .cs-nav { left: calc(50% + 150px); }
.cs-nav .brand { display: flex; gap: 8px; align-items: center; font-size: 14px; line-height: 20px; font-weight: 600; color: #fff; }
.cs-nav .brand i { color: var(--accent); font-size: 20px; }
.cs-nav .links { display: flex; gap: 16px; }
.cs-nav .links a { font-size: 14px; line-height: 20px; font-weight: 500; color: var(--muted); transition: color 300ms var(--ease); }
.cs-nav .links a:hover, .cs-nav .links a.current { color: #fff; }
.cs-nav .cta { font-size: 14px; line-height: 20px; font-weight: 600; color: #04131B !important; background: var(--accent);
  padding: 8px 12px; border-radius: 9999px; transition: transform 300ms var(--ease), background-color 300ms var(--ease);
  display: inline-flex; gap: 4px; align-items: center; }
.cs-nav .cta:hover { transform: translateY(-1px); background: var(--accent2); }
.cs-nav .cta:active { transform: scale(0.98); }

/* ---------- hero ---------- */
.cs-hero { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(380px, 100%), 1fr)); gap: 40px; align-items: center;
  margin: 16px 0 24px 0; padding: 48px 40px; border-radius: 24px; background: var(--panel); border: 1px solid var(--line);
  position: relative; overflow: hidden; animation: cs-rise 700ms var(--ease) backwards; }
.cs-eyebrow { display: inline-flex; gap: 8px; align-items: center; padding: 4px 12px; border-radius: 9999px;
  font-size: 12px; line-height: 16px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent2);
  border: 1px solid rgba(45, 212, 191, 0.32); background: var(--side); }
.cs-eyebrow .dot { width: 8px; height: 8px; border-radius: 9999px; background: var(--accent); animation: cs-pulse 1800ms var(--ease) infinite; }
.cs-h1 { font-size: 48px; line-height: 52px; font-weight: 600; letter-spacing: -0.02em; max-width: 680px; margin: 24px 0 16px 0;
  background: linear-gradient(90deg, #FFFFFF 0%, #BAE6FD 55%, #FDBA74 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.cs-sub { font-size: 18px; line-height: 28px; font-weight: 400; color: var(--muted); max-width: 680px; }
.cs-actions { display: flex; gap: 12px; align-items: center; margin-top: 32px; flex-wrap: wrap; }
.cs-btn { display: inline-flex; gap: 8px; align-items: center; padding: 8px 12px; border-radius: 12px; font-size: 16px; line-height: 24px;
  font-weight: 600; transition: transform 300ms var(--ease), background-color 300ms var(--ease), border-color 300ms var(--ease);
  border: 1px solid var(--line); }
.cs-btn.primary { background: var(--accent); color: #04131B !important; border-color: var(--accent); }
.cs-btn.primary:hover { background: var(--accent2); border-color: var(--accent2); }
.cs-btn.ghost { color: var(--text) !important; background: var(--panel2); }
.cs-btn.ghost:hover { border-color: var(--accent); }
.cs-btn:hover { transform: translateY(-1px); }
.cs-btn:active { transform: scale(0.98); }
.cs-btn:focus-visible, .cs-nav a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.cs-proofline { display: flex; gap: 8px; align-items: center; margin-top: 24px; font-size: 14px; line-height: 20px; color: var(--muted); }
.cs-proofline i { color: var(--accent); font-size: 16px; }
.cs-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }
.cs-hchip { display: inline-flex; align-items: center; gap: 8px; background: var(--panel2); border: 1px solid var(--line); border-radius: 9999px;
  padding: 8px 12px; font-size: 14px; line-height: 20px; color: var(--muted); }
.cs-hchip i { color: var(--accent); font-size: 16px; }
.cs-hchip b { color: var(--text); font-weight: 500; }

/* hero visual: a report preview tilted in 3D, with a scan line sweeping the code */
.cs-hero-visual { perspective: 1400px; animation: cs-rise 900ms var(--ease) 120ms backwards; }
.cs-preview { background: rgba(6, 18, 32, 0.72); border: 1px solid var(--line); border-radius: 24px; padding: 16px;
  transform: rotateY(-8deg) rotateX(4deg); transform-style: preserve-3d; transition: transform 700ms var(--ease); }
.cs-preview:hover { transform: rotateY(0deg) rotateX(0deg); }
.cs-preview .chrome { display: flex; gap: 8px; align-items: center; padding: 0 4px 12px 4px; }
.cs-preview .chrome span { width: 12px; height: 12px; border-radius: 9999px; background: var(--raise); }
.cs-preview .chrome span:nth-child(1) { background: #F87171; } .cs-preview .chrome span:nth-child(2) { background: #FACC15; }
.cs-preview .chrome span:nth-child(3) { background: #2DD4BF; }
.cs-preview .chrome .path { width: auto; height: auto; background: none !important; margin-left: 8px; }
.cs-preview .pane { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }
.cs-preview .pane + .pane { margin-top: 8px; }
.cs-preview .row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.cs-preview .finding { display: flex; gap: 12px; align-items: flex-start; padding: 8px 0; }
.cs-preview .finding + .finding { border-top: 1px solid var(--line); }
.cs-preview .agents { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.cs-preview .agent { background: var(--panel2); border-radius: 8px; padding: 8px 12px; }
.cs-preview .agent .title-4 { color: var(--accent2); }
.cs-scan { position: relative; overflow: hidden; padding: 12px 0 !important; font-family: var(--mono) !important; font-size: 12px; line-height: 22px;
  background: var(--deep) !important; }
.cs-scan .ln { display: grid; grid-template-columns: 28px minmax(0, 1fr) 20px; gap: 8px; padding: 0 12px; color: var(--muted); }
.cs-scan .ln .no { color: var(--dim); text-align: right; }
.cs-scan .ln .c { white-space: pre; overflow: hidden; text-overflow: ellipsis; }
.cs-scan .ln.hit { background: rgba(248, 113, 113, 0.1); box-shadow: inset 2px 0 0 var(--critical); color: var(--text); }
.cs-scan .ln .flag { color: var(--critical); font-size: 14px; animation: cs-pulse 1600ms var(--ease) infinite; }
.cs-scan .k { color: #C4B5FD; } .cs-scan .s { color: var(--warm); } .cs-scan .f { color: #7DD3FC; }
.cs-scan .beam { position: absolute; left: 0; right: 0; top: 0; height: 40px; pointer-events: none;
  background: linear-gradient(180deg, transparent, rgba(45, 212, 191, 0.16)); border-bottom: 1px solid rgba(45, 212, 191, 0.6);
  animation: cs-beam 3400ms var(--ease) infinite; }
@keyframes cs-beam { from { transform: translateY(-44px); } to { transform: translateY(150px); } }

/* ---------- agent pipeline strip ---------- */
.cs-pipe { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 8px 0 24px 0; padding: 12px;
  border-radius: 16px; background: var(--panel); border: 1px solid var(--line); animation: cs-rise 700ms var(--ease) backwards; }
.cs-node { display: flex; align-items: center; gap: 4px; padding: 4px 12px; border-radius: 8px; background: var(--panel2);
  border: 1px solid var(--line); font-size: 12px; line-height: 16px; font-weight: 500; color: var(--muted); }
.cs-node i { font-size: 16px; }
.cs-node.gate i { color: var(--warm); }
.cs-node.done { color: var(--text); border-color: rgba(45, 212, 191, 0.4); background: rgba(45, 212, 191, 0.1); }
.cs-node.done i { color: var(--accent); }
.cs-node.active { color: #fff; border-color: var(--warm); background: rgba(253, 186, 116, 0.12); animation: cs-glow 1800ms var(--ease) infinite; }
.cs-node.active i { color: var(--warm); }
.cs-node.skip { opacity: 0.45; text-decoration: line-through; }
.cs-pipe .arrow { color: var(--dim); font-size: 12px; }
.cs-pipe .par { display: flex; flex-direction: column; gap: 4px; }
@keyframes cs-glow { 0%, 100% { box-shadow: 0 0 0 0 rgba(253, 186, 116, 0.0); } 50% { box-shadow: 0 0 0 4px rgba(253, 186, 116, 0.18); } }

/* ---------- section scaffolding ---------- */
.cs-section { margin: 80px 0 32px 0; }
.cs-section .kicker { display: flex; gap: 8px; align-items: center; color: var(--accent2); }
.cs-section h2.title { font-size: 36px; line-height: 40px; font-weight: 600; margin: 12px 0 8px 0; max-width: 680px; color: #fff; padding: 0; }
.cs-grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr)); gap: 16px; margin-top: 32px; }
.cs-grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr)); gap: 16px; }
.cs-stat { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 24px;
  transition: transform 500ms var(--ease), border-color 300ms var(--ease); transform-style: preserve-3d; }
.cs-stat:hover { transform: translateY(-4px) rotateX(2deg); border-color: var(--raise); }
.cs-stat .num { font-family: var(--mono) !important; font-size: 36px; line-height: 40px; font-weight: 600; color: #fff; font-variant-numeric: tabular-nums; }
.cs-step-card { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 24px;
  transition: transform 500ms var(--ease), border-color 300ms var(--ease); transform-style: preserve-3d; }
.cs-step-card:hover { transform: translateY(-4px) rotateX(2deg); border-color: rgba(45, 212, 191, 0.45); }
.cs-step-card .icon { width: 40px; height: 40px; border-radius: 12px; background: rgba(45, 212, 191, 0.12); display: flex; align-items: center;
  justify-content: center; color: var(--accent); font-size: 20px; margin-bottom: 16px; }
.cs-step-card .n { float: right; }

@supports (animation-timeline: view()) {
  .cs-reveal { animation: cs-rise linear both; animation-timeline: view(); animation-range: entry 0% entry 40%; }
}

/* ---------- tagline reveal (B11) ---------- */
.cs-tagline { margin: 96px 0; view-timeline-name: --tagline; }
.cs-tagline p { font-size: 48px; line-height: 52px; font-weight: 600; letter-spacing: -0.02em; max-width: 680px; color: #fff; }
.cs-tagline .w { opacity: 1; }
@supports (animation-timeline: view()) {
  .cs-tagline .w { opacity: 0.25; animation: cs-word var(--ease) both; animation-timeline: --tagline;
    animation-range: cover var(--s) cover var(--e); }
}
@keyframes cs-word { from { opacity: 0.25; } to { opacity: 1; } }

/* ---------- product UI ---------- */
.cs-chip { display: inline-flex; gap: 4px; align-items: center; padding: 2px 8px; border-radius: 9999px; font-size: 12px; line-height: 16px;
  font-weight: 500; color: var(--muted); background: var(--panel2); border: 1px solid var(--line); white-space: nowrap; }
.cs-chip.ok { color: #7CF0D9; background: rgba(45, 212, 191, 0.12); border-color: rgba(45, 212, 191, 0.3); }
.cs-chip.warn { color: #FFD0A8; background: rgba(251, 146, 60, 0.12); border-color: rgba(251, 146, 60, 0.35); }
.cs-card { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 16px 24px; animation: cs-rise 600ms var(--ease) backwards; }
.cs-card + .cs-card { margin-top: 12px; }
.cs-inner { background: var(--panel2); border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px; }
.cs-badge { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; line-height: 16px; font-weight: 600;
  padding: 2px 8px; border-radius: 9999px; border: 1px solid currentColor; background: rgba(2, 8, 16, 0.35); }
.sev-critical { color: var(--critical); } .sev-high { color: var(--high); } .sev-medium { color: var(--medium); }
.sev-low { color: var(--low); } .sev-info { color: var(--info); }
.verdict-block { color: var(--critical); } .verdict-request_changes { color: var(--high); }
.verdict-approve_with_comments { color: var(--medium); } .verdict-approve { color: var(--accent); }

.cs-scoreboard { display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 16px; animation: cs-rise 700ms var(--ease) backwards; }
.cs-ring { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 16px; display: flex;
  flex-direction: column; align-items: center; justify-content: center; gap: 8px; }
.cs-ring svg circle.track { stroke: rgba(125, 211, 252, 0.12); }
.cs-ring svg circle.val { animation: cs-ring 1200ms var(--ease) both; filter: drop-shadow(0 0 8px currentColor); }
@keyframes cs-ring { from { stroke-dashoffset: var(--c); } }
.cs-board { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 24px; }
.cs-sevbar { display: flex; height: 12px; border-radius: 9999px; overflow: hidden; background: var(--raise); margin: 16px 0 12px 0; gap: 2px; }
.cs-sevbar span { display: block; height: 100%; transform-origin: left; animation: cs-grow 900ms var(--ease) both; }
@keyframes cs-grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.cs-legend { display: flex; gap: 16px; flex-wrap: wrap; }
.cs-legend span { display: inline-flex; gap: 4px; align-items: center; font-size: 12px; line-height: 16px; color: var(--muted); }
.cs-legend b { font-weight: 600; color: #fff; font-family: var(--mono) !important; }
.cs-legend i.sq { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }

.cs-agents { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr)); gap: 12px; margin-top: 12px; }
.cs-agent { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 16px; display: flex; gap: 12px;
  animation: cs-rise 700ms var(--ease) backwards; }
.cs-agent:nth-child(2) { animation-delay: 80ms; } .cs-agent:nth-child(3) { animation-delay: 160ms; }
.cs-agent .icon { width: 40px; height: 40px; flex: none; border-radius: 12px; background: rgba(45, 212, 191, 0.12); display: flex;
  align-items: center; justify-content: center; font-size: 20px; color: var(--accent); }

.cs-finding { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 16px 16px 12px 16px; margin-top: 12px;
  transition: transform 500ms var(--ease), border-color 300ms var(--ease); animation: cs-rise 600ms var(--ease) backwards; transform-style: preserve-3d; }
.cs-finding:hover { transform: translateY(-3px) rotateX(1.5deg); border-color: var(--raise); }
.cs-finding.sev-critical-b { border-color: rgba(248, 113, 113, 0.5); box-shadow: var(--shadow), inset 3px 0 0 var(--critical); }
.cs-finding .top { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.cs-finding .loc { font-family: var(--mono) !important; font-size: 12px; line-height: 16px; color: var(--accent2);
  background: rgba(45, 212, 191, 0.08); border: 1px solid rgba(45, 212, 191, 0.25); padding: 2px 8px; border-radius: 8px; }
.cs-finding .ev { margin-top: 12px; background: var(--deep); border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px;
  font-family: var(--mono) !important; font-size: 12px; line-height: 16px; color: var(--text); overflow-x: auto; white-space: pre; }

.cs-callout { border: 1px solid rgba(251, 146, 60, 0.5); background: rgba(251, 146, 60, 0.08); border-radius: 12px; padding: 12px 16px;
  font-size: 14px; line-height: 20px; color: var(--text); display: flex; gap: 8px; align-items: flex-start; }
.cs-callout i { color: var(--high); font-size: 16px; margin-top: 2px; }
.cs-callout + .cs-callout { margin-top: 8px; }

.cs-timeline { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 8px 16px; }
.cs-step { display: flex; align-items: center; gap: 12px; font-size: 14px; line-height: 20px; color: var(--text);
  padding: 8px 0; animation: cs-rise 500ms var(--ease) backwards; }
.cs-step + .cs-step { border-top: 1px solid var(--line); }
.cs-step i { color: var(--accent); font-size: 16px; }

.cs-skel { border-radius: 8px; height: 16px; margin: 8px 0;
  background: linear-gradient(90deg, var(--panel2) 0%, var(--raise) 50%, var(--panel2) 100%); background-size: 200% 100%;
  animation: cs-shimmer 1400ms linear infinite; }
@keyframes cs-shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }
.cs-skel.w60 { width: 60%; } .cs-skel.w40 { width: 40%; } .cs-skel.w80 { width: 80%; } .cs-skel.tall { height: 64px; }
.cs-empty { text-align: center; padding: 48px 24px; border: 1px dashed var(--line); border-radius: 16px; background: var(--panel); }
.cs-empty .icon { width: 48px; height: 48px; margin: 0 auto 16px auto; border-radius: 12px; background: rgba(45, 212, 191, 0.12); display: flex;
  align-items: center; justify-content: center; font-size: 24px; color: var(--accent); }

.cs-footer { margin-top: 96px; padding: 32px 0; border-top: 1px solid var(--line); display: flex; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; }
.cs-footer a { color: var(--muted); font-size: 14px; line-height: 20px; transition: color 300ms var(--ease); }
.cs-footer a:hover { color: var(--accent2); }

@keyframes cs-rise { from { opacity: 0; transform: translateY(32px); } to { opacity: 1; transform: none; } }
@keyframes cs-pulse { 0%, 100% { opacity: 0.45; } 50% { opacity: 1; } }

.cs-code { font-family: var(--mono) !important; font-size: 12px; line-height: 16px; color: var(--accent2);
  background: rgba(45, 212, 191, 0.1); padding: 2px 4px; border-radius: 4px; }

/* ---------- sidebar as a brand panel ---------- */
[data-testid="stSidebar"] { background: var(--side); border-right: none; box-shadow: inset -1px 0 0 var(--line);
  -webkit-backdrop-filter: var(--glass); backdrop-filter: var(--glass); }
[data-testid="stSidebar"] > div { background: transparent; }
.cs-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.cs-brand .mark { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; font-size: 24px; color: #04131B;
  background: linear-gradient(135deg, #5EEAD4, #2DD4BF 55%, #0EA5E9); box-shadow: inset 0 -3px 0 rgba(0, 0, 0, 0.18); }
.cs-brand .name { font-size: 20px; line-height: 28px; font-weight: 600; color: #fff; }
.cs-brand .sub { font-size: 12px; line-height: 16px; color: var(--muted); }
.cs-side-h { font-size: 12px; line-height: 16px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted);
  margin: 24px 0 8px 0; }
.cs-srow { display: flex; gap: 12px; align-items: flex-start; padding: 8px 12px; border-radius: 12px; background: var(--panel);
  border: 1px solid var(--line); margin-bottom: 8px; }
.cs-srow .ico { width: 28px; height: 28px; flex: none; border-radius: 8px; display: grid; place-items: center; font-size: 16px;
  color: var(--accent); background: rgba(45, 212, 191, 0.12); }
.cs-srow .k { font-size: 12px; line-height: 16px; color: var(--dim); }
.cs-srow .v { font-size: 14px; line-height: 20px; color: var(--text); }
.cs-slink { display: flex; gap: 8px; align-items: center; padding: 4px 0; font-size: 14px; line-height: 20px; color: var(--muted) !important;
  transition: color 300ms var(--ease); }
.cs-slink:hover { color: var(--accent2) !important; }

/* ---------- Streamlit widgets ---------- */
[data-baseweb="tab"] p, [data-testid="stPills"] button, [data-testid="stPills"] button p, [data-testid="stSegmentedControl"] button p,
[data-testid="stExpander"] summary p, [data-testid="stWidgetLabel"] p, .stCheckbox p, .stToggle p {
  font-family: 'Geist', ui-sans-serif, system-ui, sans-serif !important; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  padding: 8px 12px !important; border-radius: 12px !important; font-weight: 600 !important; min-height: 0 !important;
  border: 1px solid var(--line) !important; background: rgba(14, 34, 56, 0.82); color: var(--text);
  transition: transform 500ms var(--ease), background-color 300ms var(--ease), border-color 300ms var(--ease), color 300ms var(--ease) !important; }
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  transform: translateY(-1px); background: var(--raise); border-color: var(--accent) !important; color: var(--accent2); }
.stButton > button:active, .stDownloadButton > button:active { transform: scale(0.98); }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible { outline: 2px solid var(--accent) !important; outline-offset: 2px; }
.stButton > button[kind="primary"] { background: var(--accent) !important; color: #04131B !important; border-color: var(--accent) !important; }
.stButton > button[kind="primary"]:hover { background: var(--accent2) !important; border-color: var(--accent2) !important; color: #04131B !important; }
.stButton > button:disabled { opacity: 0.4; transform: none; }
[data-testid="stExpander"] details { border-radius: 16px !important; border: 1px solid var(--line) !important; background: var(--panel); }
[data-testid="stExpander"] summary { font-weight: 500; }
[data-testid="stExpander"] summary:hover { color: var(--accent2); }
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 4px;
  width: fit-content; max-width: 100%; }
.stTabs [data-baseweb="tab"] { font-weight: 500; padding: 8px 16px; border-radius: 12px; height: auto; color: var(--muted);
  transition: background-color 300ms var(--ease), color 300ms var(--ease); }
.stTabs [data-baseweb="tab"]:hover { color: #fff; }
.stTabs [aria-selected="true"] { background: var(--raise) !important; color: #fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
/* newer Streamlit renders tabs with react aria */
[data-testid="stTabs"] [role="tablist"] { gap: 4px; background: var(--panel); border: 1px solid var(--line) !important; border-radius: 16px;
  padding: 4px; width: fit-content; max-width: 100%; -webkit-backdrop-filter: var(--glass); backdrop-filter: var(--glass); box-shadow: var(--shadow); }
[data-testid="stTab"] { padding: 8px 16px !important; border-radius: 12px; color: var(--muted); border: none !important; box-shadow: none !important;
  transition: background-color 300ms var(--ease), color 300ms var(--ease); }
[data-testid="stTab"]::after, [data-testid="stTab"]::before { display: none !important; }
[data-testid="stTab"]:hover { color: #fff; }
[data-testid="stTab"][aria-selected="true"] { background: var(--raise); color: #fff; }
[data-testid="stTab"] p { font-weight: 500; }
[data-baseweb="textarea"], [data-baseweb="input"], [data-baseweb="select"] > div { border-radius: 12px !important;
  background: rgba(6, 18, 32, 0.88) !important; border-color: var(--line) !important; transition: border-color 300ms var(--ease); }
[data-baseweb="textarea"]:focus-within, [data-baseweb="input"]:focus-within { border-color: var(--accent) !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { border-radius: 12px !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
[data-testid="stAlert"] { border-radius: 16px; }
[data-testid="stFileUploaderDropzone"] { background: var(--panel); border: 1px dashed var(--line); border-radius: 16px; }

/* ---------- responsive (390px check) ---------- */
@media (max-width: 900px) {
  .cs-hero { padding: 32px 16px; gap: 32px; }
  .cs-preview { transform: none; }
  .cs-scoreboard { grid-template-columns: minmax(0, 1fr); }
  .cs-h1 { font-size: 36px; line-height: 40px; }
  .cs-tagline p { font-size: 30px; line-height: 36px; }
  .cs-section h2.title { font-size: 30px; line-height: 36px; }
  .cs-nav .links, .cs-nav .cs-chip { display: none; }
  .cs-nav { max-width: calc(100% - 32px); gap: 16px; left: 50% !important; }
  .cs-bg3d .orb, .cs-bg3d .ring { display: none; }
  .block-container { padding-top: 80px; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: opacity 200ms linear !important; }
  .cs-tagline .w { opacity: 1 !important; }
  .cs-reveal { opacity: 1 !important; transform: none !important; }
}
</style>
"""

BACKGROUND = """<div class="cs-bg3d" aria-hidden="true"><div class="aurora a1"></div><div class="aurora a2"></div>
<div class="aurora a3"></div><div class="ring"></div><div class="orb o1"></div><div class="orb o2"></div>
<div class="orb o3"></div><div class="orb o4"></div><div class="floor"></div></div>"""

SEV_ORDER = ["critical", "high", "medium", "low", "info"]
SEV_COLOR = {"critical": "#F87171", "high": "#FB923C", "medium": "#FACC15", "low": "#60A5FA", "info": "#A3A3A3"}
SEV_ICON = {"critical": "ph-warning-octagon", "high": "ph-warning", "medium": "ph-warning-circle", "low": "ph-info", "info": "ph-note"}
VERDICT_ICON = {"block": "ph-prohibit", "request_changes": "ph-arrow-u-up-left", "approve_with_comments": "ph-chat-circle-text",
                "approve": "ph-check-circle"}
VERDICT_LABEL = {"block": "Blocked", "request_changes": "Changes requested", "approve_with_comments": "Approved with comments",
                 "approve": "Approved"}
AGENT_ICON = {"bugs": "ph-bug-beetle", "security": "ph-shield-warning", "tests": "ph-flask"}
PIPE_NODES = [("intake", "ph-tray-arrow-down", "Intake"), ("plan", "ph-strategy", "Plan"), ("gate1", "ph-user-check", "You approve"),
              ("agents", "", ""), ("aggregate", "ph-stack", "Report"), ("gate2", "ph-hand", "You approve"),
              ("actions", "ph-lightning", "Actions")]
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


def brand() -> str:
    return ('<div class="cs-brand"><div class="mark"><i class="ph-fill ph-shield-check"></i></div><div>'
            '<div class="name">CodeSentinel</div><div class="sub">Multi agent code review · Week 3</div></div></div>')


def side_status(rows: list[tuple[str, str, str]]) -> str:
    """Sidebar status rows: (phosphor icon, label, value)."""
    body = "".join(f'<div class="cs-srow"><span class="ico"><i class="ph {i}"></i></span><div><div class="k">{e(k)}</div>'
                   f'<div class="v">{e(v)}</div></div></div>' for i, k, v in rows)
    return f'<div class="cs-side-h">System status</div>{body}'


def side_links(repo_url: str) -> str:
    links = [("ph-github-logo", "Source code", repo_url), ("ph-file-text", "Documentation", f"{repo_url}/blob/main/docs/PROJECT_DOCUMENTATION.md"),
             ("ph-chart-bar", "Eval results", f"{repo_url}/blob/main/evals/results.md")]
    return '<div class="cs-side-h">Project</div>' + "".join(
        f'<a class="cs-slink" href="{u}" target="_blank" rel="noopener"><i class="ph {i}"></i>{t}</a>' for i, t, u in links)


def pipeline(done: set[str] | frozenset = frozenset(), active: str | None = None, skipped: set[str] | frozenset = frozenset()) -> str:
    """The review graph as a strip of nodes. Agent keys are bugs, security and tests."""
    def node(key: str, icon: str, label: str) -> str:
        cls = "cs-node"
        if key.startswith("gate"):
            cls += " gate"
        if key in done:
            cls += " done"
        elif key == active:
            cls += " active"
        elif key in skipped:
            cls += " skip"
        mark = '<i class="ph-fill ph-check-circle"></i>' if key in done else f'<i class="ph {icon}"></i>'
        return f'<div class="{cls}">{mark} {label}</div>'

    parts = []
    for i, (key, icon, label) in enumerate(PIPE_NODES):
        if key == "agents":
            parts.append('<div class="par">' + "".join(node(a, AGENT_ICON[a], t) for a, t in
                                                      (("bugs", "Bugs"), ("security", "Security"), ("tests", "Tests"))) + "</div>")
        else:
            parts.append(node(key, icon, label))
        if i < len(PIPE_NODES) - 1:
            parts.append('<span class="arrow"><i class="ph ph-caret-right"></i></span>')
    return f'<div class="cs-pipe" role="img" aria-label="Review pipeline">{"".join(parts)}</div>'


def hero() -> str:
    chips = [("ph-graph", "3 agents", "on LangGraph"), ("ph-ruler", "29 rules", "as evidence"), ("ph-plugs-connected", "MCP", "server"),
             ("ph-brain", "Team memory", "Mem0 ready"), ("ph-user-check", "2 human", "approvals")]
    chip_html = "".join(f'<span class="cs-hchip"><i class="ph {i}"></i><b>{b}</b>{t}</span>' for i, b, t in chips)
    return f"""
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
    <div class="cs-chips">{chip_html}</div>
  </div>
  <div class="cs-hero-visual">
  <div class="cs-preview" role="img" aria-label="Preview of a CodeSentinel review report">
    <div class="chrome"><span></span><span></span><span></span><span class="path caption-5 mono">payments.py · review report</span></div>
    <div class="pane">
      <div class="row">
        <div><div class="caption-3">Verdict</div><div class="heading-6 verdict-block" style="margin-top:4px">Blocked</div></div>
        <div style="text-align:right"><div class="caption-3">Quality score</div><div class="heading-6" style="margin-top:4px">22 <span class="caption-5">/ 100</span></div></div>
      </div>
      <div class="cs-sevbar" style="margin:12px 0 0 0"><span style="width:44%;background:#F87171"></span><span style="width:12%;background:#FACC15"></span><span style="width:44%;background:#60A5FA"></span></div>
    </div>
    <div class="pane cs-scan">
      <div class="ln"><span class="no">32</span><span class="c"><span class="k">def</span> <span class="f">refund</span>(order_id, token):</span><span></span></div>
      <div class="ln hit"><span class="no">33</span><span class="c">    claims = jwt.<span class="f">decode</span>(token, verify=<span class="k">False</span>)</span><i class="ph-fill ph-warning-octagon flag"></i></div>
      <div class="ln"><span class="no">34</span><span class="c">    amount = <span class="f">float</span>(order[<span class="s">"total"</span>])</span><span></span></div>
      <div class="ln hit"><span class="no">50</span><span class="c">    os.<span class="f">system</span>(<span class="s">f"refund {{order_id}}"</span>)</span><i class="ph-fill ph-warning-octagon flag"></i></div>
      <div class="ln"><span class="no">51</span><span class="c">    <span class="k">return</span> {{<span class="s">"ok"</span>: <span class="k">True</span>}}</span><span></span></div>
      <div class="beam"></div>
    </div>
    <div class="pane">
      <div class="finding"><span class="cs-badge sev-critical"><i class="ph ph-warning-octagon"></i>Critical</span>
        <div><div class="title-4">JWT signature not verified</div><div class="caption-5 mono">payments.py:33 · CWE 347</div></div></div>
      <div class="finding"><span class="cs-badge sev-critical"><i class="ph ph-warning-octagon"></i>Critical</span>
        <div><div class="title-4">Shell command injection risk</div><div class="caption-5 mono">payments.py:50 · CWE 78</div></div></div>
    </div>
    <div class="pane agents">
      <div class="agent"><div class="caption-4"><i class="ph ph-bug-beetle"></i> Bugs</div><div class="title-4">done</div></div>
      <div class="agent"><div class="caption-4"><i class="ph ph-shield-warning"></i> Security</div><div class="title-4">done</div></div>
      <div class="agent"><div class="caption-4"><i class="ph ph-flask"></i> Tests</div><div class="title-4">done</div></div>
    </div>
  </div>
  </div>
</section>
<section class="cs-grid-4 cs-reveal" aria-label="Results">
  <div class="cs-stat"><div class="num">31/31</div><div class="body-6">seeded issues found across three sample services</div></div>
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
  <div style="margin-top:16px">{pipeline()}</div>
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
    color = {"block": "#F87171", "request_changes": "#FB923C", "approve_with_comments": "#FACC15", "approve": "#2DD4BF"}[verdict]
    off = c * (1 - score / 100)
    prev = f'<div class="caption-5">previous review {previous}</div>' if previous is not None else '<div class="caption-5">first review</div>'
    return f"""
<div class="cs-ring">
  <svg width="128" height="128" viewBox="0 0 128 128" aria-label="Quality score {score} of 100">
    <circle class="track" cx="64" cy="64" r="{r}" fill="none" stroke-width="10"/>
    <circle class="val" cx="64" cy="64" r="{r}" fill="none" stroke="{color}" color="{color}" stroke-width="10" stroke-linecap="round"
      stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}" style="--c:{c:.1f}" transform="rotate(-90 64 64)"/>
    <text x="64" y="62" text-anchor="middle" fill="#FFFFFF" font-family="Geist Mono" font-size="30" font-weight="600">{score}</text>
    <text x="64" y="82" text-anchor="middle" fill="#9DBBCB" font-family="Geist" font-size="12">of 100</text>
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
      <div style="text-align:right"><div class="caption-3">Findings</div><div class="heading-4 mono" style="margin-top:4px;color:#fff">{len(report["findings"])}</div></div>
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
