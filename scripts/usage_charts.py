"""Small, responsive SVG figures for a GitHub README."""
from datetime import date, timedelta
from html import escape
from math import ceil, floor, log10

W, H = 382, 214
INK, MUTED, LINE = "#eef2ff", "#a3afc5", "#30384b"
PALETTE = ["#82aaff", "#ad94ff", "#5ad1b6", "#dda35d"]
MONO = "Consolas,monospace"


def label(x, y, txt, size=12, color=MUTED, align="start", bold=False, mono=False):
    font = MONO if mono else "Segoe UI,Arial,sans-serif"
    return (f'<text x="{x:g}" y="{y:g}" fill="{color}" text-anchor="{align}" '
            f'font-family="{font}" font-weight="{650 if bold else 400}" font-size="{size}">{escape(str(txt))}</text>')


def figure(out, name, title, desc, pieces, width=W, height=H):
    alt = escape(title + ". " + desc, quote=True)
    markup = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
              f'<title>{escape(title)}</title><desc>{escape(desc)}</desc>'
              f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" fill="#10151f" stroke="{LINE}"/>'
              + "".join(pieces) + '</svg>')
    file = "assets/" + name + ".svg"
    (out / file).write_text(markup, encoding="utf-8")
    return f'<img src="{file}" width="{width}" alt="{alt}" />'


def axis_top(value):
    if value <= 0:
        return 1
    step = 10 ** floor(log10(value)) / 2
    return ceil(value / step) * step


def trend(out, days, rows, clients, names, metric, compact, period="daily"):
    token_chart = metric == "tokens"
    title = f"{period.title()} tokens" if token_chart else f"Estimated {period} cost"
    top = axis_top(max((rows[d][metric] for d in days if d in rows), default=0))
    x0, y0, x1, y1 = 47, 70, 364, 157
    dx = (x1 - x0) / len(days)
    pieces = [label(16, 27, title, 18, INK, bold=True),
              label(16, 48, f'{days[0]:%b %d} – {days[-1]:%b %d}', 12)]
    peak = max((d for d in days if d in rows), key=lambda d:rows[d][metric], default=None)
    def display(v):
        return compact(v) if token_chart else f"${v:,.0f}"
    if peak:
        pieces.append(label(365, 26, "Peak " + display(rows[peak][metric]), 12, INK, "end", mono=True))
    for ratio in (0, .5, 1):
        y = y1 - ratio * (y1-y0)
        pieces += [f'<path d="M{x0} {y}H{x1}" stroke="{LINE}" stroke-dasharray="2 4"/>',
                   label(40,y+4,display(top*ratio),10,align="end",mono=True)]
    groups = [client for client,_ in clients[:3]]
    previous = None
    for i,d in enumerate(days):
        x = x0+(i+.5)*dx
        if i in (0,len(days)//2,len(days)-1):
            tick = d.strftime("%d") if period == "daily" else (d.strftime("%b %d") if period == "weekly" else d.strftime("%b"))
            pieces.append(label(x,177,tick,10,align="middle",mono=True))
        if d not in rows:
            previous = None
            continue
        row = rows[d]
        if token_chart:
            counts = [row["perClient"].get(k,{}).get("tokens",0) for k in groups]
            counts.append(max(0,row["tokens"]-sum(counts)))
            y = y1
            for amount, color in zip(counts, PALETTE):
                h = amount/top*(y1-y0)
                y -= h
                pieces.append(f'<rect x="{x-dx*.34:.2f}" y="{y:.2f}" width="{dx*.68:.2f}" height="{h:.2f}" fill="{color}"/>')
        else:
            y = y1-row[metric]/top*(y1-y0)
            if previous:
                px,py = previous
                pieces += [f'<path d="M{px} {py}L{x} {y}V{y1}H{px}Z" fill="#65d6be" opacity=".10"/>',
                           f'<path d="M{px} {py}L{x} {y}" fill="none" stroke="#65d6be" stroke-width="2"/>']
            previous = (x,y)
            pieces.append(f'<circle cx="{x}" cy="{y}" r="2.8" fill="#65d6be"/>')
    if token_chart:
        x = 16
        for k,color in zip([names.get(k,k) for k in groups]+["Other"],PALETTE):
            pieces += [f'<rect x="{x}" y="194" width="8" height="8" fill="{color}"/>',label(x+12,202,k,11)]
            x += 26 + len(k)*6.1
    else:
        pieces += [label(16,202,f"USD · {period.title()} estimates from Token Monitor",11)]
    desc = (f"Peak on {peak:%d %b}: {rows[peak][metric]:,.0f} tokens." if token_chart else
            f"Peak on {peak:%d %b}: USD {rows[peak][metric]:,.2f}.") if peak else "No observations in this period."
    return figure(out,period+"-"+metric,title,desc,pieces)


def charts(out, export, clients, names, compact):
    rows = {date.fromisoformat(r["date"]):r for r in export["daily"]}
    end = max(rows,default=date.fromisoformat(export["generatedAt"][:10]))
    days = [end-timedelta(days=i) for i in reversed(range(14))]
    def aggregate(period):
        grouped = {}
        for day, row in rows.items():
            key = day - timedelta(days=day.weekday()) if period == "weekly" else day.replace(day=1)
            entry = grouped.setdefault(key, {"tokens": 0, "cost": 0, "perClient": {}})
            entry["tokens"] += row["tokens"]
            entry["cost"] += row["cost"]
            for client, usage in row["perClient"].items():
                agent = entry["perClient"].setdefault(client, {"tokens": 0})
                agent["tokens"] += usage["tokens"]
        return grouped
    weekly = aggregate("weekly")
    monthly = aggregate("monthly")
    periods = [
        ("daily", days, rows),
        ("weekly", sorted(weekly)[-8:], weekly),
        ("monthly", sorted(monthly)[-6:], monthly),
    ]
    tokens = "\n".join(trend(out, dates, values, clients, names, "tokens", compact, period)
                       for period, dates, values in periods)
    costs = "\n".join(trend(out, dates, values, clients, names, "cost", compact, period)
                      for period, dates, values in periods)
    start = min(rows, default=end)
    weeks = min(13, (end-(start-timedelta(days=start.weekday()))).days//7+1)
    first = end-timedelta(days=end.weekday()+7*(weeks-1))
    values = ["#263044","#293c60","#395c91","#547fd2","#9dbfff"]
    p = [label(16,27,"Activity by day",18,INK,bold=True),
         label(16,47,f"{first:%d %b} – {end:%d %b %Y} · Daily tokens",12)]
    for i,k in [(0,"Mon"),(2,"Wed"),(4,"Fri"),(6,"Sun")]:
        p.append(label(16,73+15*i,k,10))
    for week in range(weeks):
        for day in range(7):
            d=first+timedelta(weeks=week,days=day)
            if d>end:continue
            x,y=50+week*19,63+day*15
            row=rows.get(d)
            amount = row["tokens"] if row else 0
            fill = values[min(4,sum(amount>=t for t in (1,10**6,10**7,10**8)))] if row else "none"
            p.append(f'<rect x="{x}" y="{y}" width="15" height="11" rx="2" fill="{fill}" stroke="{LINE}"><title>{d}: {compact(amount) + " tokens" if row else "No record"}</title></rect>')
    p += [label(16,188,"□ No record",11),label(128,188,"Fewer",11)]
    for i,c in enumerate(values):
        p.append(f'<rect x="{165+i*15}" y="179" width="12" height="10" rx="2" fill="{c}"/>')
    p.append(label(245,188,"More tokens",11))
    total = sum(first<=d<=end for d in rows)
    heat = figure(out,"activity","Activity by day",f"{total} days with records. Outlined cells have no record.",p,height=202)
    return tokens, costs, heat


def model_charts(out, models, month, compact):
    """Render ranked model usage directly from Token Monitor's monthly perModel data."""
    total = sum(tokens for _, tokens in models)
    peak = models[0][1] if models else 1

    def render(name, title, rows, remaining=0):
        row_height = 29
        y0 = 86
        height = y0 + row_height * len(rows) + (36 if remaining else 29)
        pieces = [label(20, 31, title, 20, INK, bold=True),
                  label(20, 54, f"{month} · {len(models)} identified models · {compact(total)} tokens", 12)]
        if not rows:
            pieces.append(label(20, 112, "No identified model usage this month", 14))
            return figure(out, name, title, "No identified model usage this month.", pieces, width=760, height=145)

        x0, x1 = 285, 646
        for index, (model, tokens) in enumerate(rows):
            y = y0 + index * row_height
            fill = PALETTE[index % 3]
            bar = max(1.5, (x1 - x0) * tokens / peak)
            pieces += [label(20, y + 4, model, 12, INK if index < 3 else MUTED, mono=True),
                       f'<rect x="{x0}" y="{y-8}" width="{x1-x0}" height="11" fill="#202a3b"/>',
                       f'<rect x="{x0}" y="{y-8}" width="{bar:.2f}" height="11" fill="{fill}"><title>{escape(model)}: {tokens:,} tokens</title></rect>',
                       label(740, y + 4, compact(tokens), 12, INK, "end", mono=True)]
        if remaining:
            other_tokens = sum(tokens for _, tokens in models[len(rows):])
            pieces.append(label(20, height - 15, f"{remaining} more models · {compact(other_tokens)} tokens in full breakdown", 12))
        else:
            pieces.append(label(20, height - 12, "Monthly token counts · Source: Token Monitor", 11))
        desc = f"{len(models)} identified models in {month}, ranked by monthly tokens. " + "; ".join(
            f"{model}: {tokens:,}" for model, tokens in rows)
        return figure(out, name, title, desc, pieces, width=760, height=height)

    preview = render("model-usage", "Most used models", models[:12], max(0, len(models) - 12))
    full = render("model-breakdown", "All identified models", models)
    return preview, full
