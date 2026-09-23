"""Interactive Sales Dashboard built with Streamlit and Plotly."""

from pathlib import Path

import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

from interactive_charts.common import load_orders
from kpi_dashboard import DATABASE_URL, calculate_kpis, format_value


st.set_page_config(page_title="Interactive Sales Dashboard", layout="wide")
st.title("Interactive Sales Dashboard")

st.subheader("Sales Performance Dashboard")
kpis = calculate_kpis(create_engine(DATABASE_URL, future=True))
columns = st.columns(5)
for column, (_, kpi) in zip(columns, kpis.iterrows()):
    with column:
        st.metric(kpi["Metric"], format_value(kpi["Metric"], kpi["Current"]), kpi["Change_Display"], delta_color="inverse" if kpi["Metric"] == "Churn Rate" else "normal")
        st.markdown(
            f"<span style='color:{kpi['Color']};font-weight:700'>{kpi['Arrow']} {kpi['Status']}</span>"
            f"<br><small>Prior: {format_value(kpi['Metric'], kpi['Prior'])}</small>",
            unsafe_allow_html=True,
        )

st.divider()
st.header("Detailed Analytics")

orders = load_orders()
minimum_amount = st.sidebar.number_input("Minimum order amount", min_value=0.0, value=0.0, step=100.0)
date_range = st.sidebar.date_input("Order date range", value=(orders["order_date"].min().date(), orders["order_date"].max().date()))
products = st.sidebar.multiselect("Product line", options=sorted(orders["product_line"].unique()), default=sorted(orders["product_line"].unique()))

filtered = orders[orders["order_amount"].ge(minimum_amount)].copy()
if len(date_range) == 2:
    filtered = filtered[filtered["order_date"].dt.date.between(date_range[0], date_range[1])]
if products:
    filtered = filtered[filtered["product_line"].isin(products)]
else:
    filtered = filtered.iloc[0:0]

st.write(f"Showing {len(filtered):,} orders >= ${minimum_amount:,.2f}")
monthly = filtered.assign(month=filtered["order_date"].dt.to_period("M")).groupby("month", as_index=False)["order_amount"].sum()
figure = px.line(monthly, x="month", y="order_amount", markers=True, title="Filtered Monthly Revenue", labels={"month": "Month", "order_amount": "Revenue ($)"})
st.plotly_chart(figure, use_container_width=True)
st.dataframe(filtered[["order_date", "customer_id", "order_amount", "product_line"]].sort_values("order_date"), use_container_width=True)