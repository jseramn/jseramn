#!/usr/bin/env python3
"""
Blueprint-brutalist profile card generator for jseramn/jseramn.
Composite card: halftone portrait + neofetch + whoami + KPI grid +
24-day token chart + agent ranking. Zero rounded corners (rx=0),
24px blueprint grid, calibration corner brackets.

Theme switching: set THEME below (or env CARD_THEME) to one of:
  1_industrial_concrete_original | 2_high_glow_cyberpunk |
  3_forest_terminal | 4_oceanic_matrix
"""
import json
import os
from datetime import datetime

EXPORT_PATH = r"${USERPROFILE}/usage-registry/token-monitor-export.json"
AVATAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatar-src.png")

THEME = os.environ.get("CARD_THEME", "2_high_glow_cyberpunk")

ARCH = {
    "borderRadius": 0,
    "gridSize": 24,
    "bracketSizeLarge": 12,
    "bracketThicknessLarge": 2,
    "bracketSizeSmall": 6,
    "bracketThicknessSmall": 1,
    "fontFamily": "'JetBrains Mono','Geist Mono','Fira Code',monospace",
}

THEMES = {
    "1_industrial_concrete_original": {
        "bg_canvas": "#14171A", "bg_surface": "#1C2126", "bg_elevated": "#252B32",
        "grid_line": "rgba(148,163,184,0.14)", "border_technical": "#38414A",
        "text_primary": "#F1F5F9", "text_secondary": "#94A3B8",
        "accent_primary": "#5B8DEF", "accent_secondary": "#6366F1", "accent_alert": "#F97316",
    },
    "2_high_glow_cyberpunk": {
        "bg_canvas": "#08090C", "bg_surface": "#0E1118", "bg_elevated": "#151A26",
        "grid_line": "rgba(130,60,250,0.18)", "border_technical": "rgba(130,60,250,0.45)",
        "text_primary": "#F1F5F9", "text_secondary": "#94A3B8",
        "accent_primary": "#0E76FD", "accent_secondary": "#823CFA", "accent_alert": "#FF2A9E",
    },
    "3_forest_terminal": {
        "bg_canvas": "#0B0D0C", "bg_surface": "#121614", "bg_elevated": "#1A201D",
        "grid_line": "rgba(52,211,153,0.14)", "border_technical": "rgba(16,185,129,0.35)",
        "text_primary": "#D1FAE5", "text_secondary": "#6EE7B7",
        "accent_primary": "#10B981", "accent_secondary": "#059669", "accent_alert": "#F59E0B",
    },
    "4_oceanic_matrix": {
        "bg_canvas": "#0F172A", "bg_surface": "#1E293B", "bg_elevated": "#273549",
        "grid_line": "rgba(148,163,184,0.16)", "border_technical": "rgba(6,182,212,0.40)",
        "text_primary": "#F8FAFC", "text_secondary": "#94A3B8",
        "accent_primary": "#06B6D4", "accent_secondary": "#38BDF8", "accent_alert": "#FB7185",
    },
}

W, H = 1100, 690
FONT = ARCH["fontFamily"]


def fmt_tokens(n):
    if n >= 1e9:
        return f"{n/1e9:.2f}B"
    if n >= 1e6:
        return f"{n/1e6:.1f}M"
    if n >= 1e3:
        return f"{n/1e3:.0f}K"
    return str(int(n))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hexmix(c1, c2, t):
    a = [int(c1[i:i+2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i+2], 16) for i in (1, 3, 5)]
    return "#{:02x}{:02x}{:02x}".format(*[round(a[i] + (b[i] - a[i]) * t) for i in range(3)])


def brackets(x, y, w, h, size, thick, color):
    """Calibration L-brackets at the 4 corners of rect (x,y,w,h)."""
    s, t = size, thick
    c = []
    for cx, cy, dx, dy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        c.append(
            f'<path d="M{cx + dx*s} {cy} L{cx} {cy} L{cx} {cy + dy*s}" '
            f'fill="none" stroke="{color}" stroke-width="{t}"/>'
        )
    return "".join(c)


def render(data, theme_key):
    t = THEMES[theme_key]
    snap = data["snapshot"]
    daily = data["daily"][-24:]
    monthly = data["monthly"]
    cur_month = monthly[-1] if monthly else {}
    per_client = {k: v for k, v in cur_month.get("perClient", {}).items() if k != "unknown"}
    clients = sorted(per_client.items(), key=lambda kv: -kv[1]["tokens"])[:6]

    alltime_tokens = snap["allTime"]["totalTokens"]
    alltime_cost = snap["allTime"]["costUsd"]
    month_tokens = snap["month"]["totalTokens"]
    month_cost = snap["month"]["costUsd"]
    today_tokens = snap["today"]["totalTokens"]
    today_cost = snap["today"]["costUsd"]

    gen = data.get("generatedAt", "")
    try:
        stamp = datetime.fromisoformat(gen.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        stamp = gen[:16]

    g = ARCH["gridSize"]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="jseramn blueprint profile card">']

    # defs: 24px blueprint grid + diagonal hatch for secondary bars
    out.append(f'''<defs>
  <pattern id="grid" width="{g}" height="{g}" patternUnits="userSpaceOnUse">
    <path d="M{g} 0 L0 0 0 {g}" fill="none" stroke="{t["grid_line"]}" stroke-width="1"/>
  </pattern>
  <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="6" stroke="{t["accent_alert"]}" stroke-width="1.4" opacity="0.75"/>
  </pattern>
</defs>''')

    # canvas
    out.append(f'<rect width="{W}" height="{H}" fill="{t["bg_canvas"]}"/>')

    # ---- header strip
    out.append(f'<text x="28" y="38" font-family="{FONT}" font-size="17" font-weight="700" fill="{t["accent_primary"]}">jseramn@github</text>')
    out.append(f'<text x="{W-28}" y="38" text-anchor="end" font-family="{FONT}" font-size="11" letter-spacing="0.08em" fill="{t["text_secondary"]}">$ ai-telemetry --live &#9654; {esc(stamp)}</text>')
    out.append(f'<line x1="28" y1="52" x2="{W-28}" y2="52" stroke="{t["border_technical"]}" stroke-width="1"/>')

    # ---- ROW 1: portrait / neofetch / whoami  (y 64..244)
    r1y, r1h = 64, 180
    # neofetch panel (sin retrato: el avatar de github ya cumple ese rol)
    nx, nw = 28, 500
    out.append(f'<rect x="{nx}" y="{r1y}" width="{nw}" height="{r1h}" fill="{t["bg_surface"]}"/>')
    out.append(f'<rect x="{nx}" y="{r1y}" width="{nw}" height="{r1h}" fill="url(#grid)"/>')
    out.append(f'<rect x="{nx}" y="{r1y}" width="{nw}" height="{r1h}" fill="none" stroke="{t["border_technical"]}" stroke-width="1"/>')
    out.append(brackets(nx + 5, r1y + 5, nw - 10, r1h - 10, ARCH["bracketSizeSmall"], ARCH["bracketThicknessSmall"], t["border_technical"]))
    neo = [
        ("os", "windows 11 x64"),
        ("role", "agentic systems builder"),
        ("location", "colombia"),
        ("uptime", "4y on github"),
        ("web", "jseramn.tech"),
        ("shell", "multi-agent harness"),
        ("harnesses", "devin codex claude junie +5"),
    ]
    for i, (k, v) in enumerate(neo):
        yy = r1y + 30 + i * 22
        out.append(f'<text x="{nx+18}" y="{yy}" font-family="{FONT}" font-size="12.5" fill="{t["accent_primary"]}">{esc(k)}</text>')
        out.append(f'<text x="{nx+130}" y="{yy}" font-family="{FONT}" font-size="12.5" fill="{t["text_primary"]}">{esc(v)}</text>')

    # whoami panel
    wx = nx + nw + 24
    ww = W - 28 - wx
    out.append(f'<rect x="{wx}" y="{r1y}" width="{ww}" height="{r1h}" fill="{t["bg_surface"]}"/>')
    out.append(f'<rect x="{wx}" y="{r1y}" width="{ww}" height="{r1h}" fill="url(#grid)"/>')
    out.append(f'<rect x="{wx}" y="{r1y}" width="{ww}" height="{r1h}" fill="none" stroke="{t["border_technical"]}" stroke-width="1"/>')
    out.append(brackets(wx + 5, r1y + 5, ww - 10, r1h - 10, ARCH["bracketSizeSmall"], ARCH["bracketThicknessSmall"], t["border_technical"]))
    out.append(f'<text x="{wx+18}" y="{r1y+30}" font-family="{FONT}" font-size="12.5" font-weight="700" fill="{t["accent_primary"]}">$ whoami</text>')
    who = [
        "building agentic systems —",
        "mostly in private.",
        "",
        "contributing in public:",
        "concord-mcp · gentle-ai",
        "",
        "rendering human thoughts",
        "into synthetic machines",
    ]
    for i, line in enumerate(who):
        out.append(f'<text x="{wx+18}" y="{r1y+56+i*17}" font-family="{FONT}" font-size="12" fill="{t["text_secondary"]}">{esc(line)}</text>')

    # ---- ROW 2: KPI cards (y 256..352)
    ky, kh = 256, 96
    gap = 16
    kw = (W - 56 - 3 * gap) / 4
    kpis = [
        ("ALL-TIME TOKENS", fmt_tokens(alltime_tokens), f"${alltime_cost:,.0f} usd", t["text_primary"], t["text_secondary"]),
        ("THIS MONTH", fmt_tokens(month_tokens), f"${month_cost:,.0f} usd", t["text_primary"], t["text_secondary"]),
        ("TODAY", fmt_tokens(today_tokens), f"${today_cost:,.2f} usd", t["accent_alert"], t["accent_alert"]),
        ("AGENTS ORCHESTRATED", str(len(per_client)), "active this month", t["text_primary"], t["text_secondary"]),
    ]
    for i, (label, big, sub, bigc, subc) in enumerate(kpis):
        x = 28 + i * (kw + gap)
        out.append(f'<rect x="{x}" y="{ky}" width="{kw}" height="{kh}" fill="{t["bg_surface"]}"/>')
        out.append(f'<rect x="{x}" y="{ky}" width="{kw}" height="{kh}" fill="url(#grid)"/>')
        out.append(f'<rect x="{x}" y="{ky}" width="{kw}" height="{kh}" fill="none" stroke="{t["border_technical"]}" stroke-width="1"/>')
        out.append(brackets(x - 3, ky - 3, kw + 6, kh + 6, ARCH["bracketSizeLarge"], ARCH["bracketThicknessLarge"], t["accent_alert"]))
        out.append(f'<text x="{x+14}" y="{ky+24}" font-family="{FONT}" font-size="11" letter-spacing="0.08em" fill="{t["text_secondary"]}">{esc(label)}</text>')
        out.append(f'<text x="{x+14}" y="{ky+62}" font-family="{FONT}" font-size="32" font-weight="700" fill="{bigc}">{esc(big)}</text>')
        out.append(f'<text x="{x+kw-14}" y="{ky+84}" text-anchor="end" font-family="{FONT}" font-size="11" fill="{subc}">{esc(sub)}</text>')

    # ---- ROW 3: 24-day chart (y 364..496)
    cy, ch_h = 364, 132
    cw = W - 56
    out.append(f'<rect x="28" y="{cy}" width="{cw}" height="{ch_h}" fill="{t["bg_surface"]}"/>')
    out.append(f'<rect x="28" y="{cy}" width="{cw}" height="{ch_h}" fill="url(#grid)"/>')
    out.append(f'<rect x="28" y="{cy}" width="{cw}" height="{ch_h}" fill="none" stroke="{t["border_technical"]}" stroke-width="1"/>')
    out.append(f'<text x="42" y="{cy+22}" font-family="{FONT}" font-size="11" letter-spacing="0.08em" fill="{t["text_secondary"]}">DAILY TOKENS — LAST 24 DAYS</text>')
    chart_x, chart_y = 42, cy + 32
    chart_w, chart_h = cw - 28, ch_h - 48
    max_tok = max((d["tokens"] for d in daily), default=1) or 1
    n = len(daily)
    bgap = 5
    bw = (chart_w - bgap * (n - 1)) / n
    peak_thresh = max_tok * 0.85
    for i, d in enumerate(daily):
        h = max(2, (d["tokens"] / max_tok) * chart_h)
        x = chart_x + i * (bw + bgap)
        y = chart_y + chart_h - h
        color = t["accent_alert"] if d["tokens"] >= peak_thresh else t["accent_primary"]
        op = "1" if d["tokens"] >= peak_thresh else "0.8"
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{color}" opacity="{op}"/>')

    # ---- ROW 4: agents panel (y 508..670)
    ay, ah = 508, 158
    aw = W - 56
    out.append(f'<rect x="28" y="{ay}" width="{aw}" height="{ah}" fill="{t["bg_surface"]}"/>')
    out.append(f'<rect x="28" y="{ay}" width="{aw}" height="{ah}" fill="url(#grid)"/>')
    out.append(f'<rect x="28" y="{ay}" width="{aw}" height="{ah}" fill="none" stroke="{t["border_technical"]}" stroke-width="1"/>')
    out.append(brackets(25, ay - 3, aw + 6, ah + 6, ARCH["bracketSizeLarge"], ARCH["bracketThicknessLarge"], t["accent_alert"]))
    out.append(f'<text x="42" y="{ay+22}" font-family="{FONT}" font-size="11" letter-spacing="0.08em" fill="{t["text_secondary"]}">THIS MONTH BY AGENT</text>')
    if clients:
        maxa = clients[0][1]["tokens"] or 1
        row_h = 20
        bar_x = 150
        bar_maxw = aw - 150 - 130 - 40
        for i, (name, v) in enumerate(clients):
            yy = ay + 44 + i * row_h
            out.append(f'<text x="42" y="{yy+9}" font-family="{FONT}" font-size="12" fill="{t["text_primary"]}">{esc(name)}</text>')
            wlen = max(3, (v["tokens"] / maxa) * bar_maxw)
            if i == 0:
                out.append(f'<rect x="{bar_x}" y="{yy}" width="{wlen:.0f}" height="12" fill="{t["accent_secondary"]}"/>')
            else:
                out.append(f'<rect x="{bar_x}" y="{yy}" width="{wlen:.0f}" height="12" fill="{t["bg_elevated"]}"/>')
                out.append(f'<rect x="{bar_x}" y="{yy}" width="{wlen:.0f}" height="12" fill="url(#hatch)"/>')
            out.append(f'<text x="{bar_x+bar_maxw+12}" y="{yy+10}" font-family="{FONT}" font-size="12" text-anchor="start" fill="{t["text_primary"]}">{fmt_tokens(v["tokens"])}</text>')

    out.append('</svg>')
    return "".join(out)


def main():
    data = json.load(open(EXPORT_PATH, encoding="utf-8"))
    here = os.path.dirname(os.path.abspath(__file__))

    svg = render(data, THEME)
    with open(os.path.join(here, "token-card.svg"), "w", encoding="utf-8") as f:
        f.write(svg)

    os.makedirs(os.path.join(here, "themes"), exist_ok=True)
    for key in THEMES:
        with open(os.path.join(here, "themes", f"token-card-{key}.svg"), "w", encoding="utf-8") as f:
            f.write(render(data, key))

    print(f"rendered: token-card.svg [{THEME}] + {len(THEMES)} theme previews")


if __name__ == "__main__":
    main()
