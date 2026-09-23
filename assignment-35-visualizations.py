"""Create five business visualizations from the local visualization dataset."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "visualization_sales.csv"
OUTPUT_DIR = ROOT / "output"
REPORT_END = pd.Timestamp("2026-09-23")
WINDOW_START = REPORT_END - pd.Timedelta(days=90)

PALETTE = {
    "Analytics Suite": "#2563EB",
    "Collaboration Hub": "#14B8A6",
    "Security Monitor": "#F59E0B",
    "Data Connect": "#E11D48",
}
BACKGROUND = "#F8FAFC"
TEXT = "#0F172A"
GRID = "#CBD5E1"


def currency(value, _position=None):
    return f"${value:,.0f}"


def load_data() -> pd.DataFrame:
    frame = pd.read_csv(DATA_PATH, parse_dates=["order_date"])
    required = {"order_id", "order_date", "product_line", "order_amount", "marketing_spend"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing visualization columns: {sorted(missing)}")
    if frame.empty or frame["order_amount"].isna().any():
        raise ValueError("Visualization data must be non-empty and have order amounts")
    return frame


def style_axis(ax):
    ax.set_facecolor(BACKGROUND)
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors=TEXT)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)


def finish(fig, path: Path):
    fig.patch.set_facecolor(BACKGROUND)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close(fig)


def chart1(frame: pd.DataFrame):
    recent = frame[frame["order_date"].between(WINDOW_START, REPORT_END)]
    revenue = recent.groupby("product_line")["order_amount"].sum().sort_values()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(revenue.index, revenue.values, color=[PALETTE[p] for p in revenue.index])
    ax.set(title="Revenue by Product Line - Last 90 Days", xlabel="Revenue ($)", ylabel="Product Line")
    ax.xaxis.set_major_formatter(FuncFormatter(currency))
    style_axis(ax)
    leader = revenue.idxmax()
    ax.annotate(
        f"Highest: {leader} ({currency(revenue.max())})",
        xy=(revenue.max(), leader), xytext=(-170, 20), textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": TEXT}, color=TEXT,
    )
    for bar, value in zip(bars, revenue.values):
        ax.text(value, bar.get_y() + bar.get_height() / 2, f" {currency(value)}", va="center", color=TEXT)
    finish(fig, OUTPUT_DIR / "chart1_revenue_by_product.png")
    return revenue, recent


def chart2(frame: pd.DataFrame):
    monthly = frame.assign(month=frame["order_date"].dt.to_period("M")).pivot_table(
        index="month", columns="product_line", values="order_amount", aggfunc="sum", fill_value=0
    )
    top3 = frame.groupby("product_line")["order_amount"].sum().nlargest(3).index.tolist()
    fig, ax = plt.subplots(figsize=(11, 6))
    for product in top3:
        series = monthly[product] if product in monthly else pd.Series(0, index=monthly.index)
        ax.plot(monthly.index.astype(str), series, marker="o", linewidth=2.5, label=product, color=PALETTE[product])
    ax.set(title="Monthly Revenue Trend - Top 3 Product Lines", xlabel="Month", ylabel="Revenue ($)")
    ax.yaxis.set_major_formatter(FuncFormatter(currency))
    ax.legend(title="Product Line", frameon=False)
    style_axis(ax)
    totals = monthly[top3].sum(axis=1)
    peak = totals.idxmax()
    peak_product = monthly.loc[peak, top3].idxmax()
    peak_value = monthly.loc[peak, peak_product]
    ax.annotate(f"Peak month: {peak}\n{peak_product}: {currency(peak_value)}", xy=(str(peak), peak_value),
                xytext=(-75, 28), textcoords="offset points", arrowprops={"arrowstyle": "->", "color": TEXT}, color=TEXT)
    finish(fig, OUTPUT_DIR / "chart2_revenue_trend.png")
    return monthly, top3


def chart3(frame: pd.DataFrame):
    values = frame["order_amount"]
    mean_value = values.mean()
    median_value = values.median()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(values, bins=10, color=PALETTE["Analytics Suite"], alpha=0.85, edgecolor="white")
    ax.axvline(mean_value, color=PALETTE["Security Monitor"], linestyle="--", linewidth=2, label=f"Mean: {currency(mean_value)}")
    ax.axvline(median_value, color=PALETTE["Collaboration Hub"], linestyle=":", linewidth=2, label=f"Median: {currency(median_value)}")
    ax.set(title="Distribution of Order Values", xlabel="Order Value ($)", ylabel="Number of Orders")
    ax.xaxis.set_major_formatter(FuncFormatter(currency))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(frameon=False)
    style_axis(ax)
    ax.annotate(f"Median order: {currency(median_value)}", xy=(median_value, 1), xytext=(25, 25), textcoords="offset points",
                arrowprops={"arrowstyle": "->", "color": TEXT}, color=TEXT)
    finish(fig, OUTPUT_DIR / "chart3_order_value_distribution.png")
    return mean_value, median_value


def chart4(frame: pd.DataFrame):
    quarterly = frame.assign(quarter=frame["order_date"].dt.to_period("Q")).pivot_table(
        index="quarter", columns="product_line", values="order_amount", aggfunc="sum", fill_value=0
    )
    products = [p for p in PALETTE if p in quarterly.columns]
    fig, ax = plt.subplots(figsize=(11, 6))
    bottom = pd.Series(0.0, index=quarterly.index)
    for product in products:
        ax.bar(quarterly.index.astype(str), quarterly[product], bottom=bottom, label=product, color=PALETTE[product])
        bottom += quarterly[product]
    ax.set(title="Quarterly Revenue Composition by Product Line", xlabel="Quarter", ylabel="Revenue ($)")
    ax.yaxis.set_major_formatter(FuncFormatter(currency))
    ax.legend(title="Product Line", frameon=False, ncol=2)
    style_axis(ax)
    peak_quarter = bottom.idxmax()
    ax.annotate(f"Largest quarter: {peak_quarter} ({currency(bottom.max())})", xy=(str(peak_quarter), bottom.max()),
                xytext=(-55, 25), textcoords="offset points", arrowprops={"arrowstyle": "->", "color": TEXT}, color=TEXT)
    finish(fig, OUTPUT_DIR / "chart4_revenue_composition.png")
    return quarterly


def chart5(frame: pd.DataFrame):
    monthly = frame.assign(month=frame["order_date"].dt.to_period("M")).groupby("month").agg(
        marketing_spend=("marketing_spend", "first"), revenue=("order_amount", "sum")
    ).reset_index()
    correlation = monthly["marketing_spend"].corr(monthly["revenue"])
    slope, intercept = __import__("numpy").polyfit(monthly["marketing_spend"], monthly["revenue"], 1)
    monthly["predicted"] = slope * monthly["marketing_spend"] + intercept
    residual = (monthly["revenue"] - monthly["predicted"]).abs()
    outlier = monthly.loc[residual.idxmax()]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(monthly["marketing_spend"], monthly["revenue"], color=PALETTE["Analytics Suite"], s=70, label="Month")
    ordered = monthly.sort_values("marketing_spend")
    ax.plot(ordered["marketing_spend"], ordered["predicted"], color=PALETTE["Security Monitor"], linewidth=2, label="Linear trend")
    ax.set(title=f"Marketing Spend vs Revenue (r = {correlation:.3f})", xlabel="Marketing Spend ($)", ylabel="Revenue ($)")
    ax.xaxis.set_major_formatter(FuncFormatter(currency))
    ax.yaxis.set_major_formatter(FuncFormatter(currency))
    ax.legend(frameon=False)
    style_axis(ax)
    ax.annotate(f"Notable month: {outlier['month']}\nrevenue {currency(outlier['revenue'])}",
                xy=(outlier["marketing_spend"], outlier["revenue"]), xytext=(20, 20), textcoords="offset points",
                arrowprops={"arrowstyle": "->", "color": TEXT}, color=TEXT)
    finish(fig, OUTPUT_DIR / "chart5_marketing_vs_revenue.png")
    return monthly, correlation, outlier


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = load_data()
    revenue90, recent = chart1(frame)
    monthly, top3 = chart2(frame)
    mean_value, median_value = chart3(frame)
    quarterly = chart4(frame)
    monthly_marketing, correlation, outlier = chart5(frame)
    print(f"Loaded {len(frame)} orders from {DATA_PATH}")
    print(f"90-day window: {WINDOW_START.date()} through {REPORT_END.date()}")
    print(f"Chart 1 leader: {revenue90.idxmax()} ({currency(revenue90.max())})")
    print(f"Chart 2 top 3: {', '.join(top3)}")
    print(f"Chart 3 mean={currency(mean_value)}, median={currency(median_value)}")
    print(f"Chart 4 quarters: {len(quarterly)}")
    print(f"Chart 5 correlation: {correlation:.3f}; notable month: {outlier['month']}")


if __name__ == "__main__":
    main()