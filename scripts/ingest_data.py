import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# TASK 1 — CSV INGESTION
# ============================================================

def ingest_csv(
    filepath,
    delimiter=",",
    encoding="utf-8",
    dtype_dict=None
):
    """
    Load a CSV file with explicit parameters.

    Args:
        filepath: Path to CSV file.
        delimiter: Field separator.
        encoding: Character encoding.
        dtype_dict: Optional dictionary defining column data types.

    Returns:
        Pandas DataFrame.
    """

    try:
        df = pd.read_csv(
            filepath,
            delimiter=delimiter,
            encoding=encoding,
            dtype=dtype_dict
        )

        print(f"✓ CSV loaded: {filepath}")
        print(
            f"  Shape: {df.shape[0]} rows × "
            f"{df.shape[1]} columns"
        )
        print(f"  Columns: {list(df.columns)}")

        return df

    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise

    except UnicodeDecodeError:
        print(
            f"Encoding error: Could not decode with {encoding}"
        )
        print(
            "Try: latin-1, iso-8859-1, or cp1252"
        )
        raise

    except pd.errors.ParserError:
        print(
            f"Parsing error while reading CSV: {filepath}"
        )
        raise


# ============================================================
# TASK 2 — JSON INGESTION
# ============================================================

def ingest_json(filepath, is_nested=False):
    """
    Load JSON data.

    If is_nested=True, nested objects are flattened into
    tabular columns using pandas.json_normalize().
    """

    try:
        df = pd.read_json(filepath)

        if is_nested:

            # Convert dataframe records into dictionaries
            records = df.to_dict(orient="records")

            # Flatten nested objects
            df = pd.json_normalize(records)

            print(
                "✓ Nested JSON flattened "
                "to tabular format"
            )

        print(f"✓ JSON loaded: {filepath}")
        print(
            f"  Shape: {df.shape[0]} rows × "
            f"{df.shape[1]} columns"
        )
        print(f"  Columns: {list(df.columns)}")

        return df

    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise

    except ValueError as e:
        print(f"Error reading JSON file: {e}")
        raise


# ============================================================
# TASK 3 — ENCODING / DELIMITER FALLBACK
# ============================================================

def ingest_csv_with_fallback(
    filepath,
    delimiters=None,
    fallback_encodings=None
):
    """
    Load CSV using multiple delimiter and encoding combinations.

    The function validates that the selected delimiter actually
    separates the fields instead of silently loading the file
    as a single column.
    """

    if delimiters is None:
        delimiters = [","]

    if fallback_encodings is None:
        fallback_encodings = [
            "utf-8",
            "latin-1",
            "iso-8859-1",
            "cp1252"
        ]

    for delimiter in delimiters:

        for encoding in fallback_encodings:

            try:
                df = pd.read_csv(
                    filepath,
                    delimiter=delimiter,
                    encoding=encoding
                )

                # Prevent silent success when the wrong
                # delimiter produces only one column.
                if df.shape[1] <= 1 and delimiter != "\t":
                    print(
                        f"✗ delimiter='{delimiter}' produced "
                        f"only {df.shape[1]} column(s)"
                    )
                    continue

                print(
                    "✓ Successfully loaded with "
                    f"delimiter='{delimiter}', "
                    f"encoding='{encoding}'"
                )

                return df

            except (
                UnicodeDecodeError,
                pd.errors.ParserError
            ):
                print(
                    f"✗ Failed with delimiter='{delimiter}', "
                    f"encoding='{encoding}'"
                )
                continue

    raise ValueError(
        f"Could not load {filepath} with any "
        "encoding/delimiter combination"
    )


# ============================================================
# TASK 4 — DOCUMENT INGESTION
# ============================================================

def document_ingestion(df, source_file):
    """
    Print a comprehensive ingestion report.

    Includes:
    - Shape
    - Column names
    - Data types
    - Null counts
    - First three rows
    """

    print("\n" + "=" * 60)
    print(f"INGESTION REPORT: {source_file}")
    print("=" * 60)

    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    print("\nColumn Names & Data Types:")
    print(df.dtypes)

    print("\nNull Values Per Column:")
    print(df.isnull().sum())

    print("\nFirst 3 Rows:")
    print(df.head(3).to_string(index=False))

    print("=" * 60)

    return df


# ============================================================
# BONUS — EXCEL INGESTION
# ============================================================

def ingest_excel(filepath, sheet_name=None):
    """
    Load an Excel workbook with support for multiple sheets.

    If sheet_name is provided, only that sheet is loaded.

    If sheet_name is None, all sheets are loaded and returned
    as a dictionary of DataFrames.
    """

    try:

        if sheet_name is not None:

            df = pd.read_excel(
                filepath,
                sheet_name=sheet_name,
                engine="openpyxl"
            )

            print(
                f"✓ Excel sheet loaded: {sheet_name}"
            )

            return df

        sheets = pd.read_excel(
            filepath,
            sheet_name=None,
            engine="openpyxl"
        )

        print(
            f"✓ Excel workbook loaded: "
            f"{list(sheets.keys())}"
        )

        return sheets

    except FileNotFoundError:
        print(
            f"Error: File not found - {filepath}"
        )
        raise

    except ValueError as e:
        print(
            f"Error reading Excel file: {e}"
        )
        raise

    except Exception as e:
        print(
            f"Error loading Excel file: {e}"
        )
        raise


# ============================================================
# TASK 5 — MAIN INGESTION PIPELINE
# ============================================================

if __name__ == "__main__":

    print("\nStarting multi-format ingestion...\n")


    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    csv_file = RAW_DIR / "customers.csv"

    csv_df = ingest_csv(
        csv_file,
        delimiter=",",
        encoding="utf-8",
        dtype_dict={
            "customer_id": "int64",
            "name": "string",
            "email": "string",
            "signup_date": "string"
        }
    )

    document_ingestion(
        csv_df,
        "customers.csv"
    )

    csv_output = (
        PROCESSED_DIR /
        "customers_ingested.csv"
    )

    csv_df.to_csv(
        csv_output,
        index=False
    )

    print(
        f"✓ Saved processed CSV: {csv_output}"
    )


    # --------------------------------------------------------
    # FLAT JSON
    # --------------------------------------------------------

    json_file = RAW_DIR / "transactions.json"

    json_df = ingest_json(
        json_file,
        is_nested=False
    )

    document_ingestion(
        json_df,
        "transactions.json"
    )

    json_output = (
        PROCESSED_DIR /
        "transactions_ingested.csv"
    )

    json_df.to_csv(
        json_output,
        index=False
    )

    print(
        f"✓ Saved processed JSON: {json_output}"
    )


    # --------------------------------------------------------
    # NESTED JSON
    # --------------------------------------------------------

    nested_json_file = (
        RAW_DIR /
        "nested_transactions.json"
    )

    nested_json_df = ingest_json(
        nested_json_file,
        is_nested=True
    )

    document_ingestion(
        nested_json_df,
        "nested_transactions.json"
    )

    nested_json_output = (
        PROCESSED_DIR /
        "nested_transactions_ingested.csv"
    )

    nested_json_df.to_csv(
        nested_json_output,
        index=False
    )

    print(
        f"✓ Saved flattened JSON: "
        f"{nested_json_output}"
    )


    # --------------------------------------------------------
    # ENCODING / DELIMITER FALLBACK TEST
    # --------------------------------------------------------

    print(
        "\nTesting encoding/delimiter fallback...\n"
    )

    fallback_df = ingest_csv_with_fallback(
        RAW_DIR / "test_semicolon.csv",
        delimiters=[",", ";", "\t"]
    )

    document_ingestion(
        fallback_df,
        "test_semicolon.csv"
    )


    # --------------------------------------------------------
    # EXCEL — MULTI-SHEET INGESTION
    # --------------------------------------------------------

    print(
        "\nTesting Excel multi-sheet ingestion...\n"
    )

    excel_file = (
        RAW_DIR /
        "recruitment_data.xlsx"
    )

    excel_data = ingest_excel(
        excel_file
    )

    for sheet_name, df in excel_data.items():

        print(
            f"\n--- Sheet: {sheet_name} ---"
        )

        document_ingestion(
            df,
            f"recruitment_data.xlsx - {sheet_name}"
        )

        # Save each Excel sheet as a processed CSV
        excel_output = (
            PROCESSED_DIR /
            f"{sheet_name}_ingested.csv"
        )

        df.to_csv(
            excel_output,
            index=False
        )

        print(
            f"✓ Saved processed Excel sheet: "
            f"{excel_output}"
        )


    # --------------------------------------------------------
    # COMPLETION
    # --------------------------------------------------------

    print(
        "\n✓ All datasets ingested "
        "and saved to processed/"
    )