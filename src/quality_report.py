"""Quality report generation and CSV export."""

from pathlib import Path

import pandas as pd

from config import OUTPUTS_DIR
from data_loader import load_candidates, load_interviews, load_onboarding, load_offers, load_stages
from data_validation import collect_quality_metrics


def generate_quality_report(output_path: Path | None = None) -> pd.DataFrame:
    """Build and export a row-level quality report for every source dataset."""
    frames = {
        "candidates": load_candidates(),
        "stages": load_stages(),
        "interviews": load_interviews(),
        "offers": load_offers(),
        "onboarding": load_onboarding(),
    }
    records = []
    for name, frame in frames.items():
        metrics = collect_quality_metrics(name, frame)
        issue_count = sum(int(value) for key, value in metrics.items() if key not in {"dataset", "total_records"})
        total_checks = max(int(metrics["total_records"]) * 4, 1)
        metrics["quality_score_pct"] = round(max(0.0, 100 * (1 - issue_count / total_checks)), 2)
        records.append(metrics)

    report = pd.DataFrame(records)
    destination = output_path or OUTPUTS_DIR / "quality_report.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(destination, index=False)
    return report


if __name__ == "__main__":
    print(generate_quality_report().to_string(index=False))
