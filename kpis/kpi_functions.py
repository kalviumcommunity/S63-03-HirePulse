"""
Reusable KPI computation functions for HirePulse.

Primary dataset:
data/raw/customer_segment_data.csv
"""

from pathlib import Path

import pandas as pd


# ============================================================
# DATA FILE
# ============================================================

# Resolve the repository root regardless of where this module
# is executed from.
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "customer_segment_data.csv"
)


# ============================================================
# VALIDATION HELPER
# ============================================================

def _validate_columns(df, required_columns):
    """Validate that the DataFrame contains required columns."""

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
# KPI 1: AVERAGE REVENUE PER CUSTOMER
# ============================================================

def calculate_average_revenue_per_customer(df):
    """
    Calculate average revenue generated per unique customer.

    Formula:
        Total Revenue / Unique Customers

    Returns:
        float: Average revenue per customer.
    """

    _validate_columns(
        df,
        [
            "customer_id",
            "revenue",
        ],
    )

    unique_customers = df["customer_id"].nunique()

    if unique_customers == 0:
        return 0.0

    total_revenue = df["revenue"].sum()

    return total_revenue / unique_customers


# ============================================================
# KPI 2: CUSTOMER CHURN RATE
# ============================================================

def calculate_churn_rate(df):
    """
    Calculate customer churn rate.

    Formula:
        Churned Customers / Total Customers

    Returns:
        float:
            Churn rate as a decimal.
            Example: 0.10 = 10%
    """

    _validate_columns(
        df,
        [
            "customer_id",
            "churn",
        ],
    )

    total_customers = df["customer_id"].nunique()

    if total_customers == 0:
        return 0.0

    churned_customers = df.loc[
        df["churn"] == 1,
        "customer_id",
    ].nunique()

    return churned_customers / total_customers


# ============================================================
# KPI 3: ENTERPRISE REVENUE PER CUSTOMER
# ============================================================

def calculate_enterprise_revenue_per_customer(df):
    """
    Calculate average revenue per Enterprise customer.

    Formula:
        Enterprise Revenue / Enterprise Customer Count

    Returns:
        float: Enterprise revenue per customer.
    """

    _validate_columns(
        df,
        [
            "customer_id",
            "customer_type",
            "revenue",
        ],
    )

    enterprise_df = df[
        df["customer_type"] == "Enterprise"
    ]

    customer_count = enterprise_df[
        "customer_id"
    ].nunique()

    if customer_count == 0:
        return 0.0

    enterprise_revenue = (
        enterprise_df["revenue"].sum()
    )

    return enterprise_revenue / customer_count


# ============================================================
# KPI 4: SMB REVENUE PER CUSTOMER
# ============================================================

def calculate_smb_revenue_per_customer(df):
    """
    Calculate average revenue per SMB customer.

    Formula:
        SMB Revenue / SMB Customer Count

    Returns:
        float: SMB revenue per customer.
    """

    _validate_columns(
        df,
        [
            "customer_id",
            "customer_type",
            "revenue",
        ],
    )

    smb_df = df[
        df["customer_type"] == "SMB"
    ]

    customer_count = smb_df[
        "customer_id"
    ].nunique()

    if customer_count == 0:
        return 0.0

    smb_revenue = smb_df[
        "revenue"
    ].sum()

    return smb_revenue / customer_count


# ============================================================
# KPI 5: STARTUP REVENUE PER CUSTOMER
# ============================================================

def calculate_startup_revenue_per_customer(df):
    """
    Calculate average revenue per Startup customer.

    Formula:
        Startup Revenue / Startup Customer Count

    Returns:
        float: Startup revenue per customer.
    """

    _validate_columns(
        df,
        [
            "customer_id",
            "customer_type",
            "revenue",
        ],
    )

    startup_df = df[
        df["customer_type"] == "Startup"
    ]

    customer_count = startup_df[
        "customer_id"
    ].nunique()

    if customer_count == 0:
        return 0.0

    startup_revenue = startup_df[
        "revenue"
    ].sum()

    return startup_revenue / customer_count


# ============================================================
# KPI 6: ENTERPRISE REVENUE SHARE
# ============================================================

def calculate_enterprise_revenue_share(df):
    """
    Calculate Enterprise revenue as a share of total revenue.

    Formula:
        Enterprise Revenue / Total Revenue

    Returns:
        float:
            Enterprise revenue share as a decimal.
            Example: 0.75 = 75%
    """

    _validate_columns(
        df,
        [
            "customer_type",
            "revenue",
        ],
    )

    total_revenue = df[
        "revenue"
    ].sum()

    if total_revenue == 0:
        return 0.0

    enterprise_revenue = df.loc[
        df["customer_type"] == "Enterprise",
        "revenue",
    ].sum()

    return enterprise_revenue / total_revenue


# ============================================================
# FORMATTING HELPERS
# ============================================================

def format_currency(value):
    """
    Format a numeric value as currency.
    """

    return f"${value:,.2f}"


def format_percentage(value):
    """
    Format a decimal value as a percentage.

    Example:
        0.25 -> 25.0%
    """

    return f"{value:.1%}"


# ============================================================
# COMPUTE ALL KPIs
# ============================================================

def calculate_all_kpis(df):
    """
    Calculate all defined HirePulse KPIs.

    Returns:
        dict: KPI names mapped to numeric KPI values.
    """

    return {
        "average_revenue_per_customer":
            calculate_average_revenue_per_customer(df),

        "churn_rate":
            calculate_churn_rate(df),

        "enterprise_revenue_per_customer":
            calculate_enterprise_revenue_per_customer(df),

        "smb_revenue_per_customer":
            calculate_smb_revenue_per_customer(df),

        "startup_revenue_per_customer":
            calculate_startup_revenue_per_customer(df),

        "enterprise_revenue_share":
            calculate_enterprise_revenue_share(df),
    }


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("HIREPULSE KPI CALCULATIONS")
    print("=" * 70)

    print(f"\nDataset: {DATA_FILE}")

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    print(
        f"Rows: {len(df)}"
    )

    print(
        f"Unique customers: "
        f"{df['customer_id'].nunique()}"
    )

    # --------------------------------------------------------
    # Calculate KPIs
    # --------------------------------------------------------

    kpis = calculate_all_kpis(df)

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("KPI RESULTS")
    print("=" * 70)

    print(
        f"\nAverage Revenue per Customer: "
        f"{format_currency(kpis['average_revenue_per_customer'])}"
    )

    print(
        f"Customer Churn Rate: "
        f"{format_percentage(kpis['churn_rate'])}"
    )

    print(
        f"Enterprise Revenue per Customer: "
        f"{format_currency(kpis['enterprise_revenue_per_customer'])}"
    )

    print(
        f"SMB Revenue per Customer: "
        f"{format_currency(kpis['smb_revenue_per_customer'])}"
    )

    print(
        f"Startup Revenue per Customer: "
        f"{format_currency(kpis['startup_revenue_per_customer'])}"
    )

    print(
        f"Enterprise Revenue Share: "
        f"{format_percentage(kpis['enterprise_revenue_share'])}"
    )

    print("\n" + "=" * 70)
    print("KPI CALCULATION COMPLETE")
    print("=" * 70)