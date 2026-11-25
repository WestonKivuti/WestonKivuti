#!/usr/bin/env python3
"""
Generates the animated terminal card and the contact badges used in the
GitHub profile README.

Usage:
    python generate_assets.py

Edit ONLY the CONFIG section below (colors, font, text), run the script,
then commit the files it writes into the assets/ folder.
"""
import html
import os

# ============================== CONFIG ==============================

# Colors. Change a hex code here and re-run to re-theme everything.
COLORS = {
    "bg": "#101224",      # terminal / card background
    "bg2": "#181b33",     # badge background
    "blue": "#4d8dff",    # primary: commands, first-word highlight
    "orange": "#ff9f43",  # secondary: flags, arrow, border
    "gold": "#ffd166",    # highlight: header, cursor, status pill
    "text": "#eef2ff",    # typed lines
    "muted": "#7d86a8",   # comments and small labels
}

# Font stack. GitHub cannot load web fonts inside an image, so the first
# font that is installed on the visitor's device is used, then the next.
FONT = "'JetBrains Mono','Fira Code','IBM Plex Mono',Consolas,'DejaVu Sans Mono',monospace"

TITLE_BAR = "weston@mmu: ~/profile (main)"
STATUS_PILL = "AVAILABLE"

# First section: types once and stays on screen (does not loop).
HEADER = "Hey I'm Weston"

# Lines that type one after another and then loop.
# Each entry is (command, comment shown after it, the line that gets typed).
# To make a line ALTERNATE between several texts on each loop, put a list of
# entries in its place, like the last one below. The loop then repeats after
# every variant has been shown once.
BLOCKS = [
    ("weston --role", "# who I am", "A Software Engineering Student"),
    ("weston --learning", "# what I'm learning", "Learning software engineering skills, cloud computing and AI/ML"),
    [
        ("weston --roles", "# what I do", "Developer | Cloud Engineer | AI Builder"),
        ("weston --status", "# availability", "Open to Internships, Collaborations and Networking"),
    ],
]

# Contact badges: (label, color name from COLORS, icon). Icons: email, whatsapp, linkedin.
BADGES = [
    ("EMAIL", "orange", "email"),
    ("WHATSAPP", "gold", "whatsapp"),
    ("LINKEDIN", "blue", "linkedin"),
]

HOLD_SECONDS = 5.0      # how long the finished lines stay before the loop restarts
TYPING_SPEED = 0.045    # seconds per character for the typed lines
OUT_DIR = "assets"

# ============================ END CONFIG ============================

CW = 9.0                 # character width at font-size 15
HFS = 36                 # header font size
CWH = HFS * 0.6          # character width of the header
W = 820                  # card width
X_ARROW, X_TILDE, X_TXT = 36, 56, 76


def esc(s):
    return html.escape(s, quote=False)


def frame(pcts, decl):
    return ",".join(f"{v:.3f}%" for v in pcts) + "{" + decl + "}"


def kf(name, *frames):
    return "@keyframes " + name + "{" + "".join(frames) + "}"


def build_terminal():
    slots = [blk if isinstance(blk, list) else [blk] for blk in BLOCKS]
    n_cycles = max(len(sl) for sl in slots)

    hs = 0.6                              # header start
    hd = len(HEADER) * 0.11               # header typing time
    loop_delay = hs + hd + 0.7

    # One schedule per loop cycle. A cycle shows one variant of every slot.
    cycles = []
    off = 0.0
    for k in range(n_cycles):
        cur = 0.05
        items = []
        for sl in slots:
            cmd, com, resp = sl[k % len(sl)]
            cs = off + cur
            ce = cs + max(0.7, len(cmd) * 0.055)
            rs = ce + 0.2
            re_ = rs + len(resp) * TYPING_SPEED
            items.append(dict(cs=cs, ce=ce, rs=rs, re=re_))
            cur = re_ - off + 0.7
        fade_s = off + cur - 0.7 + HOLD_SECONDS
        fade_e = fade_s + 0.8
        cycles.append(dict(items=items, fade_s=fade_s, fade_e=fade_e))
        off = fade_e + 0.7
    P = off                               # full period of the animation

    def p(t):
        return max(0.0, t / P * 100)

    T0 = "transform:translateX(0)"

    def kf_block(name, act):
        fr = [frame([0], "opacity:0")]
        for cs, fs, fe in act:
            fr += [
                frame([p(cs) - 0.01], "opacity:0"),
                frame([p(cs), p(fs)], "opacity:1"),
                frame([p(fe)], "opacity:0"),
            ]
        fr.append(frame([100], "opacity:0"))
        return kf(name, *fr)

    def kf_cover(name, act, n, wd):
        # A cover rectangle hides its line until it slides right, one step per
        # character. Once the line is revealed the cover is parked well off the
        # card so it never sits on top of the text to its right.
        fr = [frame([0], T0)]
        for s_, e_, fe in act:
            fr += [
                frame([p(s_)], f"{T0};animation-timing-function:steps({n},end)"),
                frame([p(e_)], f"transform:translateX({wd:g}px)"),
                frame([p(e_) + 0.01, p(fe)], f"transform:translateX({wd + 700:g}px)"),
                frame([p(fe) + 0.01], T0),
            ]
        fr.append(frame([100], T0))
        return kf(name, *fr)

    def kf_cursor(name, act, n, wd):
        fr = [frame([0], T0)]
        for s_, e_, fe in act:
            fr += [
                frame([p(s_)], f"{T0};animation-timing-function:steps({n},end)"),
                frame([p(e_), p(fe)], f"transform:translateX({wd:g}px)"),
                frame([p(fe) + 0.01], T0),
            ]
        fr.append(frame([100], T0))
        return kf(name, *fr)

    def kf_window(name, act):
        fr = [frame([0], "opacity:0")]
        for s_, e_ in act:
            fr += [
                frame([p(s_) - 0.01], "opacity:0"),
                frame([p(s_), p(e_)], "opacity:1"),
                frame([p(e_) + 0.01], "opacity:0"),
            ]
        fr.append(frame([100], "opacity:0"))
        return kf(name, *fr)

    css = []
    body = []

    # y positions
    y_head = 110
    ys = []
    for i in range(len(slots)):
        yc = 172 + i * 64
        ys.append((yc, yc + 26))
    H = ys[-1][1] + 34

    # ---------- header (types once, never loops) ----------
    wh = len(HEADER) * CWH
    tv = hs + hd + 0.55
    css.append(kf("hv", "from{transform:translateX(0)}", f"to{{transform:translateX({wh:g}px)}}"))
    css.append(
        kf(
            "hcu",
            frame([0, hs / tv * 100 - 0.01], "opacity:0"),
            frame([hs / tv * 100, 99], "opacity:1"),
            frame([100], "opacity:0"),
        )
    )
    css.append(f".hv{{animation:hv {hd:.2f}s steps({len(HEADER)},end) {hs}s 1 both}}")
    css.append(f".hcuv{{animation:hcu {tv:.2f}s linear 0s 1 both}}")

    body.append(
        f'<text class="head" x="{X_ARROW}" y="{y_head}" textLength="{wh:g}" lengthAdjust="spacing">{esc(HEADER)}</text>'
    )
    body.append(f'<rect class="cover hv" x="{X_ARROW}" y="{y_head - 40}" width="{wh + 4:g}" height="56"/>')
    body.append(
        f'<g class="hv"><g class="hcuv"><rect class="cur blink" x="{X_ARROW}" y="{y_head - 30}" width="14" height="36" rx="2"/></g></g>'
    )

    # ---------- looping blocks ----------
    css.append(
        f".loop{{animation-duration:{P:.2f}s;animation-delay:{loop_delay:.2f}s;"
        "animation-iteration-count:infinite;animation-timing-function:linear}"
    )
    for i, sl in enumerate(slots):
        yc, yr = ys[i]
        last_slot = i == len(slots) - 1
        for v, (cmd, com, resp) in enumerate(sl):
            ks = [k for k in range(n_cycles) if k % len(sl) == v]   # cycles where this variant shows
            key = f"{i}v{v}"
            n_cmd, n_resp = len(cmd), len(resp)
            wd_c, wd_r = n_cmd * CW, n_resp * CW

            blk_act, cmd_act, resp_act, cc_act, cr_act, ci_act = [], [], [], [], [], []
            for k in ks:
                it, cy = cycles[k]["items"][i], cycles[k]
                blk_act.append((it["cs"], cy["fade_s"], cy["fade_e"]))
                cmd_act.append((it["cs"], it["ce"], cy["fade_e"]))
                resp_act.append((it["rs"], it["re"], cy["fade_e"]))
                cc_act.append((it["cs"], it["ce"] + 0.2))
                cr_act.append((it["rs"], cy["fade_e"] if last_slot else it["re"] + 0.3))
                ci_act.append((it["ce"], cy["fade_e"]))

            css.append(kf_block(f"b{key}", blk_act))
            css.append(kf_cursor(f"mc{key}", cmd_act, n_cmd, wd_c))
            css.append(kf_cursor(f"mr{key}", resp_act, n_resp, wd_r))
            css.append(kf_cover(f"cmc{key}", cmd_act, n_cmd, wd_c))
            css.append(kf_cover(f"cmr{key}", resp_act, n_resp, wd_r))
            css.append(kf_window(f"cc{key}", cc_act))
            css.append(kf_window(f"cr{key}", cr_act))
            css.append(kf_window(f"ci{key}", ci_act))
            for nm in ("b", "mc", "mr", "cmc", "cmr", "cc", "cr", "ci"):
                css.append(f".{nm}{key}{{animation-name:{nm}{key}}}")

            first, *rest = cmd.split(" ")
            cmd_markup = f'<tspan class="blue bold">{esc(first)}</tspan>'
            if rest:
                cmd_markup += f' <tspan class="orange">{esc(" ".join(rest))}</tspan>'
            xc = X_TXT + wd_c + 2 * CW
            wd_com = len(com) * CW

            body.append(f'<g class="loop blk b{key}">')
            body.append(f'<text class="orange bold" x="{X_ARROW}" y="{yc}">\u279c</text>')
            body.append(f'<text class="muted" x="{X_TILDE}" y="{yc}">~</text>')
            body.append(f'<text class="cmd" x="{X_TXT}" y="{yc}" textLength="{wd_c:g}" lengthAdjust="spacing">{cmd_markup}</text>')
            body.append(
                f'<text class="loop ci ci{key} muted" x="{xc:g}" y="{yc}" textLength="{wd_com:g}" lengthAdjust="spacing">{esc(com)}</text>'
            )
            body.append(f'<text class="resp" x="{X_TXT}" y="{yr}" textLength="{wd_r:g}" lengthAdjust="spacing">{esc(resp)}</text>')
            body.append(f'<rect class="cover loop cmc{key}" x="{X_TXT}" y="{yc - 22}" width="{wd_c + 3:g}" height="30"/>')
            body.append(f'<rect class="cover loop cmr{key}" x="{X_TXT}" y="{yr - 22}" width="{wd_r + 3:g}" height="30"/>')
            body.append(
                f'<g class="loop mc{key}"><g class="loop cuv cc{key}"><rect class="cur blink" x="{X_TXT}" y="{yc - 16}" width="8" height="20" rx="1"/></g></g>'
            )
            body.append(
                f'<g class="loop mr{key}"><g class="loop cuv cr{key}"><rect class="cur blink" x="{X_TXT}" y="{yr - 16}" width="8" height="20" rx="1"/></g></g>'
            )
            body.append("</g>")

    vars_css = ";".join(f"--{k_}:{v_}" for k_, v_ in COLORS.items())
    style = f"""
:root{{{vars_css};--font:{FONT}}}
text{{font-family:var(--font);font-size:15px;fill:var(--text)}}
.head{{font-size:{HFS}px;font-weight:700;fill:url(#gh)}}
.blue{{fill:var(--blue)}} .orange{{fill:var(--orange)}} .muted{{fill:var(--muted)}} .bold{{font-weight:700}}
.cover{{fill:var(--bg)}}
.cur{{fill:var(--gold)}}
.blk,.ci,.cuv,.hcuv{{opacity:0}}
.pill{{font-size:11px;font-weight:700;fill:var(--gold)}}
.title{{font-size:12px;fill:var(--muted)}}
.blink{{animation:blink 1s infinite}}
.pulse{{animation:pulse 2s ease-in-out infinite}}
@keyframes blink{{0%,49.9%{{opacity:1}}50%,100%{{opacity:0}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
{''.join(css)}
@media (prefers-reduced-motion:reduce){{
  *{{animation:none!important}}
  .cover,.cuv,.hcuv,.alt{{display:none}}
  .blk,.ci{{opacity:1!important}}
}}
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(HEADER)}">
<title>{esc(HEADER)}</title>
<style>{style}</style>
<defs>
<linearGradient id="bd" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" style="stop-color:var(--blue)"/><stop offset="0.45" style="stop-color:var(--blue)"/>
<stop offset="0.8" style="stop-color:var(--orange)"/><stop offset="1" style="stop-color:var(--gold)"/>
</linearGradient>
<linearGradient id="gh" gradientUnits="userSpaceOnUse" x1="{X_ARROW}" y1="0" x2="{X_ARROW + wh:g}" y2="0">
<stop offset="0" style="stop-color:var(--gold)"/><stop offset="1" style="stop-color:var(--orange)"/>
</linearGradient>
</defs>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="var(--bg)" stroke="url(#bd)" stroke-width="2"/>
<circle cx="28" cy="23" r="6" fill="#ff5f57"/><circle cx="48" cy="23" r="6" fill="#febc2e"/><circle cx="68" cy="23" r="6" fill="#28c840"/>
<text class="title" x="{W // 2}" y="27" text-anchor="middle">{esc(TITLE_BAR)}</text>
<rect x="{W - 134}" y="10" width="112" height="26" rx="13" fill="none" stroke="var(--gold)" stroke-width="1.2"/>
<circle class="pulse" cx="{W - 117}" cy="23" r="3.5" fill="var(--gold)"/>
<text class="pill" x="{W - 107}" y="27" textLength="76" lengthAdjust="spacing">{esc(STATUS_PILL)}</text>
<line x1="0" y1="46" x2="{W}" y2="46" stroke="var(--muted)" stroke-opacity="0.25"/>
{chr(10).join(body)}
</svg>
"""
    return svg


ICONS = {
    "email": (
        '<rect x="10" y="13" width="20" height="14" rx="2" fill="none" stroke="{d}" stroke-width="2"/>'
        '<polyline points="10.5,14.5 20,21.5 29.5,14.5" fill="none" stroke="{d}" stroke-width="2" stroke-linejoin="round"/>'
    ),
    "whatsapp": (
        '<circle cx="20" cy="19.5" r="9" fill="none" stroke="{d}" stroke-width="2"/>'
        '<path d="M11.5 29 L13.4 23.6 L16.8 27.4 Z" fill="{d}"/>'
        '<path d="M16.4 15.4c-.5.5-.6 1.2-.3 2 .9 2.2 2.6 3.9 4.8 4.8.8.3 1.5.2 2-.3l.6-.8c.2-.3.1-.6-.1-.8l-1.5-1c-.3-.2-.6-.1-.8.1l-.4.5c-1.2-.5-2.1-1.4-2.6-2.6l.5-.4c.2-.2.3-.5.1-.8l-1-1.5c-.2-.2-.5-.3-.8-.1z" fill="{d}"/>'
    ),
    "linkedin": (
        '<rect x="11" y="11" width="18" height="18" rx="3" fill="{d}"/>'
        '<circle cx="15.2" cy="16" r="1.7" fill="{a}"/>'
        '<rect x="13.8" y="19" width="2.8" height="7.5" fill="{a}"/>'
        '<path d="M19 19h2.7v1.1c.5-.8 1.4-1.3 2.6-1.3 2.2 0 2.9 1.4 2.9 3.4v4.3h-2.8v-3.8c0-.9-.3-1.6-1.2-1.6s-1.5.7-1.5 1.7v3.7H19z" fill="{a}"/>'
    ),
}


def build_badge(label, color_key, icon):
    accent = COLORS[color_key]
    dark = COLORS["bg"]
    tl = len(label) * 9.4
    w = 44 + 14 + tl + 18
    h = 40
    icon_markup = ICONS[icon].format(d=dark, a=accent)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h}" viewBox="0 0 {w:g} {h}" role="img" aria-label="{esc(label.title())}">
<title>{esc(label.title())}</title>
<rect x="0.75" y="0.75" width="{w - 1.5:g}" height="{h - 1.5}" rx="9" fill="{COLORS['bg2']}" stroke="{accent}" stroke-width="1.5"/>
<path d="M9.75 0.75H44V39.25H9.75a9 9 0 0 1-9-9V9.75a9 9 0 0 1 9-9z" fill="{accent}"/>
<g transform="translate(2,0)">{icon_markup}</g>
<text x="58" y="25.5" textLength="{tl:g}" lengthAdjust="spacing" style="font-family:{FONT};font-size:13px;font-weight:700;fill:{COLORS['text']}">{esc(label)}</text>
</svg>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "terminal.svg"), "w", encoding="utf-8") as f:
        f.write(build_terminal())
    for label, color_key, icon in BADGES:
        with open(os.path.join(OUT_DIR, f"badge-{icon}.svg"), "w", encoding="utf-8") as f:
            f.write(build_badge(label, color_key, icon))
    print(f"Wrote terminal.svg and {len(BADGES)} badges to {OUT_DIR}/")


if __name__ == "__main__":
    main()
