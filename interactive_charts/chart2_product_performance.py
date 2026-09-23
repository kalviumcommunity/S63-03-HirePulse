"""Generate an interactive product performance bar chart."""

from pathlib import Path

import plotly.graph_objects as go

from common import load_orders


OUTPUT = Path(__file__).resolve().parent / "chart2_product_performance.html"


def build_chart():
    orders = load_orders()
    summary = orders.groupby("product_line", as_index=False).agg(
        revenue=("order_amount", "sum"), order_count=("order_id", "nunique"), average_order_value=("order_amount", "mean")
    ).sort_values("revenue", ascending=False)
    figure = go.Figure(go.Bar(
        x=summary["product_line"], y=summary["revenue"],
        marker_color=["#2563EB", "#14B8A6", "#F59E0B", "#E11D48"],
        customdata=summary[["order_count", "average_order_value"]],
        hovertemplate="<b>Product Line:</b> %{x}<br><b>Revenue:</b> $%{y:,.2f}<br><b>Order Count:</b> %{customdata[0]:,}<br><b>Average Order Value:</b> $%{customdata[1]:,.2f}<extra></extra>",
    ))
    figure.update_layout(title="Revenue Performance by Product Line", xaxis_title="Product Line", yaxis_title="Revenue ($)", template="plotly_white")
    figure.write_html(OUTPUT, include_plotlyjs=True, config={"displaylogo": False, "scrollZoom": True})
    return figure


if __name__ == "__main__":
    build_chart()
    print(f"Wrote {OUTPUT}")