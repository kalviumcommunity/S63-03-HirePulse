# HirePulse KPI Mapping

This document maps recruitment KPIs to the canonical source fields and the existing candidate-level output. Unless stated otherwise, rates use distinct candidates as the denominator and exclude records outside the defined population.

| KPI | Definition | Calculation | Source fields / output | Caveats |
|---|---|---|---|---|
| Applications | Number of candidates who applied | `COUNT(DISTINCT candidate_id)` | `candidates.candidate_id` | Candidate table is the application population |
| Applications by department | Applications grouped by department | Count candidates by `department` | `candidates.department` | Department is the applied role department |
| Stage progression | Candidates reaching a named stage | Count distinct candidate IDs by `stage_name` | `recruitment_stages.candidate_id`, `stage_name` | A candidate may have multiple stage events; deduplicate per candidate and stage |
| Stage conversion rate | Candidates reaching stage B divided by candidates reaching stage A | `stage_B_candidates / stage_A_candidates` | `recruitment_stages.stage_name` | Define stage order before comparing rates |
| Interview volume | Number of interview records | `COUNT(*)` | `interviews.candidate_id` | Current sample contains one technical interview per interviewed candidate |
| Average interview score | Mean recorded interview score | `AVG(score)` | `interviews.score` | Confirm score scale before comparing teams or periods |
| Interview pass rate | Passing interview records divided by interview records | `result = Pass / total interview records` | `interviews.result` | Current generated sample only shows `Pass`; this KPI is not discriminating until outcomes vary |
| Offers issued | Number of offer records | `COUNT(*)` | `offers.candidate_id` | Assumes one offer record per candidate in the current model |
| Offer acceptance rate | Accepted offers divided by issued offers | `COUNT(accepted=True) / COUNT(offers)` | `offers.accepted` or `processed_candidates.offer_acceptance_flag` | Do not use all applicants as the denominator |
| Joining rate | Candidates with a joining date divided by candidates | `COUNT(joined_flag=1) / COUNT(candidates)` | `processed_candidates.joined_flag` | `joined_date` is sourced from onboarding or the Joined stage |
| Time to hire | Average elapsed days from application to joining | `AVG(hiring_duration_days)` for joined candidates | `processed_candidates.hiring_duration_days` | Exclude candidates without a joined date; clarify whether calendar days are intended |
| Median time to hire | Median elapsed days from application to joining | `MEDIAN(hiring_duration_days)` for joined candidates | `processed_candidates.hiring_duration_days` | More robust than mean for skewed hiring cycles |
| Onboarding completion | Candidates with completed onboarding divided by onboarding records | `onboarding_status = Completed / onboarding records` | `onboarding.onboarding_status` | This is onboarding completion, not recruitment joining rate |
| Document completion | Mean onboarding document completion | `AVG(document_completion)` | `onboarding.document_completion` | Unit is not explicitly labelled as a percentage in the schema; current values suggest a percentage |
| Offer-to-join rate | Accepted offers that joined divided by accepted offers | `joined accepted candidates / accepted offers` | `offers.accepted`, `processed_candidates.joined_flag` | Requires a defined join between accepted offers and joined candidates |

## Recommended Reporting Grain

- Use the candidate grain for applications, joining rate, and offer acceptance rate.
- Use the event grain for interviews and recruitment-stage events.
- Use `application_month` and `application_year` only for grouping the candidate-level output; they are derived from `candidates.applied_date`.
- Preserve the distinction between an offer being accepted and a candidate actually joining.
