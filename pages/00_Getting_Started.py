from __future__ import annotations
import streamlit as st
from processiq.ui import set_page

set_page("Home", icon="🏠")

st.title("ProcessIQ")
st.caption("A practical, affordable Quality Engineering toolkit — built for speed, clarity, and clean reporting.")

c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("For Quality Engineers")
    st.write("- Control charts\n- Capability (Cp/Cpk, Pp/Ppk)\n- Gage R&R\n- Fast reporting")
with c2:
    st.subheader("For Mfg Engineers")
    st.write("- Quick stability checks\n- Regression screening\n- Pareto drivers\n- Shareable results")
with c3:
    st.subheader("For Ops Managers")
    st.write("- Simple interpretation\n- Fewer clicks\n- Clean deliverables\n- Less “stats speak”")

st.divider()

st.subheader("Fast demo flow")
st.write("1) Go to **Data Explorer** → Load a sample dataset\n"
         "2) Run **Control Charts** and **Capability**\n"
         "3) Click **Add to Report Builder**\n"
         "4) Export a combined HTML report")

st.divider()

st.subheader("What makes it different")
st.write(
    "- **Typed dropdowns** (only shows compatible columns)\n"
    "- **Friendly interpretation** (what the data is telling you)\n"
    "- **Report Builder** (one deliverable across tools)\n"
    "- **Local-first** option (keep data in your environment)"
)

st.info("Tip: If you're evaluating ProcessIQ, start with the built-in sample data in Data Explorer.")
