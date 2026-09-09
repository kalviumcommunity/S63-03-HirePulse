"""Candidate-level analytical feature engineering."""

import pandas as pd


def build_candidate_features(
    candidates: pd.DataFrame,
    stages: pd.DataFrame,
    offers: pd.DataFrame,
    onboarding: pd.DataFrame,
) -> pd.DataFrame:
    """Combine source tables and add funnel and time-to-hire features."""
    result = candidates.copy()
    result["applied_date"] = pd.to_datetime(result["applied_date"], errors="coerce")
    result["application_month"] = result["applied_date"].dt.month
    result["application_year"] = result["applied_date"].dt.year

    stage_dates = stages.copy()
    stage_dates["stage_date"] = pd.to_datetime(stage_dates["stage_date"], errors="coerce")
    stage_joined_dates = (
        stage_dates.loc[stage_dates["stage_name"].eq("Joined")]
        .groupby("candidate_id", as_index=False)["stage_date"]
        .min()
        .rename(columns={"stage_date": "joined_date"})
    )
    onboarding_dates = onboarding.copy()
    onboarding_dates["joining_date"] = pd.to_datetime(onboarding_dates["joining_date"], errors="coerce")
    onboarding_dates = onboarding_dates[["candidate_id", "joining_date"]].rename(columns={"joining_date": "joined_date"})
    joined_dates = onboarding_dates.merge(stage_joined_dates, on="candidate_id", how="outer", suffixes=("_onboarding", "_stage"))
    joined_dates["joined_date"] = joined_dates["joined_date_onboarding"].fillna(joined_dates["joined_date_stage"])
    joined_dates = joined_dates[["candidate_id", "joined_date"]]
    offer_dates = offers.copy()
    offer_dates["offer_date"] = pd.to_datetime(offer_dates["offer_date"], errors="coerce")
    offer_dates = offer_dates[["candidate_id", "offer_date", "accepted"]]

    result = result.merge(offer_dates, on="candidate_id", how="left")
    result = result.merge(joined_dates, on="candidate_id", how="left")
    result["hiring_duration_days"] = (
        result["joined_date"] - result["applied_date"]
    ).dt.days
    result["offer_acceptance_flag"] = result["accepted"].astype("boolean").fillna(False).astype(int)
    result["joined_flag"] = result["joined_date"].notna().astype(int)
    return result
