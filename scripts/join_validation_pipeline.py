import json
import logging
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CUSTOMERS_PATH = PROJECT_ROOT / "data" / "raw" / "customers_join_data.csv"
ORDERS_PATH = PROJECT_ROOT / "data" / "raw" / "orders.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
MERGED_PATH = OUTPUT_DIR / "merged_customers_orders.csv"
UNMATCHED_CUSTOMERS_PATH = OUTPUT_DIR / "unmatched_customers.csv"
UNMATCHED_ORDERS_PATH = OUTPUT_DIR / "unmatched_orders.csv"
REPORT_PATH = OUTPUT_DIR / "join_report.json"

LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def load_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(CUSTOMERS_PATH)
    orders = pd.read_csv(ORDERS_PATH)
    return customers, orders


def validate_source_columns(customers: pd.DataFrame, orders: pd.DataFrame) -> None:
    expected_customer_columns = {"customer_id", "customer_name", "city"}
    expected_order_columns = {"order_id", "customer_id", "order_amount"}
    assert expected_customer_columns.issubset(customers.columns)
    assert expected_order_columns.issubset(orders.columns)


def create_outputs(customers: pd.DataFrame, orders: pd.DataFrame) -> dict[str, int | str]:
    left_rows = len(customers)
    right_rows = len(orders)
    LOGGER.info("Left table row count: %s", left_rows)
    LOGGER.info("Right table row count: %s", right_rows)

    merged = customers.merge(orders, on="customer_id", how="left", validate="one_to_many")
    merged_rows = len(merged)
    LOGGER.info("Merged row count: %s", merged_rows)
    LOGGER.info("Row count change: %s", merged_rows - left_rows)

    order_customer_ids = set(orders["customer_id"])
    customer_ids = set(customers["customer_id"])
    unmatched_customers = customers.loc[~customers["customer_id"].isin(order_customer_ids)]
    unmatched_orders = orders.loc[~orders["customer_id"].isin(customer_ids)]
    unmatched_customers.to_csv(UNMATCHED_CUSTOMERS_PATH, index=False)
    unmatched_orders.to_csv(UNMATCHED_ORDERS_PATH, index=False)
    LOGGER.info("Unmatched customers: %s", len(unmatched_customers))
    LOGGER.info("Orphaned orders: %s", len(unmatched_orders))

    inner_join = customers.merge(orders, on="customer_id", how="inner")
    left_join = customers.merge(orders, on="customer_id", how="left")
    outer_join = customers.merge(orders, on="customer_id", how="outer")
    LOGGER.info("Inner join row count: %s", len(inner_join))
    LOGGER.info("Left join row count: %s", len(left_join))
    LOGGER.info("Outer join row count: %s", len(outer_join))

    LOGGER.info("Merged column names: %s", list(merged.columns))
    customer_order_counts = merged["customer_id"].value_counts()
    max_orders_per_customer = int(customer_order_counts.max())
    LOGGER.info("Max orders per customer: %s", max_orders_per_customer)

    merged.to_csv(MERGED_PATH, index=False)
    report = {
        "join_type": "left",
        "left_table": "customers",
        "right_table": "orders",
        "join_key": "customer_id",
        "left_rows": left_rows,
        "right_rows": right_rows,
        "result_rows": merged_rows,
        "unmatched_left": len(unmatched_customers),
        "unmatched_right": len(unmatched_orders),
        "reasoning": "Left join preserves all customers; unmatched customers have no orders",
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def validate_outputs(report: dict[str, int | str]) -> None:
    assert MERGED_PATH.exists()
    assert UNMATCHED_CUSTOMERS_PATH.exists()
    assert UNMATCHED_ORDERS_PATH.exists()
    assert REPORT_PATH.exists()
    assert report["result_rows"] == len(pd.read_csv(MERGED_PATH))


def main() -> None:
    configure_logging()
    customers, orders = load_sources()
    validate_source_columns(customers, orders)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = create_outputs(customers, orders)
    validate_outputs(report)
    print("Multi-Source Merging & Join Validation Pipeline completed successfully.")


if __name__ == "__main__":
    main()