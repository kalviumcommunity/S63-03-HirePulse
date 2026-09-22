# SQL Joins & Multi-Table Analysis

## Data Sources

This analysis uses:

- `customers_join_data.csv` - customer master data
- `orders.csv` - customer order data
- `customer_features.csv` - customer behavioral features

The repository does not contain `order_items.csv` or `products.csv`. Therefore, `customer_features` is used as the third table without inventing unavailable data.

## 1. LEFT JOIN and Row Count Validation

The customer-to-order relationship is one-to-many.

- Customers: 5
- Orders: 4
- Raw LEFT JOIN rows: 6
- Grouped customer rows: 5
- Multiplication factor: 1.20x

The raw result is larger because customer `C001` has two orders. Customers without orders are still preserved by the LEFT JOIN.

## 2. Unmatched Keys

- Customers without orders: 3 of 5 (60.0%)
- Orders without a matching customer: 1 of 4 (25.0%)

The orphaned order is detected using a LEFT JOIN from orders to customers and filtering for a NULL customer key.

## 3. INNER, LEFT, and FULL OUTER JOIN

### INNER JOIN

Returns 3 rows and keeps only matched customer-order pairs.

### LEFT JOIN

Returns 6 rows and preserves all customers, including customers without orders.

### FULL OUTER JOIN

Returns 7 rows and preserves unmatched records from both sides.

SQLite does not support native FULL OUTER JOIN, so it is emulated using LEFT JOIN and UNION ALL.

## 4. Multi-Table Join

The three-table relationship is:

`customers -> orders -> customer_features`

The join uses `customer_id` as the relationship key.

The result contains 6 rows, matching the raw customer-order LEFT JOIN.

The `customer_features.customer_id` key has no duplicates, so the third-table join does not introduce unexpected multiplication.

## 5. Data Lineage

- Customer attributes come from `customers`.
- Order details come from `orders`.
- Behavioral metrics come from `customer_features`.
- `customer_id` connects the three datasets.

## 6. Business Use Case

The combined data supports customer-order reporting using customer identity, location, order information, transaction history, purchase frequency, and recency metrics.

The unmatched-key analysis can also identify data-quality issues such as customers without orders and orders referencing missing customers.

## 7. Validation Results

All automated validation checks passed.

