from __future__ import annotations
from typing import Dict
from pathlib import Path
import html

def _entry_txt(entry: Dict) -> str:
    if entry.get("type") == "breakout_confirmation":
        return f"Breakout > {entry.get('trigger')}"
    z = entry.get("zone", {})
    return f"Value {z.get('low')}–{z.get('high')}"

def _row(c: Dict) -> str:
    entry = _entry_txt(c["plan"]["entry"])
    stop = c["plan"]["exit_if_wrong"]["stop"]
    t1 = c["plan"]["targets"][0]["price"] if c["plan"]["targets"] else ""
    t2 = c["plan"]["targets"][1]["price"] if len(c["plan"]["targets"]) > 1 else ""
    labels = ", ".join(c.get("labels", []))
    return f"""<tr>
<td><b>{html.escape(c['ticker'])}</b></td>
<td>{c.get('price','')}</td>
<td>{c.get('rs_60d_vs_spy','')}</td>
<td>{c.get('vol_z','')}</td>
<td>{html.escape(entry)}</td>
<td>{stop}</td>
<td>{t1}</td>
<td>{t2}</td>
<td>{html.escape(labels)}</td>
</tr>"""

def write_report(out_dir: str, industries: Dict, early: Dict, ready: Dict):
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    ind_rows = "".join(
        f"<tr><td>{i['ticker']}</td><td>{round(i['score'],3)}</td></tr>"
        for i in industries.get("rankings", [])
    )

    ready_rows = "".join(_row(c) for c in ready.get("cards", []))
    early_rows = "".join(_row(c) for c in early.get("cards", []))

    doc = f"""<!doctype html>
<html><head><meta charset="utf-8"/>
<title>Market Scan Report</title>
<style>
body {{ font-family: Arial, sans-serif; padding: 18px; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 18px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 14px; }}
th {{ background: #f5f5f5; text-align: left; }}
h1,h2 {{ margin: 8px 0; }}
.pill {{ display:inline-block; padding:2px 8px; border-radius:999px; background:#eee; }}
</style></head>
<body>
<h1>Market Scan Report</h1>
<p><span class="pill">as_of</span> {industries.get('as_of','')}</p>

<h2>Industry / ETF Rankings</h2>
<table><tr><th>Ticker</th><th>Score</th></tr>{ind_rows}</table>

<h2>READY (Confirmed)</h2>
<table>
<tr><th>Ticker</th><th>Price</th><th>RS</th><th>VolZ</th><th>Entry</th><th>Stop</th><th>T1</th><th>T2</th><th>Labels</th></tr>
{ready_rows if ready_rows else "<tr><td colspan='9'>No READY today</td></tr>"}
</table>

<h2>EARLY / WATCH ONLY</h2>
<table>
<tr><th>Ticker</th><th>Price</th><th>RS</th><th>VolZ</th><th>Entry</th><th>Stop</th><th>T1</th><th>T2</th><th>Labels</th></tr>
{early_rows if early_rows else "<tr><td colspan='9'>No EARLY today</td></tr>"}
</table>
</body></html>"""
    Path(out_dir, "report.html").write_text(doc, encoding="utf-8")
