"""Generate an interactive Plotly revenue trend with custom hover details."""

from pathlib import Path

import plotly.graph_objects as go

from common import load_orders


OUTPUT = Path(__file__).resolve().parent / "chart1_revenue_trend.html"


def build_chart():
    orders = load_orders()
    daily = orders.groupby("order_date", as_index=False).agg(
        revenue=("order_amount", "sum"), order_count=("order_id", "nunique")
    )
    figure = go.Figure(
        go.Scatter(
            x=daily["order_date"],
            y=daily["revenue"],
            mode="lines+markers",
            line={"color": "#2563EB", "width": 3},
            marker={"color": "#14B8A6", "size": 8},
            customdata=daily[["order_count"]],
            hovertemplate="<b>Date:</b> %{x|%b %d, %Y}<br><b>Revenue:</b> $%{y:,.2f}<br><b>Order Count:</b> %{customdata[0]:,}<extra></extra>",
            name="Revenue",
        )
    )
    figure.update_layout(
        title="Daily Revenue Trend",
        xaxis_title="Order Date",
        yaxis_title="Revenue ($)",
        template="plotly_white",
        hovermode="x unified",
        xaxis={"tickformat": "%b %d, %Y", "rangeslider": {"visible": True}},
    )
    figure.write_html(OUTPUT, include_plotlyjs=True, config={"displaylogo": False, "scrollZoom": True})
    return figure


if __name__ == "__main__":
    build_chart()
    print(f"Wrote {OUTPUT}")