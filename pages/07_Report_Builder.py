# pages/07_Report_Builder.py
from __future__ import annotations

import streamlit as st

from processiq.ui import set_page
from processiq.reporting import Report
from processiq.report_builder import get_sections, remove_section, move_up, move_down, clear_sections

set_page("Report Builder", icon="🧾")

st.title("Report Builder")
st.caption("Combine multiple tool outputs into one deliverable report.")

sections = get_sections()

top = st.columns([2, 1, 1, 1])
with top[0]:
    report_title = st.text_input("Report title", value="ProcessIQ — Combined Report", key="rb_title")
with top[1]:
    subtitle = st.text_input("Subtitle", value="Multi-tool summary", key="rb_subtitle")
with top[2]:
    dataset_name_override = st.text_input("Dataset (optional)", value="", key="rb_dataset")
with top[3]:
    if st.button("Clear all", use_container_width=True, key="rb_clear_all"):
        clear_sections()
        st.rerun()

if not sections:
    st.info("No sections added yet. Go to Capability or Control Charts and click **Add to Report Builder**.")
    st.stop()

# Pick dataset name shown in header (override or first section’s dataset)
dataset_name = dataset_name_override.strip() or sections[0].get("dataset_name", "")

st.divider()
st.subheader(f"Sections ({len(sections)})")

for i, sec in enumerate(sections):
    tool = sec.get("tool", "Section")
    sec_sub = sec.get("subtitle", "")
    sec_ds = sec.get("dataset_name", "")

    with st.expander(f"{i+1}. {tool} — {sec_sub}", expanded=(i == 0)):
        st.caption(f"Dataset: {sec_ds}")

        b1, b2, b3, b4 = st.columns([1, 1, 1, 2])
        with b1:
            if st.button("Up", key=f"rb_up_{i}"):
                move_up(i)
                st.rerun()
        with b2:
            if st.button("Down", key=f"rb_down_{i}"):
                move_down(i)
                st.rerun()
        with b3:
            if st.button("Remove", key=f"rb_rm_{i}"):
                remove_section(i)
                st.rerun()
        with b4:
            st.write("")

        if sec.get("badge_text"):
            level = sec.get("badge_level", "success")
            if level == "error":
                st.error(sec["badge_text"])
            elif level == "warn":
                st.warning(sec["badge_text"])
            else:
                st.success(sec["badge_text"])

        # Preview (light)
        if sec.get("kpis"):
            st.write("**KPIs**")
            st.json({k: v for k, v in sec["kpis"]})

st.divider()
st.subheader("Download combined report")

rep = Report(
    title=report_title,
    subtitle=subtitle,
    dataset_name=dataset_name,
)

for sec in sections:
    tool = sec.get("tool", "Section")
    sec_sub = sec.get("subtitle", "")
    inputs_html = sec.get("inputs_html", "")
    interp_html = sec.get("interpretation_html", "")
    kpis = sec.get("kpis", [])
    badge_text = sec.get("badge_text")
    badge_level = sec.get("badge_level", "success")
    figs = sec.get("figures", [])
    tables = sec.get("tables", [])

    # Section summary card
    body_lines = []
    if sec_sub:
        body_lines.append(f"<b>{tool}</b> — {sec_sub}")
    else:
        body_lines.append(f"<b>{tool}</b>")
    if inputs_html:
        body_lines.append("<hr/>" + inputs_html)
    if interp_html:
        body_lines.append("<hr/>" + interp_html)

    rep.add_card(f"{tool} — Summary", "<br/>".join(body_lines))

    if badge_text:
        rep.add_badge(f"{tool} — Status", badge_text, level=badge_level)

    if kpis:
        rep.add_kpis(f"{tool} — Key results", kpis)

    for t, fig in figs:
        rep.add_figure(f"{tool} — {t}", fig)

    for t, df in tables:
        rep.add_table(f"{tool} — {t}", df)

html = rep.render_html().encode("utf-8")

st.download_button(
    "Download Combined HTML Report",
    data=html,
    file_name=rep.file_name("processiq_combined_report"),
    mime="text/html",
    use_container_width=True,
    key="rb_download",
)
