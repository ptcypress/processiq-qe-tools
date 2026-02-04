# processiq/report_builder.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st


STATE_KEY = "report_builder_sections"


@dataclass
class ReportSection:
    tool: str
    subtitle: str
    dataset_name: str
    inputs_html: str = ""
    interpretation_html: str = ""
    kpis: list[tuple[str, str]] | None = None
    badge_text: str | None = None
    badge_level: str = "success"  # success | warn | error
    figures: list[tuple[str, Any]] | None = None   # Plotly figs
    tables: list[tuple[str, Any]] | None = None    # pandas DataFrames


def _get_list() -> list[dict]:
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = []
    return st.session_state[STATE_KEY]


def get_sections() -> list[dict]:
    return list(_get_list())


def add_section(section: ReportSection) -> None:
    lst = _get_list()
    lst.append(
        {
            "tool": section.tool,
            "subtitle": section.subtitle,
            "dataset_name": section.dataset_name,
            "inputs_html": section.inputs_html,
            "interpretation_html": section.interpretation_html,
            "kpis": section.kpis or [],
            "badge_text": section.badge_text,
            "badge_level": section.badge_level,
            "figures": section.figures or [],
            "tables": section.tables or [],
        }
    )


def remove_section(idx: int) -> None:
    lst = _get_list()
    if 0 <= idx < len(lst):
        lst.pop(idx)


def move_up(idx: int) -> None:
    lst = _get_list()
    if 1 <= idx < len(lst):
        lst[idx - 1], lst[idx] = lst[idx], lst[idx - 1]


def move_down(idx: int) -> None:
    lst = _get_list()
    if 0 <= idx < len(lst) - 1:
        lst[idx + 1], lst[idx] = lst[idx], lst[idx + 1]


def clear_sections() -> None:
    st.session_state[STATE_KEY] = []
