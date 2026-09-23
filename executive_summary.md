# CHURN REDUCTION INITIATIVE
## Executive Summary

### Situation

The customer dataset contains an 11.33% churn rate: 17 of 150 customers are
marked as churned. Retention attention should be focused where the observed
risk is highest, but the available data does not support a dollar estimate of
loss or a response-time target. The immediate decision is whether to pilot a
focused retention review and improve the evidence used to manage it.

### Key Findings

- **Customer type is the clearest priority:** SMB churn is 18.00% (9 of 50),
  compared with 12.00% for Startup and 4.00% for Enterprise.
- **Support workload is a useful warning signal:** churned customers average
  11.5 support tickets, compared with 4.0 for non-churned customers; all
  churned records have 8 or more tickets in the examined sample.
- **Product is not a strong separator:** Product A and B each show 11.76%
  churn, while Product C shows 10.42%.

### Business Risks

- **Retention risk:** SMB has the highest observed churn, so a broad one-size-
  fits-all retention effort may miss the most exposed group.
- **Service risk:** High ticket volume and churn appear together. Without a
  review trigger, support teams may miss customers who need attention.
- **Measurement risk:** The data has no renewal dates, response times, ticket
  timestamps, or intervention outcomes. Management cannot yet measure whether
  faster service changes retention or quantify the cost of inaction.

### Recommendations

1. **Pilot an SMB retention review** using customer type and high ticket volume
   as the first prioritization signals. Owner: Customer Success Lead. Start
   design within four weeks. Measure follow-up completion and later churn.
2. **Create a support-load review trigger** for customers with 8 or more tickets.
   Owner: Support Manager with Customer Success. Pilot for one reporting cycle.
   Measure precision, follow-up results, and subsequent churn.
3. **Improve retention measurement** by adding renewal dates, ticket timestamps,
   response time, issue category, and intervention outcomes. Owner: Data/IT
   Owner with Operations. Define the data contract within one month.

### Decision Needed

Approve the SMB retention and support-load pilot, assign the named role owners,
and authorize the data requirements work. No budget or ROI amount is requested
until costs and financial exposure are measured.

### Next Steps

Customer Success defines the review queue in four weeks; Support documents the
8-ticket pilot rule; Data/IT specifies the missing fields within one month; the
teams review the first complete measurement period before scaling the program.