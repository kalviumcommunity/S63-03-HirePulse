# Data Workflow

## Overview

The production-style workflow reads the five relational CSV source tables in `data/`, validates their expected columns, applies the existing cleaning utilities, builds candidate-level analytical features, and writes the result to `outputs/processed_candidates.csv`. Operational events are written to `outputs/data_workflow.log`.

The workflow preserves the existing data foundation logic. `data_loader.py` remains responsible for CSV access, `data_cleaning.py` owns reusable preparation functions, and `feature_engineering.py` remains the owner of candidate-level calculations.

## Functions

- `ingest_data()` loads candidates, recruitment stages, interviews, offers, and onboarding records and rejects missing or empty inputs.
- `process_data(df)` validates source schemas, standardizes text, converts dates, removes duplicate rows, and calls `build_candidate_features()`.
- `output_results(df, output_path)` creates the destination directory and exports the processed DataFrame as CSV.
- `main()` orchestrates ingestion, processing, output, logging, error handling, and the terminal summary.

## Execution

From the repository root:

```bash
python scripts/data_workflow.py
```

Expected output resembles:

```text
✓ Data successfully processed
✓ Rows processed: 100
✓ Output saved to: .../outputs/processed_candidates.csv
```

The script exits with status `1` and logs the failure when an input file is missing, empty, structurally invalid, or cannot be processed.

## Adapting for Future Datasets

1. Add the new source path and loader to `src/config.py` and `scripts/data_workflow.py`.
2. Add its required columns and data types to `src/data_validation.py`.
3. Extend `process_data()` only with transformations that are part of the analytical contract; keep file I/O in `ingest_data()` and exporting in `output_results()`.
4. Add focused validation for new business rules and update the sample run artifact when the expected row count or output contract changes.
5. Keep the workflow's root-relative execution command unchanged so scheduled jobs and local runs use the same entry point.

## Dataset Intake Validation

`python scripts/validate_intake.py` validates the existing `data/candidates.csv` before downstream processing. The intake workflow checks that the file exists and is non-empty, confirms that its extension is a supported CSV, JSON, or XLSX format, loads it with pandas, and captures rows, columns, and file size.

Schema validation compares the loaded columns with the candidate schema declared in `src/data_validation.py` and reports both missing and unexpected columns. Encoding validation uses `chardet` to record the detected encoding and confidence for the source file.

The complete validation result, timestamp, filepath, encoding details, schema checks, errors, and dataset statistics are written to `output/intake_report.json`. Operational events and failures are written to `output/intake_validation.log`. A non-zero process status indicates that the dataset did not pass intake validation or the report could not be generated.