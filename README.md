# ProcessIQ QE Tools (Streamlit)
A practical “cheap alternative to Minitab” focused on the most used, highest-impact Quality / Manufacturing analytics.

## Included tools (v0 scaffold)
- **Data Explorer** (upload CSV/XLSX, filter, plot, export)
- **Control Charts**: I‑MR, Xbar‑R (subgroup), p-chart (attribute)
- **Capability**: Cp/Cpk/Pp/Ppk + histogram + optional normality test
- **Pareto**: counts by category + cumulative %
- **Regression Quick Check**: OLS + scatter + coefficients
- **Gage R&R (Crossed, ANOVA)**: Part × Operator with repeats

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- This is intentionally opinionated: *fast decision support* over exhaustive stats menus.
- Add new tools by creating a file under `pages/`.
