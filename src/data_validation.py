"""Data quality checks for recruitment source tables."""

import re
from collections.abc import Iterable

import pandas as pd

from config import VALID_DEPARTMENTS

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9 ()-]{7,20}$")

SCHEMAS = {
    "candidates": {
        "candidate_id": "string", "full_name": "string", "email": "string",
        "phone": "string", "department": "string", "applied_date": "datetime",
    },
    "stages": {
        "candidate_id": "string", "stage_name": "string", "status": "string", "stage_date": "datetime",
    },
    "interviews": {
        "candidate_id": "string", "interviewer_name": "string", "round_name": "string",
        "score": "numeric", "feedback": "string", "result": "string", "interview_date": "datetime",
    },
    "offers": {
        "candidate_id": "string", "offer_date": "datetime", "salary": "numeric", "accepted": "boolean",
    },
    "onboarding": {
        "candidate_id": "string", "joining_date": "datetime", "document_completion": "numeric",
        "onboarding_status": "string",
    },
}


def missing_value_count(frame: pd.DataFrame) -> int:
    return int(frame.isna().sum().sum())


def duplicate_count(frame: pd.DataFrame, subset: Iterable[str] | None = None) -> int:
    return int(frame.duplicated(subset=list(subset) if subset else None).sum())


def invalid_email_count(frame: pd.DataFrame) -> int:
    if "email" not in frame:
        return 0
    return int((~frame["email"].astype("string").str.match(EMAIL_PATTERN, na=False)).sum())


def invalid_phone_count(frame: pd.DataFrame) -> int:
    if "phone" not in frame:
        return 0
    return int((~frame["phone"].astype("string").str.match(PHONE_PATTERN, na=False)).sum())


def invalid_date_count(frame: pd.DataFrame, columns: Iterable[str] | None = None) -> int:
    date_columns = list(columns) if columns else [column for column in frame if column.endswith("_date")]
    return int(sum(pd.to_datetime(frame[column], errors="coerce").isna().sum() for column in date_columns if column in frame))


def data_type_errors(frame: pd.DataFrame, schema: dict[str, str]) -> int:
    errors = 0
    for column, expected in schema.items():
        if column not in frame:
            errors += len(frame)
            continue
        series = frame[column]
        if expected == "numeric":
            errors += int(pd.to_numeric(series, errors="coerce").isna().sum())
        elif expected == "datetime":
            errors += int(pd.to_datetime(series, errors="coerce").isna().sum())
        elif expected == "boolean":
            errors += int((~series.isin([True, False, 0, 1])).sum())
    return errors


def invalid_department_count(frame: pd.DataFrame) -> int:
    if "department" not in frame:
        return 0
    return int((~frame["department"].isin(VALID_DEPARTMENTS)).sum())


def collect_quality_metrics(name: str, frame: pd.DataFrame) -> dict[str, int | str]:
    """Return standardized quality metrics for one source table."""
    schema = SCHEMAS[name]
    return {
        "dataset": name,
        "total_records": len(frame),
        "missing_values": missing_value_count(frame),
        "duplicate_records": duplicate_count(frame),
        "invalid_emails": invalid_email_count(frame),
        "invalid_phones": invalid_phone_count(frame),
        "invalid_dates": invalid_date_count(frame),
        "data_type_errors": data_type_errors(frame, schema),
        "invalid_departments": invalid_department_count(frame),
    }
