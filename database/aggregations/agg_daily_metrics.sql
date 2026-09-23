-- Object: agg_daily_metrics
-- Purpose: persist daily completed-revenue metrics for fast dashboard reads.
-- Grain: one row per aggregation_date and metric_name.
-- Refresh purpose: rerunning this definition refreshes the physical aggregate
--                  from the current completed orders without fabricating values.
-- Output columns:
--   aggregation_date date represented by the metric
--   metric_name      stable metric identifier
--   metric_value     aggregated completed revenue
--   row_count        number of completed orders contributing to the metric
--   updated_at       timestamp of the refresh

CREATE TABLE IF NOT EXISTS agg_daily_metrics (
    aggregation_date DATE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(14, 2) NOT NULL,
    row_count BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (aggregation_date, metric_name)
);

TRUNCATE TABLE agg_daily_metrics;

INSERT INTO agg_daily_metrics
    (aggregation_date, metric_name, metric_value, row_count, updated_at)
SELECT
    o.order_date AS aggregation_date,
    'daily_completed_revenue' AS metric_name,
    SUM(o.order_amount)::NUMERIC(14, 2) AS metric_value,
    COUNT(*) AS row_count,
    CURRENT_TIMESTAMP AS updated_at
FROM orders AS o
WHERE o.order_status = 'completed'
  AND o.order_date <= CURRENT_DATE
GROUP BY o.order_date;