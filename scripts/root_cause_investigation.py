from pathlib import Path
import pandas as pd
import numpy as np

# ============================================================
# ROOT CAUSE INVESTIGATION WORKFLOW
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TRANSACTION_FILE = (
    BASE_DIR / "data" / "processed" / "deduplicated_data.csv"
)

TRANSFORMED_FILE = (
    BASE_DIR / "data" / "processed" / "transformed_transactions.csv"
)

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

REPORT_FILE = OUTPUT_DIR / "investigation_report.txt"


def load_data():
    """Load and prepare available transaction datasets."""

    df = pd.read_csv(TRANSACTION_FILE)

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce"
    )

    df["success"] = (
        df["status"].astype(str).str.lower() == "completed"
    ).astype(int)

    df["failure"] = 1 - df["success"]

    return df


def task_1_time_isolation(df):
    """
    Task 1:
    Identify anomalous dates and investigate hourly behavior.
    """

    print("\n" + "=" * 70)
    print("TASK 1: TIME WINDOW ISOLATION")
    print("=" * 70)

    daily_metrics = (
        df.groupby(df["transaction_date"].dt.date)
        .agg(
            transactions=("customer_id", "count"),
            transaction_value=("amount", "sum"),
            success_rate=("success", "mean"),
            failure_rate=("failure", "mean"),
        )
        .reset_index()
    )

    print("\nDaily Metrics:")
    print(daily_metrics.to_string(index=False))

    mean_success = daily_metrics["success_rate"].mean()
    std_success = daily_metrics["success_rate"].std(ddof=0)

    threshold = mean_success - std_success

    anomalies = daily_metrics[
        daily_metrics["success_rate"] < threshold
    ]

    print(f"\nMean success rate: {mean_success:.1%}")
    print(f"Standard deviation: {std_success:.1%}")
    print(f"Anomaly threshold: {threshold:.1%}")

    if anomalies.empty:
        print("\nNo statistically defined daily anomaly detected.")

        # Use the lowest-success day only for investigation,
        # while explicitly distinguishing it from an anomaly.
        problem_day = daily_metrics.loc[
            daily_metrics["success_rate"].idxmin(),
            "transaction_date"
        ]

        anomaly_detected = False

    else:
        print("\nAnomalies detected:")
        print(anomalies.to_string(index=False))

        problem_day = anomalies.iloc[0]["transaction_date"]
        anomaly_detected = True

    print(f"\nInvestigation date: {problem_day}")

    day_data = df[
        df["transaction_date"].dt.date == problem_day
    ].copy()

    day_data["hour"] = day_data["transaction_date"].dt.hour

    if day_data.empty:
        print("No transactions available for investigation date.")
        return {
            "daily_metrics": daily_metrics,
            "problem_day": problem_day,
            "hourly_metrics": pd.DataFrame(),
            "anomaly_detected": anomaly_detected,
            "problem_hour": None,
        }

    hourly_metrics = (
        day_data.groupby("hour")
        .agg(
            transactions=("customer_id", "count"),
            transaction_value=("amount", "sum"),
            success_rate=("success", "mean"),
            failure_rate=("failure", "mean"),
        )
        .reset_index()
    )

    print("\nHourly Breakdown:")
    print(hourly_metrics.to_string(index=False))

    problem_hour = int(
        hourly_metrics.loc[
            hourly_metrics["success_rate"].idxmin(),
            "hour"
        ]
    )

    worst_success = hourly_metrics["success_rate"].min()

    print(
        f"\nWorst hour: {problem_hour:02d}:00 "
        f"(success rate: {worst_success:.1%})"
    )

    # Before / during / after comparison
    before = df[
        df["transaction_date"] <
        pd.Timestamp(problem_day) + pd.Timedelta(hours=problem_hour)
    ]

    during_start = (
        pd.Timestamp(problem_day)
        + pd.Timedelta(hours=problem_hour)
    )

    during_end = during_start + pd.Timedelta(hours=1)

    during = df[
        (df["transaction_date"] >= during_start)
        & (df["transaction_date"] < during_end)
    ]

    after = df[
        df["transaction_date"] >= during_end
    ]

    print("\nBefore / During / After:")
    print(
        f"Before:  {len(before)} transactions, "
        f"success rate {before['success'].mean():.1%}"
        if len(before) else
        "Before:  No data"
    )

    print(
        f"During:  {len(during)} transactions, "
        f"success rate {during['success'].mean():.1%}"
        if len(during) else
        "During:  No data"
    )

    print(
        f"After:   {len(after)} transactions, "
        f"success rate {after['success'].mean():.1%}"
        if len(after) else
        "After:   No data"
    )

    return {
        "daily_metrics": daily_metrics,
        "problem_day": problem_day,
        "hourly_metrics": hourly_metrics,
        "anomaly_detected": anomaly_detected,
        "problem_hour": problem_hour,
    }


def task_2_segment_analysis(df, problem_day, problem_hour):
    """
    Task 2:
    Analyze available customer-level and status-level dimensions.
    """

    print("\n" + "=" * 70)
    print("TASK 2: SEGMENT ANALYSIS")
    print("=" * 70)

    problem_start = (
        pd.Timestamp(problem_day)
        + pd.Timedelta(hours=problem_hour)
    )

    problem_end = problem_start + pd.Timedelta(hours=1)

    problem_window = df[
        (df["transaction_date"] >= problem_start)
        & (df["transaction_date"] < problem_end)
    ].copy()

    print(
        f"\nProblem window: "
        f"{problem_start} to {problem_end}"
    )

    if problem_window.empty:
        print("No transactions fall inside the selected window.")

    # Customer-level analysis
    by_customer = (
        problem_window.groupby("customer_id")
        .agg(
            transactions=("customer_id", "count"),
            amount=("amount", "sum"),
            success_rate=("success", "mean"),
            failure_count=("failure", "sum"),
        )
        .reset_index()
    )

    print("\nBy Customer:")
    if by_customer.empty:
        print("No customer-level observations.")
    else:
        print(by_customer.to_string(index=False))

    # Status analysis
    by_status = (
        problem_window.groupby("status")
        .agg(
            count=("customer_id", "count"),
            amount=("amount", "sum"),
        )
        .reset_index()
    )

    print("\nBy Transaction Status:")
    if by_status.empty:
        print("No status observations.")
    else:
        print(by_status.to_string(index=False))

    # Required assignment dimensions unavailable
    unavailable = [
        "customer_type",
        "payment_method",
        "region",
        "device_type",
    ]

    print("\nUnavailable Investigation Dimensions:")
    for column in unavailable:
        print(f"- {column}: NOT AVAILABLE in source dataset")

    return {
        "problem_window": problem_window,
        "by_customer": by_customer,
        "by_status": by_status,
    }


def task_3_correlation_analysis(
    df,
    problem_day,
    problem_hour
):
    """
    Task 3:
    Examine available correlations and error evidence.
    """

    print("\n" + "=" * 70)
    print("TASK 3: CORRELATION ANALYSIS")
    print("=" * 70)

    problem_start = (
        pd.Timestamp(problem_day)
        + pd.Timedelta(hours=problem_hour)
    )

    problem_end = problem_start + pd.Timedelta(hours=1)

    df = df.copy()

    df["is_problem_period"] = (
        (df["transaction_date"] >= problem_start)
        & (df["transaction_date"] < problem_end)
    ).astype(int)

    # Hour cross-tab
    hour_crosstab = pd.crosstab(
        df["transaction_date"].dt.hour,
        df["is_problem_period"],
        margins=True,
    )

    print("\nHour vs Problem Period:")
    print(hour_crosstab)

    # Status cross-tab
    status_crosstab = pd.crosstab(
        df["status"],
        df["is_problem_period"],
        margins=True,
    )

    print("\nStatus vs Problem Period:")
    print(status_crosstab)

    # Day-of-week pattern
    weekday_crosstab = pd.crosstab(
        df["transaction_date"].dt.day_name(),
        df["is_problem_period"],
        margins=True,
    )

    print("\nDay of Week vs Problem Period:")
    print(weekday_crosstab)

    print("\nError Log Analysis:")
    print(
        "No error_message column exists in the available transaction data."
    )

    print("\nExternal Event Analysis:")
    print(
        "No external-event or payment-provider log is available "
        "in the repository."
    )

    return {
        "hour_crosstab": hour_crosstab,
        "status_crosstab": status_crosstab,
        "weekday_crosstab": weekday_crosstab,
    }


def task_4_document_hypothesis(
    df,
    investigation,
    segment_results,
):
    """
    Task 4:
    Document observation, evidence, hypothesis and actions.
    """

    problem_day = investigation["problem_day"]
    problem_hour = investigation["problem_hour"]
    anomaly_detected = investigation["anomaly_detected"]

    problem_window = segment_results["problem_window"]

    if anomaly_detected:
        observation = (
            f"A statistically defined success-rate anomaly was detected "
            f"on {problem_day}."
        )
    else:
        observation = (
            f"No statistically defined daily anomaly was detected. "
            f"The lowest-success day selected for investigation was "
            f"{problem_day}."
        )

    if len(problem_window):
        problem_success = problem_window["success"].mean()
        problem_failure = problem_window["failure"].mean()
        problem_transactions = len(problem_window)
        problem_value = problem_window["amount"].sum()
    else:
        problem_success = np.nan
        problem_failure = np.nan
        problem_transactions = 0
        problem_value = 0

    report = f"""
======================================================================
ROOT CAUSE INVESTIGATION REPORT
======================================================================

OBSERVATION
-----------
{observation}

Investigation date:
{problem_day}

Investigation hour:
{problem_hour:02d}:00-{problem_hour + 1:02d}:00

Transactions during selected period:
{problem_transactions}

Transaction value during selected period:
${problem_value:,.2f}

Success rate during selected period:
{
    f"{problem_success:.1%}"
    if not pd.isna(problem_success)
    else "N/A"
}

Failure rate during selected period:
{
    f"{problem_failure:.1%}"
    if not pd.isna(problem_failure)
    else "N/A"
}


ANALYSIS
--------
The available transaction dataset contains:

- customer_id
- transaction_date
- amount
- status

The analysis therefore examined:

1. Daily success/failure patterns
2. Hourly success/failure patterns
3. Customer-level concentration
4. Transaction status
5. Transaction value
6. Day-of-week and hour relationships


UNAVAILABLE DIMENSIONS
----------------------
The repository does not contain:

- payment_method
- customer_type
- region
- device_type
- error_message
- payment-provider event logs

Therefore, these dimensions cannot be used as evidence.


HYPOTHESIS
----------
The available data supports investigation of a transaction-status/time
relationship, but it does NOT contain enough evidence to identify a
specific external payment processor, competitor, product bug, or
seasonal cause.

Confidence: LOW

Reason:
The dataset is extremely small and lacks the operational metadata
required to establish a causal root cause.


CORRELATION VS CAUSATION
------------------------
A concentration of failed transactions in a particular time period
would establish a temporal association.

It would NOT, by itself, prove that a payment provider or product bug
caused the failures.

Additional evidence such as payment-provider logs, application error
logs, payment method, geography, device information, and deployment
history would be required for causal confirmation.


RECOMMENDED ACTIONS
-------------------
1. Capture payment_method for every transaction.
2. Capture customer_type and region.
3. Capture device_type.
4. Store structured error codes/messages.
5. Integrate payment-provider status and event logs.
6. Maintain higher-volume transaction history.
7. Add automated alerts for sudden success-rate changes.
8. Compare anomaly windows with deployment and infrastructure logs.


CONCLUSION
----------
The investigation framework successfully isolates the available time
and transaction dimensions.

However, the current repository data does not support confirmation of
the hypothetical Stripe outage or any other specific root cause.

The correct analytical conclusion is therefore:

"An anomaly/root-cause relationship cannot be conclusively established
from the available data. Additional operational evidence is required."
"""

    print(report)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {REPORT_FILE}")

    return report


def task_5_validate_hypothesis(
    df,
    investigation,
    correlation_results,
):
    """
    Task 5:
    Validate whether available evidence supports the hypothesis.
    """

    print("\n" + "=" * 70)
    print("TASK 5: HYPOTHESIS VALIDATION")
    print("=" * 70)

    problem_day = investigation["problem_day"]
    problem_hour = investigation["problem_hour"]

    problem_start = (
        pd.Timestamp(problem_day)
        + pd.Timedelta(hours=problem_hour)
    )

    problem_end = problem_start + pd.Timedelta(hours=1)

    problem_data = df[
        (df["transaction_date"] >= problem_start)
        & (df["transaction_date"] < problem_end)
    ]

    print("\nHYPOTHESIS VALIDATION")
    print("-" * 50)

    print(
        f"Selected investigation period: "
        f"{problem_start} to {problem_end}"
    )

    print(
        f"Transactions in period: {len(problem_data)}"
    )

    if len(problem_data):
        print(
            f"Failure rate: "
            f"{problem_data['failure'].mean():.1%}"
        )
    else:
        print("Failure rate: N/A")

    print("\nExternal evidence:")
    print("✗ No payment-provider status data available")
    print("✗ No application error logs available")
    print("✗ No payment-method field available")
    print("✗ No deployment/infrastructure event log available")

    print("\nConclusion:")
    print(
        "HYPOTHESIS NOT CONFIRMED — available internal data "
        "is insufficient for causal confirmation."
    )


def main():

    print("=" * 70)
    print("ROOT CAUSE INVESTIGATION WORKFLOW")
    print("=" * 70)

    print("\nLoading transaction data...")

    df = load_data()

    print(f"Dataset: {TRANSACTION_FILE}")
    print(f"Rows: {len(df)}")
    print(f"Date range: {df['transaction_date'].min()} "
          f"to {df['transaction_date'].max()}")

    investigation = task_1_time_isolation(df)

    segment_results = task_2_segment_analysis(
        df,
        investigation["problem_day"],
        investigation["problem_hour"],
    )

    correlation_results = task_3_correlation_analysis(
        df,
        investigation["problem_day"],
        investigation["problem_hour"],
    )

    task_4_document_hypothesis(
        df,
        investigation,
        segment_results,
    )

    task_5_validate_hypothesis(
        df,
        investigation,
        correlation_results,
    )

    print("\n" + "=" * 70)
    print("ROOT CAUSE INVESTIGATION COMPLETE")
    print("=" * 70)
    print(f"Report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
from pathlib import Path
import pandas as pd
import numpy as np

# ============================================================
# ROOT CAUSE INVESTIGATION WORKFLOW
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TRANSACTION_FILE = (
    BASE_DIR / "data" / "processed" / "deduplicated_data.csv"
)

TRANSFORMED_FILE = (
    BASE_DIR / "data" / "processed" / "transformed_transactions.csv"
)

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

REPORT_FILE = OUTPUT_DIR / "investigation_report.txt"


def load_data():
    """Load and prepare available transaction datasets."""

    df = pd.read_csv(TRANSACTION_FILE)

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce"
    )

    df["success"] = (
        df["status"].astype(str).str.lower() == "completed"
    ).astype(int)

    df["failure"] = 1 - df["success"]

    return df


def task_1_time_isolation(df):
    """
    Task 1:
    Identify anomalous dates and investigate hourly behavior.
    """

    print("\n" + "=" * 70)
    print("TASK 1: TIME WINDOW ISOLATION")
    print("=" * 70)

    daily_metrics = (
        df.groupby(df["transaction_date"].dt.date)
        .agg(
            transactions=("customer_id", "count"),
            transaction_value=("amount", "sum"),
            success_rate=("success", "mean"),
            failure_rate=("failure", "mean"),
        )
        .reset_index()
    )

    print("\nDaily Metrics:")
    print(daily_metrics.to_string(index=False))

    mean_success = daily_metrics["success_rate"].mean()
    std_success = daily_metrics["success_rate"].std(ddof=0)

    threshold = mean_success - std_success

    anomalies = daily_metrics[
        daily_metrics["success_rate"] < threshold
    ]

    print(f"\nMean success rate: {mean_success:.1%}")
    print(f"Standard deviation: {std_success:.1%}")
    print(f"Anomaly threshold: {threshold:.1%}")

    if anomalies.empty:
        print("\nNo statistically defined daily anomaly detected.")

        # Use the lowest-success day only for investigation,
        # while explicitly distinguishing it from an anomaly.
        problem_day = daily_metrics.loc[
            daily_metrics["success_rate"].idxmin(),
            "transaction_date"
        ]

        anomaly_detected = False

    else:
        print("\nAnomalies detected:")
        print(anomalies.to_string(index=False))

        problem_day = anomalies.iloc[0]["transaction_date"]
        anomaly_detected = True

    print(f"\nInvestigation date: {problem_day}")

    day_data = df[
        df["transaction_date"].dt.date == problem_day
    ].copy()

    day_data["hour"] = day_data["transaction_date"].dt.hour

    if day_data.empty:
        print("No transactions available for investigation date.")
        return {
            "daily_metrics": daily_metrics,
            "problem_day": problem_day,
            "hourly_metrics": pd.DataFrame(),
            "anomaly_detected": anomaly_detected,
            "problem_hour": None,
        }

    hourly_metrics = (
        day_data.groupby("hour")
        .agg(
            transactions=("customer_id", "count"),
            transaction_value=("amount", "sum"),
            success_rate=("success", "mean"),
            failure_rate=("failure", "mean"),
        )
        .reset_index()
    )

    print("\nHourly Breakdown:")
    print(hourly_metrics.to_string(index=False))

    problem_hour = int(
        hourly_metrics.loc[
            hourly_metrics["success_rate"].idxmin(),
            "hour"
        ]
    )

    worst_success = hourly_metrics["success_rate"].min()

    print(
        f"\nWorst hour: {problem_hour:02d}:00 "
        f"(success rate: {worst_success:.1%})"
    )

    # Before / during / after comparison
    before = df[
        df["transaction_date"] <
        pd.Timestamp(problem_day) + pd.Timedelta(hours=problem_hour)
    ]

    during_start = (
        pd.Timestamp(problem_day)
        + pd.Timedelta(hours=problem_hour)
    )

    during_end = during_start + pd.Timedelta(hours=1)

    during = df[
        (df["transaction_date"] >= during_start)
        & (df["transaction_date"] < during_end)
    ]

    after = df[
        df["transaction_date"] >= during_end
    ]

    print("\nBefore / During / After:")
    print(
        f"Before:  {len(before)} transactions, "
        f"success rate {before['success'].mean():.1%}"
        if len(before) else
        "Before:  No data"
    )

    print(
        f"During:  {len(during)} transactions, "
        f"success rate {during['success'].mean():.1%}"
        if len(during) else
        "During:  No data"
    )

    print(
        f"After:   {len(after)} transactions, "
        f"success rate {after['success'].mean():.1%}"
        if len(after) else
        "After:   No data"
    )

    return {
        "daily_metrics": daily_metrics,
        "problem_day": problem_day,
        "hourly_metrics": hourly_metrics,
        "anomaly_detected": anomaly_detected,
        "problem_hour": problem_hour,
    }


def task_2_segment_analysis(df, problem_day, problem_hour):
    """
    Task 2:
    Analyze available customer-level and status-level dimensions.
    """

    print("\n" + "=" * 70)
    print("TASK 2: SEGMENT ANALYSIS")
    print("=" * 70)

    problem_start = (
        pd.Timestamp(problem_day)
        + pd.Timedelta(hours=problem_hour)
    )

    problem_end = problem_start + pd.Timedelta(hours=1)

    problem_window = df[
        (df["transaction_date"] >= problem_start)
        & (df["transaction_date"] < problem_end)
    ].copy()

    print(
        f"\nProblem window: "
        f"{problem_start} to {problem_end}"
    )

    if problem_window.empty:
        print("No transactions fall inside the selected window.")

    # Customer-level analysis
    by_customer = (
        problem_window.groupby("customer_id")
        .agg(
            transactions=("customer_id", "count"),
            amount=("amount", "sum"),
            success_rate=("success", "mean"),
            failure_count=("failure", "sum"),
        )
        .reset_index()
    )

    print("\nBy Customer:")
    if by_customer.empty:
        print("No customer-level observations.")
    else:
        print(by_customer.to_string(index=False))

    # Status analysis
    by_status = (
        problem_window.groupby("status")
        .agg(
            count=("customer_id", "count"),
            amount=("amount", "sum"),
        )
        .reset_index()
    )

    print("\nBy Transaction Status:")
    if by_status.empty:
        print("No status observations.")
    else:
        print(by_status.to_string(index=False))

    # Required assignment dimensions unavailable
    unavailable = [
        "customer_type",
        "payment_method",
        "region",
        "device_type",
    ]

    print("\nUnavailable Investigation Dimensions:")
    for column in unavailable:
        print(f"- {column}: NOT AVAILABLE in source dataset")

    return {
        "problem_window": problem_window,
        "by_customer": by_customer,
        "by_status": by_status,
    }


def task_3_correlation_analysis(
    df,
    problem_day,
    problem_hour
):
    """
    Task 3:
    Examine available correlations and error evidence.
    """

    print("\n" + "=" * 70)
    print("TASK 3: CORRELATION ANALYSIS")
    print("=" * 70)

    problem_start = (
        pd.Timestamp(problem_day)
        + pd.Timedelta(hours=problem_hour)
    )

    problem_end = problem_start + pd.Timedelta(hours=1)

    df = df.copy()

    df["is_problem_period"] = (
        (df["transaction_date"] >= problem_start)
        & (df["transaction_date"] < problem_end)
    ).astype(int)

    # Hour cross-tab
    hour_crosstab = pd.crosstab(
        df["transaction_date"].dt.hour,
        df["is_problem_period"],
        margins=True,
    )

    print("\nHour vs Problem Period:")
    print(hour_crosstab)

    # Status cross-tab
    status_crosstab = pd.crosstab(
        df["status"],
        df["is_problem_period"],
        margins=True,
    )

    print("\nStatus vs Problem Period:")
    print(status_crosstab)

    # Day-of-week pattern
    weekday_crosstab = pd.crosstab(
        df["transaction_date"].dt.day_name(),
        df["is_problem_period"],
        margins=True,
    )

    print("\nDay of Week vs Problem Period:")
    print(weekday_crosstab)

    print("\nError Log Analysis:")
    print(
        "No error_message column exists in the available transaction data."
    )

    print("\nExternal Event Analysis:")
    print(
        "No external-event or payment-provider log is available "
        "in the repository."
    )

    return {
        "hour_crosstab": hour_crosstab,
        "status_crosstab": status_crosstab,
        "weekday_crosstab": weekday_crosstab,
    }


def task_4_document_hypothesis(
    df,
    investigation,
    segment_results,
):
    """
    Task 4:
    Document observation, evidence, hypothesis and actions.
    """

    problem_day = investigation["problem_day"]
    problem_hour = investigation["problem_hour"]
    anomaly_detected = investigation["anomaly_detected"]

    problem_window = segment_results["problem_window"]

    if anomaly_detected:
        observation = (
            f"A statistically defined success-rate anomaly was detected "
            f"on {problem_day}."
        )
    else:
        observation = (
            f"No statistically defined daily anomaly was detected. "
            f"The lowest-success day selected for investigation was "
            f"{problem_day}."
        )

    if len(problem_window):
        problem_success = problem_window["success"].mean()
        problem_failure = problem_window["failure"].mean()
        problem_transactions = len(problem_window)
        problem_value = problem_window["amount"].sum()
    else:
        problem_success = np.nan
        problem_failure = np.nan
        problem_transactions = 0
        problem_value = 0

    report = f"""
======================================================================
ROOT CAUSE INVESTIGATION REPORT
======================================================================

OBSERVATION
-----------
{observation}

Investigation date:
{problem_day}

Investigation hour:
{problem_hour:02d}:00-{problem_hour + 1:02d}:00

Transactions during selected period:
{problem_transactions}

Transaction value during selected period:
${problem_value:,.2f}

Success rate during selected period:
{
    f"{problem_success:.1%}"
    if not pd.isna(problem_success)
    else "N/A"
}

Failure rate during selected period:
{
    f"{problem_failure:.1%}"
    if not pd.isna(problem_failure)
    else "N/A"
}


ANALYSIS
--------
The available transaction dataset contains:

- customer_id
- transaction_date
- amount
- status

The analysis therefore examined:

1. Daily success/failure patterns
2. Hourly success/failure patterns
3. Customer-level concentration
4. Transaction status
5. Transaction value
6. Day-of-week and hour relationships


UNAVAILABLE DIMENSIONS
----------------------
The repository does not contain:

- payment_method
- customer_type
- region
- device_type
- error_message
- payment-provider event logs

Therefore, these dimensions cannot be used as evidence.


HYPOTHESIS
----------
The available data supports investigation of a transaction-status/time
relationship, but it does NOT contain enough evidence to identify a
specific external payment processor, competitor, product bug, or
seasonal cause.

Confidence: LOW

Reason:
The dataset is extremely small and lacks the operational metadata
required to establish a causal root cause.


CORRELATION VS CAUSATION
------------------------
A concentration of failed transactions in a particular time period
would establish a temporal association.

It would NOT, by itself, prove that a payment provider or product bug
caused the failures.

Additional evidence such as payment-provider logs, application error
logs, payment method, geography, device information, and deployment
history would be required for causal confirmation.


RECOMMENDED ACTIONS
-------------------
1. Capture payment_method for every transaction.
2. Capture customer_type and region.
3. Capture device_type.
4. Store structured error codes/messages.
5. Integrate payment-provider status and event logs.
6. Maintain higher-volume transaction history.
7. Add automated alerts for sudden success-rate changes.
8. Compare anomaly windows with deployment and infrastructure logs.


CONCLUSION
----------
The investigation framework successfully isolates the available time
and transaction dimensions.

However, the current repository data does not support confirmation of
the hypothetical Stripe outage or any other specific root cause.

The correct analytical conclusion is therefore:

"An anomaly/root-cause relationship cannot be conclusively established
from the available data. Additional operational evidence is required."
"""

    print(report)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {REPORT_FILE}")

    return report


def task_5_validate_hypothesis(
    df,
    investigation,
    correlation_results,
):
    """
    Task 5:
    Validate whether available evidence supports the hypothesis.
    """

    print("\n" + "=" * 70)
    print("TASK 5: HYPOTHESIS VALIDATION")
    print("=" * 70)

    problem_day = investigation["problem_day"]
    problem_hour = investigation["problem_hour"]

    problem_start = (
        pd.Timestamp(problem_day)
        + pd.Timedelta(hours=problem_hour)
    )

    problem_end = problem_start + pd.Timedelta(hours=1)

    problem_data = df[
        (df["transaction_date"] >= problem_start)
        & (df["transaction_date"] < problem_end)
    ]

    print("\nHYPOTHESIS VALIDATION")
    print("-" * 50)

    print(
        f"Selected investigation period: "
        f"{problem_start} to {problem_end}"
    )

    print(
        f"Transactions in period: {len(problem_data)}"
    )

    if len(problem_data):
        print(
            f"Failure rate: "
            f"{problem_data['failure'].mean():.1%}"
        )
    else:
        print("Failure rate: N/A")

    print("\nExternal evidence:")
    print("✗ No payment-provider status data available")
    print("✗ No application error logs available")
    print("✗ No payment-method field available")
    print("✗ No deployment/infrastructure event log available")

    print("\nConclusion:")
    print(
        "HYPOTHESIS NOT CONFIRMED — available internal data "
        "is insufficient for causal confirmation."
    )


def main():

    print("=" * 70)
    print("ROOT CAUSE INVESTIGATION WORKFLOW")
    print("=" * 70)

    print("\nLoading transaction data...")

    df = load_data()

    print(f"Dataset: {TRANSACTION_FILE}")
    print(f"Rows: {len(df)}")
    print(f"Date range: {df['transaction_date'].min()} "
          f"to {df['transaction_date'].max()}")

    investigation = task_1_time_isolation(df)

    segment_results = task_2_segment_analysis(
        df,
        investigation["problem_day"],
        investigation["problem_hour"],
    )

    correlation_results = task_3_correlation_analysis(
        df,
        investigation["problem_day"],
        investigation["problem_hour"],
    )

    task_4_document_hypothesis(
        df,
        investigation,
        segment_results,
    )

    task_5_validate_hypothesis(
        df,
        investigation,
        correlation_results,
    )

    print("\n" + "=" * 70)
    print("ROOT CAUSE INVESTIGATION COMPLETE")
    print("=" * 70)
    print(f"Report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
