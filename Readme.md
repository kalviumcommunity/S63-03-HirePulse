# Recruitment Analytics Data Foundation

Phase 1 provides a reproducible data ingestion, validation, cleaning, and feature engineering layer for recruitment analytics. It intentionally does not include a dashboard or visualization layer.

## Structure

```text
recruitment-analytics/
├── data/
├── src/
│   ├── config.py
│   ├── data_cleaning.py
│   ├── data_loader.py
│   ├── data_validation.py
│   ├── feature_engineering.py
│   ├── generate_sample_data.py
│   └── quality_report.py
├── outputs/
├── requirements.txt
└── Readme.md
```

## Setup and run

```bash
python -m pip install -r requirements.txt
python src/generate_sample_data.py
python src/quality_report.py
```

The generator uses a fixed random seed and produces 100 candidate records plus related funnel, interview, offer, and onboarding records. The quality report is written to `outputs/quality_report.csv`.

## Using the pipeline

Run from the project root so the modules resolve consistently:

```bash
python -c "import sys; sys.path.insert(0, 'src'); from data_loader import load_candidates; from data_cleaning import convert_dates; from feature_engineering import build_candidate_features; from data_loader import load_stages, load_offers, load_onboarding; print(build_candidate_features(convert_dates(load_candidates(), ['applied_date']), load_stages(), load_offers(), load_onboarding()).head())"
```

The cleaning module exposes `clean_missing_values`, `remove_duplicates`, `standardize_text`, `convert_dates`, and `validate_schema`. Validation covers missing values, duplicates, email and phone formats, dates, data types, and allowed departments.
 
 ///////