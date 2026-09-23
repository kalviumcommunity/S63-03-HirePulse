# Analysis Report Guide

## cleaned_data.csv

This file contains the actual customer-level analysis input from
`data/raw/customer_correlation_data.csv`. It includes the source columns such
as `customer_id`, `support_tickets`, `revenue`, and `churn`. Stakeholders can
open it in Excel to filter customers, compare churn labels, and perform their
own pivots. Each on-demand or scheduled run writes a fresh copy into a
timestamped folder under `output/generated_reports/`.

## summary_report.pdf

This PDF contains the generated executive summary and the actual observed churn
and support-ticket findings. Use it for email, leadership review, and meeting
packs. PDF generation attempts WeasyPrint first. On Windows environments where
WeasyPrint's native GTK/Pango libraries are unavailable, the exporter logs that
limitation and uses the declared `fpdf2` fallback so a real PDF is still
produced.

## interactive_report.html

This report contains the executive summary and Plotly charts for revenue by
customer type and support tickets by churn label. It supports Plotly hover,
zoom, and pan. The implementation embeds Plotly JavaScript in the file, so the
report is designed to open without internet access.

## How to Use These Files

1. Open `cleaned_data.csv` in Excel or another data-analysis tool.
2. Attach the PDF to a presentation or leadership email.
3. Open the HTML file in a browser to explore the charts.
4. Share the complete timestamped report folder when the CSV, PDF, and HTML
   need to remain together.

## When Are These Files Updated?

The Streamlit integration provides an on-demand **Export Analysis** button. The
standalone scheduler is configured for daily execution at 5:00 PM and can be
tested immediately with `scheduled_export.py --once`. Every run creates a new
folder named `YYYY-MM-DD_HHMM_analysis` under `output/generated_reports/`.

## Limitations

The source dataset is cross-sectional and does not contain response times,
renewal dates, or intervention outcomes. The export reports do not invent those
metrics or financial impact.