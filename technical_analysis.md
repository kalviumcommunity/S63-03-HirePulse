# Technical Analysis Appendix: Churn Reporting

This appendix supports `executive_summary.md`. It contains the evidence and
assumptions needed to verify the executive message without placing methodology
in front of the decision-maker.

## Data Sources

The primary source is `data/raw/customer_segment_data.csv` with 150 customer
records and the columns `customer_id`, `customer_type`, `product`, `revenue`,
and `churn`. It contains 17 churned records, or 11.33%.

The support analysis uses `data/raw/customer_correlation_data.csv`, also with
150 records. Relevant fields are `support_tickets`, `revenue`, and `churn`.
Existing lineage references include `kpis/kpi_reference.md`,
`output/segment_summary.csv`, and `output/pearson_correlation_matrix.csv`.

The repository does not contain renewal dates, support response times, ticket
timestamps, issue categories, intervention outcomes, or a validated cost-of-
churn model. It therefore cannot support response-time comparisons, historical
trends, causal claims, or financial ROI estimates.

## Verified Findings

| Finding | Evidence |
|---|---|
| SMB has the highest churn | SMB: 9/50 = 18.00%; Startup: 6/50 = 12.00%; Enterprise: 2/50 = 4.00% |
| Support workload differs by churn label | Churned: 80 records, mean 11.5 tickets; non-churned: 70 records, mean 4.0 |
| High-ticket records align with churn | Churned records range from 8–15 tickets; non-churned records range from 1–7 |
| Product is not a strong separator | Product A: 6/51 = 11.76%; B: 6/51 = 11.76%; C: 5/48 = 10.42% |
| Ticket/churn association | Pearson correlation recalculated as 0.8660254037844383 |

The support pattern is an association. The data does not establish that tickets
cause churn; ticket volume may be an early warning signal, a result of customer
friction, or both.

## Risk Analysis

### Risk 1: SMB Retention Exposure

- **What:** SMB churn is 18.00%, the highest customer-type rate.
- **Why it matters:** A generalized intervention may fail to prioritize the
  group with the highest observed rate.
- **Action:** Pilot an SMB retention review and measure later churn.

### Risk 2: Unreviewed Support Load

- **What:** Every churned record in the support sample has at least 8 tickets.
- **Why it matters:** High-ticket customers may not receive timely attention.
- **Action:** Test an 8-ticket review trigger without treating it as a causal
  rule.

### Risk 3: Incomplete Decision Evidence

- **What:** No response time, renewal date, intervention outcome, or cost data.
- **Why it matters:** Leaders cannot quantify financial exposure or prove that
  a service change improved retention.
- **Action:** Add governed fields and a measurement owner before scaling.

## Recommendation Justification

| Finding | Risk | Recommendation | How it helps |
|---|---|---|---|
| SMB churn is 18.00% | Highest observed segment exposure | SMB retention review | Tests focused follow-up where the rate is highest |
| Churned records average 11.5 tickets | High support load may go unreviewed | 8-ticket review trigger | Creates an operational signal to investigate |
| Evidence lacks timing and outcomes | Impact cannot be measured | Improve retention measurement | Enables response-time, trend, and intervention analysis |

## Validation and Assumptions

The figures were recalculated from the cited CSV sources and checked against the
existing generated segment and correlation reports. No example values from the
assignment were used. The findings are cross-sectional, and the proposed pilot
threshold is a review trigger derived from the observed sample, not a proven
optimal policy.

## Audience Follow-Up: CEO and VP Engineering

For a CEO, emphasize the decision, risk, and business priority: approve the SMB
retention and support-load pilot and authorize the data work. For a VP of
Engineering, emphasize feasibility: add timestamped support events, response
time fields, renewal dates, intervention tracking, and a reporting pipeline.
The underlying findings stay the same; only the level of detail and requested
action changes.