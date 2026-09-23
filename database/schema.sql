-- HirePulse SQL Views & Aggregation Layer assignment schema.
-- Engine: PostgreSQL
-- Purpose: provide a coherent customer/order model for the SQL data-layer objects.
-- The assignment's existing SQLite files did not contain matching customer and
-- order populations, so this isolated PostgreSQL database uses this documented
-- schema and realistic seed data.

DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL CHECK (segment IN ('Enterprise', 'SMB', 'Startup')),
    region TEXT NOT NULL,
    country TEXT NOT NULL,
    signup_date DATE NOT NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    order_amount NUMERIC(12, 2) NOT NULL CHECK (order_amount >= 0),
    order_status TEXT NOT NULL CHECK (order_status IN ('completed', 'cancelled', 'refunded'))
);

CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
CREATE INDEX idx_orders_date ON orders(order_date);

INSERT INTO customers
    (customer_id, customer_name, segment, region, country, signup_date, deleted_at)
VALUES
    ('C001', 'Avery Morgan', 'Enterprise', 'North America', 'United States', '2024-02-10', NULL),
    ('C002', 'Blake Chen', 'SMB', 'North America', 'Canada', '2024-04-18', NULL),
    ('C003', 'Casey Patel', 'Startup', 'Europe', 'United Kingdom', '2024-06-02', NULL),
    ('C004', 'Drew Williams', 'Enterprise', 'Europe', 'Germany', '2023-11-21', NULL),
    ('C005', 'Emery Garcia', 'SMB', 'Asia Pacific', 'Australia', '2025-01-12', NULL),
    ('C006', 'Finley Brown', 'Startup', 'North America', 'United States', '2025-03-09', NULL),
    ('C007', 'Gray Wilson', 'Enterprise', 'Asia Pacific', 'Singapore', '2024-08-30', NULL),
    ('C008', 'Harper Davis', 'SMB', 'Europe', 'France', '2025-02-14', NULL),
    ('C009', 'Indigo Martin', 'Startup', 'Latin America', 'Brazil', '2024-12-08', NULL),
    ('C010', 'Jordan Taylor', 'Enterprise', 'North America', 'United States', '2023-09-15', NULL),
    ('C011', 'Kendall Lee', 'SMB', 'Asia Pacific', 'Japan', '2025-04-20', NULL),
    ('C012', 'Logan Thompson', 'Startup', 'Europe', 'Netherlands', '2025-05-11', NULL),
    ('C013', 'Micah Anderson', 'Enterprise', 'North America', 'Mexico', '2024-10-01', NULL),
    ('C014', 'Nico Robinson', 'SMB', 'Europe', 'Spain', '2025-06-17', NULL),
    ('C015', 'Oakley Clark', 'Startup', 'North America', 'United States', '2024-07-07', '2026-01-31');

INSERT INTO orders
    (order_id, customer_id, order_date, order_amount, order_status)
VALUES
    ('O1001', 'C001', '2026-09-20', 1250.00, 'completed'),
    ('O1002', 'C001', '2026-09-01', 890.50, 'completed'),
    ('O1003', 'C001', '2026-08-12', 450.00, 'completed'),
    ('O1004', 'C002', '2026-09-18', 240.00, 'completed'),
    ('O1005', 'C002', '2026-08-28', 315.75, 'completed'),
    ('O1006', 'C003', '2026-08-10', 780.00, 'completed'),
    ('O1007', 'C003', '2026-07-20', 420.00, 'completed'),
    ('O1008', 'C004', '2026-09-22', 3100.00, 'completed'),
    ('O1009', 'C004', '2026-09-05', 2750.00, 'completed'),
    ('O1010', 'C004', '2026-08-15', 1800.00, 'completed'),
    ('O1011', 'C005', '2026-07-30', 195.00, 'completed'),
    ('O1012', 'C006', '2026-08-25', 510.25, 'completed'),
    ('O1013', 'C006', '2026-08-24', 225.00, 'completed'),
    ('O1014', 'C007', '2026-07-15', 4200.00, 'completed'),
    ('O1015', 'C008', '2026-09-05', 640.00, 'completed'),
    ('O1016', 'C008', '2026-08-30', 315.00, 'completed'),
    ('O1017', 'C009', '2026-08-01', 275.00, 'completed'),
    ('O1018', 'C010', '2026-09-10', 1980.00, 'completed'),
    ('O1019', 'C010', '2026-08-26', 875.00, 'completed'),
    ('O1020', 'C011', '2026-09-18', 455.00, 'completed'),
    ('O1021', 'C011', '2026-09-02', 390.00, 'completed'),
    ('O1022', 'C012', '2026-08-24', 520.00, 'completed'),
    ('O1023', 'C013', '2026-09-12', 2200.00, 'completed'),
    ('O1024', 'C013', '2026-08-20', 1450.00, 'completed'),
    ('O1025', 'C014', '2026-08-15', 330.00, 'completed'),
    ('O1026', 'C015', '2026-09-21', 999.00, 'completed'),
    ('O1027', 'C002', '2026-09-08', 100.00, 'cancelled'),
    ('O1028', 'C004', '2026-09-15', 500.00, 'refunded');