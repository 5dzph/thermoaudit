"""Self-contained reports. No JavaScript, CDN, telemetry or remote assets."""

from html import escape


def esc(value):
    return escape(str(value), quote=True)


def fmt(value):
    return "—" if value is None else f"{value:,.6g}" if isinstance(value, (int, float)) else esc(value)


def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>' + ''.join(
        f"<th>{esc(h)}</th>" for h in headers) + '</tr></thead><tbody>' + ''.join(
            '<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>' for row in rows
        ) + '</tbody></table></div>'


def scatter(data):
    """SEC/CAPEX projection with all three objectives used for membership."""
    rows = data["candidates"]
    xs = [r["sec_kwh_kg"] for r in rows]
    ys = [r["capex_usd"] for r in rows]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)

    def x(v):
        return 75 + (v - xmin) / (xmax - xmin or 1) * 590

    def y(v):
        return 280 - (v - ymin) / (ymax - ymin or 1) * 230

    dots = []
    for r in rows:
        color = '#c1c9d3' if not r['feasible'] else '#12856b' if r['id'] in data['pareto_ids'] else '#6d7f99'
        ring = ' stroke="#f6a132" stroke-width="4"' if r['id'] == data['recommendation_id'] else ''
        tip = f"{r['id']} | SEC {r['sec_kwh_kg']} | CAPEX {r['capex_usd']} | efficiency {r['exergy_efficiency']}"
        dots.append(f'<circle cx="{x(r["sec_kwh_kg"]):.2f}" cy="{y(r["capex_usd"]):.2f}" r="7" fill="{color}"{ring}><title>{esc(tip)}</title></circle>')
    return f'''<svg viewBox="0 0 740 350" role="img" aria-label="SEC versus CAPEX projection of supplied candidates">
    <path d="M75 35 V280 H690" stroke="#aab8c8" fill="none"/>
    <text x="75" y="309">{xmin:.4g}</text><text x="640" y="309">{xmax:.4g}</text>
    <text x="6" y="280">{ymin:.3g}</text><text x="6" y="55">{ymax:.3g}</text>
    <text x="300" y="338">SEC · kWh/kg</text><text x="75" y="23">CAPEX · USD</text>
    {''.join(dots)}</svg><p class="muted">Green: three-objective Pareto set · grey: dominated or excluded · amber ring: selected compromise. Hover for values. This is a two-dimensional projection; see the table for efficiency.</p>'''


def render_html(data, kind):
    if kind == "audit":
        title = data["name"]
        passes = sum(c['status'] == 'PASS' for c in data['checks'])
        intro = f"<p>{esc(data['provenance'])}</p>"
        cards = [("CHECK RESULT", data['status']), ("CHECKS PASSED", f"{passes}/{len(data['checks'])}"),
                 ("SPECIFIC ENERGY", f"{fmt(data['metrics'].get('specific_energy_kwh_kg'))} kWh/kg")]
        body = '<h2>Balance & direction checks</h2>' + table(
            ['Unit', 'Check', 'Status', 'Value', 'Limit', 'Units', 'Interpretation'],
            [[esc(c['unit']), esc(c['code']), f'<span class="{c["status"].lower()}">{c["status"]}</span>',
              fmt(c['value']), fmt(c['limit']), esc(c['quantity_unit']), esc(c['message'])] for c in data['checks']])
    else:
        title = "Candidate trade-offs"
        intro = '<p>Compare supplied SEC, exergy efficiency and capital cost. Synthetic examples are for software demonstration only.</p>'
        cards = [("FEASIBLE", f"{data['feasible_count']}/{data['candidate_count']}"),
                 ("PARETO CANDIDATES", len(data['pareto_ids'])), ("COMPROMISE", data['recommendation_id'])]
        body = '<h2>Energy / capital cost</h2>' + scatter(data) + '<h2>All supplied candidates</h2>' + table(
            ['ID', 'SEC · kWh/kg', 'Exergy efficiency', 'CAPEX · USD', 'Classification', 'Distance ↓'],
            [[esc(r['id']), fmt(r['sec_kwh_kg']), fmt(r['exergy_efficiency']), fmt(r['capex_usd']),
              'Excluded' if not r['feasible'] else 'Pareto' if r['id'] in data['pareto_ids'] else 'Dominated',
              fmt(data['scores'].get(r['id']))] for r in data['candidates']])
        body += '<p>' + esc(data['method']) + '</p><p>Normalized weights: ' + esc(data['weights']) + '</p>'
    card_html = ''.join(f'<section><small>{esc(k)}</small><strong>{esc(v)}</strong></section>' for k, v in cards)
    limits = ''.join(f'<li>{esc(s)}</li>' for s in data['limitations'])
    meta = data.get('metadata', {})
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ThermoAudit — {esc(title)}</title><style>
:root{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#19334c;background:#eef3f7}}*{{box-sizing:border-box}}
body{{margin:0}}header{{background:#102d46;color:white;padding:36px max(24px,calc((100vw - 1200px)/2))}}
header small{{color:#71dcc5;letter-spacing:.16em}}h1{{font-size:clamp(28px,4vw,42px);margin:14px 0}}header p{{color:#c8d8e5;max-width:860px;line-height:1.6}}
main{{max-width:1248px;margin:auto;padding:28px 24px}}.cards{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}
section,.panel{{background:white;border:1px solid #dde5ed;border-radius:14px;padding:24px}}section small{{font-size:11px;color:#61758b;letter-spacing:.1em}}
strong{{display:block;font-size:28px;margin-top:10px;overflow-wrap:anywhere}}.panel{{margin-top:24px}}h2{{font-size:19px;margin:0 0 18px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{text-align:left;padding:13px 10px;border-bottom:1px solid #e6edf3;overflow-wrap:anywhere}}
th{{color:#61758b;font-size:11px}}.scroll{{overflow:auto}}.pass{{color:#08795c;font-weight:700}}.fail{{color:#b53d3d;font-weight:700}}
p,li{{line-height:1.65}}.muted,footer{{color:#61758b;font-size:12px}}svg{{width:100%;max-height:420px}}svg text{{font:12px system-ui;fill:#61758b}}
footer{{overflow-wrap:anywhere;padding:24px 0}}@media(max-width:640px){{.cards{{grid-template-columns:1fr}}section{{padding:16px}}}}
@media print{{body{{background:white}}header{{color:#19334c;background:white}}header p{{color:#61758b}}.panel{{break-inside:avoid}}}}
</style></head><body><header><small>THERMOAUDIT / ENGINEERING DATA CHECKS</small><h1>{esc(title)}</h1>{intro}</header>
<main><div class="cards">{card_html}</div><article class="panel">{body}</article>
<aside class="panel"><h2>Scope & assumptions</h2><ul>{limits}</ul></aside>
<footer>ThermoAudit {esc(meta.get('version', '0.1.0'))} · input SHA-256: {esc(meta.get('input_sha256', 'not recorded'))}<br>
Offline report · no data is uploaded · JSON output contains machine-readable values.</footer></main></body></html>'''
