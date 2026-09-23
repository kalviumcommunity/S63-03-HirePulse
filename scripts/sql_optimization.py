"""
Analytical SQL Query Optimisation Suite.

Executes and benchmarks three SQL query optimization tasks against SQLite/SQLAlchemy database:
Task 1: SELECT * -> Explicit Columns & Date Range Filtering
Task 2: Filter Before Join (CTE Early Filtering & Reduction Metrics)
Task 3: Nested Subqueries -> Modular CTE Refactoring

Generates performance benchmarks and outputs report to output/sql_optimization_report.txt.
"""

from datetime import datetime, date
import json
import logging
from pathlib import Path
import sqlite3
import sys
import time
import numpy as np
import pandas as pd

# Handle Windows terminal encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_DIR = PROJECT_ROOT / "database"
OUTPUT_DIR = PROJECT_ROOT / "output"

DATABASE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

DB_PATH = DATABASE_DIR / "optimization_demo.db"
REPORT_PATH = OUTPUT_DIR / "sql_optimization_report.txt"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ==============================================================================
# DATABASE SETUP & SEEDING (DEMO DATASET FOR VERIFICATION)
# ==============================================================================

def setup_demo_database(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create and seed SQLite demo database for query optimization benchmarks.

    Returns:
        sqlite3.Connection: Active connection object.
    """
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Create schema
        cur.executescript("""
            DROP TABLE IF EXISTS transactions;
            DROP TABLE IF EXISTS customers;
            DROP TABLE IF EXISTS products;

            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                country TEXT NOT NULL,
                account_type TEXT NOT NULL,
                customer_segment TEXT NOT NULL
            );

            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL
            );

            CREATE TABLE transactions (
                transaction_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                transaction_date TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE INDEX idx_trans_date ON transactions(transaction_date);
            CREATE INDEX idx_trans_cust ON transactions(customer_id);
            CREATE INDEX idx_trans_amount ON transactions(amount);
            CREATE INDEX idx_cust_country ON customers(country);
        """)

        # Generate realistic demo records (500 customers, 50 products, 10,000 transactions)
        np.random.seed(42)

        countries = ["USA", "Canada", "UK", "Germany", "Australia", "France"]
        account_types = ["Standard", "Premium", "Enterprise"]
        segments = ["Enterprise", "Mid-Market", "SMB", "Starter"]

        customers_data = [
            (i, f"Customer_{i}", np.random.choice(countries, p=[0.4, 0.15, 0.15, 0.1, 0.1, 0.1]),
             np.random.choice(account_types), np.random.choice(segments))
            for i in range(1, 501)
        ]
        cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers_data)

        products_data = [
            (i, f"Product_{i}", f"Category_{i % 5}", round(float(np.random.uniform(20, 500)), 2))
            for i in range(1, 51)
        ]
        cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products_data)

        start_date = date(2023, 1, 1)
        end_date = date(2024, 12, 31)
        date_range_days = (end_date - start_date).days

        transactions_data = []
        for i in range(1, 10001):
            random_days = np.random.randint(0, date_range_days)
            t_date = (start_date + pd.Timedelta(days=int(random_days))).strftime("%Y-%m-%d")
            cust_id = int(np.random.randint(1, 501))
            prod_id = int(np.random.randint(1, 51))
            amt = round(float(np.random.uniform(10, 500)), 2)
            transactions_data.append((i, cust_id, prod_id, t_date, amt))

        cur.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)", transactions_data)
        conn.commit()
        logger.info("Demo database successfully initialized with 500 customers, 50 products, and 10,000 transactions.")
        return conn

    except sqlite3.Error as e:
        logger.error(f"Database setup failed: {e}")
        raise


# ==============================================================================
# TASK 1 — SELECT * -> EXPLICIT COLUMNS
# ==============================================================================

"""
DOCSTRING: Why SELECT * is Inefficient and Explicit Columns are Preferable:
1. I/O and Memory Overhead: SELECT * retrieves all table attributes (including unneeded metadata or large text/BLOB columns), inflating network bandwidth, disk I/O, and RAM allocation in application memory.
2. Index-Only Scans (Covering Indexes): Explicit column selection allows the query optimizer to utilize covering indexes without fetching data pages from disk.
3. Schema Fragility: SELECT * makes application code vulnerable to upstream schema changes (e.g. column reordering, additions, or deletions).
4. Sargable Date Filtering: Using column functions like YEAR(transaction_date) forces full table scans. Using explicit date boundaries (e.g. transaction_date >= '2024-01-01' AND transaction_date < '2025-01-01') enables B-tree index range scans.
"""

def benchmark_task1(conn: sqlite3.Connection) -> dict:
    """Benchmark Task 1: SELECT * vs Explicit Columns."""

    # Note: SQLite uses strftime('%Y', transaction_date) for YEAR() function,
    # but range filtering >= '2024-01-01' AND < '2025-01-01' is sargable and index-friendly.
    original_query = """
    SELECT *
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    WHERE strftime('%Y', t.transaction_date) = '2024'
    LIMIT 1000;
    """

    optimized_query = """
    SELECT 
        t.transaction_id,
        t.transaction_date,
        t.amount,
        t.customer_id,
        c.customer_name,
        c.country,
        c.account_type
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    WHERE t.transaction_date >= '2024-01-01' 
      AND t.transaction_date < '2025-01-01'
    LIMIT 1000;
    """

    t0 = time.perf_counter()
    df_orig = pd.read_sql_query(original_query, conn)
    t_orig = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    df_opt = pd.read_sql_query(optimized_query, conn)
    t_opt = (time.perf_counter() - t0) * 1000

    metrics = {
        "original": {
            "cols_selected": len(df_orig.columns),
            "rows_returned": len(df_orig),
            "exec_time_ms": round(t_orig, 2),
            "col_list": list(df_orig.columns)
        },
        "optimized": {
            "cols_selected": len(df_opt.columns),
            "rows_returned": len(df_opt),
            "exec_time_ms": round(t_opt, 2),
            "col_list": list(df_opt.columns)
        },
        "column_reduction": f"{len(df_orig.columns)} -> {len(df_opt.columns)} ({len(df_orig.columns) - len(df_opt.columns)} columns dropped)"
    }
    return metrics, df_orig, df_opt


# ==============================================================================
# TASK 2 — FILTER BEFORE JOIN
# ==============================================================================

def benchmark_task2(conn: sqlite3.Connection) -> dict:
    """Benchmark Task 2: Filter Before Join vs Unfiltered Join."""

    original_query = """
    SELECT t.transaction_id, t.amount, c.customer_name, p.product_name
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    JOIN products p ON t.product_id = p.id
    WHERE t.transaction_date >= '2024-01-01'
      AND t.amount > 100
      AND c.country = 'USA'
    LIMIT 5000;
    """

    optimized_query = """
    WITH filtered_transactions AS (
        SELECT transaction_id, amount, customer_id, product_id
        FROM transactions
        WHERE transaction_date >= '2024-01-01'
          AND amount > 100
    )
    SELECT ft.transaction_id, ft.amount, c.customer_name, p.product_name
    FROM filtered_transactions ft
    JOIN customers c ON ft.customer_id = c.id
    JOIN products p ON ft.product_id = p.id
    WHERE c.country = 'USA'
    LIMIT 5000;
    """

    # Compute intermediate filtering counts for metrics
    total_trans = pd.read_sql_query("SELECT COUNT(*) as total FROM transactions", conn).iloc[0]["total"]
    filtered_trans = pd.read_sql_query(
        "SELECT COUNT(*) as filtered FROM transactions WHERE transaction_date >= '2024-01-01' AND amount > 100", conn
    ).iloc[0]["filtered"]

    t0 = time.perf_counter()
    df_orig = pd.read_sql_query(original_query, conn)
    t_orig = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    df_opt = pd.read_sql_query(optimized_query, conn)
    t_opt = (time.perf_counter() - t0) * 1000

    final_count = len(df_opt)
    rows_removed = total_trans - filtered_trans
    reduction_pct = round((rows_removed / total_trans) * 100, 2) if total_trans > 0 else 0
    reduction_factor = round(total_trans / filtered_trans, 2) if filtered_trans > 0 else 0

    metrics = {
        "total_transactions": int(total_trans),
        "transactions_after_filter": int(filtered_trans),
        "rows_removed": int(rows_removed),
        "reduction_percentage": reduction_pct,
        "reduction_factor": reduction_factor,
        "final_result_count": int(final_count),
        "orig_exec_time_ms": round(t_orig, 2),
        "opt_exec_time_ms": round(t_opt, 2),
        "logical_result_match": df_orig.equals(df_opt)
    }
    return metrics, df_orig, df_opt


# ==============================================================================
# TASK 3 — NESTED SUBQUERIES -> CTEs
# ==============================================================================

def benchmark_task3(conn: sqlite3.Connection) -> dict:
    """Benchmark Task 3: Nested Subqueries vs Modular CTEs."""

    # Note: The original query contains a subtle SQL bug -- its outer query performs
    # AVG(revenue_per_transaction) without a GROUP BY customer_segment, which collapses all
    # segment rows down to a single arbitrary row. The refactored CTE fixes this and returns all segments.
    original_query = """
    SELECT customer_segment, AVG(revenue_per_transaction) as avg_transaction_value
    FROM (
        SELECT 
            c.customer_segment,
            AVG(t.amount) as revenue_per_transaction,
            COUNT(DISTINCT t.transaction_id) as transaction_count
        FROM (
            SELECT t.transaction_id, t.amount, t.customer_id
            FROM transactions t
            WHERE t.transaction_date >= '2024-01-01'
        ) t
        JOIN customers c ON t.customer_id = c.id
        GROUP BY c.customer_segment
    ) grouped
    ORDER BY avg_transaction_value DESC;
    """

    refactored_query = """
    WITH recent_transactions AS (
        -- Step 1: Filter transactions to 2024 onwards
        SELECT 
            t.transaction_id, 
            t.amount, 
            t.customer_id
        FROM transactions t
        WHERE t.transaction_date >= '2024-01-01'
    ),
    customer_with_segment AS (
        -- Step 2: Associate filtered transactions with customer segments
        SELECT 
            rt.transaction_id,
            rt.amount,
            c.customer_segment
        FROM recent_transactions rt
        JOIN customers c ON rt.customer_id = c.id
    ),
    segment_metrics AS (
        -- Step 3: Compute aggregated metrics per customer segment
        SELECT 
            cws.customer_segment,
            AVG(cws.amount) AS revenue_per_transaction,
            COUNT(DISTINCT cws.transaction_id) AS transaction_count
        FROM customer_with_segment cws
        GROUP BY cws.customer_segment
    )
    -- Step 4: Final output ordering
    SELECT 
        sm.customer_segment,
        sm.revenue_per_transaction AS avg_transaction_value
    FROM segment_metrics sm
    ORDER BY avg_transaction_value DESC;
    """

    t0 = time.perf_counter()
    df_orig = pd.read_sql_query(original_query, conn)
    t_orig = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    df_ref = pd.read_sql_query(refactored_query, conn)
    t_ref = (time.perf_counter() - t0) * 1000

    # Test independence of CTE 1: recent_transactions
    df_cte1 = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM transactions WHERE transaction_date >= '2024-01-01'", conn
    )

    metrics = {
        "orig_exec_time_ms": round(t_orig, 2),
        "ref_exec_time_ms": round(t_ref, 2),
        "orig_nesting_depth": 3,
        "ref_nesting_depth": 1,
        "orig_row_count": len(df_orig),
        "ref_row_count": len(df_ref),
        "sql_bug_identified": "Original query lacked GROUP BY in outer AVG, collapsing 4 segment rows into 1.",
        "cte1_test_count": int(df_cte1.iloc[0]["count"])
    }
    return metrics, df_orig, df_ref



# ==============================================================================
# REPORT GENERATION
# ==============================================================================

def generate_report(m1: dict, m2: dict, m3: dict):
    """Write benchmark metrics and summary report to output/sql_optimization_report.txt."""
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("ANALYTICAL SQL QUERY OPTIMISATION BENCHMARK REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write("Database Engine: SQLite (Local Demo Dataset: 500 customers, 50 products, 10,000 transactions)\n")
        f.write("Note: Benchmarks reflect functional execution on demo SQLite instance.\n\n")

        f.write("TASK 1: SELECT * -> EXPLICIT COLUMNS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Original Selected Columns : {m1['original']['cols_selected']} {m1['original']['col_list']}\n")
        f.write(f"Optimized Selected Columns: {m1['optimized']['cols_selected']} {m1['optimized']['col_list']}\n")
        f.write(f"Column Reduction Summary  : {m1['column_reduction']}\n")
        f.write(f"Original Execution Time   : {m1['original']['exec_time_ms']} ms\n")
        f.write(f"Optimized Execution Time  : {m1['optimized']['exec_time_ms']} ms\n\n")

        f.write("TASK 2: FILTER BEFORE JOIN\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Transactions        : {m2['total_transactions']:,}\n")
        f.write(f"Transactions Post-Filter  : {m2['transactions_after_filter']:,}\n")
        f.write(f"Rows Removed Before Join  : {m2['rows_removed']:,}\n")
        f.write(f"Reduction Percentage      : {m2['reduction_percentage']}%\n")
        f.write(f"Reduction Factor          : {m2['reduction_factor']}x\n")
        f.write(f"Final Result Row Count    : {m2['final_result_count']:,}\n")
        f.write(f"Logical Match Verification: {'PASS' if m2['logical_result_match'] else 'FAIL'}\n\n")

        f.write("TASK 3: NESTED SUBQUERIES -> CTEs\n")
        f.write("-" * 80 + "\n")
        f.write(f"Original Nesting Depth    : {m3['orig_nesting_depth']} levels\n")
        f.write(f"Refactored Nesting Depth  : {m3['ref_nesting_depth']} level (Modular CTEs)\n")
        f.write(f"Original Row Count        : {m3['orig_row_count']} row (due to missing GROUP BY in outer AVG)\n")
        f.write(f"Refactored Row Count      : {m3['ref_row_count']} rows (all segments represented)\n")
        f.write(f"Original Execution Time   : {m3['orig_exec_time_ms']} ms\n")
        f.write(f"Refactored Execution Time : {m3['ref_exec_time_ms']} ms\n")
        f.write(f"Bug Analysis              : {m3['sql_bug_identified']}\n\n")
        f.write("=" * 80 + "\n")

    logger.info(f"Optimization report successfully saved to {REPORT_PATH}")


def main():
    print("\n" + "=" * 80)
    print("STARTING ANALYTICAL SQL QUERY OPTIMISATION SUITE")
    print("=" * 80)

    try:
        conn = setup_demo_database()
    except Exception as e:
        print(f"ERROR: Database connection / setup failed: {e}")
        sys.exit(1)

    try:
        print("\n[Task 1/3] Benchmarking SELECT * -> Explicit Columns...")
        m1, df1_orig, df1_opt = benchmark_task1(conn)
        print(f"  ✓ Columns reduced from {m1['original']['cols_selected']} to {m1['optimized']['cols_selected']}")

        print("\n[Task 2/3] Benchmarking Filter Before Join...")
        m2, df2_orig, df2_opt = benchmark_task2(conn)
        print(f"  ✓ Transaction rows reduced by {m2['reduction_percentage']}% ({m2['reduction_factor']}x reduction factor) before joining.")

        print("\n[Task 3/3] Benchmarking Nested Subqueries -> CTEs...")
        m3, df3_orig, df3_ref = benchmark_task3(conn)
        print(f"  ✓ Refactored 3-level nested subquery into modular CTEs (Fixed un-grouped outer AVG bug, returned {m3['ref_row_count']} segments).")

        generate_report(m1, m2, m3)

        print("\n" + "=" * 80)
        print("SQL QUERY OPTIMISATION BENCHMARK COMPLETE")
        print(f"Report generated: {REPORT_PATH}")
        print("=" * 80 + "\n")

    finally:
        conn.close()



if __name__ == "__main__":
    main()
