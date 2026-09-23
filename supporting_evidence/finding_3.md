# Finding

Higher support-ticket counts are associated with the churn label in the
available customer sample.

## Supporting Evidence

- Dataset: `data/raw/customer_correlation_data.csv`
- Existing report: `output/pearson_correlation_matrix.csv`
- Metric: Pearson correlation between `support_tickets` and `churn`
- Correlation: 0.8660254037844383
- Non-churned records: 70 customers, average 4.0 tickets, range 1–7
- Churned records: 80 customers, average 11.5 tickets, range 8–15
- Comparison: every churned row in this dataset has at least 8 tickets, while
  every non-churned row has 7 or fewer.

## Why This Evidence Matters

Ticket volume can be used as a practical review signal. However, the dataset has
no ticket timestamps, issue categories, response times, or intervention results.

## Business Meaning

Support and Customer Success should investigate high-ticket accounts early, but
should not interpret this relationship as proof that tickets cause churn.