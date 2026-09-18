"""Data profiling and quality assessment suite."""

import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



def profile_nulls_and_duplicates(df: pd.DataFrame) -> dict:
    """Compute null percentage and duplicate counts per column.

    Returns: Dictionary with null analysis by column.
    """
    profile = {
        'null_counts': {},
        'null_percentages': {},
        'exact_duplicate_count': 0
    }

    total_records = len(df)
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = (null_count / total_records) * 100 if total_records > 0 else 0.0
        profile['null_counts'][col] = null_count
        profile['null_percentages'][col] = round(null_pct, 2)

    dup_count = int(df.duplicated().sum())
    dup_pct = (dup_count / total_records) * 100 if total_records > 0 else 0.0
    profile['exact_duplicate_count'] = dup_count
    profile['duplicate_percentage'] = round(dup_pct, 2)

    return profile


def profile_numerical_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise numerical columns with statistical measures.

    Returns: DataFrame with min, max, mean, median, std.
    """
    numerical_cols = df.select_dtypes(include=[np.number]).columns

    stats = {}
    for col in numerical_cols:
        series = df[col].dropna()
        if len(series) == 0:
            stats[col] = {
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'std': None,
                'null_count': int(df[col].isnull().sum())
            }
        else:
            stats[col] = {
                'min': round(float(series.min()), 2),
                'max': round(float(series.max()), 2),
                'mean': round(float(series.mean()), 2),
                'median': round(float(series.median()), 2),
                'std': round(float(series.std()), 2) if len(series) > 1 else 0.0,
                'null_count': int(df[col].isnull().sum())
            }

    return pd.DataFrame(stats).T


def profile_categorical_columns(df: pd.DataFrame, top_n: int = 5) -> dict:
    """Summarise categorical columns with value distributions.

    Returns: Dictionary with unique counts and top values.
    """
    categorical_cols = df.select_dtypes(include=['object', 'string', 'category']).columns

    profile = {}
    for col in categorical_cols:
        top_vals = df[col].value_counts(dropna=True).head(top_n).to_dict()
        profile[col] = {
            'unique_count': int(df[col].nunique()),
            'top_values': top_vals,
            'null_count': int(df[col].isnull().sum())
        }

    return profile


def identify_quality_issues(df: pd.DataFrame, null_threshold: float = 30.0, duplicate_threshold: float = 5.0) -> list:
    """Identify data quality problems based on thresholds.

    Returns: List of issues found with severity and recommendations.
    """
    issues = []
    total_records = len(df)

    # Check nulls
    null_pcts = (df.isnull().sum() / total_records) * 100 if total_records > 0 else 0
    for col, pct in null_pcts.items():
        if pct > null_threshold:
            issues.append({
                'type': 'High nulls',
                'column': col,
                'severity': 'HIGH',
                'value': f"{pct:.1f}% missing",
                'recommendation': 'Consider imputation or column exclusion'
            })

    # Check duplicates
    dup_count = df.duplicated().sum()
    dup_pct = (dup_count / total_records) * 100 if total_records > 0 else 0
    if dup_pct > duplicate_threshold:
        issues.append({
            'type': 'High duplicates',
            'column': 'Full row',
            'severity': 'HIGH',
            'value': f"{dup_pct:.1f}% duplicated",
            'recommendation': 'Deduplication required before analysis'
        })

    # Check for invalid ranges
    for col in df.select_dtypes(include=[np.number]).columns:
        if (df[col] < 0).any() and 'amount' in col.lower():
            issues.append({
                'type': 'Invalid range',
                'column': col,
                'severity': 'MEDIUM',
                'value': 'Contains negative values',
                'recommendation': 'Investigate negative entries'
            })

    return issues


def generate_profile_report(df: pd.DataFrame, filepath: str | Path, output_path: str | Path | None = None) -> dict:
    """Generate complete data quality report and save to JSON.

    Returns: Complete profile report dictionary.
    """
    report = {
        'dataset': str(filepath),
        'record_count': len(df),
        'column_count': len(df.columns),
        'nulls_and_duplicates': profile_nulls_and_duplicates(df),
        'numerical_stats': profile_numerical_columns(df).to_dict(),
        'categorical_stats': profile_categorical_columns(df),
        'quality_issues': identify_quality_issues(df)
    }

    # Save report
    out_file = Path(output_path) if output_path else Path('output/profile_report.json')
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    print(f"\n{'='*60}")
    print(f"DATA QUALITY PROFILE: {filepath}")
    print(f"{'='*60}")
    print(f"Records: {report['record_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"\nQuality Issues Found: {len(report['quality_issues'])}")
    for issue in report['quality_issues']:
        print(f"  [{issue['severity']}] {issue['type']} in {issue['column']}")
        print(f"    Value: {issue['value']} → {issue['recommendation']}")
    print(f"{'='*60}\n")

    return report


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    test_csv = project_root / "data" / "raw" / "quality_test.csv"

    if test_csv.exists():
        data_df = pd.read_csv(test_csv)
        report_output = project_root / "output" / "profile_report.json"
        generate_profile_report(data_df, test_csv, report_output)
    else:
        print(f"Test dataset not found at {test_csv}")
