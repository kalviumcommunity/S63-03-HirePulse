"""Generate a Plotly dropdown for available revenue and order-count metrics."""

from pathlib import Path

import plotly.graph_objects as go

from common import load_orders


OUTPUT = Path(__file__).resolve().parent / "chart3_metric_selector.html"


def build_chart():
    orders = load_orders()
    monthly = orders.assign(month=orders["order_date"].dt.to_period("M")).groupby("month", as_index=False).agg(
        revenue=("order_amount", "sum"), order_count=("order_id", "nunique")
    )
    months = monthly["month"].astype(str).tolist()
    profit_unavailable = [True] * len(months)
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=months, y=monthly["revenue"], mode="lines+markers", name="Revenue", visible=True, line={"color": "#2563EB"}))
    figure.add_trace(go.Scatter(x=months, y=monthly["order_count"], mode="lines+markers", name="Order Count", visible=False, line={"color": "#14B8A6"}))
    figure.add_trace(go.Scatter(x=months, y=[None] * len(months), mode="lines+markers", name="Profit unavailable", visible=False, line={"color": "#94A3B8"}))
    figure.update_layout(
        title="Monthly Revenue",
        xaxis_title="Month",
        yaxis_title="Revenue ($)",
        template="plotly_white",
        updatemenus=[{"buttons": [
            {"label": "Revenue", "method": "update", "args": [{"visible": [True, False, False]}, {"title": "Monthly Revenue", "yaxis": {"title": "Revenue ($)", "tickformat": "$,.0f"}}]},
            {"label": "Order Count", "method": "update", "args": [{"visible": [False, True, False]}, {"title": "Monthly Order Count", "yaxis": {"title": "Order Count", "tickformat": ","}}]},
            {"label": "Profit (unavailable)", "method": "update", "args": [{"visible": [False, False, True]}, {"title": "Profit unavailable: no profit column or cost basis", "yaxis": {"title": "Profit unavailable"}}]},
        ], "direction": "down", "x": 1.0, "xanchor": "right", "y": 1.15}],
        annotations=[{"text": "Profit is not calculated because the inspected schema has no cost/profit fields.", "xref": "paper", "yref": "paper", "x": 0, "y": -0.18, "showarrow": False, "font": {"color": "#475569"}}],
    )
    figure.write_html(OUTPUT, include_plotlyjs=True, config={"displaylogo": False, "scrollZoom": True})
    return figure


if __name__ == "__main__":
    build_chart()
    print(f"Wrote {OUTPUT}")