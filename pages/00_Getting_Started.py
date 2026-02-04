from __future__ import annotations

import streamlit as st

from processiq.ui import set_page
from processiq.sample import load_sample_quality, load_sample_grr
from processiq.state import set_df, get_df, clear_df

set_page("Getting Started", icon="🚀")

st.title("ProcessIQ")
st.caption("A focused, QE-first toolbox for the most-used quality analyses (Minitab-lite).")

shared_df, shared_name = get_df()
if shared_df is not None:
    st.success(f"Current shared dataset: {shared_name}")
    if st.button("Clear shared dataset"):
        clear_df()
        st.rerun()
else:
    st.info("No shared dataset loaded yet. Load a sample dataset below, or upload your own in Data Explorer.")

st.subheader("Try it in 30 seconds")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### Sample: Quality dataset")
    st.write("Best for: Control Charts, Capability, Pareto, Regression.")
    if st.button("Load sample (Quality)", use_container_width=True):
        df = load_sample_quality()
        set_df(df, "Sample: Quality dataset")
        st.success("Loaded sample quality dataset.")
        st.rerun()

with c2:
    st.markdown("### Sample: Gage R&R dataset")
    st.write("Best for: Gage R&R (crossed).")
    if st.button("Load sample (Gage R&R)", use_container_width=True):
        df = load_sample_grr()
        set_df(df, "Sample: Gage R&R dataset")
        st.success("Loaded sample Gage R&R dataset.")
        st.rerun()

st.divider()

st.subheader("Suggested first clicks")
st.markdown(
    """
**1) Control Charts → I-MR**
- Pick `measurement`
- Look for rule violations and special cause signals

**2) Process Capability**
- Pick `measurement`
- Enter LSL/USL + Target
- Compare Mean vs Target and Cp/Cpk vs Pp/Ppk

**3) Data Explorer**
- Filter by `shift` or `operator`
- Quick histogram/boxplot checks
"""
)

st.subheader("What ProcessIQ does differently")
st.markdown(
    """
- **Decision guidance:** plain-English callouts for stability and capability
- **Fast workflow:** upload once → reuse across tools
- **Focused scope:** the most-used QE tools, not everything under the sun
"""
)

st.caption("Tip: Load a sample dataset first, then jump into Control Charts or Capability.")
