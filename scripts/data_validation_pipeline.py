from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "customer_validation_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
FAILURES_PATH = OUTPUT_DIR / "validation_failures.csv"
CLEAN_PATH = OUTPUT_DIR / "validated_clean_data.csv"
REPORT_PATH = OUTPUT_DIR / "validation_report.csv"


def validate_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add one boolean column for each validation rule and the overall result."""
    today = pd.Timestamp.today().normalize()

    dataframe["birth_date"] = pd.to_datetime(dataframe["birth_date"], errors="coerce")
    dataframe["start_date"] = pd.to_datetime(dataframe["start_date"], errors="coerce")
    dataframe["end_date"] = pd.to_datetime(dataframe["end_date"], errors="coerce")

    dataframe["valid_age"] = dataframe["age"].between(0, 150, inclusive="both")
    dataframe["valid_price"] = dataframe["price"].ge(0)
    dataframe["valid_birth_date"] = dataframe["birth_date"].between(
        pd.Timestamp("1920-01-01"), today, inclusive="both"
    )
    dataframe["valid_customer_id"] = dataframe["customer_id"].notna()
    dataframe["valid_email"] = dataframe["email"].notna()
    dataframe["valid_email_format"] = dataframe["email"].fillna("").str.contains("@", regex=False)
    dataframe["valid_phone"] = dataframe["phone"].fillna("").str.fullmatch(r"\d{10}").fillna(False)
    dataframe["valid_date_order"] = dataframe["end_date"].ge(dataframe["start_date"])

    validation_columns = [
        "valid_age",
        "valid_price",
        "valid_birth_date",
        "valid_customer_id",
        "valid_email",
        "valid_email_format",
        "valid_phone",
        "valid_date_order",
    ]
    dataframe["passes_all_checks"] = dataframe[validation_columns].all(axis=1)
    return dataframe


def create_report(dataframe: pd.DataFrame) -> pd.DataFrame:
    validation_columns = [
        "valid_age",
        "valid_price",
        "valid_birth_date",
        "valid_customer_id",
        "valid_email",
        "valid_email_format",
        "valid_phone",
        "valid_date_order",
    ]
    return pd.DataFrame(
        {
            "rule_name": validation_columns,
            "passed_count": [int(dataframe[column].sum()) for column in validation_columns],
            "failed_count": [int((~dataframe[column]).sum()) for column in validation_columns],
        }
    )


def main() -> None:
    dataframe = validate_data(pd.read_csv(INPUT_PATH))
    report = create_report(dataframe)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dataframe.loc[~dataframe["passes_all_checks"]].to_csv(FAILURES_PATH, index=False)
    dataframe.loc[dataframe["passes_all_checks"]].to_csv(CLEAN_PATH, index=False)
    report.to_csv(REPORT_PATH, index=False)

    assert FAILURES_PATH.exists()
    assert REPORT_PATH.exists()
    assert CLEAN_PATH.exists()
    assert "passes_all_checks" in dataframe.columns

    total_records = len(dataframe)
    passed_records = int(dataframe["passes_all_checks"].sum())
    failed_records = total_records - passed_records
    print(f"Total Records: {total_records}")
    print(f"Passed Records: {passed_records}")
    print(f"Failed Records: {failed_records}")
    print("Data Consistency & Validation Rules Pipeline completed successfully.")


if __name__ == "__main__":
    main()