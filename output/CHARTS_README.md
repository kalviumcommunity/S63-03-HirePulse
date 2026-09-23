# Business Visualisation Principles

## Data Source Note

The inspected PostgreSQL database contains `customers`, `orders`, and `logins`,
but its order table does not contain product-line, 12-month history, or
marketing-spend columns. Existing CSV examples also did not provide a coherent
dataset with all required fields. To avoid inventing fields in the existing
schema, this assignment uses the version-controlled local dataset
`data/visualization_sales.csv`.

It contains 132 deterministic order observations from October 2025 through
September 2026, four product lines, order amounts, and monthly marketing spend.
The dataset was created specifically to satisfy the visualization requirements;
all insights below are calculated by `assignment-35-visualizations.py` from
those rows.

## Chart 1 - Revenue by Product Line

- **Type:** Horizontal bar chart
- **Business question:** Which product line generated the most revenue during the last 90 days?
- **Data source:** `data/visualization_sales.csv`
- **Columns:** `order_date`, `product_line`, `order_amount`
- **Time period:** 2026-06-25 through 2026-09-23
- **Calculation:** Sum `order_amount` by `product_line` after the date filter.
- **Actual key insight:** Analytics Suite generated the highest 90-day revenue at `$68,200`.
- **Annotation:** Marks the highest-revenue product line and its actual amount.
- **Why this chart:** Horizontal bars make sorted category comparisons and currency labels easy to scan.

Output: `chart1_revenue_by_product.png`

## Chart 2 - Revenue Trend

- **Type:** Multi-series line chart
- **Business question:** How has revenue changed over the last 12 months, and how do the top three product lines compare?
- **Data source:** `data/visualization_sales.csv`
- **Columns:** `order_date`, `product_line`, `order_amount`
- **Time period:** October 2025 through September 2026
- **Calculation:** Monthly sum of `order_amount`; the three plotted products are selected by actual total revenue.
- **Actual key insight:** The actual top three are Analytics Suite, Security Monitor, and Collaboration Hub.
- **Annotation:** Marks the peak combined month calculated from those three series.
- **Why this chart:** Lines show direction and month-to-month change while preserving product comparison.

Output: `chart2_revenue_trend.png`

## Chart 3 - Order Value Distribution

- **Type:** Histogram
- **Business question:** What is the distribution of order values?
- **Data source:** `data/visualization_sales.csv`
- **Columns:** `order_amount`
- **Time period:** All 132 observations in the dataset
- **Calculation:** Histogram using 10 bins selected from the observed order-value range.
- **Actual key insight:** The mean order value is `$4,450` and the median is `$4,225`.
- **Annotation:** Shows the actual median, with mean and median reference lines.
- **Why this chart:** A histogram reveals concentration and spread that a single average would hide.

Output: `chart3_order_value_distribution.png`

## Chart 4 - Quarterly Revenue Composition

- **Type:** Stacked bar chart
- **Business question:** How does revenue composition differ by quarter and product line?
- **Data source:** `data/visualization_sales.csv`
- **Columns:** `order_date`, `product_line`, `order_amount`
- **Time period:** Q4 2025 through Q3 2026
- **Calculation:** Sum `order_amount` by calendar quarter and product line, stacking the product totals.
- **Actual key insight:** Four calendar quarters are represented, with product contributions visible within each total.
- **Annotation:** Marks the quarter with the largest calculated total revenue.
- **Why this chart:** Stacking shows both total quarterly scale and the composition of each total.

Output: `chart4_revenue_composition.png`

## Chart 5 - Marketing Spend vs Revenue

- **Type:** Scatter plot with linear trend line
- **Business question:** What is the relationship between marketing spend and revenue?
- **Data source:** `data/visualization_sales.csv`
- **Columns:** `order_date`, `marketing_spend`, `order_amount`
- **Time period:** October 2025 through September 2026, aggregated to month
- **Calculation:** Monthly marketing spend and monthly revenue; Pearson correlation and least-squares trend line are calculated from the 12 monthly observations.
- **Actual key insight:** The calculated correlation coefficient is `r = 0.987`.
- **Annotation:** Identifies the month with the largest absolute residual from the calculated trend line.
- **Why this chart:** A scatter plot shows the strength and direction of association while exposing notable observations.

## Reproduce

```bash
.venv-1/Scripts/python.exe assignment-35-visualizations.py
```

The script writes all five PNGs at 300 DPI to `output/` and prints the actual
calculated insights used in this document.