"""Generate deterministic, relational sample data for the project."""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from config import DATA_DIR, VALID_DEPARTMENTS

RNG = np.random.default_rng(42)
FIRST_NAMES = ["Aisha", "Ben", "Carla", "Dinesh", "Elena", "Fatima", "Grace", "Hugo", "Iris", "Jonah"]
LAST_NAMES = ["Adams", "Bennett", "Chen", "Davis", "Evans", "Foster", "Green", "Harris", "Ibrahim", "Jones"]
DEPARTMENTS = sorted(VALID_DEPARTMENTS)


def generate_data(output_dir: Path = DATA_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    start = date(2025, 1, 6)
    candidates = []
    for index in range(100):
        first = FIRST_NAMES[index % len(FIRST_NAMES)]
        last = LAST_NAMES[(index * 3) % len(LAST_NAMES)]
        candidates.append({
            "candidate_id": f"C{index + 1:04d}",
            "full_name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}{index + 1}@example.com",
            "phone": f"+1-555-{100 + index // 100:03d}-{1000 + index:04d}",
            "department": DEPARTMENTS[index % len(DEPARTMENTS)],
            "applied_date": start + timedelta(days=int(index * 2.1)),
        })
    candidates_df = pd.DataFrame(candidates)

    stages = []
    interviews = []
    offers = []
    onboarding = []
    stage_names = ["Applied", "Screening", "Technical Interview", "HR Interview", "Offer Sent", "Joined"]
    for index, candidate in candidates_df.iterrows():
        applied = candidate["applied_date"]
        outcome = index % 10
        reached = 6 if outcome < 5 else 5 if outcome < 7 else 4 if outcome < 8 else 2 if outcome < 9 else 1
        for stage_index, stage_name in enumerate(stage_names[:reached]):
            stage_date = applied + timedelta(days=stage_index * 4 + (index % 3))
            status = "Completed"
            if stage_name == "Joined" and outcome >= 5:
                continue
            stages.append({"candidate_id": candidate["candidate_id"], "stage_name": stage_name, "status": status, "stage_date": stage_date})
        if reached >= 3:
            interviews.append({"candidate_id": candidate["candidate_id"], "interviewer_name": f"Interviewer {(index % 8) + 1}", "round_name": "Technical Interview", "score": int(65 + (index * 7) % 36), "feedback": "Strong problem-solving and communication skills.", "result": "Pass" if outcome < 8 else "Fail", "interview_date": applied + timedelta(days=9 + index % 4)})
        if outcome < 7:
            offer_date = applied + timedelta(days=20 + index % 5)
            accepted = outcome < 5
            offers.append({"candidate_id": candidate["candidate_id"], "offer_date": offer_date, "salary": int(70000 + (index % 10) * 4500), "accepted": accepted})
        if outcome < 5:
            onboarding.append({"candidate_id": candidate["candidate_id"], "joining_date": applied + timedelta(days=28 + index % 6), "document_completion": int(85 + index % 16), "onboarding_status": "Completed"})

    candidates_df.to_csv(output_dir / "candidates.csv", index=False)
    pd.DataFrame(stages).to_csv(output_dir / "recruitment_stages.csv", index=False)
    pd.DataFrame(interviews).to_csv(output_dir / "interviews.csv", index=False)
    pd.DataFrame(offers).to_csv(output_dir / "offers.csv", index=False)
    pd.DataFrame(onboarding).to_csv(output_dir / "onboarding.csv", index=False)


if __name__ == "__main__":
    generate_data()
