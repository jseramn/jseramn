#!/usr/bin/env python3
"""
Renderiza token-card-dark.svg y token-card-light.svg desde el export del token monitor.
Estetica terminal/monospace coherente con la ASCII card del perfil.
"""
import json
import sys
from datetime import datetime, timezone

EXPORT_PATH = r"${USERPROFILE}/usage-registry/token-monitor-export.json"

W, H = 1000, 400

THEMES = {
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "text": "#c9d1d9", "dim": "#8b949e",
        "accent": "#3fb950", "accent2": "#58a6ff", "accent3": "#d29922",
        "bar_bg": "#21262d", "gridline": "#21262d",
    },
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "text": "#1f2328", "dim": "#59636e",
        "accent": "#1a7f37", "accent2": "#0969da", "accent3": "#9a6700",
        "bar_bg": "#eaeef2", "gridline": "#eaeef2",
    },
}

CLIENT_COLORS_DARK = {"devin": "#a371f7", "codex": "#3fb950", "antigravity": "#58a6ff", "grok": "#f778ba", "opencode": "#d29922", "hermes": "#76e3ea", "claude": "#e3b341", "cursor": "#79c0ff"}
CLIENT_COLORS_LIGHT = {"devin": "#8250df", "codex": "#1a7f37", "antigravity": "#0969da", "grok": "#bf3989", "opencode": "#9a6700", "hermes": "#1b7c83", "claude": "#9a6700", "cursor": "#0550ae"}


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


def render(theme_name, data):
    t = THEMES[theme_name]
    client_colors = CLIENT_COLORS_DARK if theme_name == "dark" else CLIENT_COLORS_LIGHT
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
        gen_dt = datetime.fromisoformat(gen.replace("Z", "+00:00"))
        stamp = gen_dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        stamp = gen[:16]

    mono = "'Consolas','Menlo','DejaVu Sans Mono',monospace"
    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="AI token telemetry for jseramn">')
    out.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="8" fill="{t["bg"]}" stroke="{t["border"]}"/>')

    # ---- header ----
    out.append(f'<text x="28" y="38" fill="{t["accent"]}" font-family="{mono}" font-size="15" font-weight="bold">$ ai-telemetry --live</text>')
    out.append(f'<text x="972" y="38" fill="{t["dim"]}" font-family="{mono}" font-size="11" text-anchor="end">updated {esc(stamp)} · refreshes every 24h</text>')

    # ---- hero metrics (4 columns spread full width) ----
    hero_y = 92
    n_agents = len(per_client)
    heroes = [
        ("ALL-TIME TOKENS", fmt_tokens(alltime_tokens), f"${alltime_cost:,.0f} usd", t["accent"]),
        ("THIS MONTH", fmt_tokens(month_tokens), f"${month_cost:,.0f} usd", t["accent2"]),
        ("TODAY", fmt_tokens(today_tokens), f"${today_cost:,.2f} usd", t["accent3"]),
        ("AGENTS ORCHESTRATED", str(n_agents), "this month", "#f778ba" if theme_name == "dark" else "#bf3989"),
    ]
    for i, (label, big, sub, color) in enumerate(heroes):
        x = 28 + i * 245
        out.append(f'<text x="{x}" y="{hero_y - 22}" fill="{t["dim"]}" font-family="{mono}" font-size="11" letter-spacing="2">{label}</text>')
        out.append(f'<text x="{x}" y="{hero_y + 16}" fill="{color}" font-family="{mono}" font-size="36" font-weight="bold">{big}</text>')
        out.append(f'<text x="{x}" y="{hero_y + 40}" fill="{t["dim"]}" font-family="{mono}" font-size="12">{sub}</text>')

    # divider
    out.append(f'<line x1="28" y1="158" x2="972" y2="158" stroke="{t["border"]}" stroke-width="1"/>')

    # ---- daily bar chart (bottom left) ----
    chart_x, chart_y, chart_w, chart_h = 28, 250, 560, 100
    out.append(f'<text x="{chart_x}" y="{chart_y - 12}" fill="{t["dim"]}" font-family="{mono}" font-size="11" letter-spacing="2">DAILY TOKENS — LAST {len(daily)} ACTIVE DAYS</text>')
    max_tok = max((d["tokens"] for d in daily), default=1) or 1
    n = len(daily)
    gap = 4
    bw = (chart_w - gap * (n - 1)) / n
    for i, d in enumerate(daily):
        h = max(2, (d["tokens"] / max_tok) * chart_h)
        x = chart_x + i * (bw + gap)
        y = chart_y + chart_h - h
        today_mark = ' stroke="{}" stroke-width="1.5"'.format(t["accent3"]) if i == n - 1 else ""
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="1.5" fill="{t["accent"]}" opacity="0.85"{today_mark}/>')
    # baseline
    out.append(f'<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="{t["border"]}" stroke-width="1"/>')
    # min/max labels
    out.append(f'<text x="{chart_x}" y="{chart_y + chart_h + 18}" fill="{t["dim"]}" font-family="{mono}" font-size="10">{esc(daily[0]["date"][5:]) if daily else ""}</text>')
    out.append(f'<text x="{chart_x + chart_w}" y="{chart_y + chart_h + 18}" fill="{t["dim"]}" font-family="{mono}" font-size="10" text-anchor="end">{esc(daily[-1]["date"][5:]) if daily else ""} · peak {fmt_tokens(max_tok)}</text>')

    # ---- per-client bars (right column) — values right-aligned at fixed x ----
    cx, cy = 640, 250
    val_x = 962  # right edge for values
    bar_max_w = 130
    out.append(f'<text x="{cx}" y="{cy - 12}" fill="{t["dim"]}" font-family="{mono}" font-size="11" letter-spacing="2">THIS MONTH BY AGENT (log)</text>')
    max_ct = max((v["tokens"] for _, v in clients), default=1) or 1
    row_h = 21
    for i, (name, v) in enumerate(clients):
        y = cy + 8 + i * row_h
        color = client_colors.get(name, t["accent2"])
        import math
        bar_w = max(2, (math.log10(v["tokens"] + 1) / math.log10(max_ct + 1)) * bar_max_w)
        out.append(f'<text x="{cx}" y="{y + 11}" fill="{t["text"]}" font-family="{mono}" font-size="11">{esc(name[:12])}</text>')
        out.append(f'<rect x="{cx + 100}" y="{y}" width="{bar_w:.1f}" height="13" rx="2" fill="{color}" opacity="0.9"/>')
        out.append(f'<text x="{val_x}" y="{y + 11}" fill="{t["dim"]}" font-family="{mono}" font-size="10" text-anchor="end">{fmt_tokens(v["tokens"])}</text>')

    # ---- footer ----
    fy = H - 18
    out.append(f'<text x="28" y="{fy}" fill="{t["dim"]}" font-family="{mono}" font-size="10">tokens measured across local agent sessions · source: private token monitor</text>')

    out.append("</svg>")
    return "\n".join(out)


def main():
    with open(EXPORT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    for theme in ("dark", "light"):
        svg = render(theme, data)
        import os.path
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"token-card-{theme}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"OK {path} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
