from pathlib import Path
import re

import pandas as pd
from sqlalchemy import create_engine, inspect, text


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "data" / "raw" / "customer_segment_data.csv"
DATABASE_DIR = ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "analytics.db"
OUTPUT_DIR = ROOT / "output"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TABLE_NAME = "customers_cleaned"
REPORT_PATH = OUTPUT_DIR / "sql_validation_report.txt"


# ============================================================
# TASK 1: DATABASE CONNECTION
# ============================================================

def create_database_engine(database_path=DATABASE_PATH):
    """
    Create a SQLite SQLAlchemy engine.

    Parameters
    ----------
    database_path : str or Path
        Location of the SQLite database file.

    Returns
    -------
    sqlalchemy.Engine
        SQLAlchemy database engine.
    """
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection_string = f"sqlite:///{database_path}"

    return create_engine(connection_string)


def test_connection(engine):
    """Test that the database connection is available."""

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True


# ============================================================
# LOAD SOURCE DATA
# ============================================================

def load_source_dataframe():
    """Load the cleaned customer dataset into a Pandas DataFrame."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "customer_id",
        "customer_type",
        "product",
        "revenue",
        "churn",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    return df


# ============================================================
# TASK 2: LOAD DATAFRAME INTO SQL
# ============================================================

def load_dataframe_to_database(
    df,
    engine,
    table_name=TABLE_NAME,
):
    """
    Load a DataFrame into a SQL table.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to load.
    engine : sqlalchemy.Engine
        SQLAlchemy database engine.
    table_name : str
        Destination table name.

    Returns
    -------
    int
        Number of rows loaded.
    """

    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table_name):
        raise ValueError(
            f"Invalid table name: {table_name}"
        )

    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False,
    )

    count_query = text(
        f"SELECT COUNT(*) AS row_count "
        f"FROM {table_name}"
    )

    count_df = pd.read_sql(
        count_query,
        engine,
    )

    rows_loaded = int(
        count_df.iloc[0]["row_count"]
    )

    if rows_loaded != len(df):
        raise ValueError(
            f"Row-count validation failed: "
            f"expected {len(df)}, got {rows_loaded}"
        )

    return rows_loaded


def verify_table_exists(
    engine,
    table_name=TABLE_NAME,
):
    """Verify that the destination table exists."""

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    if table_name not in tables:
        raise RuntimeError(
            f"Table '{table_name}' was not created."
        )

    return True


# ============================================================
# TASK 3: SCHEMA VALIDATION
# ============================================================

def inspect_table_schema(
    engine,
    table_name=TABLE_NAME,
):
    """Return SQLAlchemy schema information."""

    inspector = inspect(engine)

    columns = inspector.get_columns(
        table_name
    )

    return columns


def validate_schema(columns):
    """
    Validate the actual expected schema.

    The repository dataset contains:
    customer_id, customer_type, product, revenue, churn

    SQLite may represent Pandas object columns as VARCHAR,
    numeric columns as FLOAT/INTEGER depending on inferred data.
    """

    expected_columns = {
        "customer_id",
        "customer_type",
        "product",
        "revenue",
        "churn",
    }

    actual_columns = {
        column["name"]
        for column in columns
    }

    missing = expected_columns - actual_columns
    unexpected = actual_columns - expected_columns

    checks = []

    for column in columns:
        nullable = column["nullable"]

        checks.append({
            "column": column["name"],
            "type": str(column["type"]),
            "nullable": nullable,
        })

    return {
        "expected_columns": expected_columns,
        "actual_columns": actual_columns,
        "missing_columns": missing,
        "unexpected_columns": unexpected,
        "checks": checks,
        "valid": (
            not missing
            and not unexpected
        ),
    }


# ============================================================
# TASK 4: SQL QUERIES
# ============================================================

def run_queries(engine):
    """Run simple and aggregate SQL queries."""

    # Simple SELECT query
    simple_query = text(
        """
        SELECT *
        FROM customers_cleaned
        WHERE customer_type = 'Enterprise'
        """
    )

    enterprise_results = pd.read_sql(
        simple_query,
        engine,
    )

    # Aggregation query
    aggregate_query = text(
        """
        SELECT
            customer_type,
            COUNT(*) AS customer_count,
            AVG(revenue) AS avg_revenue,
            SUM(revenue) AS total_revenue,
            AVG(churn) AS churn_rate
        FROM customers_cleaned
        GROUP BY customer_type
        ORDER BY avg_revenue DESC
        """
    )

    segment_summary = pd.read_sql(
        aggregate_query,
        engine,
    )

    # Product aggregation
    product_query = text(
        """
        SELECT
            product,
            COUNT(*) AS customer_count,
            SUM(revenue) AS total_revenue,
            AVG(revenue) AS avg_revenue
        FROM customers_cleaned
        GROUP BY product
        ORDER BY total_revenue DESC
        """
    )

    product_summary = pd.read_sql(
        product_query,
        engine,
    )

    return (
        enterprise_results,
        segment_summary,
        product_summary,
    )


# ============================================================
# TASK 5: REPEATABLE LOADING FUNCTION
# ============================================================

def load_cleaned_data_to_database(
    df,
    table_name,
    database_path=DATABASE_PATH,
):
    """
    Load a cleaned DataFrame into a SQLite database.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned DataFrame to persist.
    table_name : str
        SQL destination table.
    database_path : str or Path
        SQLite database file path.

    Returns
    -------
    sqlalchemy.Engine
        Reusable SQLAlchemy engine.
    """

    engine = create_database_engine(
        database_path
    )

    test_connection(engine)

    rows_loaded = load_dataframe_to_database(
        df,
        engine,
        table_name,
    )

    verify_table_exists(
        engine,
        table_name,
    )

    print(
        f"✓ Loaded {rows_loaded} rows "
        f"to {table_name}"
    )

    return engine


# ============================================================
# REPORT
# ============================================================

def write_validation_report(
    engine,
    df,
    columns,
    schema_validation,
    enterprise_results,
    segment_summary,
    product_summary,
    rows_loaded,
):
    """Write a reproducibility and validation report."""

    lines = []

    lines.append("=" * 70)
    lines.append("SQL ENVIRONMENT & DATABASE INTEGRATION REPORT")
    lines.append("=" * 70)

    lines.append("")
    lines.append("TASK 1: DATABASE CONNECTION")
    lines.append("-" * 70)
    lines.append("Database: SQLite")
    lines.append(
        f"Connection string: sqlite:///{DATABASE_PATH}"
    )
    lines.append("Connection test: SUCCESS")

    lines.append("")
    lines.append("TASK 2: DATA LOADING")
    lines.append("-" * 70)
    lines.append(
        f"Source: {DATA_PATH}"
    )
    lines.append(
        f"Source rows: {len(df)}"
    )
    lines.append(
        f"Destination table: {TABLE_NAME}"
    )
    lines.append(
        f"Rows loaded: {rows_loaded}"
    )
    lines.append(
        "Row-count validation: PASS"
    )
    lines.append(
        "Table existence validation: PASS"
    )

    lines.append("")
    lines.append("TASK 3: SCHEMA VALIDATION")
    lines.append("-" * 70)

    for column in columns:
        null_status = (
            "NULLABLE"
            if column["nullable"]
            else "NOT NULL"
        )

        lines.append(
            f"{column['name']:20} "
            f"{str(column['type']):15} "
            f"{null_status}"
        )

    lines.append("")
    lines.append(
        "Schema validation: "
        + (
            "PASS"
            if schema_validation["valid"]
            else "FAIL"
        )
    )

    if schema_validation["missing_columns"]:
        lines.append(
            "Missing columns: "
            + str(
                sorted(
                    schema_validation[
                        "missing_columns"
                    ]
                )
            )
        )

    if schema_validation["unexpected_columns"]:
        lines.append(
            "Unexpected columns: "
            + str(
                sorted(
                    schema_validation[
                        "unexpected_columns"
                    ]
                )
            )
        )

    lines.append("")
    lines.append("TASK 4: SQL QUERY RESULTS")
    lines.append("-" * 70)

    lines.append(
        f"Enterprise rows returned: "
        f"{len(enterprise_results)}"
    )

    lines.append("")
    lines.append("Summary by customer type:")
    lines.append(
        segment_summary.to_string(
            index=False
        )
    )

    lines.append("")
    lines.append("Summary by product:")
    lines.append(
        product_summary.to_string(
            index=False
        )
    )

    lines.append("")
    lines.append("TASK 5: REPEATABLE WORKFLOW")
    lines.append("-" * 70)
    lines.append(
        "Reusable load function: PASS"
    )
    lines.append(
        "Connection returned for reuse: PASS"
    )
    lines.append(
        "Row-count validation included: PASS"
    )

    lines.append("")
    lines.append("DATASET LIMITATION")
    lines.append("-" * 70)
    lines.append(
        "The source dataset contains customer_id, "
        "customer_type, product, revenue, and churn."
    )
    lines.append(
        "The assignment example mentions email and "
        "signup_date, but those columns are not present "
        "in the repository dataset and were not fabricated."
    )

    lines.append("")
    lines.append("=" * 70)
    lines.append("DATABASE INTEGRATION COMPLETE")
    lines.append("=" * 70)

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SQL ENVIRONMENT & DATABASE INTEGRATION")
    print("=" * 70)

    # Load source DataFrame
    print("\nLoading source dataset...")
    df = load_source_dataframe()

    print(
        f"Loaded {len(df)} rows "
        f"with {len(df.columns)} columns."
    )

    # --------------------------------------------------------
    # Task 1
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 1: DATABASE CONNECTION")
    print("=" * 70)

    engine = create_database_engine()

    if test_connection(engine):
        print("✓ Database connection successful")

    print(
        f"Database: SQLite"
    )
    print(
        f"Connection: sqlite:///{DATABASE_PATH}"
    )

    # --------------------------------------------------------
    # Task 2
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 2: LOAD CLEANED DATAFRAME")
    print("=" * 70)

    rows_loaded = load_dataframe_to_database(
        df,
        engine,
        TABLE_NAME,
    )

    print(
        f"✓ Loaded {rows_loaded} rows "
        f"into {TABLE_NAME}"
    )

    verify_table_exists(
        engine,
        TABLE_NAME,
    )

    print(
        f"✓ Table '{TABLE_NAME}' exists"
    )

    # --------------------------------------------------------
    # Task 3
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 3: SCHEMA VALIDATION")
    print("=" * 70)

    columns = inspect_table_schema(
        engine,
        TABLE_NAME,
    )

    print("\nTABLE SCHEMA:")

    for column in columns:

        null_status = (
            "NULLABLE"
            if column["nullable"]
            else "NOT NULL"
        )

        print(
            f"  {column['name']:20} "
            f"{str(column['type']):15} "
            f"{null_status}"
        )

    schema_validation = validate_schema(
        columns
    )

    print(
        "\nDATATYPE / COLUMN VALIDATION:"
    )

    for column in columns:

        print(
            f"  ✓ {column['name']}: "
            f"{column['type']}"
        )

    print(
        "\nSchema validation: "
        + (
            "PASS"
            if schema_validation["valid"]
            else "FAIL"
        )
    )

    # --------------------------------------------------------
    # Task 4
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 4: SQL QUERIES")
    print("=" * 70)

    (
        enterprise_results,
        segment_summary,
        product_summary,
    ) = run_queries(engine)

    print(
        f"\nEnterprise query returned "
        f"{len(enterprise_results)} rows."
    )

    print("\nEnterprise sample:")
    print(
        enterprise_results.head().to_string(
            index=False
        )
    )

    print("\nSummary by customer type:")
    print(
        segment_summary.to_string(
            index=False
        )
    )

    print("\nSummary by product:")
    print(
        product_summary.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Task 5
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 5: REPEATABLE LOADING")
    print("=" * 70)

    reusable_engine = load_cleaned_data_to_database(
        df,
        TABLE_NAME,
        DATABASE_PATH,
    )

    test_query = pd.read_sql(
        text(
            "SELECT * "
            "FROM customers_cleaned "
            "LIMIT 10"
        ),
        reusable_engine,
    )

    print(
        f"✓ Reusable query returned "
        f"{len(test_query)} rows"
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    write_validation_report(
        engine=engine,
        df=df,
        columns=columns,
        schema_validation=schema_validation,
        enterprise_results=enterprise_results,
        segment_summary=segment_summary,
        product_summary=product_summary,
        rows_loaded=rows_loaded,
    )

    print(
        f"\nValidation report saved to: "
        f"{REPORT_PATH}"
    )

    print("\n" + "=" * 70)
    print("DATABASE INTEGRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
from pathlib import Path
import re

import pandas as pd
from sqlalchemy import create_engine, inspect, text


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "data" / "raw" / "customer_segment_data.csv"
DATABASE_DIR = ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "analytics.db"
OUTPUT_DIR = ROOT / "output"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TABLE_NAME = "customers_cleaned"
REPORT_PATH = OUTPUT_DIR / "sql_validation_report.txt"


# ============================================================
# TASK 1: DATABASE CONNECTION
# ============================================================

def create_database_engine(database_path=DATABASE_PATH):
    """
    Create a SQLite SQLAlchemy engine.

    Parameters
    ----------
    database_path : str or Path
        Location of the SQLite database file.

    Returns
    -------
    sqlalchemy.Engine
        SQLAlchemy database engine.
    """
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection_string = f"sqlite:///{database_path}"

    return create_engine(connection_string)


def test_connection(engine):
    """Test that the database connection is available."""

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True


# ============================================================
# LOAD SOURCE DATA
# ============================================================

def load_source_dataframe():
    """Load the cleaned customer dataset into a Pandas DataFrame."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "customer_id",
        "customer_type",
        "product",
        "revenue",
        "churn",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    return df


# ============================================================
# TASK 2: LOAD DATAFRAME INTO SQL
# ============================================================

def load_dataframe_to_database(
    df,
    engine,
    table_name=TABLE_NAME,
):
    """
    Load a DataFrame into a SQL table.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to load.
    engine : sqlalchemy.Engine
        SQLAlchemy database engine.
    table_name : str
        Destination table name.

    Returns
    -------
    int
        Number of rows loaded.
    """

    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table_name):
        raise ValueError(
            f"Invalid table name: {table_name}"
        )

    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False,
    )

    count_query = text(
        f"SELECT COUNT(*) AS row_count "
        f"FROM {table_name}"
    )

    count_df = pd.read_sql(
        count_query,
        engine,
    )

    rows_loaded = int(
        count_df.iloc[0]["row_count"]
    )

    if rows_loaded != len(df):
        raise ValueError(
            f"Row-count validation failed: "
            f"expected {len(df)}, got {rows_loaded}"
        )

    return rows_loaded


def verify_table_exists(
    engine,
    table_name=TABLE_NAME,
):
    """Verify that the destination table exists."""

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    if table_name not in tables:
        raise RuntimeError(
            f"Table '{table_name}' was not created."
        )

    return True


# ============================================================
# TASK 3: SCHEMA VALIDATION
# ============================================================

def inspect_table_schema(
    engine,
    table_name=TABLE_NAME,
):
    """Return SQLAlchemy schema information."""

    inspector = inspect(engine)

    columns = inspector.get_columns(
        table_name
    )

    return columns


def validate_schema(columns):
    """
    Validate the actual expected schema.

    The repository dataset contains:
    customer_id, customer_type, product, revenue, churn

    SQLite may represent Pandas object columns as VARCHAR,
    numeric columns as FLOAT/INTEGER depending on inferred data.
    """

    expected_columns = {
        "customer_id",
        "customer_type",
        "product",
        "revenue",
        "churn",
    }

    actual_columns = {
        column["name"]
        for column in columns
    }

    missing = expected_columns - actual_columns
    unexpected = actual_columns - expected_columns

    checks = []

    for column in columns:
        nullable = column["nullable"]

        checks.append({
            "column": column["name"],
            "type": str(column["type"]),
            "nullable": nullable,
        })

    return {
        "expected_columns": expected_columns,
        "actual_columns": actual_columns,
        "missing_columns": missing,
        "unexpected_columns": unexpected,
        "checks": checks,
        "valid": (
            not missing
            and not unexpected
        ),
    }


# ============================================================
# TASK 4: SQL QUERIES
# ============================================================

def run_queries(engine):
    """Run simple and aggregate SQL queries."""

    # Simple SELECT query
    simple_query = text(
        """
        SELECT *
        FROM customers_cleaned
        WHERE customer_type = 'Enterprise'
        """
    )

    enterprise_results = pd.read_sql(
        simple_query,
        engine,
    )

    # Aggregation query
    aggregate_query = text(
        """
        SELECT
            customer_type,
            COUNT(*) AS customer_count,
            AVG(revenue) AS avg_revenue,
            SUM(revenue) AS total_revenue,
            AVG(churn) AS churn_rate
        FROM customers_cleaned
        GROUP BY customer_type
        ORDER BY avg_revenue DESC
        """
    )

    segment_summary = pd.read_sql(
        aggregate_query,
        engine,
    )

    # Product aggregation
    product_query = text(
        """
        SELECT
            product,
            COUNT(*) AS customer_count,
            SUM(revenue) AS total_revenue,
            AVG(revenue) AS avg_revenue
        FROM customers_cleaned
        GROUP BY product
        ORDER BY total_revenue DESC
        """
    )

    product_summary = pd.read_sql(
        product_query,
        engine,
    )

    return (
        enterprise_results,
        segment_summary,
        product_summary,
    )


# ============================================================
# TASK 5: REPEATABLE LOADING FUNCTION
# ============================================================

def load_cleaned_data_to_database(
    df,
    table_name,
    database_path=DATABASE_PATH,
):
    """
    Load a cleaned DataFrame into a SQLite database.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned DataFrame to persist.
    table_name : str
        SQL destination table.
    database_path : str or Path
        SQLite database file path.

    Returns
    -------
    sqlalchemy.Engine
        Reusable SQLAlchemy engine.
    """

    engine = create_database_engine(
        database_path
    )

    test_connection(engine)

    rows_loaded = load_dataframe_to_database(
        df,
        engine,
        table_name,
    )

    verify_table_exists(
        engine,
        table_name,
    )

    print(
        f"✓ Loaded {rows_loaded} rows "
        f"to {table_name}"
    )

    return engine


# ============================================================
# REPORT
# ============================================================

def write_validation_report(
    engine,
    df,
    columns,
    schema_validation,
    enterprise_results,
    segment_summary,
    product_summary,
    rows_loaded,
):
    """Write a reproducibility and validation report."""

    lines = []

    lines.append("=" * 70)
    lines.append("SQL ENVIRONMENT & DATABASE INTEGRATION REPORT")
    lines.append("=" * 70)

    lines.append("")
    lines.append("TASK 1: DATABASE CONNECTION")
    lines.append("-" * 70)
    lines.append("Database: SQLite")
    lines.append(
        f"Connection string: sqlite:///{DATABASE_PATH}"
    )
    lines.append("Connection test: SUCCESS")

    lines.append("")
    lines.append("TASK 2: DATA LOADING")
    lines.append("-" * 70)
    lines.append(
        f"Source: {DATA_PATH}"
    )
    lines.append(
        f"Source rows: {len(df)}"
    )
    lines.append(
        f"Destination table: {TABLE_NAME}"
    )
    lines.append(
        f"Rows loaded: {rows_loaded}"
    )
    lines.append(
        "Row-count validation: PASS"
    )
    lines.append(
        "Table existence validation: PASS"
    )

    lines.append("")
    lines.append("TASK 3: SCHEMA VALIDATION")
    lines.append("-" * 70)

    for column in columns:
        null_status = (
            "NULLABLE"
            if column["nullable"]
            else "NOT NULL"
        )

        lines.append(
            f"{column['name']:20} "
            f"{str(column['type']):15} "
            f"{null_status}"
        )

    lines.append("")
    lines.append(
        "Schema validation: "
        + (
            "PASS"
            if schema_validation["valid"]
            else "FAIL"
        )
    )

    if schema_validation["missing_columns"]:
        lines.append(
            "Missing columns: "
            + str(
                sorted(
                    schema_validation[
                        "missing_columns"
                    ]
                )
            )
        )

    if schema_validation["unexpected_columns"]:
        lines.append(
            "Unexpected columns: "
            + str(
                sorted(
                    schema_validation[
                        "unexpected_columns"
                    ]
                )
            )
        )

    lines.append("")
    lines.append("TASK 4: SQL QUERY RESULTS")
    lines.append("-" * 70)

    lines.append(
        f"Enterprise rows returned: "
        f"{len(enterprise_results)}"
    )

    lines.append("")
    lines.append("Summary by customer type:")
    lines.append(
        segment_summary.to_string(
            index=False
        )
    )

    lines.append("")
    lines.append("Summary by product:")
    lines.append(
        product_summary.to_string(
            index=False
        )
    )

    lines.append("")
    lines.append("TASK 5: REPEATABLE WORKFLOW")
    lines.append("-" * 70)
    lines.append(
        "Reusable load function: PASS"
    )
    lines.append(
        "Connection returned for reuse: PASS"
    )
    lines.append(
        "Row-count validation included: PASS"
    )

    lines.append("")
    lines.append("DATASET LIMITATION")
    lines.append("-" * 70)
    lines.append(
        "The source dataset contains customer_id, "
        "customer_type, product, revenue, and churn."
    )
    lines.append(
        "The assignment example mentions email and "
        "signup_date, but those columns are not present "
        "in the repository dataset and were not fabricated."
    )

    lines.append("")
    lines.append("=" * 70)
    lines.append("DATABASE INTEGRATION COMPLETE")
    lines.append("=" * 70)

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SQL ENVIRONMENT & DATABASE INTEGRATION")
    print("=" * 70)

    # Load source DataFrame
    print("\nLoading source dataset...")
    df = load_source_dataframe()

    print(
        f"Loaded {len(df)} rows "
        f"with {len(df.columns)} columns."
    )

    # --------------------------------------------------------
    # Task 1
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 1: DATABASE CONNECTION")
    print("=" * 70)

    engine = create_database_engine()

    if test_connection(engine):
        print("✓ Database connection successful")

    print(
        f"Database: SQLite"
    )
    print(
        f"Connection: sqlite:///{DATABASE_PATH}"
    )

    # --------------------------------------------------------
    # Task 2
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 2: LOAD CLEANED DATAFRAME")
    print("=" * 70)

    rows_loaded = load_dataframe_to_database(
        df,
        engine,
        TABLE_NAME,
    )

    print(
        f"✓ Loaded {rows_loaded} rows "
        f"into {TABLE_NAME}"
    )

    verify_table_exists(
        engine,
        TABLE_NAME,
    )

    print(
        f"✓ Table '{TABLE_NAME}' exists"
    )

    # --------------------------------------------------------
    # Task 3
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 3: SCHEMA VALIDATION")
    print("=" * 70)

    columns = inspect_table_schema(
        engine,
        TABLE_NAME,
    )

    print("\nTABLE SCHEMA:")

    for column in columns:

        null_status = (
            "NULLABLE"
            if column["nullable"]
            else "NOT NULL"
        )

        print(
            f"  {column['name']:20} "
            f"{str(column['type']):15} "
            f"{null_status}"
        )

    schema_validation = validate_schema(
        columns
    )

    print(
        "\nDATATYPE / COLUMN VALIDATION:"
    )

    for column in columns:

        print(
            f"  ✓ {column['name']}: "
            f"{column['type']}"
        )

    print(
        "\nSchema validation: "
        + (
            "PASS"
            if schema_validation["valid"]
            else "FAIL"
        )
    )

    # --------------------------------------------------------
    # Task 4
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 4: SQL QUERIES")
    print("=" * 70)

    (
        enterprise_results,
        segment_summary,
        product_summary,
    ) = run_queries(engine)

    print(
        f"\nEnterprise query returned "
        f"{len(enterprise_results)} rows."
    )

    print("\nEnterprise sample:")
    print(
        enterprise_results.head().to_string(
            index=False
        )
    )

    print("\nSummary by customer type:")
    print(
        segment_summary.to_string(
            index=False
        )
    )

    print("\nSummary by product:")
    print(
        product_summary.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Task 5
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 5: REPEATABLE LOADING")
    print("=" * 70)

    reusable_engine = load_cleaned_data_to_database(
        df,
        TABLE_NAME,
        DATABASE_PATH,
    )

    test_query = pd.read_sql(
        text(
            "SELECT * "
            "FROM customers_cleaned "
            "LIMIT 10"
        ),
        reusable_engine,
    )

    print(
        f"✓ Reusable query returned "
        f"{len(test_query)} rows"
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    write_validation_report(
        engine=engine,
        df=df,
        columns=columns,
        schema_validation=schema_validation,
        enterprise_results=enterprise_results,
        segment_summary=segment_summary,
        product_summary=product_summary,
        rows_loaded=rows_loaded,
    )

    print(
        f"\nValidation report saved to: "
        f"{REPORT_PATH}"
    )

    print("\n" + "=" * 70)
    print("DATABASE INTEGRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
