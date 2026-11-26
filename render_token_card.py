#!/usr/bin/env python3
"""
Renderiza token-card.svg desde el export del token monitor.
Lenguaje visual: el mismo de los badges del perfil —
flat-square rx=0, cara #0E1118, borde tecnico purple 45%,
texto ice-white, sheen purple diagonal, linea neon azul->purple en la base.
Sin glows, sin brackets, sin grid: limpio como un chip.
"""
import json
import os.path
from datetime import datetime

EXPORT_PATH = r"${USERPROFILE}/usage-registry/token-monitor-export.json"

W, H = 1000, 400

# tokens compartidos con los badges
FACE = "#0E1118"
ELEVATED = "#151A26"
ICE = "#E0E6ED"
SECONDARY = "#94A3B8"
NEON_BLUE = "#0E76FD"
NEON_PURPLE = "#823CFA"
ALERT = "#FF2A9E"
BORDER = "#823CFA"
BORDER_OP = "0.45"

FONT = "'JetBrains Mono','Geist Mono','Fira Code',monospace"


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
        stamp = datetime.fromisoformat(gen.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        stamp = gen[:16]

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="AI token telemetry for jseramn">']

    # defs: la linea neon de la base + sheen diagonal, identicos en espiritu a los badges
    out.append(f'''<defs>
  <linearGradient id="neonline" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{NEON_BLUE}" stop-opacity="0.9"/>
    <stop offset="1" stop-color="{NEON_PURPLE}" stop-opacity="0.9"/>
  </linearGradient>
  <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="6" stroke="{NEON_PURPLE}" stroke-width="1.3" opacity="0.6"/>
  </pattern>
</defs>''')

    # cara del chip: flat navy, sheen purple diagonal, borde tecnico 1px, rx=0
    out.append(f'<rect width="{W}" height="{H}" fill="{FACE}"/>')
    out.append(f'<polygon points="{W*0.55:.0f},0 {W},0 {W},{H}" fill="{NEON_PURPLE}" opacity="0.05"/>')

    # header
    out.append(f'<text x="28" y="36" font-family="{FONT}" font-size="15" font-weight="700" fill="{ICE}">$ ai-telemetry <tspan fill="{NEON_PURPLE}">--live</tspan></text>')
    out.append(f'<text x="{W-28}" y="36" text-anchor="end" font-family="{FONT}" font-size="11" fill="{SECONDARY}">{esc(stamp)}</text>')
    out.append(f'<line x1="28" y1="48" x2="{W-28}" y2="48" stroke="{BORDER}" stroke-opacity="{BORDER_OP}" stroke-width="1"/>')

    # KPIs: fila de cifras flat, separadas por hairlines purple
    heroes = [
        ("ALL-TIME TOKENS", fmt_tokens(alltime_tokens), f"${alltime_cost:,.0f} usd", ICE),
        ("THIS MONTH", fmt_tokens(month_tokens), f"${month_cost:,.0f} usd", NEON_BLUE),
        ("TODAY", fmt_tokens(today_tokens), f"${today_cost:,.2f} usd", ALERT),
        ("AGENTS", str(len(per_client)), "orchestrated", NEON_PURPLE),
    ]
    kw = (W - 56) / 4
    for i, (label, big, sub, bigc) in enumerate(heroes):
        x = 28 + i * kw
        if i:
            out.append(f'<line x1="{x}" y1="70" x2="{x}" y2="140" stroke="{BORDER}" stroke-opacity="0.25" stroke-width="1"/>')
        out.append(f'<text x="{x+16}" y="{78}" font-family="{FONT}" font-size="10.5" letter-spacing="0.08em" fill="{SECONDARY}">{esc(label)}</text>')
        out.append(f'<text x="{x+16}" y="{116}" font-family="{FONT}" font-size="30" font-weight="700" fill="{bigc}">{esc(big)}</text>')
        out.append(f'<text x="{x+16}" y="{138}" font-family="{FONT}" font-size="11" fill="{SECONDARY}">{esc(sub)}</text>')

    # chart 24 dias: barras flat blue, picos en purple, hoy en alert
    chart_x, chart_y, chart_w, chart_h = 28, 200, 560, 120
    out.append(f'<text x="{chart_x}" y="{chart_y - 14}" font-family="{FONT}" font-size="10.5" letter-spacing="0.08em" fill="{SECONDARY}">DAILY TOKENS — LAST 24 DAYS</text>')
    max_tok = max((d["tokens"] for d in daily), default=1) or 1
    n = len(daily)
    gap = 4
    bw = (chart_w - gap * (n - 1)) / n
    peak = max_tok * 0.85
    for i, d in enumerate(daily):
        h = max(2, (d["tokens"] / max_tok) * chart_h)
        x = chart_x + i * (bw + gap)
        y = chart_y + chart_h - h
        color = ALERT if i == n - 1 else (NEON_PURPLE if d["tokens"] >= peak else NEON_BLUE)
        op = "1" if color != NEON_BLUE else "0.85"
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{color}" opacity="{op}"/>')
    out.append(f'<line x1="{chart_x}" y1="{chart_y + chart_h + 6}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h + 6}" stroke="{BORDER}" stroke-opacity="{BORDER_OP}" stroke-width="1"/>')

    # agentes: ranking flat con hairline left, lider solido purple, resto hatch
    ax = chart_x + chart_w + 40
    aw = W - 28 - ax
    out.append(f'<text x="{ax}" y="{chart_y - 14}" font-family="{FONT}" font-size="10.5" letter-spacing="0.08em" fill="{SECONDARY}">THIS MONTH BY AGENT</text>')
    if clients:
        maxa = clients[0][1]["tokens"] or 1
        row_h = 19
        bar_x = ax + 108
        bar_maxw = aw - 108 - 74
        for i, (name, v) in enumerate(clients):
            yy = chart_y + 8 + i * row_h
            out.append(f'<text x="{ax}" y="{yy+10}" font-family="{FONT}" font-size="11.5" fill="{ICE}">{esc(name[:12])}</text>')
            wlen = max(3, (v["tokens"] / maxa) * bar_maxw)
            if i == 0:
                out.append(f'<rect x="{bar_x}" y="{yy}" width="{wlen:.0f}" height="11" fill="{NEON_PURPLE}"/>')
            else:
                out.append(f'<rect x="{bar_x}" y="{yy}" width="{wlen:.0f}" height="11" fill="{ELEVATED}"/>')
                out.append(f'<rect x="{bar_x}" y="{yy}" width="{wlen:.0f}" height="11" fill="url(#hatch)"/>')
            out.append(f'<text x="{bar_x+bar_maxw+10}" y="{yy+10}" font-family="{FONT}" font-size="11" fill="{SECONDARY}">{fmt_tokens(v["tokens"])}</text>')

    # footer: la firma del sistema de badges — linea neon azul->purple en la base + borde tecnico
    out.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="none" stroke="{BORDER}" stroke-opacity="{BORDER_OP}"/>')
    out.append(f'<rect x="0" y="{H-3}" width="{W}" height="3" fill="url(#neonline)"/>')

    out.append('</svg>')
    return "".join(out)


def main():
    data = json.load(open(EXPORT_PATH, encoding="utf-8"))
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "token-card.svg"), "w", encoding="utf-8") as f:
        f.write(render(data))
    print("rendered: token-card.svg [badge-design language]")


if __name__ == "__main__":
    main()
