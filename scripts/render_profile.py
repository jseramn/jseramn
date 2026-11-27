"""Build a local GitHub profile design study from the existing public README and usage totals."""
import base64
import html
import json
import os
import re
import sys
from usage_charts import charts
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
OUT = ROOT
ASSETS = OUT / "assets"
SOURCE = ROOT
ASSETS.mkdir(parents=True, exist_ok=True)
export_path = Path(os.environ.get("TOKEN_MONITOR_EXPORT", Path.home() / "usage-registry" / "token-monitor-export.json"))
export = json.loads(export_path.read_text(encoding="utf-8-sig"))
stamp = datetime.fromisoformat(export["generatedAt"].replace("Z", "+00:00")).astimezone(timezone.utc)
period = next(row for row in export["monthly"] if row["month"] == stamp.strftime("%Y-%m"))
clients = sorted(((k, v["tokens"]) for k, v in period["perClient"].items() if k != "unknown" and v["tokens"] > 0), key=lambda kv: (-kv[1], kv[0]))
names = {"devin":"Devin", "antigravity":"Antigravity", "codex":"Codex", "junie":"Junie", "hermes":"Hermes", "grok":"Grok Build", "kilo":"Kilo", "claude":"Claude Code", "opencode":"OpenCode"}
e = html.escape

def compact(n):
    for scale, suffix in [(1e9,"B"), (1e6,"M"), (1e3,"K")]:
        if n >= scale:
            return (f"{n/scale:.2f}" if scale == 1e9 else f"{n/scale:.1f}").rstrip("0").rstrip(".") + suffix
    return str(int(n)) if float(n).is_integer() else str(n)

def make_badge(client, tokens):
    name = names.get(client, client)
    value = compact(tokens)
    slug = re.sub(r"[^a-z0-9-]", "-", client.lower())
    filename = f"assets/harness-{slug}.svg"
    logo_dir = ROOT / "scripts" / "logos"
    if client in {"kilo","opencode","grok"} and (logo_dir/f"{client}-brand.svg").exists():
        raw = (logo_dir/f"{client}-brand.svg").read_text(encoding="utf-8")
        logo = raw[raw.index("<svg"):]
        logo = re.sub(r'(<svg\b[^>]*?)\s(?:width|height)="[^"]+"', r"\1",logo, count=1)
        logo = re.sub(r'(<svg\b[^>]*?)\s(?:width|height)="[^"]+"', r"\1",logo, count=1)
        logo = logo.replace("<svg ", '<svg x="13" y="14" width="28" height="28" ',1)
    elif (logo_dir / f"{client}.png").exists():
        icon = base64.b64encode((logo_dir / f"{client}.png").read_bytes()).decode()
        logo = f'<image x="11" y="12" width="32" height="32" href="data:image/png;base64,{icon}"/>'
    else:
        logo = f'<text x="27" y="34" text-anchor="middle" font-size="16" fill="#cfc6ff">{e(name[:2].upper())}</text>'
    width = max(268, 151 + len(name)*8)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="56" viewBox="0 0 {width} 56" role="img" aria-label="{e(name)}: {tokens:,} tokens">
  <defs>
    <linearGradient id="edge"><stop stop-color="#0e76fd"/><stop offset="1" stop-color="#823cfa"/></linearGradient>
    <pattern id="grain" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".55" fill="#b7aeff" opacity=".22"/></pattern>
  </defs>
  <rect width="{width}" height="56" fill="#0e1118"/>
  <path d="M{width-78} 56L{width-22} 0h22v56z" fill="#1b172c"/>
  <rect width="{width}" height="56" fill="url(#grain)"/>
  <rect x=".5" y=".5" width="{width-1}" height="55" stroke="#44415d" fill="none"/>
  {logo}
  <g font-family="Consolas,monospace" font-weight="bold">
    <text x="{width-13}" y="34" text-anchor="end" font-size="18" fill="#cfc6ff">{value}</text>
  </g>
  <text x="53" y="33" font-family="Segoe UI,Arial,sans-serif" font-size="15" font-weight="600" fill="#eef3fb">{e(name)}</text>
  <rect y="53" width="{width}" height="3" fill="url(#edge)"/>
</svg>'''
    (OUT / filename).write_text(svg, encoding="utf-8")
    return f'<img src="{filename}" width="{width}" height="56" alt="{e(name)}: {tokens:,} tokens" />'

repo = "https://github.com/Get-Concord-AI/concord-mcp"
def link(label, url):
    return f'<a href="{e(url, quote=True)}">{label}</a>'

month = stamp.strftime("%B %Y")
lookup = link("See all my Concord pull requests →", repo+"/pulls?q=is%3Apr+author%3Ajseramn")
prs = [
    ("412","Keep custom settings on reinstall","The Concord installer now preserves timeouts, disabled flags and other client settings."),
    ("404","Connect coding harnesses across worktrees","I documented how Claude Code, Codex and OpenCode share a Concord workspace in T3 Code."),
]
rows = "\n".join(f'<li>{link(f"<strong>{title}</strong>",repo+"/pull/"+num)} · <code>#{num}</code><br />{desc}</li>' for num,title,desc in prs)
badges = "\n".join(make_badge(c,t) for c,t in clients)
original = (SOURCE/"scripts/badge-catalogue.md").read_text(encoding="utf-8")
catalogue = re.findall(r'<p align="left"><b>(languages|stack|harnesses|workshop|daily)</b></p>\s*<p align="left">(.*?)</p>',original,re.S)
assert len(catalogue) == 5
tools = "\n".join(f'<p><strong>{group.capitalize()}</strong></p>\n<p>{contents}</p>' for group,contents in catalogue)
token_charts, cost_charts, heat = charts(OUT, export, clients, names, compact)
snap = export["snapshot"]
totals = " · ".join(f'<strong>{compact(snap[key]["totalTokens"])}</strong> {label} (${snap[key]["costUsd"]:,.2f})' for key,label in [("today","today"),("month","this month"),("allTime","all time")])
source_link = link("Token Monitor", "https://github.com/Javis603/token-monitor")
body = f'''<img src="assets/banner.png" alt="Coding harness streams converge into a shared workspace" width="100%" />

<h1>I build tools for coding harnesses.</h1>
<p>Most of my client work and product development happens in private. In public, I contribute to {link("Concord MCP",repo)}, to help developers coordinate work across coding harnesses.</p>

<h2>Open source contributions</h2>
<p><strong>Concord MCP</strong> · Selected merged pull requests</p>
<ul>
{rows}
</ul>
<p>{lookup}</p>

<h2>Harnesses in my workflow</h2>
<p><strong>{len(clients)} active harnesses</strong> · Monthly tokens · {month}</p>
<p>
{badges}
</p>
<p>Usage data from {source_link} · {stamp.strftime("%d %b %Y, %H:%M UTC")}</p>
<p>
{token_charts}
</p>
<details>
<summary>Show estimated costs · daily, weekly and monthly</summary>
<p>{cost_charts}</p>
</details>
<details>
<summary>Activity calendar and token totals</summary>
<p>{heat}</p>
<p>{' · '.join(f'{compact(snap[key]["totalTokens"])} {label}' for key,label in [("today","today"),("month","this month"),("allTime","all time")])}</p>
</details>

<h2>Toolbox</h2>
<details>
<summary>Explore my languages, stack and tools</summary>
{tools}
</details>
'''
(OUT/"README.md").write_text(body, encoding="utf-8")
print("Generated README and telemetry assets")
