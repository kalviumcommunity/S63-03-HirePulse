import sqlite3
import pandas as pd

DB_PATH = "database/sql_joins.db"

customers = pd.read_csv("data/raw/customers_join_data.csv")
orders = pd.read_csv("data/raw/orders.csv")
features = pd.read_csv("data/raw/customer_features.csv")

conn = sqlite3.connect(DB_PATH)

customers.to_sql("customers", conn, if_exists="replace", index=False)
orders.to_sql("orders", conn, if_exists="replace", index=False)
features.to_sql("customer_features", conn, if_exists="replace", index=False)


def query(sql):
    return pd.read_sql_query(sql, conn)


customers_count = len(customers)
orders_count = len(orders)

raw_left = query("""
SELECT c.customer_id, o.order_id, o.order_amount
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
""")

grouped_left = query("""
SELECT
    c.customer_id,
    COUNT(DISTINCT o.order_id) AS order_count,
    COALESCE(SUM(o.order_amount), 0) AS total_spent
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id
""")

inner_join = query("""
SELECT c.customer_id, o.order_id, o.order_amount
FROM customers c
INNER JOIN orders o
    ON c.customer_id = o.customer_id
""")

full_join = query("""
SELECT c.customer_id, o.order_id, o.order_amount
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id

UNION ALL

SELECT c.customer_id, o.order_id, o.order_amount
FROM orders o
LEFT JOIN customers c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
""")

unmatched_customers = query("""
SELECT c.customer_id
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL
""")

orphaned_orders = query("""
SELECT o.order_id
FROM orders o
LEFT JOIN customers c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
""")

multi_table = query("""
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    o.order_id,
    o.order_amount,
    f.total_transactions,
    f.total_spent,
    f.days_since_last_purchase,
    f.purchase_count
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
LEFT JOIN customer_features f
    ON c.customer_id = f.customer_id
""")

feature_duplicates = int(
    features["customer_id"].duplicated().sum()
)

multiplication_factor = len(raw_left) / customers_count
customer_unmatched_pct = (
    len(unmatched_customers) / customers_count * 100
)
order_orphan_pct = len(orphaned_orders) / orders_count * 100

expected_raw_left = 6
expected_inner = 3
expected_full = 7
expected_grouped_left = 5

checks = {
    "Customer row count": customers_count == 5,
    "Order row count": orders_count == 4,
    "LEFT JOIN raw row count": len(raw_left) == expected_raw_left,
    "LEFT JOIN grouped row count": len(grouped_left) == expected_grouped_left,
    "INNER JOIN row count": len(inner_join) == expected_inner,
    "FULL OUTER JOIN row count": len(full_join) == expected_full,
    "Unmatched customer count": len(unmatched_customers) == 3,
    "Orphaned order count": len(orphaned_orders) == 1,
    "Customer feature keys unique": feature_duplicates == 0,
    "3-table join row count preserved": len(multi_table) == expected_raw_left,
}

report = []

report.append("SQL JOINS AND MULTI-TABLE ANALYSIS")
report.append("=" * 50)
report.append("")

report.append("SOURCE ROW COUNTS")
report.append(f"Customers: {customers_count}")
report.append(f"Orders: {orders_count}")
report.append(f"Customer features: {len(features)}")
report.append("")

report.append("TASK 1 - LEFT JOIN VALIDATION")
report.append(f"Raw LEFT JOIN rows: {len(raw_left)}")
report.append(f"Grouped customer rows: {len(grouped_left)}")
report.append(f"Multiplication factor: {multiplication_factor:.2f}x")
report.append(
    "Explanation: Customer C001 has two orders, so the raw LEFT JOIN "
    "produces two rows for C001. Customers without orders are still "
    "preserved with NULL order values."
)
report.append("")

report.append("TASK 2 - UNMATCHED KEYS")
report.append(
    f"Customers without orders: {len(unmatched_customers)} "
    f"({customer_unmatched_pct:.1f}%)"
)
report.append(
    f"Orders without matching customer: {len(orphaned_orders)} "
    f"({order_orphan_pct:.1f}%)"
)
report.append("")

report.append("TASK 3 - JOIN TYPE COMPARISON")
report.append(f"INNER JOIN rows: {len(inner_join)}")
report.append(f"LEFT JOIN rows: {len(raw_left)}")
report.append(f"FULL OUTER JOIN rows: {len(full_join)}")
report.append(
    "INNER JOIN keeps only matched customer-order pairs. "
    "LEFT JOIN preserves every customer. "
    "FULL OUTER JOIN preserves both matched records and the orphaned order."
)
report.append("")

report.append("TASK 4 - MULTI-TABLE JOIN")
report.append(f"3-table join rows: {len(multi_table)}")
report.append(
    f"Customer feature duplicate keys: {feature_duplicates}"
)
report.append(
    "The third table is customer_features because the repository does "
    "not contain order_items or products tables. It is joined on the "
    "unique customer_id key to enrich customer-order records without "
    "creating unexpected multiplication."
)
report.append("")

report.append("TASK 5 - VALIDATION CHECKS")
for name, passed in checks.items():
    report.append(f"{name}: {'PASS' if passed else 'FAIL'}")

report.append("")
report.append("JOIN DECISIONS")
report.append(
    "1. customers LEFT JOIN orders: preserves all customers for "
    "customer-level reporting."
)
report.append(
    "2. orders LEFT JOIN customers with IS NULL: identifies orphaned orders."
)
report.append(
    "3. customers LEFT JOIN customer_features: adds customer behavior "
    "metrics while preserving customer-order rows."
)
report.append(
    "4. INNER JOIN is used for matched customer-order analysis."
)
report.append(
    "5. SQLite FULL OUTER JOIN is emulated using LEFT JOIN + UNION ALL."
)

with open("output/sql_joins_validation.txt", "w", encoding="utf-8") as file:
    file.write("\n".join(report))

print("\n".join(report))

conn.close()
