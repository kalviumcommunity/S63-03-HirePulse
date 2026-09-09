"""Project paths and validation constants."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

DATA_FILES = {
    "candidates": DATA_DIR / "candidates.csv",
    "stages": DATA_DIR / "recruitment_stages.csv",
    "interviews": DATA_DIR / "interviews.csv",
    "offers": DATA_DIR / "offers.csv",
    "onboarding": DATA_DIR / "onboarding.csv",
}

VALID_DEPARTMENTS = {
    "Engineering",
    "Data Analytics",
    "Product",
    "Marketing",
    "Sales",
    "Human Resources",
    "Finance",
    "Operations",
}
VALID_STAGE_NAMES = {
    "Applied",
    "Screening",
    "Technical Interview",
    "HR Interview",
    "Offer Sent",
    "Joined",
}
VALID_STAGE_STATUSES = {"Completed", "In Progress", "Dropped", "Pending"}
VALID_ONBOARDING_STATUSES = {"Not Started", "In Progress", "Completed"}
