# Interactive Plotly Charts

## Data and Assumptions

The inspected PostgreSQL schema contains `orders.order_date` and
`orders.order_amount`, but no product, profit, or marketing-spend columns.
This assignment reuses the version-controlled `data/visualization_sales.csv`
dataset created for the prior visualization assignment because it contains the
required product line, order date, order amount, and marketing-spend fields.
There is no legitimate cost basis in the project, so Profit is explicitly shown
as unavailable in the metric selector rather than fabricated.

## Generated Charts

- `chart1_revenue_trend.html`: daily revenue line/marker chart with date,
  currency, and order-count hover details.
- `chart2_product_performance.html`: product revenue bar chart with revenue,
  order count, and AOV hover details.
- `chart3_metric_selector.html`: monthly dropdown for Revenue and Order Count,
  with an explicit unavailable Profit state.
- `chart4_interactive.html`: marketing-spend/order-value scatter plot with
  zoom, pan, reset, box select, lasso select, and hover controls.

## Date Range Controls in Plotly

For a weekly revenue time series, use a `rangeselector` for quick relative
windows and a `rangeslider` for direct interval selection. Buttons are useful
when users repeatedly need standard windows such as the last month, quarter,
or all history. A range slider is useful when users need to choose an exact
continuous period, such as only Q1 2024.

```python
import plotly.graph_objects as go

weekly = ...  # DataFrame with week and revenue columns
fig = go.Figure(go.Scatter(
    x=weekly["week"],
    y=weekly["revenue"],
    mode="lines+markers",
    hovertemplate="Week: %{x|%b %d, %Y}<br>Revenue: $%{y:,.2f}<extra></extra>",
))
fig.update_xaxes(
    rangeselector=dict(
        buttons=[
            dict(count=1, label="1M", step="month", stepmode="backward"),
            dict(count=3, label="3M", step="month", stepmode="backward"),
            dict(step="all", label="All"),
        ]
    ),
    rangeslider=dict(visible=True),
    title="Weekly Revenue",
)
fig.show()
```

The same `update_xaxes` configuration can be added to
`chart1_revenue_trend.py` when the chart is generated.