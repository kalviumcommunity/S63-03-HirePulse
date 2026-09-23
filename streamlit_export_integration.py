"""Streamlit-compatible data, summary, charts, and export-button helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px

from export_functions import export_analysis


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "raw" / "customer_correlation_data.csv"
OUTPUT_DIR = ROOT / "output" / "generated_reports"


def load_analysis_data() -> pd.DataFrame:
    frame = pd.read_csv(DATA_PATH)
    required = {"customer_id", "support_tickets", "revenue", "churn"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing analysis columns: {sorted(missing)}")
    return frame


def build_summary(frame: pd.DataFrame) -> str:
    churn_rate = frame["churn"].mean() * 100
    churned = frame[frame["churn"].eq(1)]["support_tickets"].mean()
    retained = frame[frame["churn"].eq(0)]["support_tickets"].mean()
    return f"""# Customer Churn Analysis

The analysis contains **{len(frame):,} customer records** and an observed churn rate of **{churn_rate:.2f}%**.

- Churned customers average **{churned:.1f} support tickets**.
- Non-churned customers average **{retained:.1f} support tickets**.
- The available data supports an association review, not a causal claim or financial loss estimate.
"""


def build_charts(frame: pd.DataFrame) -> dict:
    segment = pd.read_csv(ROOT / "data" / "raw" / "customer_segment_data.csv")
    segment_summary = segment.groupby("customer_type", as_index=False).agg(revenue=("revenue", "sum"), churn_rate=("churn", "mean"))
    return {
        "Revenue by Customer Type": px.bar(segment_summary, x="customer_type", y="revenue", title="Revenue by Customer Type", labels={"revenue": "Revenue ($)", "customer_type": "Customer Type"}),
        "Support Tickets and Churn": px.box(frame, x="churn", y="support_tickets", title="Support Tickets by Churn Status", labels={"churn": "Churn Label", "support_tickets": "Support Tickets"}),
    }


def generate_current_report() -> Path:
    frame = load_analysis_data()
    return export_analysis(frame, build_summary(frame), build_charts(frame), OUTPUT_DIR)


def render_export_section(st):
    """Render the export controls inside an existing Streamlit app."""
    st.sidebar.header("Export Analysis")
    if st.sidebar.button("Export Analysis"):
        try:
            report_dir = generate_current_report()
            st.sidebar.success(f"Report generated: {report_dir}")
            st.sidebar.download_button("Download CSV", (report_dir / "cleaned_data.csv").read_bytes(), file_name="cleaned_data.csv", mime="text/csv")
            st.sidebar.download_button("Download HTML", (report_dir / "interactive_report.html").read_bytes(), file_name="interactive_report.html", mime="text/html")
        except Exception as error:
            st.sidebar.error(f"Export failed: {error}")


def main():
    import streamlit as st

    st.set_page_config(page_title="Analysis Export", layout="wide")
    st.title("Customer Analysis Export")
    frame = load_analysis_data()
    st.write(f"Loaded {len(frame):,} analysis records from the validated correlation dataset.")
    st.dataframe(frame.head(25), use_container_width=True)
    render_export_section(st)


if __name__ == "__main__":
    main()