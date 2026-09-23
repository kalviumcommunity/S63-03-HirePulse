"""Generate a scatter chart with Plotly exploration controls."""

from pathlib import Path

import plotly.express as px

from common import load_orders


OUTPUT = Path(__file__).resolve().parent / "chart4_interactive.html"


def build_chart():
    orders = load_orders()
    figure = px.scatter(
        orders, x="marketing_spend", y="order_amount", color="product_line",
        hover_data={"order_id": True, "order_date": True, "marketing_spend": ":$,.2f", "order_amount": ":$,.2f"},
        title="Order Value vs Monthly Marketing Spend",
        labels={"marketing_spend": "Marketing Spend ($)", "order_amount": "Order Value ($)", "product_line": "Product Line"},
        color_discrete_sequence=["#2563EB", "#14B8A6", "#F59E0B", "#E11D48"],
    )
    figure.update_layout(template="plotly_white", dragmode="zoom")
    figure.write_html(OUTPUT, include_plotlyjs=True, config={
        "displaylogo": False, "scrollZoom": True, "modeBarButtonsToAdd": ["select2d", "lasso2d", "resetScale2d"],
    })
    return figure


if __name__ == "__main__":
    build_chart()
    print(f"Wrote {OUTPUT}")