"""
Behavioural Analysis & User Segmentation
HirePulse - Segment Comparison Analysis

Assignment Tasks:
1. Define segments and compute 4+ metrics
2. Create summary statistics and rankings
3. Create a heatmap comparison
4. Identify top/bottom segment performance
5. Generate business-facing insights
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# 1. CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/raw/customer_segment_data.csv")
OUTPUT_DIR = Path("output")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. LOAD DATA
# ============================================================

print("=" * 70)
print("BEHAVIOURAL ANALYSIS & USER SEGMENTATION")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"\nDataset loaded: {INPUT_FILE}")
print(f"Rows: {len(df)}")
print(f"Columns: {list(df.columns)}")


# ============================================================
# 3. VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = [
    "customer_id",
    "customer_type",
    "product",
    "revenue",
    "churn",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ============================================================
# 4. DEFINE SEGMENTS
# ============================================================

print("\n" + "=" * 70)
print("SEGMENT DEFINITION")
print("=" * 70)

segments = df["customer_type"].dropna().unique()

print("Segmentation dimension: customer_type")
print(f"Number of segments: {len(segments)}")
print(f"Segments: {', '.join(sorted(segments))}")


# ============================================================
# 5. COMPUTE SEGMENT METRICS
# ============================================================

segment_metrics = df.groupby("customer_type").agg(
    avg_ltv=("revenue", "mean"),
    churn_rate=("churn", "mean"),
    avg_revenue=("revenue", "mean"),
    customer_count=("customer_id", "count"),
    total_revenue=("revenue", "sum"),
)

print("\n" + "=" * 70)
print("SEGMENT METRICS")
print("=" * 70)

print(segment_metrics)


# ============================================================
# 6. ADD RANKINGS
# ============================================================

segment_summary = segment_metrics.copy()

# Rank by average customer value.
# Higher value gets rank 1.

segment_summary["ltv_rank"] = (
    segment_summary["avg_ltv"]
    .rank(ascending=False, method="min")
    .astype(int)
)

# Rank by churn.
# Lower churn gets rank 1.

segment_summary["churn_rank"] = (
    segment_summary["churn_rate"]
    .rank(ascending=True, method="min")
    .astype(int)
)

# Rank by total revenue.
# Higher revenue gets rank 1.

segment_summary["revenue_rank"] = (
    segment_summary["total_revenue"]
    .rank(ascending=False, method="min")
    .astype(int)
)


print("\n" + "=" * 70)
print("SEGMENT RANKINGS")
print("=" * 70)

print(
    segment_summary[
        [
            "avg_ltv",
            "ltv_rank",
            "churn_rate",
            "churn_rank",
            "avg_revenue",
            "revenue_rank",
            "customer_count",
        ]
    ]
)


# ============================================================
# 7. SAVE SUMMARY CSV
# ============================================================

summary_csv = OUTPUT_DIR / "segment_summary.csv"

segment_summary.to_csv(summary_csv)

print(f"\nSummary saved to: {summary_csv}")


# ============================================================
# 8. READABLE SUMMARY TABLE
# ============================================================

readable_summary = segment_summary.copy()

readable_summary["avg_ltv"] = readable_summary[
    "avg_ltv"
].map(lambda x: f"${x:,.0f}")

readable_summary["avg_revenue"] = readable_summary[
    "avg_revenue"
].map(lambda x: f"${x:,.0f}")

readable_summary["total_revenue"] = readable_summary[
    "total_revenue"
].map(lambda x: f"${x:,.0f}")

readable_summary["churn_rate"] = readable_summary[
    "churn_rate"
].map(lambda x: f"{x:.1%}")


print("\n" + "=" * 70)
print("READABLE SEGMENT SUMMARY")
print("=" * 70)

print(
    readable_summary[
        [
            "avg_ltv",
            "ltv_rank",
            "churn_rate",
            "churn_rank",
            "avg_revenue",
            "revenue_rank",
            "customer_count",
        ]
    ]
)


# ============================================================
# 9. HEATMAP VISUALIZATION
# ============================================================

print("\n" + "=" * 70)
print("CREATING SEGMENT HEATMAP")
print("=" * 70)

heatmap_data = segment_metrics[
    [
        "avg_ltv",
        "churn_rate",
        "avg_revenue",
        "customer_count",
    ]
].copy()

# Normalize metrics so different scales can be
# compared visually in the heatmap.

heatmap_normalized = heatmap_data.copy()

for column in heatmap_normalized.columns:

    minimum = heatmap_normalized[column].min()
    maximum = heatmap_normalized[column].max()

    if maximum != minimum:
        heatmap_normalized[column] = (
            heatmap_normalized[column] - minimum
        ) / (maximum - minimum)
    else:
        heatmap_normalized[column] = 0.5


plt.figure(figsize=(11, 6))

sns.heatmap(
    heatmap_normalized,
    annot=heatmap_data,
    fmt=".2f",
    cmap="RdYlGn",
    linewidths=0.5,
    cbar_kws={"label": "Normalized Value"},
)

plt.title("Customer Segment Comparison Heatmap")
plt.xlabel("Metrics")
plt.ylabel("Customer Segment")

plt.tight_layout()

heatmap_file = OUTPUT_DIR / "segment_heatmap.png"

plt.savefig(
    heatmap_file,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print(f"Heatmap saved to: {heatmap_file}")


# ============================================================
# 10. TOP AND BOTTOM PERFORMER ANALYSIS
# ============================================================

top_value_segment = segment_metrics[
    "avg_ltv"
].idxmax()

top_value = segment_metrics.loc[
    top_value_segment,
    "avg_ltv",
]

highest_churn_segment = segment_metrics[
    "churn_rate"
].idxmax()

highest_churn = segment_metrics.loc[
    highest_churn_segment,
    "churn_rate",
]

lowest_churn_segment = segment_metrics[
    "churn_rate"
].idxmin()

lowest_churn = segment_metrics.loc[
    lowest_churn_segment,
    "churn_rate",
]

largest_segment = segment_metrics[
    "customer_count"
].idxmax()

largest_segment_count = segment_metrics.loc[
    largest_segment,
    "customer_count",
]


print("\n" + "=" * 70)
print("TOP AND BOTTOM PERFORMER ANALYSIS")
print("=" * 70)

print(
    f"Highest value: {top_value_segment} "
    f"= ${top_value:,.0f} average revenue"
)

print(
    f"Highest churn: {highest_churn_segment} "
    f"= {highest_churn:.1%}"
)

print(
    f"Lowest churn: {lowest_churn_segment} "
    f"= {lowest_churn:.1%}"
)

print(
    f"Largest segment: {largest_segment} "
    f"= {largest_segment_count} customers"
)


# ============================================================
# 11. BUSINESS-FACING INSIGHTS
# ============================================================

insight_lines = []

insight_lines.append("=" * 70)
insight_lines.append("SEGMENT STRATEGY SUMMARY")
insight_lines.append("=" * 70)
insight_lines.append("")


for segment in segment_metrics.index:

    row = segment_metrics.loc[segment]

    avg_ltv = row["avg_ltv"]
    churn = row["churn_rate"]
    count = int(row["customer_count"])

    # Enterprise / highest-value segment
    if segment == top_value_segment:

        insight = (
            f"{segment} has the highest average customer value at "
            f"${avg_ltv:,.0f} and the lowest observed churn at "
            f"{churn:.1%}. This combination indicates a high-value "
            f"segment where retention and account expansion should "
            f"remain important priorities."
        )

    # Highest-churn segment
    elif segment == highest_churn_segment:

        insight = (
            f"{segment} has an average customer value of "
            f"${avg_ltv:,.0f}, but it also has the highest observed "
            f"churn at {churn:.1%}. Because churn is materially "
            f"higher than the other segments, prioritize targeted "
            f"retention, onboarding, and customer-support interventions."
        )

    # Remaining segment
    else:

        insight = (
            f"{segment} has an average customer value of "
            f"${avg_ltv:,.0f} with a churn rate of {churn:.1%}. "
            f"The segment sits between the other customer types on "
            f"the observed metrics, so targeted engagement should "
            f"focus on improving retention while protecting customer value."
        )

    insight_lines.append(
        f"{segment} ({count} customers):"
    )

    insight_lines.append(insight)
    insight_lines.append("")


# ============================================================
# 12. SAMPLE SIZE CAUTION
# ============================================================

insight_lines.append("=" * 70)
insight_lines.append("SAMPLE SIZE CAUTION")
insight_lines.append("=" * 70)

insight_lines.append(
    "Each segment contains 50 customers in this dataset, so the "
    "segment sizes are balanced for this comparison. However, "
    "larger real-world segments generally provide more stable "
    "estimates, while smaller segments can be more sensitive to "
    "individual customers and should be interpreted cautiously."
)

insight_lines.append("")


# ============================================================
# 13. ACTIONABILITY THRESHOLD
# ============================================================

insight_lines.append("=" * 70)
insight_lines.append("ACTIONABILITY THRESHOLD")
insight_lines.append("=" * 70)

insight_lines.append(
    "A segment difference should be considered actionable when "
    "it is materially large for the business, supported by a "
    "sufficient sample size, and consistent across related metrics "
    "or repeated observations. Small differences from a limited "
    "sample should be monitored before changing strategy."
)

insight_lines.append("")


# ============================================================
# 14. HEATMAP EXPLANATION
# ============================================================

insight_lines.append("=" * 70)
insight_lines.append("VISUALIZATION EXPLANATION")
insight_lines.append("=" * 70)

insight_lines.append(
    "The heatmap provides a side-by-side comparison of customer "
    "segments across average value, churn, average revenue, and "
    "customer count. Color intensity makes differences between "
    "segments easy to identify, while the annotations show the "
    "underlying metric values."
)

insight_lines.append("")


# ============================================================
# 15. SAVE INSIGHTS
# ============================================================

insights_file = OUTPUT_DIR / "segment_insights.txt"

with open(
    insights_file,
    "w",
    encoding="utf-8",
) as file:

    file.write(
        "\n".join(insight_lines)
    )

print(
    f"Insights saved to: {insights_file}"
)


# ============================================================
# 16. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("SEGMENT ANALYSIS COMPLETE")
print("=" * 70)

print(f"Input:    {INPUT_FILE}")
print(f"Summary:  {summary_csv}")
print(f"Heatmap:  {heatmap_file}")
print(f"Insights: {insights_file}")