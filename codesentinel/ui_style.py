"""Visual system and HTML components for the Streamlit app.

Built from the two skills in elayadesign/ai-design-skills:

landing-page-design
  Part A  one offer, one primary action: hero, proof in a bento grid, how it works as a zig zag,
          tagline reveal, benefits bento, FAQ, risk reversal, final call to action, footer
  B1      Geist only (Geist Mono for code and figures), named text styles, no italics, no hyphens in copy
  B2/B3   spacing tokens only; Tailwind radii with the nested radius rule
  B4      flat surfaces from the allowed dark list, full borders only, no background gradients
  B5      Heading 1 gradient text #FFFFFF to #9B9B9B, heading and subheading max 680px
  B6/B7   Phosphor icons; cubic-bezier(0.22,1,0.36,1), transform and opacity only, reduced motion respected
  B9/B11  every state, skeletons, composed empty states; word by word tagline reveal

figma-designer
  Two color layers: Core Colors palettes (10+ shades each) feed a Color System of semantic tokens with
  Light and Dark modes; components bind only to Color System tokens. One accent under 80% saturation.
  Hero heading has no periods and no eyebrow tag. Buttons: 5 types x 5 states. Bento and zig zag
  layouts instead of three equal cards. A Foundations view that renders straight from the tokens.
"""

from __future__ import annotations

import html
import re

e = html.escape

# ------------------------------------------------------------------ layer 1: Core Colors


def _mix(hex_a: str, hex_b: str, t: float) -> str:
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def _palette(base: str, steps: list[int]) -> dict[str, str]:
    """00 is near white, 500 is the base hue, 1000 is near black."""
    out = {}
    for s in steps:
        if s < 500:
            out[f"{s:02d}" if s else "00"] = _mix(base, "#FFFFFF", (500 - s) / 500 * 0.96)
        elif s == 500:
            out["500"] = base
        else:
            out[str(s)] = _mix(base, "#000000", (s - 500) / 500 * 0.94)
    return out


_STEPS = [0, 50, 100, 150, 200, 300, 400, 500, 600, 700, 800, 850, 900, 950, 1000]
CORE: dict[str, dict[str, str]] = {
    "Primary": _palette("#9283EB", [0, 50, 100, 150, 200, 300, 350, 400, 450, 500, 600, 700, 800, 850, 900, 950, 1000]),
    "Secondary": _palette("#7B8CA6", _STEPS),
    "Accent": _palette("#B3A8F2", _STEPS),
    "Grayscale": {"00": "#FFFFFF", "50": "#F7F7F7", "100": "#EDEDED", "150": "#E2E2E2", "200": "#D4D4D4", "250": "#C4C4C4",
                  "300": "#B0B0B0", "400": "#9B9B9B", "450": "#8A8A8A", "500": "#757575", "600": "#5C5C5C", "700": "#454545",
                  "750": "#313131", "800": "#272727", "850": "#1F1F1F", "870": "#181818", "900": "#121212", "950": "#0A0A0A",
                  "1000": "#000000"},
    "Red": _palette("#E5484D", _STEPS),
    "Green": _palette("#3DB984", _STEPS),
    "Yellow": _palette("#E8B931", _STEPS),
}

# ------------------------------------------------------------------ layer 2: Color System (Light and Dark modes)
# token: (name, css variable, dark alias, light alias). Every value is an alias to a Core Color.
SYSTEM: dict[str, list[tuple[str, str, str, str]]] = {
    "Surface": [
        ("Surface/Page", "surface-page", "Grayscale/1000", "Grayscale/50"),
        ("Surface/Primary", "surface-primary", "Grayscale/870", "Grayscale/00"),
        ("Surface/Primary-Hover", "surface-primary-hover", "Grayscale/800", "Grayscale/100"),
        ("Surface/Primary-subtle", "surface-subtle", "Grayscale/850", "Grayscale/50"),
        ("Surface/Secondary", "surface-secondary", "Grayscale/800", "Grayscale/100"),
        ("Surface/Secondary-Hover", "surface-secondary-hover", "Grayscale/700", "Grayscale/150"),
        ("Surface/Accent-subtle", "surface-accent-subtle", "Primary/900", "Primary/100"),
        ("Surface/Error-subtle", "surface-error-subtle", "Red/900", "Red/100"),
        ("Surface/Warning-subtle", "surface-warning-subtle", "Yellow/900", "Yellow/100"),
        ("Surface/Success-Subtle", "surface-success-subtle", "Green/900", "Green/100"),
    ],
    "Border": [
        ("Border/Primary", "border-primary", "Grayscale/750", "Grayscale/150"),
        ("Border/Primary-light", "border-light", "Grayscale/700", "Grayscale/200"),
        ("Border/Action-Primary", "border-action", "Primary/400", "Primary/600"),
        ("Border/Error", "border-error", "Red/400", "Red/600"),
        ("Border/Success", "border-success", "Green/400", "Green/600"),
        ("Border/Warning", "border-warning", "Yellow/300", "Yellow/700"),
    ],
    "Action": [
        ("Action/Primary", "action-primary", "Primary/500", "Primary/500"),
        ("Action/Primary-Hover", "action-primary-hover", "Primary/400", "Primary/600"),
        ("Action/Primary-Click", "action-primary-click", "Primary/600", "Primary/700"),
        ("Action/Primary-Disabled", "action-primary-disabled", "Primary/800", "Primary/200"),
        ("Action/Secondary", "action-secondary", "Grayscale/750", "Grayscale/100"),
        ("Action/Secondary-Hover", "action-secondary-hover", "Grayscale/700", "Grayscale/150"),
        ("Action/Secondary-Click", "action-secondary-click", "Grayscale/800", "Grayscale/200"),
        ("Action/Error", "action-error", "Red/700", "Red/600"),
        ("Action/Error-Hover", "action-error-hover", "Red/800", "Red/700"),
        ("Action/Warning", "action-warning", "Yellow/500", "Yellow/500"),
        ("Action/Warning - Hover", "action-warning-hover", "Yellow/600", "Yellow/600"),
    ],
    "Text": [
        ("Text/Primary", "text-primary", "Grayscale/50", "Grayscale/950"),
        ("Text/Secondary", "text-secondary", "Grayscale/200", "Grayscale/700"),
        ("Text/Tertiary", "text-tertiary", "Grayscale/400", "Grayscale/600"),
        ("Text/Primary-Subtle", "text-subtle", "Grayscale/450", "Grayscale/500"),
        ("Text/Inverted", "text-inverted", "Grayscale/870", "Grayscale/50"),
        ("Text/Info", "text-info", "Primary/350", "Primary/700"),
        ("Text/Error", "text-error", "Red/400", "Red/700"),
        ("Text/Success", "text-success", "Green/400", "Green/700"),
        ("Text/Warning", "text-warning", "Yellow/400", "Yellow/800"),
    ],
    "Icon": [
        ("Icon/Default", "icon-default", "Grayscale/50", "Grayscale/950"),
        ("Icon/Subtle", "icon-subtle", "Grayscale/450", "Grayscale/500"),
        ("Icon/Info", "icon-info", "Primary/350", "Primary/600"),
        ("Icon/Success", "icon-success", "Green/400", "Green/600"),
        ("Icon/Warning", "icon-warning", "Yellow/400", "Yellow/700"),
        ("Icon/Error", "icon-error", "Red/400", "Red/600"),
    ],
}
# data visualisation colors for review severity (kept apart from the brand accent)
SEV_COLOR = {"critical": "#F87171", "high": "#FB923C", "medium": "#FACC15", "low": "#60A5FA", "info": "#A3A3A3"}
SPACING = [("spacing-0", 0), ("spacing-25", 2), ("spacing-50", 4), ("spacing-75", 8), ("spacing-100", 12), ("spacing-200", 16),
           ("spacing-300", 24), ("spacing-400", 32), ("spacing-500", 40), ("spacing-600", 48), ("spacing-700", 64),
           ("spacing-800", 80), ("spacing-900", 96)]
RADIUS = [("radius-0", 0), ("radius-2", 2), ("radius-4", 4), ("radius-6", 6), ("radius-8", 8), ("radius-12", 12),
          ("radius-16", 16), ("radius-24", 24), ("radius-full", 9999)]
TEXT_STYLES = [("Heading 1", 60, 60, 600), ("Heading 2", 48, 48, 600), ("Heading 3", 36, 40, 600), ("Heading 4", 30, 36, 600),
               ("Heading 5", 24, 32, 600), ("Heading 6", 20, 28, 600), ("Title 1", 20, 28, 500), ("Title 2", 18, 28, 500),
               ("Title 3", 16, 24, 500), ("Title 4", 14, 20, 500), ("Title 5", 12, 16, 500), ("Body 1", 16, 24, 600),
               ("Body 3", 16, 24, 400), ("Body 4", 14, 20, 600), ("Body 6", 14, 20, 400), ("Button-md", 16, 24, 600),
               ("Button-sm", 14, 20, 600), ("Caption 1", 14, 20, 500), ("Caption 3", 12, 16, 600), ("Caption 5", 12, 16, 400)]


def resolve(alias: str) -> str:
    pal, shade = alias.split("/")
    return CORE[pal][shade]


def _var(alias: str) -> str:
    pal, shade = alias.split("/")
    return f"var(--{pal.lower()}-{shade})"


def _token_css() -> str:
    core = "".join(f"--{p.lower()}-{s}:{h};" for p, shades in CORE.items() for s, h in shades.items())
    dark = "".join(f"--{var}:{_var(d)};" for g in SYSTEM.values() for _n, var, d, _l in g)
    light = "".join(f"--{var}:{_var(lt)};" for g in SYSTEM.values() for _n, var, _d, lt in g)
    space = "".join(f"--{n}:{v}px;" for n, v in SPACING)
    rad = "".join(f"--{n}:{v}px;" for n, v in RADIUS)
    return f":root{{{core}{dark}{space}{rad}}}\n.cs-mode-light{{{light}}}\n"


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap');
@import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css');
@import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/fill/style.css');
""" + _token_css() + """
:root { --ease: cubic-bezier(0.22, 1, 0.36, 1); --mono: 'Geist Mono', ui-monospace, monospace; }

html, body, .stApp, .stMarkdown, button, input, textarea, select, label, p, li, h1, h2, h3, h4, h5, h6 {
  font-family: 'Geist', ui-sans-serif, system-ui, sans-serif !important; font-style: normal !important; }
code, pre, .stCode, kbd, .mono { font-family: var(--mono) !important; }
[class^="ph"], [class*=" ph"] { font-family: 'Phosphor', 'Phosphor-Fill' !important; }
.ph-fill { font-family: 'Phosphor-Fill' !important; }
.stApp { background: var(--surface-page); color: var(--text-primary); }
[data-testid="stHeader"] { background: transparent; }
.stAppDeployButton, [data-testid="stAppDeployButton"] { display: none; }
.block-container { padding-top: 96px; padding-bottom: 64px; max-width: 1200px; }
h1, h2, h3, h4 { font-weight: 600 !important; text-wrap: balance; letter-spacing: -0.01em; }
p, li { text-wrap: pretty; }
a, a:hover, a:visited, [data-testid="stMarkdownContainer"] a { text-decoration: none !important; }

/* ---------- named text styles (B1) ---------- */
.heading-1 { font-size: 60px; line-height: 60px; font-weight: 600; }
.heading-2 { font-size: 48px; line-height: 48px; font-weight: 600; }
.heading-3 { font-size: 36px; line-height: 40px; font-weight: 600; color: var(--text-primary); }
.heading-4 { font-size: 30px; line-height: 36px; font-weight: 600; }
.heading-5 { font-size: 24px; line-height: 32px; font-weight: 600; color: var(--text-primary); }
.heading-6 { font-size: 20px; line-height: 28px; font-weight: 600; color: var(--text-primary); }
.title-1 { font-size: 20px; line-height: 28px; font-weight: 500; color: var(--text-primary); }
.title-2 { font-size: 18px; line-height: 28px; font-weight: 500; color: var(--text-primary); }
.title-3 { font-size: 16px; line-height: 24px; font-weight: 500; color: var(--text-primary); }
.title-4 { font-size: 14px; line-height: 20px; font-weight: 500; color: var(--text-primary); }
.body-3 { font-size: 16px; line-height: 24px; font-weight: 400; color: var(--text-tertiary); }
.body-6 { font-size: 14px; line-height: 20px; font-weight: 400; color: var(--text-tertiary); }
.caption-1 { font-size: 14px; line-height: 20px; font-weight: 500; color: var(--text-secondary); }
.caption-3 { font-size: 12px; line-height: 16px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.06em; }
.caption-4 { font-size: 12px; line-height: 16px; font-weight: 500; color: var(--text-tertiary); }
.caption-5 { font-size: 12px; line-height: 16px; font-weight: 400; color: var(--text-subtle); }

/* ---------- floating nav (B7): translucent surface over a blur ---------- */
.cs-nav { position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 999990;
  display: flex; align-items: center; gap: 24px; padding: 8px 8px 8px 16px; border-radius: 9999px;
  background: rgba(24, 24, 24, 0.8); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-primary); white-space: nowrap; }
.stApp:has([data-testid="stSidebar"][data-collapsed="false"]) .cs-nav { left: calc(50% + 150px); }
.cs-nav .brand { display: flex; gap: 8px; align-items: center; font-size: 14px; line-height: 20px; font-weight: 600; color: var(--text-primary); }
.cs-nav .brand i { color: var(--icon-info); font-size: 20px; }
.cs-nav .links { display: flex; gap: 16px; }
.cs-nav .links a { font-size: 14px; line-height: 20px; font-weight: 500; color: var(--text-tertiary); transition: color 300ms var(--ease); }
.cs-nav .links a:hover, .cs-nav .links a.current { color: var(--text-primary); }
.cs-nav .cta { font-size: 14px; line-height: 20px; font-weight: 600; color: var(--text-inverted) !important; background: var(--action-primary);
  padding: 8px 12px; border-radius: 9999px; display: inline-flex; gap: 4px; align-items: center;
  transition: background-color 300ms var(--ease), transform 500ms var(--ease); }
.cs-nav .cta:hover { background: var(--action-primary-hover); transform: translateY(-1px); }
.cs-nav .cta:active { background: var(--action-primary-click); transform: scale(0.98); }

/* ---------- buttons: 5 types x 5 states (figma-designer) ---------- */
.cs-b { display: inline-flex; gap: 8px; align-items: center; justify-content: center; padding: 8px 12px; border-radius: 12px;
  font-size: 16px; line-height: 24px; font-weight: 600; border: 1px solid transparent; cursor: pointer;
  transition: background-color 300ms var(--ease), border-color 300ms var(--ease), color 300ms var(--ease), transform 500ms var(--ease); }
.cs-b.sm { font-size: 14px; line-height: 20px; }
.cs-b.t-primary { background: var(--action-primary); color: var(--text-inverted) !important; }
.cs-b.t-primary:hover, .cs-b.t-primary.s-hover { background: var(--action-primary-hover); }
.cs-b.t-primary:active, .cs-b.t-primary.s-pressed { background: var(--action-primary-click); transform: scale(0.98); }
.cs-b.t-secondary { background: var(--action-secondary); color: var(--text-primary) !important; border-color: var(--border-light); }
.cs-b.t-secondary:hover, .cs-b.t-secondary.s-hover { background: var(--action-secondary-hover); }
.cs-b.t-secondary:active, .cs-b.t-secondary.s-pressed { background: var(--action-secondary-click); transform: scale(0.98); }
.cs-b.t-tertiary { background: transparent; color: var(--text-info) !important; }
.cs-b.t-tertiary:hover, .cs-b.t-tertiary.s-hover { background: var(--surface-primary-hover); }
.cs-b.t-tertiary:active, .cs-b.t-tertiary.s-pressed { background: var(--surface-secondary); transform: scale(0.98); }
.cs-b.t-error { background: var(--action-error); color: #FFFFFF !important; }
.cs-b.t-error:hover, .cs-b.t-error.s-hover { background: var(--action-error-hover); }
.cs-b.t-error:active, .cs-b.t-error.s-pressed { transform: scale(0.98); }
.cs-b.t-warning { background: var(--action-warning); color: var(--text-inverted) !important; }
.cs-b.t-warning:hover, .cs-b.t-warning.s-hover { background: var(--action-warning-hover); }
.cs-b.t-warning:active, .cs-b.t-warning.s-pressed { transform: scale(0.98); }
.cs-b:focus-visible, .cs-b.s-focus { outline: 2px solid var(--border-action); outline-offset: 2px; }
.cs-b.s-disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

/* ---------- hero (B5): no eyebrow, no periods, Heading 1 ---------- */
.cs-hero { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(420px, 100%), 1fr)); gap: 48px; align-items: center; margin: 32px 0 48px 0; }
.cs-h1 { max-width: 680px; margin: 0 0 24px 0; letter-spacing: -0.02em;
  background: linear-gradient(90deg, #FFFFFF, #9B9B9B); -webkit-background-clip: text; background-clip: text; color: transparent; }
.cs-sub { font-size: 18px; line-height: 28px; font-weight: 400; color: var(--text-tertiary); max-width: 680px; }
.cs-actions { display: flex; gap: 12px; align-items: center; margin-top: 32px; flex-wrap: wrap; }
.cs-proofline { display: flex; gap: 8px; align-items: center; margin-top: 24px; font-size: 14px; line-height: 20px; color: var(--text-tertiary); }
.cs-proofline i { color: var(--icon-success); font-size: 16px; }

/* hero visual: the real report, flat */
.cs-preview { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 24px; padding: 16px; }
.cs-preview .chrome { display: flex; gap: 8px; align-items: center; padding: 0 4px 12px 4px; }
.cs-preview .chrome span { width: 12px; height: 12px; border-radius: 9999px; background: var(--surface-secondary); }
.cs-preview .chrome .path { width: auto; height: auto; background: none !important; margin-left: 8px; }
.cs-preview .pane { background: var(--surface-subtle); border: 1px solid var(--border-primary); border-radius: 8px; padding: 16px; }
.cs-preview .pane + .pane { margin-top: 8px; }
.cs-preview .row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.cs-preview .finding { display: flex; gap: 12px; align-items: flex-start; padding: 8px 0; }
.cs-preview .finding + .finding { border-top: 1px solid var(--border-primary); }
.cs-scan { position: relative; overflow: hidden; padding: 12px 0 !important; font-family: var(--mono) !important; font-size: 12px; line-height: 24px;
  background: var(--grayscale-1000) !important; }
.cs-scan .ln { display: grid; grid-template-columns: 24px minmax(0, 1fr) 16px; gap: 8px; padding: 0 12px; color: var(--text-tertiary); }
.cs-scan .ln .no { color: var(--text-subtle); text-align: right; }
.cs-scan .ln .c { white-space: pre; overflow: hidden; text-overflow: ellipsis; }
.cs-scan .ln.hit { background: var(--surface-error-subtle); color: var(--text-primary); }
.cs-scan .ln .flag { color: var(--icon-error); font-size: 14px; line-height: 24px; }
.cs-scan .k { color: var(--primary-300); } .cs-scan .s { color: var(--yellow-300); } .cs-scan .f { color: var(--secondary-200); }
.cs-scan .beam { position: absolute; left: 0; right: 0; top: 12px; height: 24px; pointer-events: none; background: rgba(146, 131, 235, 0.12);
  border-top: 1px solid var(--border-action); border-bottom: 1px solid var(--border-action); animation: cs-beam 3600ms var(--ease) infinite; }
@keyframes cs-beam { from { transform: translateY(0); } to { transform: translateY(96px); } }

/* ---------- bento proof grid ---------- */
.cs-bento { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); grid-auto-rows: minmax(152px, auto); gap: 16px; }
.cs-tile { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 24px; padding: 24px;
  display: flex; flex-direction: column; justify-content: space-between; gap: 16px; transition: border-color 300ms var(--ease), transform 500ms var(--ease); }
.cs-tile:hover { border-color: var(--border-light); transform: translateY(-2px); }
.cs-tile.big { grid-column: span 2; grid-row: span 2; }
.cs-tile.wide { grid-column: span 2; }
.cs-tile .num { font-family: var(--mono) !important; font-size: 48px; line-height: 48px; font-weight: 600; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.cs-tile .num.xl { font-size: 72px; line-height: 72px; }
.cs-tile .ico { width: 40px; height: 40px; border-radius: 12px; background: var(--surface-accent-subtle); color: var(--icon-info);
  display: grid; place-items: center; font-size: 20px; }
.cs-bars { display: flex; flex-direction: column; gap: 12px; }
.cs-bars .r { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4px 12px; align-items: center; }
.cs-bars .track { grid-column: 1 / -1; height: 8px; border-radius: 9999px; background: var(--surface-secondary); overflow: hidden; }
.cs-bars .track i { display: block; height: 100%; border-radius: 9999px; background: var(--action-primary); transform-origin: left; animation: cs-grow 900ms var(--ease) backwards; }
.cs-stack { display: flex; flex-wrap: wrap; gap: 8px; }
.cs-tag { display: inline-flex; gap: 8px; align-items: center; padding: 4px 12px; border-radius: 9999px; border: 1px solid var(--border-primary);
  background: var(--surface-subtle); font-size: 14px; line-height: 20px; color: var(--text-secondary); }
.cs-tag i { color: var(--icon-info); }

/* ---------- zig zag how it works ---------- */
.cs-zz { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 48px; align-items: center; padding: 40px 0; }
.cs-zz + .cs-zz { border-top: 1px solid var(--border-primary); }
.cs-zz.rev .txt { order: 2; }
.cs-zz .n { font-family: var(--mono) !important; font-size: 14px; line-height: 20px; color: var(--text-info); }
.cs-zz h3 { font-size: 30px !important; line-height: 36px !important; margin: 8px 0 12px 0; padding: 0; color: var(--text-primary); }
.cs-mini { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 16px; padding: 16px; }
.cs-mini .line { display: flex; gap: 8px; align-items: center; padding: 8px 12px; border-radius: 8px; background: var(--surface-subtle);
  border: 1px solid var(--border-primary); font-size: 14px; line-height: 20px; color: var(--text-secondary); }
.cs-mini .line + .line { margin-top: 8px; }
.cs-mini .line i { color: var(--icon-info); font-size: 16px; }
.cs-mini .line .ok { margin-left: auto; }
.cs-mini .line .ok i { color: var(--icon-success); }
.cs-mini .run { margin-left: auto; width: 64px; height: 4px; border-radius: 9999px; background: var(--surface-secondary); overflow: hidden; flex: none; }
.cs-mini .run i { display: block; height: 100%; width: 40%; background: var(--action-primary); border-radius: 9999px; animation: cs-run 1600ms var(--ease) infinite; }
@keyframes cs-run { from { transform: translateX(-100%); } to { transform: translateX(260%); } }
.cs-check { width: 16px; height: 16px; border-radius: 4px; border: 1px solid var(--border-light); display: grid; place-items: center; font-size: 12px; flex: none; }
.cs-check.on { background: var(--action-primary); border-color: var(--action-primary); }
.cs-check.on i { color: var(--text-inverted) !important; font-size: 12px !important; }

/* ---------- agent pipeline strip ---------- */
.cs-pipe { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 8px 0 24px 0; padding: 12px;
  border-radius: 16px; background: var(--surface-primary); border: 1px solid var(--border-primary); }
.cs-node { display: flex; align-items: center; gap: 4px; padding: 4px 8px; border-radius: 4px; background: var(--surface-subtle);
  border: 1px solid var(--border-primary); font-size: 12px; line-height: 16px; font-weight: 500; color: var(--text-tertiary); }
.cs-node i { font-size: 16px; color: var(--icon-subtle); }
.cs-node.done { color: var(--text-primary); border-color: var(--border-success); background: var(--surface-success-subtle); }
.cs-node.done i { color: var(--icon-success); }
.cs-node.active { color: var(--text-primary); border-color: var(--border-action); background: var(--surface-accent-subtle); }
.cs-node.active i { color: var(--icon-info); }
.cs-node.active small { color: var(--text-info); font-size: 12px; }
.cs-node.skip { opacity: 0.5; text-decoration: line-through; }
.cs-pipe .arrow { color: var(--icon-subtle); font-size: 12px; }
.cs-pipe .par { display: flex; flex-direction: column; gap: 4px; }

/* ---------- section scaffolding ---------- */
.cs-section { margin: 96px 0 32px 0; }
.cs-section .kicker { display: flex; gap: 8px; align-items: center; color: var(--text-info); }
.cs-section h2.title { margin: 12px 0 8px 0; max-width: 680px; padding: 0; }
.cs-band { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr)); gap: 24px; padding: 32px;
  border-radius: 24px; background: var(--surface-primary); border: 1px solid var(--border-primary); }
.cs-band .it { display: flex; gap: 12px; align-items: flex-start; }
.cs-band .it i { color: var(--icon-success); font-size: 20px; margin-top: 2px; }
.cs-grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr)); gap: 16px; }
.cs-stat { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 16px; padding: 24px; }
.cs-stat .num { font-family: var(--mono) !important; font-size: 36px; line-height: 40px; font-weight: 600; color: var(--text-primary); }

@supports (animation-timeline: view()) {
  .cs-reveal { animation: cs-rise linear both; animation-timeline: view(); animation-range: entry 0% entry 40%; }
}

/* ---------- tagline reveal (B11) ---------- */
.cs-tagline { margin: 96px 0; view-timeline-name: --tagline; }
.cs-tagline p { font-size: 60px; line-height: 60px; font-weight: 600; letter-spacing: -0.02em; max-width: 880px; color: var(--text-primary); }
.cs-tagline .w { opacity: 1; }
@supports (animation-timeline: view()) {
  .cs-tagline .w { opacity: 0.3; animation: cs-word var(--ease) both; animation-timeline: --tagline; animation-range: cover var(--s) cover var(--e); }
}
@keyframes cs-word { from { opacity: 0.3; } to { opacity: 1; } }

/* ---------- product UI ---------- */
.cs-chip { display: inline-flex; gap: 4px; align-items: center; padding: 2px 8px; border-radius: 9999px; font-size: 12px; line-height: 16px;
  font-weight: 500; color: var(--text-tertiary); background: var(--surface-subtle); border: 1px solid var(--border-primary); white-space: nowrap; }
.cs-chip.ok { color: var(--text-success); border-color: var(--border-success); background: var(--surface-success-subtle); }
.cs-chip.warn { color: var(--text-warning); border-color: var(--border-warning); background: var(--surface-warning-subtle); }
.cs-chip.info { color: var(--text-info); border-color: var(--border-action); background: var(--surface-accent-subtle); }
.cs-card { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 16px; padding: 16px 24px; animation: cs-rise 600ms var(--ease) backwards; }
.cs-card + .cs-card { margin-top: 12px; }
.cs-inner { background: var(--surface-subtle); border: 1px solid var(--border-primary); border-radius: 8px; padding: 8px 12px; }
.cs-badge { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; line-height: 16px; font-weight: 600;
  padding: 2px 8px; border-radius: 9999px; border: 1px solid currentColor; }
.sev-critical { color: #F87171; } .sev-high { color: #FB923C; } .sev-medium { color: #FACC15; } .sev-low { color: #60A5FA; } .sev-info { color: #A3A3A3; }
.verdict-block { color: var(--text-error); } .verdict-request_changes { color: #FB923C; }
.verdict-approve_with_comments { color: var(--text-warning); } .verdict-approve { color: var(--text-success); }

.cs-scoreboard { display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 16px; animation: cs-rise 700ms var(--ease) backwards; }
.cs-ring { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 16px; padding: 16px; display: flex;
  flex-direction: column; align-items: center; justify-content: center; gap: 8px; }
.cs-ring svg circle.track { stroke: var(--surface-secondary); }
.cs-ring svg circle.val { animation: cs-ring 1200ms var(--ease) both; }
@keyframes cs-ring { from { stroke-dashoffset: var(--c); } }
.cs-board { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 16px; padding: 24px; }
.cs-sevbar { display: flex; height: 12px; border-radius: 9999px; overflow: hidden; background: var(--surface-secondary); margin: 16px 0 12px 0; gap: 2px; }
.cs-sevbar span { display: block; height: 100%; transform-origin: left; animation: cs-grow 900ms var(--ease) backwards; }
@keyframes cs-grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.cs-legend { display: flex; gap: 16px; flex-wrap: wrap; }
.cs-legend span { display: inline-flex; gap: 4px; align-items: center; font-size: 12px; line-height: 16px; color: var(--text-tertiary); }
.cs-legend b { font-weight: 600; color: var(--text-primary); font-family: var(--mono) !important; }
.cs-legend i.sq { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }

.cs-agents { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr)); gap: 12px; margin-top: 12px; }
.cs-agent { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 16px; padding: 16px; display: flex; gap: 12px;
  animation: cs-rise 700ms var(--ease) backwards; }
.cs-agent .icon { width: 40px; height: 40px; flex: none; border-radius: 12px; background: var(--surface-accent-subtle); display: flex;
  align-items: center; justify-content: center; font-size: 20px; color: var(--icon-info); }

.cs-finding { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 16px; padding: 16px 16px 12px 16px; margin-top: 12px;
  transition: border-color 300ms var(--ease), transform 500ms var(--ease); animation: cs-rise 600ms var(--ease) backwards; }
.cs-finding:hover { transform: translateY(-2px); border-color: var(--border-light); }
.cs-finding.sev-critical-b { border-color: var(--border-error); }
.cs-finding .top { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.cs-finding .loc { font-family: var(--mono) !important; font-size: 12px; line-height: 16px; color: var(--text-info);
  background: var(--surface-accent-subtle); border: 1px solid var(--border-action); padding: 2px 8px; border-radius: 8px; }
.cs-finding .ev { margin-top: 12px; background: var(--grayscale-1000); border: 1px solid var(--border-primary); border-radius: 8px; padding: 8px 12px;
  font-family: var(--mono) !important; font-size: 12px; line-height: 16px; color: var(--text-primary); overflow-x: auto; white-space: pre; }

.cs-callout { border: 1px solid var(--border-warning); background: var(--surface-warning-subtle); border-radius: 12px; padding: 12px 16px;
  font-size: 14px; line-height: 20px; color: var(--text-primary); display: flex; gap: 8px; align-items: flex-start; }
.cs-callout i { color: var(--icon-warning); font-size: 16px; margin-top: 2px; }
.cs-callout + .cs-callout { margin-top: 8px; }

.cs-timeline { background: var(--surface-primary); border: 1px solid var(--border-primary); border-radius: 16px; padding: 8px 16px; }
.cs-step { display: flex; align-items: center; gap: 12px; font-size: 14px; line-height: 20px; color: var(--text-primary);
  padding: 8px 0; animation: cs-rise 500ms var(--ease) backwards; }
.cs-step + .cs-step { border-top: 1px solid var(--border-primary); }
.cs-step i { color: var(--icon-success); font-size: 16px; }

.cs-skel { border-radius: 8px; height: 16px; margin: 8px 0; background: var(--surface-secondary); animation: cs-pulse 1400ms var(--ease) infinite; }
.cs-skel.w60 { width: 60%; } .cs-skel.w40 { width: 40%; } .cs-skel.w80 { width: 80%; } .cs-skel.tall { height: 64px; }
.cs-empty { text-align: center; padding: 48px 24px; border: 1px dashed var(--border-light); border-radius: 16px; background: var(--surface-primary); }
.cs-empty .icon { width: 48px; height: 48px; margin: 0 auto 16px auto; border-radius: 12px; background: var(--surface-accent-subtle); display: flex;
  align-items: center; justify-content: center; font-size: 24px; color: var(--icon-info); }

.cs-footer { margin-top: 96px; padding: 32px 0; border-top: 1px solid var(--border-primary); display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.cs-footer a { color: var(--text-tertiary); font-size: 14px; line-height: 20px; transition: color 300ms var(--ease); }
.cs-footer a:hover { color: var(--text-primary); }

@keyframes cs-rise { from { opacity: 0; transform: translateY(32px); } to { opacity: 1; transform: none; } }
@keyframes cs-pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
.cs-code { font-family: var(--mono) !important; font-size: 12px; line-height: 16px; color: var(--text-info); background: var(--surface-accent-subtle);
  padding: 2px 4px; border-radius: 4px; }

/* ---------- foundations view (figma-designer) ---------- */
.cs-fd h4 { font-size: 20px !important; line-height: 28px !important; margin: 32px 0 12px 0; padding: 0; color: var(--text-primary); }
.cs-fd .pal { display: grid; grid-template-columns: 104px minmax(0, 1fr); gap: 12px; align-items: center; margin-bottom: 8px; }
.cs-fd .sw { display: flex; gap: 4px; overflow-x: auto; padding-bottom: 4px; }
.cs-fd .sw div { min-width: 52px; flex: 1; }
.cs-fd .sw b { display: block; height: 40px; border-radius: 8px; border: 1px solid var(--border-primary); }
.cs-fd .sw span { display: block; font-family: var(--mono) !important; font-size: 12px; line-height: 16px; color: var(--text-subtle); margin-top: 4px; }
.cs-fd table { width: 100%; border-collapse: collapse; font-size: 14px; line-height: 20px; }
.cs-fd th { text-align: left; color: var(--text-tertiary); font-weight: 500; padding: 8px 12px; border-bottom: 1px solid var(--border-primary); }
.cs-fd td { padding: 8px 12px; border-bottom: 1px solid var(--border-primary); color: var(--text-secondary); vertical-align: middle; }
.cs-fd td.mode { font-family: var(--mono) !important; font-size: 12px; white-space: nowrap; }
.cs-fd td.mode i { display: inline-block; width: 16px; height: 16px; border-radius: 4px; border: 1px solid var(--border-light); vertical-align: middle; margin-right: 8px; }
.cs-fd .bars div { display: grid; grid-template-columns: 104px 48px minmax(0, 1fr); gap: 12px; align-items: center; margin-bottom: 4px;
  font-family: var(--mono) !important; font-size: 12px; color: var(--text-tertiary); }
.cs-fd .bars b { display: block; height: 12px; border-radius: 2px; background: var(--action-primary); }
.cs-fd .radii { display: flex; flex-wrap: wrap; gap: 16px; }
.cs-fd .radii div { text-align: center; font-family: var(--mono) !important; font-size: 12px; color: var(--text-tertiary); }
.cs-fd .radii b { display: block; width: 64px; height: 64px; background: var(--surface-secondary); border: 1px solid var(--border-light); margin-bottom: 4px; }
.cs-fd .ts div { display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 16px; align-items: baseline; padding: 8px 0; border-bottom: 1px solid var(--border-primary); }
.cs-fd .ts span { font-family: var(--mono) !important; font-size: 12px; color: var(--text-subtle); }
.cs-fd .ts p { margin: 0; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cs-fd .btns { display: grid; grid-template-columns: 96px repeat(5, minmax(96px, 1fr)); gap: 8px; align-items: center; overflow-x: auto; }
.cs-fd .btns .h { font-size: 12px; color: var(--text-tertiary); }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: var(--surface-primary); border-right: none; }
[data-testid="stSidebar"] > div { background: transparent; }
.cs-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.cs-brand .mark { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; font-size: 24px; color: var(--text-inverted); background: var(--action-primary); }
.cs-brand .name { font-size: 20px; line-height: 28px; font-weight: 600; color: var(--text-primary); }
.cs-brand .sub { font-size: 12px; line-height: 16px; color: var(--text-tertiary); }
.cs-side-h { font-size: 12px; line-height: 16px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-tertiary); margin: 24px 0 8px 0; }
.cs-srow { display: flex; gap: 12px; align-items: flex-start; padding: 8px 12px; border-radius: 12px; background: var(--surface-subtle);
  border: 1px solid var(--border-primary); margin-bottom: 8px; }
.cs-srow .ico { width: 28px; height: 28px; flex: none; border-radius: 4px; display: grid; place-items: center; font-size: 16px; color: var(--icon-info); background: var(--surface-accent-subtle); }
.cs-srow .k { font-size: 12px; line-height: 16px; color: var(--text-subtle); }
.cs-srow .v { font-size: 14px; line-height: 20px; color: var(--text-primary); word-break: break-word; }
.cs-slink { display: flex; gap: 8px; align-items: center; padding: 4px 0; font-size: 14px; line-height: 20px; color: var(--text-tertiary) !important; transition: color 300ms var(--ease); }
.cs-slink:hover { color: var(--text-primary) !important; }

/* ---------- Streamlit widgets bound to the same tokens ---------- */
[data-baseweb="tab"] p, [data-testid="stPills"] button, [data-testid="stPills"] button p, [data-testid="stSegmentedControl"] button p,
[data-testid="stExpander"] summary p, [data-testid="stWidgetLabel"] p, .stCheckbox p, .stToggle p {
  font-family: 'Geist', ui-sans-serif, system-ui, sans-serif !important; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  padding: 8px 12px !important; border-radius: 12px !important; font-weight: 600 !important; min-height: 0 !important;
  background: var(--action-secondary); color: var(--text-primary); border: 1px solid var(--border-light) !important;
  transition: background-color 300ms var(--ease), border-color 300ms var(--ease), transform 500ms var(--ease) !important; }
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover { background: var(--action-secondary-hover); color: var(--text-primary); }
.stButton > button:active, .stDownloadButton > button:active { background: var(--action-secondary-click); transform: scale(0.98); }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible { outline: 2px solid var(--border-action) !important; outline-offset: 2px; }
.stButton > button[kind="primary"] { background: var(--action-primary) !important; color: var(--text-inverted) !important; border-color: var(--action-primary) !important; }
.stButton > button[kind="primary"]:hover { background: var(--action-primary-hover) !important; border-color: var(--action-primary-hover) !important; }
.stButton > button[kind="primary"]:active { background: var(--action-primary-click) !important; }
.stButton > button[kind="tertiary"] { background: transparent; border-color: transparent !important; color: var(--text-info); }
.stButton > button[kind="tertiary"]:hover { background: var(--surface-primary-hover); }
.stButton > button:disabled { opacity: 0.4; transform: none; }
.st-key-reject_report button { background: var(--action-error) !important; border-color: var(--action-error) !important; color: #FFFFFF !important; }
.st-key-reject_report button:hover { background: var(--action-error-hover) !important; }
.st-key-clear_caches button { background: var(--action-warning) !important; border-color: var(--action-warning) !important; color: var(--text-inverted) !important; }
.st-key-clear_caches button:hover { background: var(--action-warning-hover) !important; }
[data-testid="stExpander"] details { border-radius: 16px !important; border: 1px solid var(--border-primary) !important; background: var(--surface-primary); }
[data-testid="stExpander"] summary { font-weight: 500; }
[data-testid="stTabs"] [role="tablist"], .stTabs [data-baseweb="tab-list"] { gap: 4px; background: var(--surface-primary); border: 1px solid var(--border-primary) !important;
  border-radius: 16px; padding: 4px; width: fit-content; max-width: 100%; }
[data-testid="stTab"], .stTabs [data-baseweb="tab"] { padding: 8px 16px !important; border-radius: 12px; color: var(--text-tertiary); border: none !important;
  box-shadow: none !important; height: auto; transition: background-color 300ms var(--ease), color 300ms var(--ease); }
[data-testid="stTab"]::after, [data-testid="stTab"]::before, .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }
[data-testid="stTab"]:hover { color: var(--text-primary); }
[data-testid="stTab"][aria-selected="true"], .stTabs [aria-selected="true"] { background: var(--surface-secondary); color: var(--text-primary); }
[data-testid="stTab"] p { font-weight: 500; }
[data-baseweb="textarea"], [data-baseweb="input"], [data-baseweb="select"] > div { border-radius: 12px !important; background: var(--surface-primary) !important;
  border-color: var(--border-primary) !important; transition: border-color 300ms var(--ease); }
[data-baseweb="textarea"]:focus-within, [data-baseweb="input"]:focus-within { border-color: var(--border-action) !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--border-primary); border-radius: 12px; overflow: hidden; }
[data-testid="stAlert"] { border-radius: 16px; }
[data-testid="stFileUploaderDropzone"] { background: var(--surface-primary); border: 1px dashed var(--border-light); border-radius: 16px; }

/* ---------- responsive (390px check) ---------- */
@media (max-width: 900px) {
  .cs-bento { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .cs-zz { grid-template-columns: minmax(0, 1fr); gap: 24px; padding: 32px 0; }
  .cs-zz.rev .txt { order: 0; }
  .cs-scoreboard { grid-template-columns: minmax(0, 1fr); }
  .heading-1, .cs-h1 { font-size: 36px; line-height: 40px; }
  .cs-tagline p { font-size: 36px; line-height: 40px; }
  .heading-3 { font-size: 30px; line-height: 36px; }
  .cs-nav .links, .cs-nav .cs-chip { display: none; }
  .cs-nav { max-width: calc(100% - 32px); gap: 16px; left: 50% !important; }
  .block-container { padding-top: 80px; }
  .cs-fd .ts div { grid-template-columns: minmax(0, 1fr); gap: 4px; }
}
@media (max-width: 560px) {
  .cs-bento { grid-template-columns: minmax(0, 1fr); }
  .cs-tile.big, .cs-tile.wide { grid-column: auto; grid-row: auto; }
  .cs-tile .num.xl { font-size: 60px; line-height: 60px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: opacity 200ms linear !important; }
  .cs-tagline .w { opacity: 1 !important; }
  .cs-reveal { opacity: 1 !important; transform: none !important; }
}
</style>
"""

SEV_ORDER = ["critical", "high", "medium", "low", "info"]
SEV_ICON = {"critical": "ph-warning-octagon", "high": "ph-warning", "medium": "ph-warning-circle", "low": "ph-info", "info": "ph-note"}
VERDICT_ICON = {"block": "ph-prohibit", "request_changes": "ph-arrow-u-up-left", "approve_with_comments": "ph-chat-circle-text",
                "approve": "ph-check-circle"}
VERDICT_LABEL = {"block": "Blocked", "request_changes": "Changes requested", "approve_with_comments": "Approved with comments",
                 "approve": "Approved"}
AGENT_ICON = {"bugs": "ph-bug-beetle", "security": "ph-shield-warning", "tests": "ph-flask"}
PIPE_NODES = [("intake", "ph-tray-arrow-down", "Intake"), ("plan", "ph-strategy", "Plan"), ("gate1", "ph-user-check", "You approve"),
              ("agents", "", ""), ("aggregate", "ph-stack", "Report"), ("gate2", "ph-hand", "You approve"),
              ("actions", "ph-lightning", "Actions")]


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
    body = "".join(f'<div class="cs-srow"><span class="ico"><i class="ph {i}"></i></span><div><div class="k">{e(k)}</div>'
                   f'<div class="v">{e(v)}</div></div></div>' for i, k, v in rows)
    return f'<div class="cs-side-h">System status</div>{body}'


def side_links(repo_url: str) -> str:
    links = [("ph-github-logo", "Source code", repo_url), ("ph-file-text", "Documentation", f"{repo_url}/blob/main/docs/PROJECT_DOCUMENTATION.md"),
             ("ph-chart-bar", "Eval results", f"{repo_url}/blob/main/evals/results.md")]
    return '<div class="cs-side-h">Project</div>' + "".join(
        f'<a class="cs-slink" href="{u}" target="_blank" rel="noopener"><i class="ph {i}"></i>{t}</a>' for i, t, u in links)


def pipeline(done: set[str] | frozenset = frozenset(), active: str | None = None, skipped: set[str] | frozenset = frozenset()) -> str:
    """The review graph as a strip of nodes. State is shown by icon and label, never by color alone."""
    def node(key: str, icon: str, label: str) -> str:
        if key in done:
            return f'<div class="cs-node done"><i class="ph-fill ph-check-circle"></i> {label}</div>'
        if key == active:
            return f'<div class="cs-node active"><i class="ph ph-hourglass-medium"></i> {label} <small>· waiting</small></div>'
        if key in skipped:
            return f'<div class="cs-node skip"><i class="ph ph-minus-circle"></i> {label}</div>'
        return f'<div class="cs-node"><i class="ph {icon}"></i> {label}</div>'

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
    return """
<section class="cs-hero" aria-label="Introduction">
  <div>
    <h1 class="cs-h1 heading-1">Catch the bugs your<br>reviewers miss<br>before you merge</h1>
    <div class="cs-sub">Three specialist agents check every change for bugs, security holes and missing tests
    at the same time. You approve the plan, you approve the report, and nothing ships without you.</div>
    <div class="cs-actions">
      <a class="cs-b t-primary" href="#workspace"><i class="ph ph-play"></i>Run a free review</a>
      <a class="cs-b t-tertiary" href="#how-it-works">See how it works<i class="ph ph-arrow-down"></i></a>
    </div>
    <div class="cs-proofline"><i class="ph-fill ph-seal-check"></i>Found 31 of 31 seeded issues with 100% precision in our evals</div>
  </div>
  <div class="cs-preview" role="img" aria-label="Preview of a CodeSentinel review report">
    <div class="chrome"><span></span><span></span><span></span><span class="path caption-5 mono">payments.py · review report</span></div>
    <div class="pane">
      <div class="row">
        <div><div class="caption-3">Verdict</div><div class="heading-6 verdict-block" style="margin-top:4px"><i class="ph ph-prohibit"></i> Blocked</div></div>
        <div style="text-align:right"><div class="caption-3">Quality score</div><div class="heading-6 mono" style="margin-top:4px">22 <span class="caption-5">/ 100</span></div></div>
      </div>
      <div class="cs-sevbar" style="margin:12px 0 0 0"><span style="width:44%;background:#F87171"></span><span style="width:12%;background:#FACC15"></span><span style="width:44%;background:#60A5FA"></span></div>
    </div>
    <div class="pane cs-scan">
      <div class="ln"><span class="no">32</span><span class="c"><span class="k">def</span> <span class="f">refund</span>(order_id, token):</span><span></span></div>
      <div class="ln hit"><span class="no">33</span><span class="c">    claims = jwt.<span class="f">decode</span>(token, verify=<span class="k">False</span>)</span><i class="ph-fill ph-warning-octagon flag"></i></div>
      <div class="ln"><span class="no">34</span><span class="c">    amount = <span class="f">float</span>(order[<span class="s">"total"</span>])</span><span></span></div>
      <div class="ln hit"><span class="no">50</span><span class="c">    os.<span class="f">system</span>(<span class="s">f"refund {order_id}"</span>)</span><i class="ph-fill ph-warning-octagon flag"></i></div>
      <div class="ln"><span class="no">51</span><span class="c">    <span class="k">return</span> {<span class="s">"ok"</span>: <span class="k">True</span>}</span><span></span></div>
      <div class="beam"></div>
    </div>
    <div class="pane">
      <div class="finding"><span class="cs-badge sev-critical"><i class="ph ph-warning-octagon"></i>Critical</span>
        <div><div class="title-4">JWT signature not verified</div><div class="caption-5 mono">payments.py:33 · CWE 347</div></div></div>
      <div class="finding"><span class="cs-badge sev-critical"><i class="ph ph-warning-octagon"></i>Critical</span>
        <div><div class="title-4">Shell command injection risk</div><div class="caption-5 mono">payments.py:50 · CWE 78</div></div></div>
    </div>
  </div>
</section>
<section class="cs-bento cs-reveal" aria-label="Results">
  <div class="cs-tile big">
    <div><div class="caption-3">Seeded issues found</div><div class="num xl" style="margin-top:12px">31/31</div>
    <div class="body-6" style="margin-top:8px">Line level ground truth across three sample services, rule based mode</div></div>
    <div class="cs-bars">
      <div class="r"><span class="caption-1">Loyalty portal API</span><span class="caption-4 mono">12/12</span><div class="track"><i style="width:100%"></i></div></div>
      <div class="r"><span class="caption-1">Inventory sync pipeline</span><span class="caption-4 mono">12/12</span><div class="track"><i style="width:100%"></i></div></div>
      <div class="r"><span class="caption-1">Checkout refunds with tests</span><span class="caption-4 mono">7/7</span><div class="track"><i style="width:100%"></i></div></div>
    </div>
  </div>
  <div class="cs-tile"><span class="ico"><i class="ph ph-crosshair"></i></span><div><div class="num">100%</div><div class="body-6">precision on bug and security findings</div></div></div>
  <div class="cs-tile"><span class="ico"><i class="ph ph-ruler"></i></span><div><div class="num">29</div><div class="body-6">grounded rules the agents use as evidence</div></div></div>
  <div class="cs-tile wide"><div><div class="caption-3">Human approvals</div><div class="num" style="margin-top:12px">2</div></div>
    <div class="body-6">One before the agents run, one before anything is saved, posted or remembered</div></div>
</section>"""


def how_it_works() -> str:
    plan = """<div class="cs-mini"><div class="caption-3">Review plan · risk high</div>
<div class="line" style="margin-top:12px"><i class="ph ph-bug-beetle"></i>Bug and anti pattern agent<span class="ok"><i class="ph-fill ph-check-circle"></i></span></div>
<div class="line"><i class="ph ph-shield-warning"></i>Security agent<span class="ok"><i class="ph-fill ph-check-circle"></i></span></div>
<div class="line"><i class="ph ph-target"></i>Focus: authorization on every route</div></div>"""
    agents = """<div class="cs-mini"><div class="caption-3">Running in parallel</div>
<div class="line" style="margin-top:12px"><i class="ph ph-bug-beetle"></i>Bugs · read_code<span class="run"><i></i></span></div>
<div class="line"><i class="ph ph-shield-warning"></i>Security · run_static_checks<span class="run"><i style="animation-delay:-500ms"></i></span></div>
<div class="line"><i class="ph ph-flask"></i>Tests · list_functions<span class="run"><i style="animation-delay:-1000ms"></i></span></div></div>"""
    approve = """<div class="cs-mini"><div class="caption-3">Approve actions</div>
<div class="line" style="margin-top:12px"><span class="cs-check on"><i class="ph ph-check"></i></span>Save the report</div>
<div class="line"><span class="cs-check"></span>Post the pull request comment</div>
<div class="line"><span class="cs-check on"><i class="ph ph-check"></i></span>Remember my feedback</div>
<div style="margin-top:12px"><span class="cs-b t-primary sm"><i class="ph ph-check"></i>Approve and run actions</span></div></div>"""
    rows = [
        ("01", "The orchestrator plans", "It reads the change, rates the risk and decides which specialists run. The graph pauses so you can edit or approve the plan.", plan, False),
        ("02", "Three agents work in parallel", "Bug, security and test agents each run a reasoning loop with read only tools, and quote the exact line for every claim they make.", agents, True),
        ("03", "You decide what ships", "Findings arrive ranked with a score and a verdict. Dismiss false positives, then tick only the actions you want to run.", approve, False),
    ]
    body = "".join(f'<div class="cs-zz{" rev" if rev else ""}"><div class="txt"><div class="n">{n}</div><h3>{t}</h3>'
                   f'<div class="body-3" style="max-width:480px">{d}</div></div><div>{v}</div></div>' for n, t, d, v, rev in rows)
    return f"""
<section class="cs-section cs-reveal" id="how-it-works">
  <div class="kicker caption-3"><i class="ph ph-graph"></i>How it works</div>
  <h2 class="title heading-3">A review team that never<br>skips the checklist</h2>
  <div class="body-3" style="max-width:680px">Built as a LangGraph state machine with checkpoints, so a review can pause for you and resume exactly where it stopped.</div>
  <div style="margin-top:16px">{body}</div>
  {pipeline()}
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
    return """
<section class="cs-section cs-reveal" aria-label="Benefits">
  <div class="kicker caption-3"><i class="ph ph-sparkle"></i>Why teams keep it</div>
  <h2 class="title heading-3">Built for reviews<br>you can trust</h2>
  <div class="cs-bento" style="margin-top:32px">
    <div class="cs-tile wide"><div><span class="ico"><i class="ph ph-crosshair"></i></span>
      <div class="title-2" style="margin-top:16px">Grounded, not guessed</div>
      <div class="body-6" style="margin-top:8px">Every finding quotes the real line. Claims whose quote is not in the file are dropped and counted on the Monitor tab.</div></div>
      <div class="cs-finding" style="margin:0;animation:none"><div class="top"><span class="loc">app.py:13</span><span class="cs-chip ok"><i class="ph ph-check"></i>evidence found in file</span></div>
      <div class="ev">app.config["SECRET_KEY"] = "f9c2e71be04d..."</div></div>
    </div>
    <div class="cs-tile wide"><div><span class="ico"><i class="ph ph-brain"></i></span>
      <div class="title-2" style="margin-top:16px">Remembers your team</div>
      <div class="body-6" style="margin-top:8px">Dismiss a false positive once and it stays dismissed. Conventions you add feed every agent prompt for that project.</div></div>
      <div class="cs-stack"><span class="cs-tag"><i class="ph ph-book-open"></i>Money uses Decimal</span><span class="cs-tag"><i class="ph ph-eye-slash"></i>1 finding suppressed</span></div>
    </div>
    <div class="cs-tile wide"><div><span class="ico"><i class="ph ph-plugs-connected"></i></span>
      <div class="title-2" style="margin-top:16px">Fits the tools you use</div>
      <div class="body-6" style="margin-top:8px">The same graph runs as an MCP server for Claude Desktop, Claude Code or Cursor, and an A2A agent card describes its skills.</div></div>
      <div class="cs-stack"><span class="cs-tag"><i class="ph ph-terminal"></i>review_code</span><span class="cs-tag"><i class="ph ph-github-logo"></i>review_github</span><span class="cs-tag"><i class="ph ph-shield"></i>scan_security</span></div>
    </div>
    <div class="cs-tile wide"><div><span class="ico"><i class="ph ph-lifebuoy"></i></span>
      <div class="title-2" style="margin-top:16px">Works when the model fails</div>
      <div class="body-6" style="margin-top:8px">Retries, a backup provider, JSON repair and a rule based fallback keep every review running, and the monitor shows which path ran.</div></div>
      <div class="cs-stack"><span class="cs-tag">Retry</span><span class="cs-tag">Backup model</span><span class="cs-tag">JSON repair</span><span class="cs-tag">Rules</span></div>
    </div>
  </div>
</section>"""


def risk_reversal() -> str:
    items = [("ph-key", "No API key needed", "Runs in rule based mode out of the box. Add a key to switch on the LLM agents."),
             ("ph-eye", "Read only agents", "Agents never edit code, post or run what they review."),
             ("ph-hand", "You approve every write", "Saving, posting and remembering wait for your tick, and criticals need an acknowledgement."),
             ("ph-terminal-window", "Run it yourself", "Clone the repository and start it with uv in one command.")]
    cells = "".join(f'<div class="it"><i class="ph-fill {i}"></i><div><div class="title-3">{t}</div>'
                    f'<div class="body-6" style="margin-top:4px">{d}</div></div></div>' for i, t, d in items)
    return f'<section class="cs-section cs-reveal" aria-label="What you risk"><div class="cs-band">{cells}</div></section>'


def section_head(anchor: str, icon: str, kicker: str, title: str, body: str = "") -> str:
    return (f'<section class="cs-section" id="{anchor}" style="margin-bottom:24px"><div class="kicker caption-3"><i class="ph {icon}"></i>{kicker}</div>'
            f'<h2 class="title heading-3">{title}</h2>' + (f'<div class="body-3" style="max-width:680px">{body}</div>' if body else "") + "</section>")


def footer(repo_url: str) -> str:
    return f"""
<footer class="cs-footer">
  <div><div class="title-4"><i class="ph-fill ph-shield-check" style="color:var(--icon-info)"></i> CodeSentinel</div>
  <div class="caption-5" style="margin-top:4px">Week 3 project by Bala · Mastering Agentic AI, The Gen Academy</div></div>
  <div style="display:flex;gap:24px;flex-wrap:wrap">
    <a href="{repo_url}" target="_blank" rel="noopener"><i class="ph ph-github-logo"></i> Source code</a>
    <a href="{repo_url}/blob/main/docs/PROJECT_DOCUMENTATION.md" target="_blank" rel="noopener"><i class="ph ph-file-text"></i> Documentation</a>
    <a href="{repo_url}/blob/main/evals/results.md" target="_blank" rel="noopener"><i class="ph ph-chart-bar"></i> Eval results</a>
    <a href="#workspace"><i class="ph ph-arrow-up"></i> Back to workspace</a>
  </div>
</footer>"""


def foundations() -> str:
    """The Foundations frame from figma-designer, rendered from the same tokens the CSS uses."""
    pals = "".join(
        f'<div class="pal"><div class="title-4">{p}</div><div class="sw">' + "".join(
            f'<div><b style="background:{h}"></b><span>{s}</span></div>' for s, h in shades.items()) + "</div></div>"
        for p, shades in CORE.items())
    rows = []
    for toks in SYSTEM.values():
        for name, _var, dark, light in toks:
            rows.append(f'<tr><td>{e(name)}</td><td class="mode"><i style="background:{resolve(dark)}"></i>{dark}</td>'
                        f'<td class="mode"><i style="background:{resolve(light)}"></i>{light}</td></tr>')
    table = f'<table><tr><th>Token</th><th>Dark</th><th>Light</th></tr>{"".join(rows)}</table>'
    bars = "".join(f'<div><span>{n}</span><span>{v}px</span><b style="width:{max(v, 1)}px"></b></div>' for n, v in SPACING)
    radii = "".join(f'<div><b style="border-radius:{min(v, 32)}px"></b>{n}</div>' for n, v in RADIUS)
    styles = "".join(f'<div><span>{n} · {s}/{lh} · {w}</span><p style="font-size:{s}px;line-height:{lh}px;font-weight:{w}">Catch the bugs your reviewers miss</p></div>'
                     for n, s, lh, w in TEXT_STYLES)
    states = ["default", "hover", "pressed", "focus", "disabled"]
    btns = '<div class="h"></div>' + "".join(f'<div class="h">{s.title()}</div>' for s in states)
    for t in ["primary", "secondary", "tertiary", "error", "warning"]:
        btns += f'<div class="h">{t.title()}</div>' + "".join(
            f'<span class="cs-b sm t-{t} s-{s}" role="presentation">Approve</span>' for s in states)
    return f"""<div class="cs-fd">
<div class="body-6">Rendered from the design tokens in <code class="cs-code">codesentinel/ui_style.py</code>. Change a Core Color there and every swatch,
token and component on this page follows, the same way the Foundations frame works in the figma-designer skill.</div>
<h4>Core Colors</h4>{pals}
<h4>Color System · Dark and Light modes</h4><div class="cs-card" style="padding:0;overflow-x:auto">{table}</div>
<h4>Buttons · 5 types × 5 states</h4><div class="cs-card"><div class="btns">{btns}</div></div>
<h4>Spacing</h4><div class="cs-card bars">{bars}</div>
<h4>Radius</h4><div class="cs-card radii">{radii}</div>
<h4>Text styles</h4><div class="cs-card ts">{styles}</div>
</div>"""


def score_ring(score: int, verdict: str, previous: int | None) -> str:
    r, c = 52, 2 * 3.14159 * 52
    color = {"block": resolve("Red/400"), "request_changes": "#FB923C", "approve_with_comments": resolve("Yellow/400"),
             "approve": resolve("Green/400")}[verdict]
    off = c * (1 - score / 100)
    prev = f'<div class="caption-5">previous review {previous}</div>' if previous is not None else '<div class="caption-5">first review</div>'
    return f"""
<div class="cs-ring">
  <svg width="128" height="128" viewBox="0 0 128 128" aria-label="Quality score {score} of 100">
    <circle class="track" cx="64" cy="64" r="{r}" fill="none" stroke-width="10"/>
    <circle class="val" cx="64" cy="64" r="{r}" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"
      stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}" style="--c:{c:.1f}" transform="rotate(-90 64 64)"/>
    <text x="64" y="62" text-anchor="middle" fill="#F7F7F7" font-family="Geist Mono" font-size="30" font-weight="600">{score}</text>
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
      <div style="text-align:right"><div class="caption-3">Findings</div><div class="heading-4 mono" style="margin-top:4px;color:var(--text-primary)">{len(report["findings"])}</div></div>
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
<span class="cs-chip {'info' if r['mode'] == 'llm' else ''}">{mode}</span><span class="cs-chip">{r.get('duration_s', 0)}s</span>
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
