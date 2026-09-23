# Customer Churn Analysis: Executive Summary

## 1. Context / Problem Statement

Customer churn matters because leaving customers reduce future-revenue stability
and make retention work harder than keeping an existing relationship healthy.
This analysis asks where churn is concentrated and whether the available
customer-support signal can identify customers who may need attention. The
decision is how to prioritize customer-success and support follow-up without
treating an observed pattern as proof of its cause. The analysis does not
estimate financial losses because contract value, renewal dates, and a validated
cost-of-churn model are absent.

## 2. Data Summary / What We Examined

The primary source is `data/raw/customer_segment_data.csv`, a 150-record
customer-level dataset with customer ID, customer type, product, revenue, and a
binary churn field. It has 17 churned records, giving an overall churn rate of
11.33%. It has no event date, renewal date, or response-time column, so the
findings are cross-sectional rather than a month-by-month trend.

We also examined `data/raw/customer_correlation_data.csv`, which contains 150
records with engagement, transactions per month, support-ticket count, revenue,
and churn. Ticket count is the available support measure, not response time, so
response-time buckets cannot be calculated. Existing KPI and segment reports
were used as lineage references; the figures below were recalculated from the
source rows.

## 3. Key Findings

- Churn is not evenly distributed across customer types: SMB churn is 18.00%
  (9 of 50), Startup churn is 12.00% (6 of 50), and Enterprise churn is 4.00%
  (2 of 50). SMB is 14 percentage points above Enterprise.
- The product split is comparatively narrow. Product A and Product B each have
  a 11.76% churn rate (6 of 51), while Product C has 10.42% (5 of 48).
  Customer type is therefore a clearer prioritization signal than product in
  this dataset.
- Support-ticket volume is strongly associated with the churn label in the
  correlation output: the recalculated Pearson correlation is 0.866. Churned
  customers average 11.5 tickets, compared with 4.0 for non-churned customers.
  This is an association, not proof that tickets cause churn.

## 4. Anomaly Investigation / Why Is This Happening?

The strongest operational pattern is the separation between support-ticket
counts of 1–7 for every non-churned record and 8–15 for every churned record.
That pattern is consistent with support demand being an early warning signal,
or with struggling customers creating more tickets. The data cannot distinguish
those explanations because it has no ticket timestamps, response times, issue
categories, or customer comments.

SMB has the highest churn while Enterprise has the lowest. Product churn is
close across all three products, so a product-only intervention is not supported.
The absence of dates also prevents a claim about churn changing over time.

## 5. Recommendations

## Recommendation 1: Prioritize SMB Retention Reviews

### Action
Create a recurring SMB customer-success review for accounts showing elevated
support activity.

### Why
SMB churn is 18.00%, the highest observed customer-type rate.

### Expected Impact
The expected impact should be measured as a change in SMB churn and retained
customers after the review process begins; the current data does not support a
numeric improvement target.

### Owner
Customer Success Lead.

### Timeline
Design the review queue within four weeks and assess it after the next complete
measurement period.

## Recommendation 2: Add Support-Load Alerts

### Action
Flag customers reaching the observed high-support range of 8 or more tickets
for proactive review.

### Why
All churned records in the examined support dataset have at least 8 tickets,
while non-churned records have 7 or fewer.

### Expected Impact
Measure alert precision, follow-up completion, and subsequent churn. No savings
estimate is justified without intervention outcomes.

### Owner
Support Manager with Customer Success.

### Timeline
Pilot the rule for one reporting cycle, then review false positives and misses.

## Recommendation 3: Improve Retention Measurement

### Action
Add renewal dates, support timestamps, response time, issue category, and
intervention outcomes to the clean customer dataset.

### Why
The current data supports segment and ticket-volume comparisons but cannot show
timing, response-time buckets, or change over time.

### Expected Impact
The next analysis can test whether faster responses precede lower churn and can
measure actual retention impact rather than relying on a cross-sectional signal.

### Owner
Data/IT Owner with Operations and Customer Success.

### Timeline
Define fields and ownership within one month, then validate the first complete
reporting period.

## Business Language Check

Technical outputs were translated into plain business language. Correlation is
described as an association, not causation, and unsupported response-time,
trend, and financial claims are explicitly excluded.