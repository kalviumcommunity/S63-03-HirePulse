# Ambiguous Columns and Interpretation Notes

These fields need explicit interpretation when Assignment 2.17 documentation is consumed by analysts or extended by future work.

| Column | Dataset | Ambiguity | Current interpretation | Required future clarification |
|---|---|---|---|---|
| `status` | `recruitment_stages.csv` | Could describe the stage event, candidate state, or workflow state | Status of the candidate at that stage event | Confirm whether a row is retained after a candidate is dropped and whether status is historical or current |
| `stage_name` | `recruitment_stages.csv` | Stage labels can represent milestones or current state | Named recruitment milestone: Applied through Joined | Confirm whether stage order is fixed and whether repeated stage attempts are valid |
| `result` | `interviews.csv` | Could be interview result, candidate result, or hiring decision | Outcome of the interview record | Define complete controlled vocabulary such as Pass, Fail, Pending, and No-show |
| `score` | `interviews.csv` | Scale and scoring rubric are not documented | Numeric interview assessment score; current sample values are 65-100 | Document minimum, maximum, weighting, and whether scores are comparable across rounds |
| `document_completion` | `onboarding.csv` | Name does not state whether value is a count, ratio, or percentage | Numeric completion measure; current sample values of 85-100 suggest percentage | Confirm unit, maximum, minimum, and treatment of partially completed documents |
| `accepted` | `offers.csv` | Boolean does not identify acceptance date or withdrawal/rejection state | Whether the offer was accepted | Add acceptance date and explicit declined/expired states if business reporting needs them |
| `joining_date` | `onboarding.csv` | May differ from the actual start date or Joined stage date | Onboarding-record joining date | Define authoritative joining date when it conflicts with a Joined stage event |
| `joined_date` | `processed_candidates.csv` | Derived from two possible source dates | Onboarding joining date, otherwise earliest Joined stage date | Define conflict resolution when both dates exist but differ |
| `full_name` | `candidates.csv` | Combined name prevents separate surname analysis | Display name for the candidate | Keep as display text or add governed first/last-name fields if needed |
| `salary` | `offers.csv` | Currency, pay period, and base/total compensation are absent | Numeric proposed salary | Document currency, period, compensation components, and whether revisions create multiple offers |
| `feedback` | `interviews.csv` | Free text may contain sensitive or inconsistent content | Qualitative interviewer comments | Define retention, redaction, and reporting rules |

## Documentation Principle

The current source code and generated sample are the evidence for existing behavior. Where business meaning is not explicit, this document records the interpretation without silently changing schemas or inventing a new controlled vocabulary.
