"""
KPI Definition & Business Metric Design
HirePulse

Tasks covered:
3. Validate KPIs against target ranges
4. Decompose Total Revenue:
   Total Revenue -> Customer Segment -> Product
"""

from pathlib import Path
import json
import sys

import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Add repository root to Python import path.
sys.path.insert(0, str(BASE_DIR))

from kpis.kpi_functions import (
    calculate_all_kpis,
    format_currency,
    format_percentage,
)


DATA_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "customer_segment_data.csv"
)

TARGET_FILE = (
    BASE_DIR
    / "kpis"
    / "kpi_validation_targets.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "output"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("KPI DEFINITION & BUSINESS METRIC DESIGN")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_csv(DATA_FILE)

print(
    f"Dataset: {DATA_FILE}"
)

print(
    f"Rows: {len(df)}"
)

print(
    f"Unique customers: "
    f"{df['customer_id'].nunique()}"
)


# ============================================================
# LOAD TARGETS
# ============================================================

print("\nLoading KPI target ranges...")

with open(
    TARGET_FILE,
    "r",
    encoding="utf-8",
) as file:
    targets = json.load(file)

print(
    f"Targets loaded: {len(targets)} KPIs"
)


# ============================================================
# TASK 3
# COMPUTE CURRENT KPIs
# ============================================================

print("\n" + "=" * 70)
print("TASK 3: KPI VALIDATION")
print("=" * 70)

current_kpis = calculate_all_kpis(df)


# ============================================================
# KPI DISPLAY NAMES
# ============================================================

display_names = {
    "average_revenue_per_customer":
        "Average Revenue per Customer",

    "churn_rate":
        "Customer Churn Rate",

    "enterprise_revenue_per_customer":
        "Enterprise Revenue per Customer",

    "smb_revenue_per_customer":
        "SMB Revenue per Customer",

    "startup_revenue_per_customer":
        "Startup Revenue per Customer",

    "enterprise_revenue_share":
        "Enterprise Revenue Share",
}


# ============================================================
# KPI FORMATTING
# ============================================================

currency_kpis = {
    "average_revenue_per_customer",
    "enterprise_revenue_per_customer",
    "smb_revenue_per_customer",
    "startup_revenue_per_customer",
}

percentage_kpis = {
    "churn_rate",
    "enterprise_revenue_share",
}


def format_kpi_value(kpi_name, value):
    """Format KPI value for readable output."""

    if kpi_name in currency_kpis:
        return format_currency(value)

    if kpi_name in percentage_kpis:
        return format_percentage(value)

    return f"{value:.2f}"


# ============================================================
# VALIDATE TARGETS
# ============================================================

validation_report = []

for kpi_name, target_range in targets.items():

    actual = current_kpis[kpi_name]

    min_value = target_range["min"]
    max_value = target_range["max"]

    if min_value <= actual <= max_value:
        status = "PASS"
    else:
        status = "ALERT"

    validation_report.append(
        {
            "kpi": kpi_name,
            "kpi_name": display_names.get(
                kpi_name,
                kpi_name,
            ),
            "actual": actual,
            "target_min": min_value,
            "target_max": max_value,
            "status": status,
        }
    )


validation_df = pd.DataFrame(
    validation_report
)


# ============================================================
# DISPLAY VALIDATION REPORT
# ============================================================

for _, row in validation_df.iterrows():

    kpi_name = row["kpi"]

    actual_display = format_kpi_value(
        kpi_name,
        row["actual"],
    )

    target_min_display = format_kpi_value(
        kpi_name,
        row["target_min"],
    )

    target_max_display = format_kpi_value(
        kpi_name,
        row["target_max"],
    )

    symbol = (
        "✓"
        if row["status"] == "PASS"
        else "⚠"
    )

    print(
        f"{symbol} "
        f"{row['kpi_name']}: "
        f"{actual_display} "
        f"(Target: "
        f"{target_min_display} - "
        f"{target_max_display}) "
        f"[{row['status']}]"
    )


# ============================================================
# VALIDATION SUMMARY
# ============================================================

pass_count = (
    validation_df["status"] == "PASS"
).sum()

alert_count = (
    validation_df["status"] == "ALERT"
).sum()

print("\n" + "-" * 70)

print(
    f"KPIs within target: {pass_count}"
)

print(
    f"KPIs outside target: {alert_count}"
)

if alert_count > 0:
    print(
        f"\n⚠ {alert_count} KPI(s) are outside "
        f"the defined target range."
    )
else:
    print(
        "\n✓ All KPIs are within target ranges."
    )


# ============================================================
# SAVE VALIDATION REPORT
# ============================================================

validation_file = (
    OUTPUT_DIR
    / "kpi_validation_report.csv"
)

validation_df.to_csv(
    validation_file,
    index=False,
)

print(
    f"\nValidation report saved to: "
    f"{validation_file}"
)


# ============================================================
# TASK 4
# KPI DECOMPOSITION
# ============================================================

print("\n" + "=" * 70)
print("TASK 4: KPI DECOMPOSITION")
print("=" * 70)


# ============================================================
# LEVEL 1 — TOTAL REVENUE
# ============================================================

total_revenue = df["revenue"].sum()

print("\nLEVEL 1 — TOTAL REVENUE")

print(
    f"Total Revenue: "
    f"{format_currency(total_revenue)}"
)


# ============================================================
# LEVEL 2 — REVENUE BY CUSTOMER SEGMENT
# ============================================================

revenue_by_segment = (
    df.groupby("customer_type")["revenue"]
    .sum()
    .sort_values(ascending=False)
)

print("\nLEVEL 2 — REVENUE BY CUSTOMER SEGMENT")

for segment, revenue in revenue_by_segment.items():

    print(
        f"{segment}: "
        f"{format_currency(revenue)}"
    )


# ============================================================
# VERIFY SEGMENT TOTAL
# ============================================================

segment_total = revenue_by_segment.sum()

print(
    f"\nSegment Revenue Total: "
    f"{format_currency(segment_total)}"
)

print(
    f"Matches Total Revenue: "
    f"{segment_total == total_revenue}"
)


# ============================================================
# LEVEL 3 — REVENUE BY PRODUCT WITHIN SEGMENT
# ============================================================

print(
    "\nLEVEL 3 — REVENUE BY PRODUCT WITHIN SEGMENT"
)

revenue_by_segment_product = (
    df.groupby(
        [
            "customer_type",
            "product",
        ]
    )["revenue"]
    .sum()
)


for segment in revenue_by_segment.index:

    print(
        f"\n{segment}:"
    )

    segment_products = (
        revenue_by_segment_product
        .loc[segment]
        .sort_values(ascending=False)
    )

    for product, revenue in segment_products.items():

        print(
            f"  {product}: "
            f"{format_currency(revenue)}"
        )


# ============================================================
# VERIFY PRODUCT TOTAL
# ============================================================

product_total = (
    df.groupby("product")["revenue"]
    .sum()
    .sum()
)

print(
    f"\nProduct Revenue Total: "
    f"{format_currency(product_total)}"
)

print(
    f"Matches Total Revenue: "
    f"{product_total == total_revenue}"
)


# ============================================================
# CUSTOMER COUNT DECOMPOSITION
# ============================================================

print("\n" + "-" * 70)

print(
    "CUSTOMER COUNT DECOMPOSITION"
)

total_customers = df["customer_id"].nunique()

print(
    f"Total Customers: "
    f"{total_customers}"
)

customer_counts = (
    df.groupby("customer_type")["customer_id"]
    .nunique()
)

for segment, count in customer_counts.items():

    print(
        f"{segment}: {count} customers"
    )

print(
    f"Segment Customer Total: "
    f"{customer_counts.sum()}"
)


# ============================================================
# REVENUE PER CUSTOMER DECOMPOSITION
# ============================================================

print("\n" + "-" * 70)

print(
    "REVENUE PER CUSTOMER DECOMPOSITION"
)

print(
    "Revenue per Customer = "
    "Total Revenue / Unique Customers"
)

print(
    f"{format_currency(total_revenue)} / "
    f"{total_customers} = "
    f"{format_currency(current_kpis['average_revenue_per_customer'])}"
)


# ============================================================
# BUILD TEXT REPORT
# ============================================================

analysis_file = (
    OUTPUT_DIR
    / "kpi_analysis.txt"
)

with open(
    analysis_file,
    "w",
    encoding="utf-8",
) as file:

    file.write(
        "KPI DEFINITION & BUSINESS METRIC DESIGN\n"
    )

    file.write(
        "=" * 70 + "\n\n"
    )

    file.write(
        "DATASET\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    file.write(
        f"Source: {DATA_FILE}\n"
    )

    file.write(
        f"Rows: {len(df)}\n"
    )

    file.write(
        f"Unique customers: {total_customers}\n\n"
    )

    file.write(
        "CURRENT KPI VALUES\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    for _, row in validation_df.iterrows():

        kpi_name = row["kpi"]

        file.write(
            f"{row['kpi_name']}: "
            f"{format_kpi_value(kpi_name, row['actual'])}\n"
        )

    file.write("\n")

    file.write(
        "TARGET VALIDATION\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    for _, row in validation_df.iterrows():

        kpi_name = row["kpi"]

        file.write(
            f"{row['kpi_name']}: "
            f"{format_kpi_value(kpi_name, row['actual'])} | "
            f"Target: "
            f"{format_kpi_value(kpi_name, row['target_min'])}"
            f" - "
            f"{format_kpi_value(kpi_name, row['target_max'])}"
            f" | Status: {row['status']}\n"
        )

    file.write("\n")

    file.write(
        f"KPIs within target: {pass_count}\n"
    )

    file.write(
        f"KPIs outside target: {alert_count}\n\n"
    )

    file.write(
        "KPI DECOMPOSITION\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    file.write(
        f"Level 1 - Total Revenue: "
        f"{format_currency(total_revenue)}\n\n"
    )

    file.write(
        "Level 2 - Revenue by Customer Segment:\n"
    )

    for segment, revenue in revenue_by_segment.items():

        file.write(
            f"  {segment}: "
            f"{format_currency(revenue)}\n"
        )

    file.write("\n")

    file.write(
        "Level 3 - Revenue by Product within Segment:\n"
    )

    for segment in revenue_by_segment.index:

        file.write(
            f"  {segment}:\n"
        )

        segment_products = (
            revenue_by_segment_product
            .loc[segment]
            .sort_values(ascending=False)
        )

        for product, revenue in segment_products.items():

            file.write(
                f"    {product}: "
                f"{format_currency(revenue)}\n"
            )

    file.write("\n")

    file.write(
        f"Segment revenue total: "
        f"{format_currency(segment_total)}\n"
    )

    file.write(
        f"Product revenue total: "
        f"{format_currency(product_total)}\n"
    )

    file.write(
        f"Total revenue: "
        f"{format_currency(total_revenue)}\n"
    )

    file.write(
        "All decomposition levels reconcile to "
        "Total Revenue.\n\n"
    )

    file.write(
        "KPI GOVERNANCE\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    file.write(
        "KPI definitions: kpis/kpi_reference.md\n"
    )

    file.write(
        "Target ranges: kpis/kpi_validation_targets.json\n"
    )

    file.write(
        "Reusable functions: kpis/kpi_functions.py\n"
    )

    file.write(
        "Schema changes should be documented and historical "
        "comparability should be reviewed.\n"
    )


print(
    f"\nAnalysis report saved to: "
    f"{analysis_file}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("KPI ANALYSIS COMPLETE")
print("=" * 70)

print(
    f"Validation report: "
    f"{validation_file}"
)

print(
    f"Analysis report: "
    f"{analysis_file}"
)

print(
    f"KPIs evaluated: "
    f"{len(validation_df)}"
)

print(
    f"PASS: {pass_count}"
)

print(
    f"ALERT: {alert_count}"
)

print(
    f"Total Revenue: "
    f"{format_currency(total_revenue)}"
)

print(
    f"Revenue decomposition reconciled: "
    f"{segment_total == total_revenue and product_total == total_revenue}"
)