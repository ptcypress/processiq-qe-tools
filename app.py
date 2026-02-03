from __future__ import annotations
import streamlit as st
from processiq.ui import set_page

set_page("ProcessIQ — QE Tools", icon="🧰")

st.title("ProcessIQ — QE Tools")
st.caption("A practical, lightweight alternative to Minitab for day-to-day Quality + Manufacturing decisions.")

st.markdown("### Core workflow")
st.markdown(
"""
1. Upload data (CSV/XLSX)
2. Pick the tool
3. Get charts + metrics you can act on fast
"""
)

st.divider()

st.markdown("## Tools")
cols = st.columns(3)
with cols[0]:
    st.page_link("pages/01_Data_Explorer.py", label="Data Explorer", icon="🗂️")
    st.page_link("pages/02_Control_Charts.py", label="Control Charts", icon="📈")
with cols[1]:
    st.page_link("pages/03_Capability.py", label="Capability (Cp/Cpk/Pp/Ppk)", icon="🎯")
    st.page_link("pages/04_Pareto.py", label="Pareto", icon="📊")
with cols[2]:
    st.page_link("pages/05_Regression.py", label="Regression", icon="📉")
    st.page_link("pages/06_Gage_RR.py", label="Gage R&R (Crossed)", icon="🧪")

st.divider()
st.markdown("### Quick jump")
q = st.text_input("Search tool names (e.g., xbar, p-chart, grr, pareto)")
tools = [
    ("Data Explorer", "pages/01_Data_Explorer.py"),
    ("Control Charts", "pages/02_Control_Charts.py"),
    ("Capability", "pages/03_Capability.py"),
    ("Pareto", "pages/04_Pareto.py"),
    ("Regression", "pages/05_Regression.py"),
    ("Gage R&R", "pages/06_Gage_RR.py"),
]
if q:
    qq = q.lower().strip()
    matches = [(n,p) for n,p in tools if qq in n.lower()]
    for n,p in matches:
        st.page_link(p, label=n, icon="➡️")
    if not matches:
        st.write("No matches.")
