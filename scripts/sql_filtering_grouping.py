from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
QUERY_DIR = ROOT / "queries" / "filtering_grouping"
DATABASE_PATH = ROOT / "database" / "filtering_grouping.db"
REPORT_PATH = ROOT / "output" / "sql_filtering_grouping_validation.txt"


def load_query(name):
    path = QUERY_DIR / f"{name}.sql"
    return path.read_text(encoding="utf-8")


def main():
    transactions = pd.read_csv(
        ROOT / "data" / "raw" / "transactions.csv"
    )

    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    conn = sqlite3.connect(DATABASE_PATH)

    try:
        transactions.to_sql(
            "transactions",
            conn,
            if_exists="replace",
            index=False
        )

        query_names = [
            "where_filtering",
            "group_by_aggregation",
            "having_filtering",
            "where_having_combined",
            "ranking"
        ]

        results = {}

        for name in query_names:
            print()
            print("=" * 60)
            print(name)
            print("=" * 60)

            query = load_query(name)
            df = pd.read_sql_query(query, conn)
            results[name] = df
            print(df.to_string(index=False))

        validations = []

        where_df = results["where_filtering"]
        group_df = results["group_by_aggregation"]
        having_df = results["having_filtering"]
        combined_df = results["where_having_combined"]
        ranking_df = results["ranking"]

        check = (
            not where_df.empty
            and (where_df["total_revenue"] > 0).all()
        )
        validations.append(
            f"Task 1 WHERE check: {'PASS' if check else 'FAIL'}"
        )

        check = (
            not group_df.empty
            and (group_df["transaction_count"] > 0).all()
            and (group_df["monthly_revenue"] > 0).all()
        )
        validations.append(
            f"Task 2 GROUP BY check: {'PASS' if check else 'FAIL'}"
        )

        check = (
            not having_df.empty
            and (having_df["total_revenue"] > 1000).all()
        )
        validations.append(
            f"Task 3 HAVING check: {'PASS' if check else 'FAIL'}"
        )

        check = (
            not combined_df.empty
            and (combined_df["total_revenue"] > 1000).all()
        )
        validations.append(
            f"Task 4 WHERE + HAVING check: {'PASS' if check else 'FAIL'}"
        )

        check = (
            not ranking_df.empty
            and ranking_df["revenue_rank"].notna().all()
            and ranking_df["revenue_rank"].min() >= 1
            and len(ranking_df) <= 20
        )
        validations.append(
            f"Task 5 RANK check: {'PASS' if check else 'FAIL'}"
        )

        print()
        print("VALIDATION RESULTS")
        print("=" * 60)

        for item in validations:
            print(item)

        overall = all(
            "PASS" in item for item in validations
        )

        print()
        print(
            f"Overall validation: "
            f"{'PASS' if overall else 'FAIL'}"
        )

        with open(
            REPORT_PATH,
            "w",
            encoding="utf-8"
        ) as report:

            report.write(
                "SQL FILTERING, GROUPING & AGGREGATION REPORT\n"
            )
            report.write("=" * 60 + "\n\n")

            report.write(
                "Source: data/raw/transactions.csv\n"
            )
            report.write(
                "Database: SQLite\n\n"
            )

            report.write(
                "Data limitation: transactions.csv contains "
                "only customer_id, transaction_date, and amount.\n"
            )
            report.write(
                "Fields such as transaction_status, customer_type, "
                "and industry are not available and were not fabricated.\n\n"
            )

            for name, df in results.items():
                report.write(name.upper() + "\n")
                report.write("-" * 60 + "\n")
                report.write(
                    df.to_string(index=False) + "\n\n"
                )

            report.write("VALIDATION RESULTS\n")
            report.write("-" * 60 + "\n")

            for item in validations:
                report.write(item + "\n")

            report.write("\n")
            report.write(
                f"OVERALL VALIDATION: "
                f"{'PASS' if overall else 'FAIL'}\n"
            )

        print()
        print(
            f"Report written to: {REPORT_PATH}"
        )
        print("SQL FILTERING GROUPING COMPLETE")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
