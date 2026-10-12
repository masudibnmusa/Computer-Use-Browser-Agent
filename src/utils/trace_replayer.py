from __future__ import annotations

import html
import json
from pathlib import Path


def load_trace(run_dir: str | Path) -> list[dict]:
    f = Path(run_dir) / "trace.jsonl"
    return [json.loads(line) for line in f.read_text().splitlines() if line.strip()]


def render_html(run_dir: str | Path) -> Path:
    """Writes report.html next to the trace so a run can be stepped through visually."""
    run_dir = Path(run_dir)
    task = json.loads((run_dir / "task.json").read_text())["task"]
    rows = []
    for s in load_trace(run_dir):
        color = "#2e7d32" if s["ok"] else "#c62828"
        rows.append(f"""
<section style="border:1px solid #ccc;margin:16px 0;padding:12px;border-left:6px solid {color}">
  <h3>Step {s['step']}: {html.escape(s['action'])} <small>risk={s['risk']}</small></h3>
  <p><b>URL:</b> {html.escape(s['url'])}</p>
  <p><b>Args:</b> <code>{html.escape(json.dumps(s['args']))}</code></p>
  <p><b>Reasoning:</b> {html.escape(s['reasoning'] or '')}</p>
  <p><b>Result:</b> {html.escape(s['message'] or '')} | <b>Effect:</b> {html.escape(s['effect'] or '')}</p>
  <img src="{html.escape(s['screenshot'])}" style="max-width:100%;border:1px solid #ddd">
</section>""")
    out = run_dir / "report.html"
    out.write_text(f"<!doctype html><meta charset=utf-8><title>Trace</title>"
                   f"<body style='font-family:sans-serif;max-width:1000px;margin:auto'>"
                   f"<h1>{html.escape(task)}</h1>{''.join(rows)}</body>")
    return out