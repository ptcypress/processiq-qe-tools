# processiq/reporting.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

import pandas as pd

try:
    import plotly.io as pio
except Exception:  # pragma: no cover
    pio = None


CSS = """
<style>
:root { --fg:#111; --muted:#666; --card:#f6f7f9; --line:#e6e8eb; }
body { font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial,sans-serif; color:var(--fg); margin:0; padding:24px; background:#fff; }
h1 { margin:0 0 4px 0; font-size:28px; }
h2 { margin:22px 0 8px; font-size:18px; border-top:1px solid var(--line); padding-top:14px; }
h3 { margin:14px 0 6px; font-size:15px; }
.small { color:var(--muted); font-size:12px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 14px; margin:10px 0; }
.kpis { display:flex; flex-wrap:wrap; gap:10px; margin:10px 0; }
.kpi { background:white; border:1px solid var(--line); border-radius:12px; padding:10px 12px; min-width:160px; }
.kpi .label { color:var(--muted); font-size:12px; }
.kpi .value { font-size:18px; font-weight:600; margin-top:2px; }
table { border-collapse:collapse; width:100%; margin:8px 0 0; }
th, td { border:1px solid var(--line); padding:8px; font-size:12px; text-align:left; }
th { background:#fafbfc; }
.badge { display:inline-block; padding:3px 8px; border-radius:999px; font-size:12px; border:1px solid var(--line); background:white; }
.badge.success { background:#e9f7ef; border-color:#bfe6cf; }
.badge.warn { background:#fff7e6; border-color:#ffe0a3; }
.badge.error { background:#fdecec; border-color:#f7baba; }
hr { border:none; border-top:1px solid var(--line); margin:16px 0; }
</style>
"""


def _escape(x: Any) -> str:
    s = "" if x is None else str(x)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def df_to_html(df: pd.DataFrame, max_rows: int = 200) -> str:
    if df is None:
        return ""
    if len(df) > max_rows:
        df = df.head(max_rows).copy()
    return df.to_html(index=False, escape=True)


def fig_to_html(fig) -> str:
    if fig is None:
        return ""
    if pio is None:
        return "<div class='card'>Plotly is not available to export this figure.</div>"
    # Use CDN to keep file small
    return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)


@dataclass
class Report:
    title: str
    subtitle: str = ""
    dataset_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sections: list[str] = field(default_factory=list)

    def add_card(self, heading: str, body: str) -> None:
        self.sections.append(f"<h2>{_escape(heading)}</h2><div class='card'>{body}</div>")

    def add_kpis(self, heading: str, kpis: Iterable[tuple[str, str]]) -> None:
        items = []
        for label, value in kpis:
            items.append(
                f"<div class='kpi'><div class='label'>{_escape(label)}</div>"
                f"<div class='value'>{_escape(value)}</div></div>"
            )
        block = "<div class='kpis'>" + "".join(items) + "</div>"
        self.sections.append(f"<h2>{_escape(heading)}</h2>{block}")

    def add_badge(self, heading: str, text: str, level: str = "success") -> None:
        level = level if level in {"success", "warn", "error"} else "success"
        self.sections.append(
            f"<h2>{_escape(heading)}</h2>"
            f"<div class='card'><span class='badge {level}'>{_escape(text)}</span></div>"
        )

    def add_figure(self, heading: str, fig) -> None:
        self.sections.append(f"<h2>{_escape(heading)}</h2>{fig_to_html(fig)}")

    def add_table(self, heading: str, df: pd.DataFrame) -> None:
        self.sections.append(f"<h2>{_escape(heading)}</h2>{df_to_html(df)}")

    def render_html(self) -> str:
        header = f"""
        {CSS}
        <h1>{_escape(self.title)}</h1>
        <div class="small">
            {_escape(self.subtitle)}<br/>
            <b>Dataset:</b> {_escape(self.dataset_name)} &nbsp; | &nbsp;
            <b>Generated:</b> {_escape(self.created_at)}
        </div>
        <hr/>
        """
        body = "\n".join(self.sections) if self.sections else "<div class='card'>No content captured.</div>"
        return "<html><head><meta charset='utf-8'/></head><body>" + header + body + "</body></html>"

    def file_name(self, slug: str) -> str:
        safe = "".join([c if c.isalnum() or c in "-_." else "_" for c in slug])[:60]
        ts = self.created_at.replace(":", "").replace(" ", "_")
        return f"{safe}_{ts}.html"
