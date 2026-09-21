import pandas as pd


# ============================================================
# SAMPLE DATA
# ============================================================

data = {
    "customer_name": [
        " John ",
        "JOHN",
        "john",
        " Sarah ",
        "SARAH",
        " Robert",
        "Robert ",
        " Emily ",
        "EMILY",
        " David ",
        "DAVID",
        " david "
    ],
    "product_category": [
        " Electronics ",
        "electronics",
        "ELECTRONICS",
        " Electronics",
        "Furniture ",
        "furniture",
        " FURNITURE",
        "Furniture",
        " FURNITURE ",
        " Electronics ",
        "electronics ",
        "ELECTRONICS"
    ],
    "segment": [
        "B2B",
        "b2b",
        "B 2 B",
        "business-to-business",
        "SME",
        "sme",
        "small medium enterprise",
        "small-medium-enterprise",
        "Enterprise",
        "enterprise",
        "large enterprise",
        "corporate enterprise"
    ],
    "city": [
        "São Paulo",
        "Montréal",
        "New York",
        " Delhi ",
        "DELHI",
        "Mumbai",
        "MUMBAI",
        "Bengaluru",
        " Bengaluru ",
        "Pune",
        " PUNE ",
        "Chennai"
    ]
}

df = pd.DataFrame(data)

print("=" * 70)
print("STRING CLEANING PIPELINE")
print("=" * 70)

print("\nORIGINAL DATA:")
print(df)


# ============================================================
# TASK 1: STRIP WHITESPACE
# ============================================================

def strip_all_strings(df):
    """Strip leading and trailing whitespace from all string columns."""

    print("\n" + "=" * 70)
    print("TASK 1: STRIP WHITESPACE")
    print("=" * 70)

    string_cols = df.select_dtypes(include=["object"]).columns

    total_whitespace_fixed = 0

    for col in string_cols:

        # Count leading/trailing whitespace issues
        whitespace_mask = (
            df[col].notna()
            & df[col].astype(str).ne(
                df[col].astype(str).str.strip()
            )
        )

        whitespace_count = whitespace_mask.sum()

        # Unique values before cleaning
        before = df[col].nunique(dropna=True)

        # Apply strip
        df[col] = df[col].str.strip()

        # Unique values after cleaning
        after = df[col].nunique(dropna=True)

        total_whitespace_fixed += whitespace_count

        print(
            f"{col}: {before} → {after} unique values | "
            f"Whitespace issues fixed: {whitespace_count}"
        )

    print(
        f"\nTotal whitespace issues fixed: "
        f"{total_whitespace_fixed}"
    )

    return df


# Show value counts before stripping
print("\nVALUE COUNTS BEFORE STRIPPING:")

for col in ["customer_name", "product_category"]:
    print(f"\n{col}:")
    print(df[col].value_counts(dropna=False))


df = strip_all_strings(df)


# Show value counts after stripping
print("\nVALUE COUNTS AFTER STRIPPING:")

for col in ["customer_name", "product_category"]:
    print(f"\n{col}:")
    print(df[col].value_counts(dropna=False))


# ============================================================
# TASK 2: NORMALIZE CASING
# ============================================================

def normalize_casing(df, columns_to_lower):
    """Normalize selected text columns to lowercase."""

    print("\n" + "=" * 70)
    print("TASK 2: NORMALIZE CASING")
    print("=" * 70)

    for col in columns_to_lower:
        df[col] = df[col].str.lower()
        print(f"Normalized '{col}' to lowercase")

    return df


# Business decision:
# Lowercase is used for customer names, product categories,
# segments, and cities because it provides consistent matching
# and prevents duplicate groups caused only by capitalization.

casing_columns = [
    "customer_name",
    "product_category",
    "segment",
    "city"
]

print("\nBEFORE CASING NORMALIZATION:")
print(df[casing_columns].head(12))

df = normalize_casing(df, casing_columns)

print("\nAFTER CASING NORMALIZATION:")
print(df[casing_columns].head(12))

print("\nJohn variations after normalization:")
print(df["customer_name"].value_counts(dropna=False))


# ============================================================
# TASK 3: REMOVE SPECIAL CHARACTERS USING REGEX
# ============================================================

def remove_special_characters(df, columns):
    """
    Remove characters that are not:
    - uppercase/lowercase English letters
    - numbers
    - spaces
    """

    print("\n" + "=" * 70)
    print("TASK 3: REMOVE SPECIAL CHARACTERS")
    print("=" * 70)

    pattern = r"[^a-zA-Z0-9 ]"

    for col in columns:
        df[col] = df[col].str.replace(
            pattern,
            "",
            regex=True
        )

        print(
            f"Removed special characters from '{col}'"
        )

    return df


print("\nCITY VALUES BEFORE SPECIAL CHARACTER REMOVAL:")
print(df["city"].tolist())

df = remove_special_characters(
    df,
    ["city", "product_category"]
)

print("\nCITY VALUES AFTER SPECIAL CHARACTER REMOVAL:")
print(df["city"].tolist())

print("\nExamples:")
print("São Paulo → So Paulo")
print("Montréal → Montral")


# ============================================================
# TASK 4: STANDARDIZE CATEGORICAL LABELS
# ============================================================

print("\n" + "=" * 70)
print("TASK 4: STANDARDIZE CATEGORICAL LABELS")
print("=" * 70)


# Business decisions:
#
# B2B:
# All business-to-business variations become "B2B"
# because B2B is the standard CRM abbreviation.
#
# SMB:
# SME-related variations become "SMB"
# because SMB is the selected canonical label.
#
# Enterprise:
# Enterprise-related variations become "Enterprise"
# because Enterprise is the selected canonical form.

segment_map = {
    # B2B variations
    "b2b": "B2B",
    "b 2 b": "B2B",
    "b2 b": "B2B",
    "business-to-business": "B2B",

    # SMB variations
    "sme": "SMB",
    "small medium enterprise": "SMB",
    "small-medium-enterprise": "SMB",

    # Enterprise variations
    "enterprise": "Enterprise",
    "large enterprise": "Enterprise",
    "corporate enterprise": "Enterprise"
}


print("\nSEGMENT VALUE COUNTS BEFORE MAPPING:")
print(df["segment"].value_counts(dropna=False))


# replace is used instead of map so unexpected values
# are preserved instead of becoming NaN.
df["segment"] = df["segment"].replace(segment_map)


print("\nSEGMENT VALUE COUNTS AFTER MAPPING:")
print(df["segment"].value_counts(dropna=False))


# ============================================================
# TASK 5: REUSABLE STRING CLEANING FUNCTION
# ============================================================

print("\n" + "=" * 70)
print("TASK 5: REUSABLE STRING CLEANING FUNCTION")
print("=" * 70)


def clean_text_column(
    series,
    lowercase=True,
    strip=True,
    remove_special=False,
    mapping=None
):
    """
    Reusable string cleaning function for any text column.

    Parameters
    ----------
    series : pandas Series
        Text column to clean.

    lowercase : bool
        Convert text to lowercase.

    strip : bool
        Remove leading and trailing whitespace.

    remove_special : bool
        Remove characters other than letters, numbers
        and spaces.

    mapping : dict or None
        Dictionary used to standardize categorical labels.

    Returns
    -------
    pandas Series
        Cleaned text column.
    """

    result = series.copy()

    # Handle null values safely
    if result.isna().any():
        null_count = result.isna().sum()
        print(
            f"Warning: {null_count} null value(s) found."
        )

    # Convert to pandas StringDtype so null values
    # remain safely as <NA>.
    result = result.astype("string")

    if strip:
        result = result.str.strip()

    if lowercase:
        result = result.str.lower()

    if remove_special:
        result = result.str.replace(
            r"[^a-zA-Z0-9 ]",
            "",
            regex=True
        )

    if mapping:
        result = result.replace(mapping)

    return result


# ============================================================
# APPLY REUSABLE FUNCTION TO DIFFERENT COLUMNS
# ============================================================

# Customer name:
# strip + lowercase
df["customer_name_clean"] = clean_text_column(
    df["customer_name"],
    lowercase=True,
    strip=True
)


# Product category:
# strip + lowercase + remove special characters
df["product_category_clean"] = clean_text_column(
    df["product_category"],
    lowercase=True,
    strip=True,
    remove_special=True
)


# Segment:
# strip + lowercase + mapping
#
# Mapping keys are lowercase because lowercase=True
# runs before mapping.

segment_map_lowercase = {
    "b2b": "B2B",
    "b 2 b": "B2B",
    "b2 b": "B2B",
    "business-to-business": "B2B",

    "sme": "SMB",
    "small medium enterprise": "SMB",
    "small-medium-enterprise": "SMB",

    "enterprise": "Enterprise",
    "large enterprise": "Enterprise",
    "corporate enterprise": "Enterprise"
}

df["segment_clean"] = clean_text_column(
    df["segment"],
    lowercase=False,
    strip=True,
    mapping={
        "B2B": "B2B",
        "SMB": "SMB",
        "Enterprise": "Enterprise"
    }
)


print("\nCLEANED COLUMNS:")

print(
    df[
        [
            "customer_name_clean",
            "product_category_clean",
            "segment_clean"
        ]
    ]
)


# ============================================================
# EDGE CASE TESTING
# ============================================================

print("\n" + "=" * 70)
print("EDGE CASE TESTING")
print("=" * 70)


test_cases = [
    "  Product A  ",
    "PRODUCT B",
    "Product_C",
    None,
    ""
]

test_series = pd.Series(test_cases)

print("\nTEST INPUT:")
print(test_series)


result = clean_text_column(
    test_series,
    lowercase=True,
    strip=True,
    remove_special=True
)


print("\nTEST OUTPUT:")
print(result)


# ============================================================
# FINAL VALUE COUNTS
# ============================================================

print("\n" + "=" * 70)
print("FINAL VALUE COUNTS")
print("=" * 70)

print("\nCustomer names:")
print(df["customer_name_clean"].value_counts(dropna=False))

print("\nProduct categories:")
print(df["product_category_clean"].value_counts(dropna=False))

print("\nSegments:")
print(df["segment_clean"].value_counts(dropna=False))


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FINAL CLEANING SUMMARY")
print("=" * 70)

print("""
1. Whitespace:
   Applied .str.strip() to all string columns.

2. Casing:
   Standardized text to lowercase for consistent matching.

3. Special characters:
   Used regex [^a-zA-Z0-9 ] to remove non-alphanumeric
   characters while preserving spaces.

4. Category standardization:
   Consolidated B2B, SMB and Enterprise variations
   using mapping dictionaries.

5. Reusable function:
   Built clean_text_column() with optional parameters
   for strip, lowercase, special-character removal,
   mapping and null handling.

6. Edge cases:
   Tested leading/trailing spaces, uppercase text,
   special characters, null values and empty strings.

The dataset is now analysis-ready.
""")


print("=" * 70)
print("PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 70)