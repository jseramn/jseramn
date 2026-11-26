#!/usr/bin/env python3
"""
Renderiza token-card.svg desde el export del token monitor.
Sistema de tokens de diseno del perfil:
  neon-blue #0E76FD / neon-purple #823CFA / warm-amber #B67E5A
  ice-white #E0E6ED / abyss-navy #0D172A / void-black #131317
"""
import json
import math
import os.path
from datetime import datetime

EXPORT_PATH = r"${USERPROFILE}/usage-registry/token-monitor-export.json"

W, H = 1000, 400

# CAPA 1+2: tokens primitivos -> semanticos
NEON_BLUE = "#0E76FD"
NEON_PURPLE = "#823CFA"
WARM_AMBER = "#B67E5A"
ICE_WHITE = "#E0E6ED"
ABYSS_NAVY = "#0D172A"
VOID_BLACK = "#131317"
TEXT_SECONDARY = "#94A3B8"
SURFACE_ELEVATED = "#162238"

# por agente: rotacion de acentos del sistema (el top agente es neon-purple por jerarquia)
AGENT_ROTATION = [NEON_PURPLE, NEON_BLUE, NEON_BLUE, NEON_BLUE, NEON_BLUE, NEON_BLUE]


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


def render(data):
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

    # defs: glow filters + gradientes
    out.append(f'''<defs>
  <filter id="glow-blue" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="5" result="b"/>
    <feFlood flood-color="{NEON_BLUE}" flood-opacity="0.55" result="c"/>
    <feComposite in="c" in2="b" operator="in" result="glow"/>
    <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow-purple" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="5" result="b"/>
    <feFlood flood-color="{NEON_PURPLE}" flood-opacity="0.6" result="c"/>
    <feComposite in="c" in2="b" operator="in" result="glow"/>
    <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow-amber" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="4" result="b"/>
    <feFlood flood-color="{WARM_AMBER}" flood-opacity="0.55" result="c"/>
    <feComposite in="c" in2="b" operator="in" result="glow"/>
    <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="bar-grad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{NEON_BLUE}" stop-opacity="1"/>
    <stop offset="1" stop-color="{NEON_BLUE}" stop-opacity="0.45"/>
  </linearGradient>
  <linearGradient id="card-sheen" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{NEON_PURPLE}" stop-opacity="0.10"/>
    <stop offset="0.35" stop-color="{NEON_PURPLE}" stop-opacity="0"/>
  </linearGradient>
</defs>''')

    # superficie: abyss-navy sobre void, borde glow purple (border-glow del sistema)
    out.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="8" fill="{ABYSS_NAVY}" stroke="{NEON_PURPLE}" stroke-opacity="0.45"/>')
    out.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="8" fill="url(#card-sheen)"/>')

    # ---- header ----
    out.append(f'<text x="28" y="38" fill="{NEON_BLUE}" font-family="{mono}" font-size="15" font-weight="bold" filter="url(#glow-blue)">$ ai-telemetry --live</text>')
    out.append(f'<text x="972" y="38" fill="{TEXT_SECONDARY}" font-family="{mono}" font-size="11" text-anchor="end">updated {esc(stamp)} · refreshes every 24h</text>')

    # ---- hero metrics ----
    hero_y = 92
    n_agents = len(per_client)
    heroes = [
        ("ALL-TIME TOKENS", fmt_tokens(alltime_tokens), f"${alltime_cost:,.0f} usd", NEON_BLUE, "glow-blue"),
        ("THIS MONTH", fmt_tokens(month_tokens), f"${month_cost:,.0f} usd", NEON_PURPLE, "glow-purple"),
        ("TODAY", fmt_tokens(today_tokens), f"${today_cost:,.2f} usd", WARM_AMBER, "glow-amber"),
        ("AGENTS ORCHESTRATED", str(n_agents), "this month", ICE_WHITE, None),
    ]
    for i, (label, big, sub, color, glow) in enumerate(heroes):
        x = 28 + i * 245
        out.append(f'<text x="{x}" y="{hero_y - 22}" fill="{TEXT_SECONDARY}" font-family="{mono}" font-size="11" letter-spacing="2">{label}</text>')
        filt = f' filter="url(#{glow})"' if glow else ""
        out.append(f'<text x="{x}" y="{hero_y + 16}" fill="{color}" font-family="{mono}" font-size="36" font-weight="bold"{filt}>{big}</text>')
        out.append(f'<text x="{x}" y="{hero_y + 40}" fill="{TEXT_SECONDARY}" font-family="{mono}" font-size="12">{sub}</text>')

    # divider sutil (border-subtle del sistema)
    out.append(f'<line x1="28" y1="158" x2="972" y2="158" stroke="{ICE_WHITE}" stroke-opacity="0.12" stroke-width="1"/>')

    # ---- daily bar chart ----
    chart_x, chart_y, chart_w, chart_h = 28, 250, 560, 100
    out.append(f'<text x="{chart_x}" y="{chart_y - 12}" fill="{TEXT_SECONDARY}" font-family="{mono}" font-size="11" letter-spacing="2">DAILY TOKENS — LAST {len(daily)} ACTIVE DAYS</text>')
    max_tok = max((d["tokens"] for d in daily), default=1) or 1
    n = len(daily)
    gap = 4
    bw = (chart_w - gap * (n - 1)) / n
    for i, d in enumerate(daily):
        h = max(2, (d["tokens"] / max_tok) * chart_h)
        x = chart_x + i * (bw + gap)
        y = chart_y + chart_h - h
        if i == n - 1:
            # hoy: amber con glow
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="1.5" fill="{WARM_AMBER}" filter="url(#glow-amber)"/>')
        else:
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="1.5" fill="url(#bar-grad)"/>')
    out.append(f'<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="{ICE_WHITE}" stroke-opacity="0.12" stroke-width="1"/>')
    out.append(f'<text x="{chart_x}" y="{chart_y + chart_h + 18}" fill="{TEXT_SECONDARY}" font-family="{mono}" font-size="10">{esc(daily[0]["date"][5:]) if daily else ""}</text>')
    out.append(f'<text x="{chart_x + chart_w}" y="{chart_y + chart_h + 18}" fill="{TEXT_SECONDARY}" font-family="{mono}" font-size="10" text-anchor="end">{esc(daily[-1]["date"][5:]) if daily else ""} · peak {fmt_tokens(max_tok)}</text>')

    # ---- per-client bars (escala log, valores right-aligned) ----
    cx, cy = 640, 250
    val_x = 962
    bar_max_w = 130
    out.append(f'<text x="{cx}" y="{cy - 12}" fill="{TEXT_SECONDARY}" font-family="{mono}" font-size="11" letter-spacing="2">THIS MONTH BY AGENT (log)</text>')
    max_ct = max((v["tokens"] for _, v in clients), default=1) or 1
    row_h = 21
    for i, (name, v) in enumerate(clients):
        y = cy + 8 + i * row_h
        color = AGENT_ROTATION[i] if i < len(AGENT_ROTATION) else NEON_BLUE
        bar_w = max(2, (math.log10(v["tokens"] + 1) / math.log10(max_ct + 1)) * bar_max_w)
        out.append(f'<text x="{cx}" y="{y + 11}" fill="{ICE_WHITE}" font-family="{mono}" font-size="11">{esc(name[:12])}</text>')
        glow = ' filter="url(#glow-purple)"' if i == 0 else ""
        out.append(f'<rect x="{cx + 100}" y="{y}" width="{bar_w:.1f}" height="13" rx="2" fill="{color}" opacity="0.9"{glow}/>')
        out.append(f'<text x="{val_x}" y="{y + 11}" fill="{TEXT_SECONDARY}" font-family="{mono}" font-size="10" text-anchor="end">{fmt_tokens(v["tokens"])}</text>')

    # ---- footer ----
    fy = H - 18
    out.append(f'<text x="28" y="{fy}" fill="{TEXT_SECONDARY}" font-family="{mono}" font-size="10">tokens measured across local agent sessions · source: private token monitor</text>')

    out.append("</svg>")
    return "\n".join(out)


def main():
    with open(EXPORT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    svg = render(data)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token-card.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"OK {path} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
