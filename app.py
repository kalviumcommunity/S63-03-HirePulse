"""
HirePulse - Recruitment Analytics Dashboard Web Application.
Provides interactive visual insights, funnel analysis, KPIs, and candidate exploration.
"""

from pathlib import Path
import json
import math
import pandas as pd
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUTS_DIR = BASE_DIR / "outputs"


def safe_int(val, default=0):
    try:
        if pd.isna(val):
            return default
        return int(val)
    except Exception:
        return default


def safe_float(val, default=0.0):
    try:
        if pd.isna(val) or math.isnan(val):
            return default
        return round(float(val), 2)
    except Exception:
        return default


def load_dataset():
    """Load and merge candidate and recruitment pipeline datasets."""
    candidates_path = DATA_DIR / "candidates.csv"
    stages_path = DATA_DIR / "recruitment_stages.csv"
    offers_path = DATA_DIR / "offers.csv"
    interviews_path = DATA_DIR / "interviews.csv"
    onboarding_path = DATA_DIR / "onboarding.csv"

    candidates_df = pd.read_csv(candidates_path) if candidates_path.exists() else pd.DataFrame()
    stages_df = pd.read_csv(stages_path) if stages_path.exists() else pd.DataFrame()
    offers_df = pd.read_csv(offers_path) if offers_path.exists() else pd.DataFrame()
    interviews_df = pd.read_csv(interviews_path) if interviews_path.exists() else pd.DataFrame()
    onboarding_df = pd.read_csv(onboarding_path) if onboarding_path.exists() else pd.DataFrame()

    return {
        "candidates": candidates_df,
        "stages": stages_df,
        "offers": offers_df,
        "interviews": interviews_df,
        "onboarding": onboarding_df,
    }


def compute_metrics():
    """Compute executive KPI metrics."""
    data = load_dataset()
    candidates = data["candidates"]
    stages = data["stages"]
    offers = data["offers"]
    onboarding = data["onboarding"]

    total_candidates = len(candidates)
    
    # Calculate funnel stages count
    stage_names = ["Applied", "Screening", "Technical Interview", "HR Interview", "Offer Sent", "Joined"]
    stage_counts = {}
    for stage in stage_names:
        if not stages.empty and "stage_name" in stages.columns:
            count = stages[stages["stage_name"] == stage]["candidate_id"].nunique()
            stage_counts[stage] = count
        else:
            stage_counts[stage] = 0

    if stage_counts["Applied"] == 0:
        stage_counts["Applied"] = total_candidates

    total_offers = len(offers) if not offers.empty else 0
    accepted_offers = len(offers[offers["accepted"] == True]) if not offers.empty and "accepted" in offers.columns else 0
    offer_acceptance_rate = (accepted_offers / total_offers * 100) if total_offers > 0 else 0.0

    joined_count = stage_counts.get("Joined", 0)
    if joined_count == 0 and not onboarding.empty and "onboarding_status" in onboarding.columns:
        joined_count = len(onboarding[onboarding["onboarding_status"] == "Completed"])

    conversion_rate = (joined_count / total_candidates * 100) if total_candidates > 0 else 0.0

    # Calculate average time to hire (days from applied_date to joining_date)
    avg_time_to_hire = 0.0
    if not candidates.empty and not onboarding.empty:
        merged = candidates.merge(onboarding, on="candidate_id", how="inner")
        if "applied_date" in merged.columns and "joining_date" in merged.columns:
            merged["applied_date"] = pd.to_datetime(merged["applied_date"], errors="coerce")
            merged["joining_date"] = pd.to_datetime(merged["joining_date"], errors="coerce")
            duration = (merged["joining_date"] - merged["applied_date"]).dt.days.dropna()
            if not duration.empty:
                avg_time_to_hire = round(duration[duration >= 0].mean(), 1)

    # Average Offer Salary
    avg_salary = 0
    if not offers.empty and "salary" in offers.columns:
        valid_salaries = offers["salary"].dropna()
        if not valid_salaries.empty:
            avg_salary = int(valid_salaries.mean())

    # Department breakdown
    dept_counts = {}
    if not candidates.empty and "department" in candidates.columns:
        dept_counts = candidates["department"].value_counts().to_dict()

    top_department = max(dept_counts, key=dept_counts.get) if dept_counts else "N/A"

    return {
        "total_candidates": total_candidates,
        "total_offers": total_offers,
        "accepted_offers": accepted_offers,
        "joined_count": joined_count,
        "offer_acceptance_rate": round(offer_acceptance_rate, 1),
        "overall_conversion_rate": round(conversion_rate, 1),
        "avg_time_to_hire_days": avg_time_to_hire if not math.isnan(avg_time_to_hire) else 0.0,
        "avg_salary": avg_salary,
        "top_department": top_department,
        "stage_counts": stage_counts,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summary")
def api_summary():
    try:
        metrics = compute_metrics()
        return jsonify({"status": "success", "data": metrics})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/funnel")
def api_funnel():
    try:
        data = load_dataset()
        stages_df = data["stages"]
        candidates_df = data["candidates"]

        stage_order = ["Applied", "Screening", "Technical Interview", "HR Interview", "Offer Sent", "Joined"]
        funnel_data = []

        total_applied = len(candidates_df)
        prev_count = total_applied

        for idx, stage in enumerate(stage_order):
            if stage == "Applied":
                count = total_applied
            else:
                count = stages_df[stages_df["stage_name"] == stage]["candidate_id"].nunique() if not stages_df.empty else 0

            drop_off = prev_count - count if prev_count >= count else 0
            drop_off_pct = round((drop_off / prev_count * 100), 1) if prev_count > 0 else 0.0
            overall_pct = round((count / total_applied * 100), 1) if total_applied > 0 else 0.0

            funnel_data.append({
                "stage": stage,
                "count": count,
                "drop_off": drop_off,
                "drop_off_pct": drop_off_pct,
                "overall_conversion_pct": overall_pct,
            })
            prev_count = count

        return jsonify({"status": "success", "data": funnel_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/departments")
def api_departments():
    try:
        data = load_dataset()
        candidates = data["candidates"]
        offers = data["offers"]
        onboarding = data["onboarding"]
        stages = data["stages"]

        if candidates.empty:
            return jsonify({"status": "success", "data": []})

        # Calculate metrics by department
        dept_stats = []
        for dept, group in candidates.groupby("department"):
            c_ids = set(group["candidate_id"])
            total_cand = len(c_ids)

            # Offers in this dept
            dept_offers = offers[offers["candidate_id"].isin(c_ids)] if not offers.empty else pd.DataFrame()
            num_offers = len(dept_offers)
            num_accepted = len(dept_offers[dept_offers["accepted"] == True]) if not dept_offers.empty and "accepted" in dept_offers.columns else 0

            # Joined in this dept
            dept_stages = stages[stages["candidate_id"].isin(c_ids)] if not stages.empty else pd.DataFrame()
            joined = len(dept_stages[dept_stages["stage_name"] == "Joined"]) if not dept_stages.empty else 0

            # Avg salary
            avg_salary = int(dept_offers["salary"].mean()) if not dept_offers.empty and "salary" in dept_offers.columns and not pd.isna(dept_offers["salary"].mean()) else 0

            dept_stats.append({
                "department": dept,
                "total_candidates": total_cand,
                "offers_sent": num_offers,
                "offers_accepted": num_accepted,
                "joined": joined,
                "avg_salary": avg_salary,
                "hire_rate": round((joined / total_cand * 100), 1) if total_cand > 0 else 0.0,
            })

        dept_stats.sort(key=lambda x: x["total_candidates"], reverse=True)
        return jsonify({"status": "success", "data": dept_stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/timeline")
def api_timeline():
    try:
        data = load_dataset()
        candidates = data["candidates"]

        if candidates.empty or "applied_date" not in candidates.columns:
            return jsonify({"status": "success", "data": []})

        cand = candidates.copy()
        cand["applied_date"] = pd.to_datetime(cand["applied_date"], errors="coerce")
        cand = cand.dropna(subset=["applied_date"])
        cand["month_year"] = cand["applied_date"].dt.strftime("%Y-%m")

        monthly = cand.groupby("month_year").size().reset_index(name="applications")
        monthly = monthly.sort_values("month_year")

        return jsonify({
            "status": "success",
            "data": {
                "labels": monthly["month_year"].tolist(),
                "values": monthly["applications"].tolist(),
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/candidates")
def api_candidates():
    try:
        data = load_dataset()
        candidates = data["candidates"]
        stages = data["stages"]
        offers = data["offers"]
        interviews = data["interviews"]
        onboarding = data["onboarding"]

        if candidates.empty:
            return jsonify({"status": "success", "data": []})

        # Enrich candidates with current stage, offer status, and interview score
        records = []
        for _, row in candidates.iterrows():
            cid = row["candidate_id"]

            # Stages for this candidate
            c_stages = stages[stages["candidate_id"] == cid] if not stages.empty else pd.DataFrame()
            current_stage = "Applied"
            stage_status = "Pending"
            if not c_stages.empty:
                last_stage = c_stages.iloc[-1]
                current_stage = last_stage.get("stage_name", "Applied")
                stage_status = last_stage.get("status", "In Progress")

            # Offer details
            c_offer = offers[offers["candidate_id"] == cid] if not offers.empty else pd.DataFrame()
            offer_salary = None
            offer_accepted = None
            if not c_offer.empty:
                offer_salary = safe_int(c_offer.iloc[0].get("salary"))
                offer_accepted = bool(c_offer.iloc[0].get("accepted"))

            # Interview count & avg score
            c_interviews = interviews[interviews["candidate_id"] == cid] if not interviews.empty else pd.DataFrame()
            num_interviews = len(c_interviews)
            avg_score = safe_float(c_interviews["score"].mean()) if num_interviews > 0 and "score" in c_interviews.columns else None

            # Onboarding
            c_onboarding = onboarding[onboarding["candidate_id"] == cid] if not onboarding.empty else pd.DataFrame()
            onb_status = c_onboarding.iloc[0].get("onboarding_status", "N/A") if not c_onboarding.empty else "N/A"
            joining_date = str(c_onboarding.iloc[0].get("joining_date", "")) if not c_onboarding.empty else ""

            records.append({
                "candidate_id": cid,
                "full_name": row.get("full_name", "Unknown"),
                "email": row.get("email", ""),
                "phone": row.get("phone", ""),
                "department": row.get("department", "Unassigned"),
                "applied_date": str(row.get("applied_date", "")),
                "current_stage": current_stage,
                "stage_status": stage_status,
                "offer_salary": offer_salary,
                "offer_accepted": offer_accepted,
                "interviews_count": num_interviews,
                "avg_interview_score": avg_score,
                "onboarding_status": onb_status,
                "joining_date": joining_date,
            })

        return jsonify({"status": "success", "data": records})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/candidate/<int:cid>")
def api_candidate_detail(cid):
    try:
        data = load_dataset()
        candidates = data["candidates"]
        stages = data["stages"]
        offers = data["offers"]
        interviews = data["interviews"]
        onboarding = data["onboarding"]

        cand = candidates[candidates["candidate_id"] == cid]
        if cand.empty:
            return jsonify({"status": "error", "message": "Candidate not found"}), 404

        cand_dict = cand.iloc[0].to_dict()
        c_stages = stages[stages["candidate_id"] == cid].to_dict(orient="records") if not stages.empty else []
        c_offers = offers[offers["candidate_id"] == cid].to_dict(orient="records") if not offers.empty else []
        c_interviews = interviews[interviews["candidate_id"] == cid].to_dict(orient="records") if not interviews.empty else []
        c_onboarding = onboarding[onboarding["candidate_id"] == cid].to_dict(orient="records") if not onboarding.empty else []

        return jsonify({
            "status": "success",
            "candidate": cand_dict,
            "stages": c_stages,
            "offers": c_offers,
            "interviews": c_interviews,
            "onboarding": c_onboarding,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/anomalies")
def api_anomalies():
    """Returns detected data quality issues, drop-off anomalies, and salary outliers."""
    try:
        data = load_dataset()
        candidates = data["candidates"]
        offers = data["offers"]
        stages = data["stages"]

        anomalies = []

        # 1. Salary Outliers (IQR method)
        if not offers.empty and "salary" in offers.columns:
            salaries = offers["salary"].dropna()
            if len(salaries) > 4:
                q25 = salaries.quantile(0.25)
                q75 = salaries.quantile(0.75)
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr

                outliers = offers[(offers["salary"] < lower_bound) | (offers["salary"] > upper_bound)]
                for _, row in outliers.iterrows():
                    cand_match = candidates[candidates["candidate_id"] == row["candidate_id"]]
                    cand_name = cand_match.iloc[0]["full_name"] if not cand_match.empty else f"Candidate #{row['candidate_id']}"
                    dept = cand_match.iloc[0]["department"] if not cand_match.empty else "N/A"
                    anomalies.append({
                        "type": "Salary Outlier",
                        "severity": "Warning",
                        "title": f"Unusual Offer Compensation: ${row['salary']:,.0f}",
                        "candidate_id": safe_int(row["candidate_id"]),
                        "details": f"{cand_name} ({dept}) received an offer deviating significantly from standard bounds (${lower_bound:,.0f} - ${upper_bound:,.0f}).",
                    })

        # 2. Dropped Candidates in Critical Stages
        if not stages.empty:
            tech_drops = stages[(stages["stage_name"] == "Technical Interview") & (stages["status"] == "Dropped")]
            if len(tech_drops) > 0:
                anomalies.append({
                    "type": "Funnel Drop-Off",
                    "severity": "Info",
                    "title": f"Technical Round Bottleneck ({len(tech_drops)} Drop-offs)",
                    "candidate_id": None,
                    "details": f"{len(tech_drops)} candidate(s) exited during or after the technical assessment phase.",
                })

        # 3. High Interview Round Duration or Stage Gaps
        if not candidates.empty and not stages.empty:
            merged = stages[stages["stage_name"] == "Joined"].merge(candidates, on="candidate_id")
            if "applied_date" in merged.columns and "stage_date" in merged.columns:
                merged["app_dt"] = pd.to_datetime(merged["applied_date"], errors="coerce")
                merged["stg_dt"] = pd.to_datetime(merged["stage_date"], errors="coerce")
                merged["days"] = (merged["stg_dt"] - merged["app_dt"]).dt.days
                prolonged = merged[merged["days"] > 45]
                for _, row in prolonged.iterrows():
                    anomalies.append({
                        "type": "Prolonged Cycle",
                        "severity": "Warning",
                        "title": f"Extended Time-to-Hire: {row['days']} Days",
                        "candidate_id": safe_int(row["candidate_id"]),
                        "details": f"{row.get('full_name', 'Candidate')} ({row.get('department', 'N/A')}) took {row['days']} days from application to joining.",
                    })

        return jsonify({"status": "success", "data": anomalies, "total_count": len(anomalies)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  [+] HirePulse Recruitment Analytics Web Dashboard")
    print("  [*] Running locally at: http://127.0.0.1:5000")
    print("  [*] Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=True)
