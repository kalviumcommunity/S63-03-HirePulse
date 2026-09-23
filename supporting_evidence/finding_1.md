# Finding

Customer type is the clearest observed churn-prioritization signal.

## Supporting Evidence

- Chart/report: `output/segment_summary.csv`
- Dataset: `data/raw/customer_segment_data.csv`
- Metric: churned customers divided by customers in each `customer_type`
- Enterprise: 2 of 50 churned, 4.00%
- SMB: 9 of 50 churned, 18.00%
- Startup: 6 of 50 churned, 12.00%
- Comparison: SMB is 14 percentage points above Enterprise.

## Why This Evidence Matters

The difference shows where a retention review can start. It does not prove that
customer type causes churn, but it identifies SMB as the group with the highest
observed rate.

## Business Meaning

Customer Success can prioritize an SMB retention review before applying the
same intervention across every customer type.