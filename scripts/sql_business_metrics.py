from pathlib import Path
import sqlite3
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

QUERY_DIR = ROOT / "queries"
DATABASE_DIR = ROOT / "database"
OUTPUT_DIR = ROOT / "output"

DATABASE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "business_metrics.db"
REPORT_PATH = OUTPUT_DIR / "sql_business_metrics_validation.txt"


def create_database():
    """Create a SQLite database and load the real source datasets."""
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    conn = sqlite3.connect(DATABASE_PATH)

    transactions = pd.read_csv(
        ROOT / "data" / "raw" / "transactions.csv"
    )

    customers = pd.read_csv(
        ROOT / "data" / "raw" / "customers.csv"
    )

    customer_segments = pd.read_csv(
        ROOT / "data" / "raw" / "customer_segment_data.csv"
    )

    transactions.to_sql(
        "transactions",
        conn,
        if_exists="replace",
        index=False
    )

    customers.to_sql(
        "customers",
        conn,
        if_exists="replace",
        index=False
    )

    customer_segments.to_sql(
        "customer_segments",
        conn,
        if_exists="replace",
        index=False
    )

    return conn


def load_query(query_name):
    """Load a reusable SQL query from the queries directory."""
    query_path = QUERY_DIR / f"{query_name}.sql"

    if not query_path.exists():
        raise FileNotFoundError(
            f"SQL query not found: {query_path}"
        )

    return query_path.read_text(encoding="utf-8")


def execute_metrics(conn):
    """Load and execute all business metric SQL queries."""

    mau_query = load_query("monthly_active_users")
    mau = pd.read_sql_query(mau_query, conn)

    revenue_query = load_query("revenue_by_segment")
    revenue = pd.read_sql_query(revenue_query, conn)

    funnel_query = load_query("conversion_funnel")
    funnel = pd.read_sql_query(funnel_query, conn)

    return mau, revenue, funnel


def validate_metrics(mau_df, revenue_df, funnel_df):
    """Validate metric outputs."""

    validation_results = []

    # MAU null validation
    mau_nulls = int(mau_df.isnull().sum().sum())
    validation_results.append(
        f"MAU null check: {'PASS' if mau_nulls == 0 else 'FAIL'} "
        f"(nulls={mau_nulls})"
    )

    # Revenue null validation
    revenue_nulls = int(revenue_df.isnull().sum().sum())
    validation_results.append(
        f"Revenue null check: "
        f"{'PASS' if revenue_nulls == 0 else 'FAIL'} "
        f"(nulls={revenue_nulls})"
    )

    # Revenue positive validation
    positive_revenue = (
        not revenue_df.empty
        and (revenue_df["total_revenue"] > 0).all()
    )

    validation_results.append(
        f"Revenue positive check: "
        f"{'PASS' if positive_revenue else 'FAIL'}"
    )

    # Funnel conversion range
    if funnel_df.empty:
        conversion_range_valid = True
    else:
        conversion_range_valid = (
            funnel_df["conversion_pct"].dropna().between(0, 100).all()
        )

    validation_results.append(
        f"Conversion range check: "
        f"{'PASS' if conversion_range_valid else 'FAIL'}"
    )

    # Revenue customer count
    customer_count_valid = (
        not revenue_df.empty
        and (revenue_df["customer_count"] > 0).all()
    )

    validation_results.append(
        f"Revenue customer-count check: "
        f"{'PASS' if customer_count_valid else 'FAIL'}"
    )

    all_passed = all("PASS" in result for result in validation_results)

    return validation_results, all_passed


def write_report(
    mau_df,
    revenue_df,
    funnel_df,
    validation_results,
    all_passed
):
    """Write metric results and validation details to a report."""

    with open(REPORT_PATH, "w", encoding="utf-8") as report:

        report.write("SQL BUSINESS METRICS VALIDATION REPORT\n")
        report.write("=" * 60 + "\n\n")

        report.write("DATABASE\n")
        report.write("-" * 60 + "\n")
        report.write(f"Database: {DATABASE_PATH}\n")
        report.write("Engine: SQLite\n\n")

        report.write("SOURCE DATA\n")
        report.write("-" * 60 + "\n")
        report.write(
            "transactions.csv -> transactions table\n"
        )
        report.write(
            "customers.csv -> customers table\n"
        )
        report.write(
            "customer_segment_data.csv -> customer_segments table\n\n"
        )

        report.write("IMPORTANT DATA LIMITATION\n")
        report.write("-" * 60 + "\n")
        report.write(
            "The transaction dataset uses customer IDs 101-104, "
            "while customers.csv uses IDs 1-3 and "
            "customer_segment_data.csv uses IDs C0001-C0150.\n"
        )
        report.write(
            "Therefore, these datasets are not assumed to represent "
            "the same customer population.\n"
        )
        report.write(
            "The revenue-by-segment metric uses customer_segments "
            "directly, while MAU uses transactions directly.\n"
        )
        report.write(
            "The conversion funnel uses only exact customer_id matches.\n\n"
        )

        report.write("1. MONTHLY ACTIVE USERS\n")
        report.write("-" * 60 + "\n")
        report.write(
            mau_df.to_string(index=False)
            if not mau_df.empty
            else "No MAU rows returned."
        )
        report.write("\n\n")

        report.write("2. REVENUE BY SEGMENT\n")
        report.write("-" * 60 + "\n")
        report.write(
            revenue_df.to_string(index=False)
            if not revenue_df.empty
            else "No revenue rows returned."
        )
        report.write("\n\n")

        report.write("3. CONVERSION FUNNEL\n")
        report.write("-" * 60 + "\n")
        report.write(
            funnel_df.to_string(index=False)
            if not funnel_df.empty
            else "No funnel rows returned."
        )
        report.write("\n\n")

        report.write("VALIDATION RESULTS\n")
        report.write("-" * 60 + "\n")

        for result in validation_results:
            report.write(result + "\n")

        report.write("\n")
        report.write(
            f"OVERALL VALIDATION: "
            f"{'PASS' if all_passed else 'FAIL'}\n"
        )


def main():
    print("Starting SQL Business Metrics workflow...")

    conn = create_database()

    try:
        print("\nDatabase tables loaded.")

        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """,
            conn
        )

        print("\nTables:")
        print(tables)

        mau, revenue, funnel = execute_metrics(conn)

        print("\nMonthly Active Users:")
        print(mau)

        print("\nRevenue by Segment:")
        print(revenue)

        print("\nConversion Funnel:")
        print(funnel)

        validation_results, all_passed = validate_metrics(
            mau,
            revenue,
            funnel
        )

        print("\nValidation:")
        for result in validation_results:
            print(result)

        print(
            f"\nOverall validation: "
            f"{'PASS' if all_passed else 'FAIL'}"
        )

        write_report(
            mau,
            revenue,
            funnel,
            validation_results,
            all_passed
        )

        print(
            f"\nReport written to: {REPORT_PATH}"
        )

        print("\nSQL BUSINESS METRICS COMPLETE")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
