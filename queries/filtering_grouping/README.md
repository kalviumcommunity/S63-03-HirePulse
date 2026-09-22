# SQL Filtering, Grouping & Aggregation

## WHERE vs HAVING

### WHERE

WHERE filters individual rows before aggregation.

Use it for date ranges, positive transaction amounts, data-quality rules, and removing invalid records.

Example:

WHERE transaction_date >= '2025-01-01'
AND amount > 0

### GROUP BY

GROUP BY defines the unit at which aggregate metrics are calculated.

Example:

GROUP BY strftime('%Y-%m-01', transaction_date)

This produces one result per month.

### HAVING

HAVING filters groups after aggregation.

Use it for revenue thresholds, minimum transaction counts, minimum customer counts, and other business rules applied to aggregate values.

Example:

HAVING SUM(amount) > 1000

### WHERE + HAVING

The two clauses can be combined:

WHERE amount > 0
GROUP BY customer_id
HAVING SUM(amount) > 1000

The execution pattern is:

1. WHERE filters rows
2. GROUP BY creates groups
3. Aggregate functions calculate metrics
4. HAVING filters groups
5. ORDER BY sorts the result

## Data Limitation

The available transactions.csv contains customer_id, transaction_date, and amount.

It does not contain transaction_status, customer_type, or industry. Therefore, those fields are not fabricated in these queries.

The transaction dataset contains four customer IDs (101-104), while the other customer datasets use different ID formats. The filtering and aggregation queries therefore operate on the transaction dataset independently.
