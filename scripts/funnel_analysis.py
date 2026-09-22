"""
Funnel Analysis & Drop-Off Detection
HirePulse Recruitment Funnel

Assignment Tasks:
1. Define funnel stages and count candidates
2. Calculate drop-off and completion rates
3. Visualize the funnel
4. Calculate business impact
5. Generate actionable recommendations
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/recruitment_stages.csv")
OUTPUT_DIR = Path("output")
NOTEBOOK_DIR = Path("notebooks")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. LOAD DATA
# ============================================================

print("=" * 70)
print("FUNNEL ANALYSIS & DROP-OFF DETECTION")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"\nDataset loaded: {INPUT_FILE}")
print(f"Rows: {len(df)}")
print(f"Unique candidates: {df['candidate_id'].nunique()}")


# ============================================================
# 3. VALIDATE DATA
# ============================================================

required_columns = [
    "candidate_id",
    "stage_name",
    "status",
    "stage_date",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ============================================================
# 4. DEFINE FUNNEL STAGES
# ============================================================

stage_order = [
    "Applied",
    "Screening",
    "Technical Interview",
    "HR Interview",
    "Offer Sent",
    "Joined",
]


print("\n" + "=" * 70)
print("FUNNEL STAGES")
print("=" * 70)

stages = {}

for stage in stage_order:

    count = df.loc[
        df["stage_name"] == stage,
        "candidate_id",
    ].nunique()

    stages[stage] = count

    print(f"{stage:<25} {count:>5} candidates")


# ============================================================
# 5. VALIDATE STAGE PROGRESSION
# ============================================================

stage_counts = list(stages.values())

for i in range(len(stage_counts) - 1):

    if stage_counts[i + 1] > stage_counts[i]:

        raise ValueError(
            f"Invalid funnel progression: "
            f"{stage_order[i + 1]} has more candidates than "
            f"{stage_order[i]}."
        )


# ============================================================
# 6. COMPUTE DROP-OFF METRICS
# ============================================================

print("\n" + "=" * 70)
print("DROP-OFF ANALYSIS")
print("=" * 70)

drop_off = []

for i in range(len(stage_order) - 1):

    from_stage = stage_order[i]
    to_stage = stage_order[i + 1]

    users_before = stages[from_stage]
    users_after = stages[to_stage]

    users_lost = users_before - users_after

    if users_before > 0:

        completion_rate = (
            users_after / users_before
        ) * 100

        drop_rate = (
            users_lost / users_before
        ) * 100

    else:

        completion_rate = 0
        drop_rate = 0

    drop_off.append(
        {
            "from_stage": from_stage,
            "to_stage": to_stage,
            "users_before": users_before,
            "users_after": users_after,
            "users_lost": users_lost,
            "completion_rate": completion_rate,
            "drop_rate": drop_rate,
        }
    )


funnel_df = pd.DataFrame(drop_off)


print(
    funnel_df.to_string(
        index=False,
        formatters={
            "completion_rate": "{:.1f}%".format,
            "drop_rate": "{:.1f}%".format,
        },
    )
)


# ============================================================
# 7. IDENTIFY BIGGEST DROP
# ============================================================

biggest_drop_idx = funnel_df["users_lost"].idxmax()

biggest_drop = funnel_df.loc[
    biggest_drop_idx
]

highest_drop_rate_idx = funnel_df[
    "drop_rate"
].idxmax()

highest_drop_rate = funnel_df.loc[
    highest_drop_rate_idx
]


print("\n" + "=" * 70)
print("BIGGEST FUNNEL BOTTLENECK")
print("=" * 70)

print(
    f"Biggest absolute drop: "
    f"{biggest_drop['from_stage']} -> "
    f"{biggest_drop['to_stage']}"
)

print(
    f"Users lost: "
    f"{int(biggest_drop['users_lost'])}"
)

print(
    f"Drop rate: "
    f"{biggest_drop['drop_rate']:.1f}%"
)

print(
    f"Highest drop-rate transition: "
    f"{highest_drop_rate['from_stage']} -> "
    f"{highest_drop_rate['to_stage']} "
    f"({highest_drop_rate['drop_rate']:.1f}%)"
)


# ============================================================
# 8. CALCULATE OVERALL CONVERSION
# ============================================================

starting_users = stages[stage_order[0]]
final_users = stages[stage_order[-1]]

overall_conversion = (
    final_users / starting_users
) * 100

overall_drop = 100 - overall_conversion


print("\n" + "=" * 70)
print("OVERALL FUNNEL PERFORMANCE")
print("=" * 70)

print(
    f"Starting candidates: {starting_users}"
)

print(
    f"Joined candidates: {final_users}"
)

print(
    f"Overall conversion: {overall_conversion:.1f}%"
)

print(
    f"Overall drop-off: {overall_drop:.1f}%"
)


# ============================================================
# 9. VISUALIZE FUNNEL
# ============================================================

print("\n" + "=" * 70)
print("CREATING FUNNEL VISUALIZATION")
print("=" * 70)

fig, ax = plt.subplots(
    figsize=(12, 7)
)

bars = ax.bar(
    stage_order,
    stage_counts,
)

ax.set_ylabel(
    "Candidates",
    fontsize=12,
)

ax.set_xlabel(
    "Recruitment Stage",
    fontsize=12,
)

ax.set_title(
    "Recruitment Funnel: Candidate Volume by Stage",
    fontsize=14,
    fontweight="bold",
)

ax.set_ylim(
    0,
    max(stage_counts) * 1.15,
)

# Annotate candidate counts
for bar, count in zip(bars, stage_counts):

    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        str(count),
        ha="center",
        va="bottom",
        fontweight="bold",
    )


plt.xticks(
    rotation=35,
    ha="right",
)

plt.tight_layout()

funnel_chart = OUTPUT_DIR / "funnel_chart.png"

plt.savefig(
    funnel_chart,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print(
    f"Funnel visualization saved to: "
    f"{funnel_chart}"
)


# ============================================================
# 10. BUSINESS IMPACT
# ============================================================

# This is a scenario-based business value assumption.
# The dataset does not contain salary/profit/LTV per hire,
# so we explicitly use $100 as an illustrative value per
# successful conversion, matching the assignment example.

revenue_per_customer = 100

impact_analysis = []

for _, row in funnel_df.iterrows():

    users_lost = int(row["users_lost"])

    revenue_lost = (
        users_lost * revenue_per_customer
    )

    if revenue_lost > 1000:
        priority = "HIGH"
    elif revenue_lost > 500:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    impact_analysis.append(
        {
            "drop_point": (
                f"{row['from_stage']} -> "
                f"{row['to_stage']}"
            ),
            "users_lost": users_lost,
            "drop_rate": row["drop_rate"],
            "revenue_impact": revenue_lost,
            "priority": priority,
        }
    )


impact_df = pd.DataFrame(
    impact_analysis
)

impact_df = impact_df.sort_values(
    "revenue_impact",
    ascending=False,
)


print("\n" + "=" * 70)
print("BUSINESS IMPACT ANALYSIS")
print("=" * 70)

print(
    impact_df.to_string(
        index=False,
        formatters={
            "drop_rate": "{:.1f}%".format,
            "revenue_impact": "${:,.0f}".format,
        },
    )
)


# ============================================================
# 11. EXPECTED IMPACT OF IMPROVEMENT
# ============================================================

improvement_rate = 0.10

additional_conversions = int(
    biggest_drop["users_lost"]
    * improvement_rate
)

additional_revenue = (
    additional_conversions
    * revenue_per_customer
)


# ============================================================
# 12. BUSINESS RECOMMENDATION
# ============================================================

recommendation = f"""
FUNNEL OPTIMIZATION PRIORITY
=============================

BIGGEST BOTTLENECK:
Stage: {biggest_drop['from_stage']} -> {biggest_drop['to_stage']}
Users Lost: {int(biggest_drop['users_lost']):,}
Drop Rate: {biggest_drop['drop_rate']:.1f}%
Illustrative Revenue Impact: ${int(biggest_drop['users_lost'] * revenue_per_customer):,.0f}

WHY THIS MATTERS:
This transition has the largest absolute candidate loss in the
observed recruitment funnel. Improving this stage can increase
the number of candidates progressing toward the final Joined stage.

ROOT CAUSE HYPOTHESES:
1. The step may have unclear instructions or expectations.
2. The process may require too much time or effort.
3. Candidates may experience scheduling or communication friction.
4. Candidates may receive insufficient information before proceeding.
5. The timing of the step may create unnecessary delays.

RECOMMENDED ACTION:
1. Investigate candidate feedback around this transition.
2. Review the process for unnecessary complexity or delays.
3. Test a simplified version of the step.
4. Monitor completion rate and drop rate after the change.
5. Compare the revised funnel against the baseline.

EXPECTED IMPACT OF A 10% RELATIVE IMPROVEMENT:
Additional conversions: {additional_conversions:,}
Illustrative additional revenue: ${additional_revenue:,.0f}

SUCCESS CRITERIA:
- Increase completion rate at the bottleneck stage.
- Reduce the stage-specific drop rate.
- Track whether improvement persists across multiple cohorts.
- Monitor final Joined conversion to confirm downstream impact.

BUSINESS VALUE ASSUMPTION:
The dataset does not contain an actual revenue-per-hire or
customer LTV value. Therefore, $100 per successful conversion is
used only as an illustrative scenario value, consistent with the
assignment example. Replace this value with an actual business
value if one becomes available.
"""


print("\n" + "=" * 70)
print("ACTIONABLE RECOMMENDATION")
print("=" * 70)

print(recommendation)


# ============================================================
# 13. SAVE FUNNEL ANALYSIS REPORT
# ============================================================

analysis_file = OUTPUT_DIR / "funnel_analysis.txt"

with open(
    analysis_file,
    "w",
    encoding="utf-8",
) as file:

    file.write(
        "FUNNEL ANALYSIS & DROP-OFF DETECTION\n"
    )

    file.write(
        "=" * 70 + "\n\n"
    )

    file.write(
        "STAGE COUNTS\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    for stage, count in stages.items():

        file.write(
            f"{stage}: {count} candidates\n"
        )

    file.write("\n")

    file.write(
        "DROP-OFF ANALYSIS\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    for _, row in funnel_df.iterrows():

        file.write(
            f"{row['from_stage']} -> "
            f"{row['to_stage']}: "
            f"{int(row['users_lost'])} users lost, "
            f"{row['drop_rate']:.1f}% drop rate, "
            f"{row['completion_rate']:.1f}% completion rate\n"
        )

    file.write("\n")

    file.write(
        "OVERALL CONVERSION\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    file.write(
        f"Starting candidates: {starting_users}\n"
    )

    file.write(
        f"Joined candidates: {final_users}\n"
    )

    file.write(
        f"Overall conversion: {overall_conversion:.1f}%\n"
    )

    file.write(
        f"Overall drop-off: {overall_drop:.1f}%\n\n"
    )

    file.write(
        "BIGGEST BOTTLENECK\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    file.write(
        f"{biggest_drop['from_stage']} -> "
        f"{biggest_drop['to_stage']}\n"
    )

    file.write(
        f"Users lost: "
        f"{int(biggest_drop['users_lost'])}\n"
    )

    file.write(
        f"Drop rate: "
        f"{biggest_drop['drop_rate']:.1f}%\n"
    )

    file.write(
        f"Illustrative revenue impact: "
        f"${int(biggest_drop['users_lost'] * revenue_per_customer):,.0f}\n\n"
    )

    file.write(
        "BUSINESS IMPACT BY DROP-OFF\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    for _, row in impact_df.iterrows():

        file.write(
            f"{row['drop_point']}: "
            f"{row['users_lost']} users lost, "
            f"{row['drop_rate']:.1f}% drop rate, "
            f"${row['revenue_impact']:,.0f} illustrative impact, "
            f"Priority: {row['priority']}\n"
        )

    file.write("\n")

    file.write(
        recommendation
    )


print(
    f"\nFunnel analysis report saved to: "
    f"{analysis_file}"
)


# ============================================================
# 14. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("FUNNEL ANALYSIS COMPLETE")
print("=" * 70)

print(
    f"Chart:    {funnel_chart}"
)

print(
    f"Report:   {analysis_file}"
)

print(
    f"Stages analyzed: {len(stage_order)}"
)

print(
    f"Overall conversion: {overall_conversion:.1f}%"
)

print(
    f"Biggest bottleneck: "
    f"{biggest_drop['from_stage']} -> "
    f"{biggest_drop['to_stage']}"
)