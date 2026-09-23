# Analytical SQL Query Optimisation & Performance Benchmark Report

## 1. Executive Summary
This document provides a comprehensive analysis and technical refactoring report for three analytical SQL queries. The optimizations address common performance bottlenecks, including over-fetching attributes (`SELECT *`), delayed filtering across expensive joins, deep query nesting, non-sargable functions, and un-grouped aggregate logic.

All benchmarks were executed against an initialized SQLite database (`database/optimization_demo.db`) containing **10,000 transactions**, **500 customers**, and **50 products** via [scripts/sql_optimization.py](file:///d:/S63-03-HirePulse/scripts/sql_optimization.py).

---

## 2. Query 1: `SELECT *` → Explicit Columns & Date Range Filtering

### Original Query
```sql
SELECT *
FROM transactions t
JOIN customers c ON t.customer_id = c.id
WHERE YEAR(t.transaction_date) = 2024
LIMIT 1000;
```

### Optimized Query
```sql
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
```

### Problem Identified
1. **Unnecessary Column Transport (`SELECT *`)**: Fetches all 10 attributes across both joined tables, including duplicated key columns (`t.customer_id` and `c.id`), leading to excessive memory allocation and higher network I/O payload.
2. **Non-Sargable Predicate (`YEAR(...)`)**: Wrapping `transaction_date` in a scalar function forces a **Full Table Scan**, preventing the database optimizer from utilizing B-tree range indexes on `transaction_date`.

### Optimization Applied
1. **Explicit Attribute Selection**: Restricted projection to exactly 7 required business attributes.
2. **Sargable Date Range Filter**: Rewritten as `t.transaction_date >= '2024-01-01' AND t.transaction_date < '2025-01-01'`, enabling index range scans on `idx_trans_date`.

### Performance Results
* **Columns Selected**: `10` $\rightarrow$ `7` (**30.0% attribute reduction**)
* **Execution Time (Demo SQLite)**: `4.93 ms` $\rightarrow$ `3.72 ms` (**~24.5% speedup**)
* **Columns Dropped**: `product_id`, `c.id`, `customer_segment` (unneeded for transaction-customer audit view).

### Business Relevance of Selected Columns
* `transaction_id`: Unique identifier for auditability and transaction tracking.
* `transaction_date`: Temporal context for cohort and trend modeling.
* `amount`: Financial value of transaction.
* `customer_id`: Primary relational key linking entity.
* `customer_name`: Entity identification for customer communication.
* `country`: Geographic segmentation metric.
* `account_type`: Customer tier classification (`Standard`, `Premium`, `Enterprise`).

### Technical Explanation: Why `SELECT *` is Inefficient
> [!IMPORTANT]
> `SELECT *` increases disk I/O, network latency, and memory consumption by transporting unneeded data bytes. It prevents database query engines from leveraging **Index-Only Scans** (where queries are satisfied entirely from index pages without accessing table heap pages). Furthermore, `SELECT *` creates schema fragility in data pipelines—adding or reordering columns in source tables can break downstream application code or schema mappings.

---

## 3. Query 2: Filter Before Join (Early Filtering via CTE)

### Original Query
```sql
SELECT t.transaction_id, t.amount, c.customer_name, p.product_name
FROM transactions t
JOIN customers c ON t.customer_id = c.id
JOIN products p ON t.product_id = p.id
WHERE t.transaction_date >= '2024-01-01'
  AND t.amount > 100
  AND c.country = 'USA'
LIMIT 5000;
```

### Optimized Query (Filter-First CTE)
```sql
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
```

### Problem Identified & Optimization Applied
In naive join execution, tables are joined before predicates are applied, forcing the engine to construct large intermediate join trees in memory. By wrapping `transactions` in an early-filtering CTE (`filtered_transactions`), candidate rows are filtered before performing hash/nested loop joins against `customers` and `products`.

### Measured Filtering Impact (Demo Dataset)
* **Total Transactions in Table**: `10,000`
* **Transactions Remaining Post-Filter (`>= 2024-01-01` & `amount > 100`)**: `4,131`
* **Rows Filtered Out Before Joins**: `5,869`
* **Reduction Percentage**: **58.69%**
* **Reduction Factor**: **2.42x**
* **Final Result Row Count (After `country = 'USA'`)**: `1,661`
* **Logical Result Match**: **PASS** (100% data equivalence verified)

### Optimizer Execution Behavior Note
> [!NOTE]
> Modern Cost-Based Optimizers (CBOs) in production relational engines (such as PostgreSQL, Oracle, and MySQL 8.0+) automatically perform **Predicate Pushdown**, attempting to push WHERE filters down below joins even in implicit join queries. However, writing explicit filter-first CTEs guarantees early data reduction in simpler database engines (e.g., embedded SQLite), enforces logical clarity for code maintainability, and prevents optimizer edge cases during multi-table joins.

---

## 4. Query 3: Nested Subqueries → Modular CTE Refactoring

### Original Query (3-Level Deep Nesting)
```sql
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
```

### Refactored Query (Step-by-Step Modular CTEs)
```sql
WITH recent_transactions AS (
    -- Step 1: Filter transactions to 2024 onwards and select required attributes
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
-- Step 4: Final output selection and ordering
SELECT 
    sm.customer_segment,
    ROUND(sm.revenue_per_transaction, 2) AS avg_transaction_value
FROM segment_metrics sm
ORDER BY avg_transaction_value DESC;
```

### Explanation of CTE Modules
1. `recent_transactions`: Isolates temporal filtering (`>= 2024-01-01`) and projects only relevant attributes (`transaction_id`, `amount`, `customer_id`).
2. `customer_with_segment`: Joins filtered transactions with `customers` to map segment metadata (`customer_segment`).
3. `segment_metrics`: Aggregates transaction counts and mean revenue per segment.
4. Final `SELECT`: Projects formatted output sorted by `avg_transaction_value DESC`.

### Critical Analysis: Original Query Bug & Corrected Result
> [!WARNING]
> **Identified Design Flaw in Original Query**: The outer query of the original statement contained an un-grouped aggregate function: `SELECT customer_segment, AVG(revenue_per_transaction) ... FROM ( ... GROUP BY c.customer_segment ) grouped`.
> Because the outer query lacked a `GROUP BY customer_segment` clause, standard SQL engines collapse all 4 segment summary rows into **1 single row**, picking an arbitrary `customer_segment` label (`Enterprise`) and computing the average of averages.
>
> The CTE refactoring corrects this logical oversight by cleanly grouping segment metrics in `segment_metrics`, returning all 4 distinct segments (**SMB**: `$260.99`, **Starter**: `$258.67`, **Enterprise**: `$253.68`, **Mid-Market**: `$251.50`).

### Readability & Testability Improvements
* **Nesting Depth**: Reduced from 3 nested subquery levels to 1 top-level `WITH` block.
* **Independent Testability**: Each CTE can be individually queried and verified (e.g., testing `recent_transactions` independently returning `4,980` rows).

---

## 5. Summary Comparison Matrix

| Metric / Dimension | Task 1: Column Selection | Task 2: Join Filtering | Task 3: Structure & Refactoring |
| :--- | :--- | :--- | :--- |
| **Optimization Focus** | Eliminating `SELECT *` & Sargable Dates | Early Filtering via CTE | Modular CTEs vs Nested Subqueries |
| **Columns Selected** | `10` $\rightarrow$ `7` (**30% reduction**) | `4` explicit attributes | `2` final output columns |
| **Intermediate Rows Processed**| `10,000` rows | `10,000` $\rightarrow$ `4,131` (**58.69% reduction**) | `10,000` $\rightarrow$ `4,980` transactions |
| **Nesting Depth** | 0 (Flat) | 1 (Single CTE) | 3 Levels $\rightarrow$ 1 Level (Modular CTEs) |
| **Execution Time (SQLite)** | `4.93 ms` $\rightarrow$ `3.72 ms` | `4.80 ms` $\rightarrow$ `4.15 ms` | `3.95 ms` $\rightarrow$ `4.13 ms` |
| **Readability Score** | High | High | High (Fixed 1-row aggregate bug to 4 rows) |

---

## 6. Applied SQL Best Practices

1. **Avoid `SELECT *`**: Always specify explicit required columns to optimize I/O and memory payload.
2. **Sargable Predicates**: Avoid wrapping index columns in scalar functions (e.g., use `date >= '2024-01-01'` instead of `YEAR(date) = 2024`).
3. **Early Filtering**: Filter records prior to joins to reduce intermediate hash table sizes and comparison loops.
4. **Modular CTE Structure**: Use top-level Common Table Expressions to replace deeply nested subqueries.
5. **Empirical Benchmarking**: Measure execution times and row/column metrics rather than assuming performance behavior.

---

## 7. Task 5: Follow-Up Questions & Technical Deep-Dive

### Question 1: How Does an Index on a High-Cardinality Column Improve Performance?
* **Index Lookup vs. Table Scan**: A High-Cardinality column (e.g., `customer_id` or `transaction_id` with millions of unique values) allows a **B-tree index** to traverse root, branch, and leaf nodes in $O(\log N)$ search time. Instead of scanning millions of table rows (**Full Table Scan**), the engine performs a **Point Lookup** or narrow **Index Range Scan**, jumping directly to target record pointer locations.
* **Trade-offs & Overhead**:
  1. **Storage Footprint**: Indexes occupy additional disk space and buffer pool RAM.
  2. **Write Amplification (DML Overhead)**: Every `INSERT`, `UPDATE`, or `DELETE` operation must update both the table data pages and all associated B-tree indexes, slowing down write throughput.
  3. **Index Maintenance**: Fragmented B-tree indexes require periodic re-indexing (`REINDEX` or `ALTER INDEX REBUILD`).

### Question 2: Do CTEs Always Get Cached or Materialized?
* **Database & Optimizer Dependent Behavior**:
  * **PostgreSQL (v12+)**: Non-recursive, side-effect-free CTEs referenced only once are **inlined** by default into the main query tree (allowing predicate pushdown across CTE boundaries). PostgreSQL materializes CTEs only if they are referenced multiple times or explicitly marked with `AS MATERIALIZED`. Prior to v12, all CTEs acted as optimization fences (always materialized).
  * **SQLite**: Inlines simple CTEs as subqueries; materializes recursive CTEs or CTEs referenced multiple times in temporary tables.
  * **MySQL (8.0+) & SQL Server**: Treat non-recursive CTEs as derived tables and inline them into the query optimizer graph.

### Question 3: Additional Optimization Techniques for 100-Million Row Datasets
When dataset size reaches 100M+ rows, SQL query tuning must be complemented by system architecture optimizations:
1. **Table Partitioning**: Range/List partition tables by `transaction_date` (e.g., monthly or yearly partitions). Queries automatically perform **Partition Pruning**, skipping un-targeted physical data files.
2. **Columnar Storage Formats**: Use columnar storage engines (e.g., DuckDB, ClickHouse, Apache Parquet, Snowflake, BigQuery) instead of row-oriented storage. Columnar engines read only the requested attributes from disk, achieving 10x-100x speedups on analytical aggregations.
3. **Materialized Views & Summary Tables**: Pre-aggregate metrics (e.g., daily segment totals) asynchronously via materialized views (`CREATE MATERIALIZED VIEW`) refreshed on a schedule.
4. **Parallel Query Execution & Hash Joins**: Configure multi-threaded parallel scans and hash joins across distributed worker nodes.
5. **Query & Result Caching**: Cache query result sets in Redis or database query caches for frequent read-only dashboards.
