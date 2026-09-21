"""Duplicate detection, record deduplication, and audit logging module."""

from datetime import datetime
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


def detect_exact_duplicates(df: pd.DataFrame) -> tuple[int, pd.DataFrame]:
    """Find rows where all values are identical.

    Returns: Tuple of (count, duplicate_rows_dataframe)
    """
    exact_dups = int(df.duplicated().sum())
    dup_rows = df[df.duplicated(keep=False)].sort_values(by=df.columns.tolist())

    print("\nEXACT DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Exact duplicates found: {exact_dups}")
    print(f"Total duplicate rows (including originals): {len(dup_rows)}")

    if len(dup_rows) > 0:
        print("\nSample duplicate rows:")
        print(dup_rows.head(10).to_string())

    return exact_dups, dup_rows


def detect_near_duplicates(df: pd.DataFrame, key_columns: list[str]) -> pd.DataFrame:
    """Find rows with same key values but different other fields.

    Args:
        df: Input DataFrame
        key_columns: Columns defining uniqueness (e.g., ['customer_id', 'date'])

    Returns:
        DataFrame showing near-duplicates grouped by key
    """
    duplicate_keys = df[df.duplicated(subset=key_columns, keep=False)]

    print("\nNEAR-DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Records with duplicate keys: {len(duplicate_keys)}")
    unique_groups = len(duplicate_keys.groupby(key_columns)) if len(duplicate_keys) > 0 else 0
    print(f"Unique key combinations with duplicates: {unique_groups}")

    if len(duplicate_keys) > 0:
        print("\nSample groups with duplicate keys:")
        groups = list(duplicate_keys.groupby(key_columns))[:3]
        for keys, group in groups:
            print(f"\n  Key: {keys}")
            print(f"  Records in group: {len(group)}")
            print(group.to_string())

    return duplicate_keys


def remove_exact_duplicates(df: pd.DataFrame, keep: str | bool = 'first') -> pd.DataFrame:
    """Remove exact duplicates, choosing which record to keep.

    Args:
        df: Input DataFrame
        keep: 'first' (keep oldest), 'last' (keep newest), or False (remove all)

    Returns:
        Deduplicated DataFrame with row counts documented
    """
    rows_before = len(df)

    df_dedup = df.drop_duplicates(keep=keep)

    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after
    removal_pct = (rows_removed / rows_before) * 100 if rows_before > 0 else 0.0

    print("\nEXACT DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {rows_after:,}")
    print(f"Rows removed: {rows_removed:,} ({removal_pct:.2f}%)")

    return df_dedup


def remove_near_duplicates(df: pd.DataFrame, key_columns: list[str], keep_strategy: str = 'most_complete') -> pd.DataFrame:
    """Remove near-duplicates by choosing best record.

    Args:
        df: Input DataFrame
        key_columns: Columns defining uniqueness
        keep_strategy: 'most_complete' (fewest nulls), 'first', 'last'

    Returns:
        Deduplicated DataFrame
    """
    rows_before = len(df)

    if keep_strategy == 'most_complete':
        if len(df) > 0:
            indices_to_keep = []
            for _, group in df.groupby(key_columns):
                null_counts = group.isnull().sum(axis=1)
                best_idx = null_counts.idxmin()
                indices_to_keep.append(best_idx)
            df_dedup = df.loc[indices_to_keep]
        else:
            df_dedup = df.copy()

    elif keep_strategy == 'last':
        df_dedup = df.drop_duplicates(subset=key_columns, keep='last')

    else:
        df_dedup = df.drop_duplicates(subset=key_columns, keep='first')

    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after
    removal_pct = (rows_removed / rows_before) * 100 if rows_before > 0 else 0.0

    print("\nNEAR-DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep_strategy}")
    print(f"Key columns: {key_columns}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {rows_after:,}")
    print(f"Rows removed: {rows_removed:,} ({removal_pct:.2f}%)")

    return df_dedup


def log_removed_duplicates(df_original: pd.DataFrame, df_dedup: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Save all removed duplicate rows to audit file for compliance.

    Returns: Audit summary tuple
    """
    removed_mask = ~df_original.index.isin(df_dedup.index)
    removed_records = df_original[removed_mask]

    print("\nAUDIT LOGGING")
    print("=" * 60)
    print(f"Total records removed: {len(removed_records)}")

    out_csv = Path('output/removed_duplicates_audit.csv')
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    removed_records.to_csv(out_csv, index=False)
    print("✓ Removed records saved to audit file")

    audit_summary = {
        'removal_timestamp': datetime.now().isoformat(),
        'total_removed': int(len(removed_records)),
        'reason': 'Duplicate detection and deduplication',
        'audit_file': 'output/removed_duplicates_audit.csv',
        'audit_note': 'All removed records logged for compliance and recovery if needed'
    }

    out_json = Path('output/dedup_audit_summary.json')
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(audit_summary, f, indent=2, default=str)

    print("✓ Audit summary saved")
    print("=" * 60)

    return removed_records, audit_summary


def compare_before_after(df_original: pd.DataFrame, df_dedup: pd.DataFrame) -> dict:
    """Log before/after metrics confirming deduplication worked.

    Returns: Comparison dictionary
    """
    rows_before = len(df_original)
    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after
    removal_pct = round((rows_removed / rows_before) * 100, 2) if rows_before > 0 else 0.0

    comparison = {
        'rows_before': rows_before,
        'rows_after': rows_after,
        'rows_removed': rows_removed,
        'removal_percentage': removal_pct,
        'columns': len(df_original.columns),
        'nulls_before': int(df_original.isnull().sum().sum()),
        'nulls_after': int(df_dedup.isnull().sum().sum()),
        'timestamp': datetime.now().isoformat()
    }

    print("\n" + "=" * 70)
    print("DEDUPLICATION FINAL SUMMARY")
    print("=" * 70)
    print(f"Rows before: {comparison['rows_before']:,}")
    print(f"Rows after:  {comparison['rows_after']:,}")
    print(f"Removed:     {comparison['rows_removed']:,} ({comparison['removal_percentage']}%)")
    print(f"\nNulls before: {comparison['nulls_before']:,}")
    print(f"Nulls after:  {comparison['nulls_after']:,}")
    print(f"Null change:  {comparison['nulls_before'] - comparison['nulls_after']:,}")
    print("=" * 70)

    out_json = Path('output/dedup_summary.json')
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2)

    return comparison


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    input_csv = project_root / "data" / "raw" / "data_with_dupes.csv"

    if not input_csv.exists():
        print(f"Input file not found at {input_csv}")
        sys.exit(1)

    df_original = pd.read_csv(input_csv)
    df = df_original.copy()

    print("\n" + "=" * 70)
    print("STARTING DEDUPLICATION WORKFLOW")
    print("=" * 70)
    print(f"Initial record count: {len(df):,}")

    # Step 1: Detect exact duplicates
    print("\n[Step 1/4] Detecting exact duplicates...")
    exact_count, exact_rows = detect_exact_duplicates(df)

    # Step 2: Detect near-duplicates
    print("\n[Step 2/4] Detecting near-duplicates by key...")
    near_dups = detect_near_duplicates(df, key_columns=['customer_id', 'transaction_date'])

    # Step 3: Remove exact duplicates
    print("\n[Step 3/4] Removing exact duplicates (keeping first)...")
    df = remove_exact_duplicates(df, keep='first')

    # Step 4: Remove near-duplicates
    print("\n[Step 4/4] Removing near-duplicates (keeping most complete)...")
    df = remove_near_duplicates(
        df,
        key_columns=['customer_id', 'transaction_date'],
        keep_strategy='most_complete'
    )

    # Log removals comparing original dataset with final deduplicated dataset
    print("\n[Audit] Logging removed records for compliance...")
    log_removed_duplicates(df_original, df)

    # Compare metrics
    compare_before_after(df_original, df)

    # Save deduplicated data
    output_csv = project_root / "data" / "processed" / "deduplicated_data.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"\n✓ Deduplicated data saved to {output_csv}")
