# HirePulse Data Dictionary

## Scope

This dictionary describes the canonical recruitment datasets in `data/` and the candidate-level analytical output in `outputs/processed_candidates.csv`. The five canonical source tables are the authoritative HirePulse domain model:

- `candidates.csv`
- `recruitment_stages.csv`
- `interviews.csv`
- `offers.csv`
- `onboarding.csv`

The earlier customer and transaction samples under `data/raw/` and `data/processed/` belong to the multi-format ingestion exercise and are not part of the recruitment business model.

The machine-readable column catalog is [data_dictionary.csv](data_dictionary.csv).

## Conventions

- Source files are comma-separated CSV files.
- Columns use lowercase `snake_case`.
- Dates are represented as `YYYY-MM-DD` in source files.
- `candidate_id` is the shared business key.
- Source values are parsed and validated by [src/data_validation.py](../src/data_validation.py).
- Date conversion, text normalization, and derived fields are implemented by the existing workflow rather than by this document.

## Dataset Purpose

| Dataset | Current rows | Grain | Purpose |
|---|---:|---|---|
| `candidates.csv` | 100 | One row per candidate | Candidate master and application intake |
| `recruitment_stages.csv` | 470 | One row per candidate-stage event | Recruitment funnel progression |
| `interviews.csv` | 80 | One row per interview | Interview evaluation and feedback |
| `offers.csv` | 70 | One row per offer | Offer issuance, compensation, and acceptance |
| `onboarding.csv` | 50 | One row per onboarding record | Joining and onboarding readiness |
| `processed_candidates.csv` | 100 | One row per candidate | Candidate-level analytical features |

## Keys and Sensitivity

`candidate_id` is the primary key of `candidates.csv` and a foreign key in the other source tables. `full_name`, `email`, and `phone` are personally identifiable fields. The committed sample values are synthetic, but these fields should be treated as restricted if real data is introduced.

## Validation Vocabulary

Departments, recruitment stages, stage statuses, and onboarding statuses are controlled by constants in [src/config.py](../src/config.py). The allowed values are documented in [data_dictionary.csv](data_dictionary.csv). Values currently observed in the generated sample may be narrower than the allowed vocabulary.

## Derived Output

The workflow combines source data into `outputs/processed_candidates.csv`. `joined_date` uses the onboarding joining date when available and otherwise the earliest `Joined` stage date. `hiring_duration_days` is the date difference between `joined_date` and `applied_date`. Missing offers and joins remain nullable in the carried date/value fields; the two indicator fields convert those conditions into `0` or `1`.

## Maintenance Rule

When a source column, allowed value, or derived feature changes, update the CSV catalog and this guide together. Do not change source schemas solely to improve documentation; schema changes belong to the relevant assignment and workflow contract.
