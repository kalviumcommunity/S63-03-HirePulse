# HirePulse — Recruitment & Talent Pipeline Analytics

HirePulse is a recruitment analytics application designed to help teams understand hiring performance, monitor recruitment funnel progression, explore candidate data, and identify potential pipeline issues through an interactive web dashboard.

The application combines a Python-based data processing foundation with a Flask web interface for recruitment analytics and reporting.

**Live Demo:** https://s63-03-hirepulse.onrender.com/  
**Repository:** https://github.com/kalviumcommunity/S63-03-HirePulse

## Features

### Interactive Recruitment Dashboard
- Executive-level recruitment KPIs.
- Recruitment funnel and conversion analysis.
- Application intake trend visualization.
- Department-level hiring performance.
- Candidate explorer and directory.
- Anomaly detection and recruitment pipeline health monitoring.

### Data Engineering & Analytics
- Recruitment data ingestion and loading.
- Data cleaning and standardization.
- Data validation and quality reporting.
- Feature engineering for candidate-level analytics.
- Recruitment funnel analysis and reporting.
- Support for candidate, interview, offer, onboarding, and recruitment-stage datasets.

### Web Application
- Flask-based backend and server-rendered web interface.
- HTML templates and static assets for the dashboard.
- Interactive dashboard components and candidate workflows.
- Deployable as a single web application.

## Tech Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Backend & Web Framework | Flask |
| Web Server | Gunicorn |
| Frontend | HTML, CSS, JavaScript |
| Data Processing | Pandas / Python data-processing modules, where used |
| Data Sources | CSV files and PostgreSQL, depending on the active configuration |
| Deployment | Render |
| Testing | Python test suite |

## Project Structure

```text
S63-03-HirePulse/
├── app.py
├── data/
├── src/
│   ├── config.py
│   ├── data_cleaning.py
│   ├── data_loader.py
│   ├── data_validation.py
│   ├── feature_engineering.py
│   ├── generate_sample_data.py
│   └── quality_report.py
├── templates/
├── static/
├── outputs/
├── tests/
├── requirements.txt
└── README.md
```

*Note: The structure above highlights the main application and pipeline components. Individual files may vary by repository version.*

## Getting Started

### Prerequisites
- Python installed on your system.
- Git.
- A terminal or code editor.

### 1. Clone the Repository

```bash
git clone https://github.com/kalviumcommunity/S63-03-HirePulse.git
cd S63-03-HirePulse
```

### 2. Create a Virtual Environment

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

Open your browser at:

```text
http://127.0.0.1:5000
```

The dashboard provides access to recruitment KPIs, hiring funnel analytics, candidate exploration, and other implemented dashboard features.

### 5. Run the Data Pipeline

From the project root, run:

```bash
python src/generate_sample_data.py
python src/quality_report.py
```

The sample-data generator is designed to produce reproducible recruitment data using a fixed random seed. The original pipeline documentation specifies 100 candidate records along with related recruitment-stage, interview, offer, and onboarding records.

The quality report is written to:

```text
outputs/quality_report.csv
```

Run the generator when you intentionally want to regenerate sample data. If your application uses existing production or project datasets, verify the configured data source before replacing any files.

## Using the Data Pipeline

Run pipeline commands from the project root to ensure imports resolve consistently.

The following example loads candidate, recruitment-stage, offer, and onboarding data, converts application dates, and builds candidate-level features:

```bash
python -c "import sys; sys.path.insert(0, 'src'); from data_loader import load_candidates, load_stages, load_offers, load_onboarding; from data_cleaning import convert_dates; from feature_engineering import build_candidate_features; print(build_candidate_features(convert_dates(load_candidates(), ['applied_date']), load_stages(), load_offers(), load_onboarding()).head())"
```

### Data Cleaning

The cleaning module documents the following operations:

- `clean_missing_values` — handle missing values.
- `remove_duplicates` — identify or remove duplicate records.
- `standardize_text` — standardize text fields.
- `convert_dates` — convert date columns into appropriate formats.
- `validate_schema` — validate the expected data structure.

### Data Validation

The validation layer covers data-quality checks such as:

- Missing values.
- Duplicate records.
- Email and phone number formats.
- Date validity.
- Data types.
- Allowed department values.

## Deployment

HirePulse is deployed on Render.

**Live application:** https://s63-03-hirepulse.onrender.com/

The Flask application serves the web interface and backend from the same deployment. Gunicorn can be used as the production WSGI server.

A typical Render start command for this application is:

```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

The Python version and dependencies should match the application's deployment configuration. Configure database credentials and other secrets through environment variables when required; do not commit credentials to the repository.

## Testing

Run the project's test suite, if configured:

```bash
python -m pytest
```

Ensure the required dependencies are installed and the relevant test data and configuration are available before running tests.

## Future Improvements

Potential areas for further development include:

- Additional recruitment conversion and time-to-hire metrics.
- Enhanced data-quality monitoring.
- More detailed department and candidate-segment analysis.
- Improved automated testing and deployment checks.
- Expanded recruitment reporting and operational insights.

## Project Goal

HirePulse aims to make recruitment data more actionable by combining a reproducible data-processing workflow with an interactive dashboard for exploring hiring performance and recruitment pipeline health.
