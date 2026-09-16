import pandas as pd
from pathlib import Path

output_path = Path("data/raw/recruitment_data.xlsx")

candidates = pd.DataFrame({
    "candidate_id": [1, 2, 3],
    "name": ["Alice", "Bob", "Carol"],
    "department": ["Engineering", "Marketing", "Engineering"]
})

interviews = pd.DataFrame({
    "interview_id": [101, 102, 103],
    "candidate_id": [1, 2, 3],
    "status": ["Passed", "Rejected", "Passed"]
})

onboarding = pd.DataFrame({
    "candidate_id": [1, 3],
    "onboarding_status": ["Completed", "In Progress"]
})

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    candidates.to_excel(writer, sheet_name="Candidates", index=False)
    interviews.to_excel(writer, sheet_name="Interviews", index=False)
    onboarding.to_excel(writer, sheet_name="Onboarding", index=False)

print(f"✓ Excel sample created: {output_path}")