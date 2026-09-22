from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "data" / "raw" / "transactions.csv"
OUTPUT_DIR = ROOT / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ANOMALY_LOG_PATH = OUTPUT_DIR / "anomalies_log.csv"
PLOT_PATH = OUTPUT_DIR / "anomaly_detection.png"


# Business thresholds from the assignment
ALERT_RULES = {
    "daily_revenue": {"min": 5000, "max": 50000},
    "transaction_count": {"min": 100, "max": 10000},
    "signup_rate": {"min": 10, "max": 500},
}


# ============================================================
# LOAD DATA
# ============================================================

def load_transactions():
    """Load and validate transaction data."""
    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "customer_id",
        "transaction_date",
        "amount",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce"
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["transaction_date", "amount"]
    ).copy()

    return df


# ============================================================
# TASK 1: THRESHOLD-BASED ANOMALY DETECTION
# ============================================================

def check_thresholds(metrics, rules):
    """Alert if metrics are outside business thresholds."""

    alerts = []

    for metric_name, rule in rules.items():

        if metric_name not in metrics:
            continue

        value = metrics[metric_name]

        if value < rule["min"]:
            alerts.append({
                "metric": metric_name,
                "value": value,
                "threshold": rule["min"],
                "direction": "BELOW_MIN",
                "severity": "HIGH",
            })

        elif value > rule["max"]:
            alerts.append({
                "metric": metric_name,
                "value": value,
                "threshold": rule["max"],
                "direction": "ABOVE_MAX",
                "severity": "MEDIUM",
            })

    return alerts


# ============================================================
# TASK 2: Z-SCORE ANOMALY DETECTION
# ============================================================

def detect_anomalies_zscore(series, threshold=2):
    """
    Detect values whose absolute z-score exceeds threshold.

    The calculation is made against the available historical
    observations within the 30-day lookback window.
    """

    mean = series.mean()
    std = series.std()

    if pd.isna(std) or std == 0:
        z_scores = pd.Series(
            0.0,
            index=series.index
        )

        anomalies = series.iloc[0:0]

        return anomalies, z_scores, mean, std

    z_scores = (series - mean) / std

    anomalies = series[
        z_scores.abs() > threshold
    ]

    return anomalies, z_scores, mean, std


# ============================================================
# TASK 3: SEVERITY CLASSIFICATION
# ============================================================

def classify_severity(value, mean, std):
    """Classify anomaly severity using z-score thresholds."""

    if pd.isna(std) or std == 0:
        return "LOW"

    z_score = abs((value - mean) / std)

    if z_score > 3:
        return "CRITICAL"

    elif z_score > 2:
        return "HIGH"

    elif z_score > 1.5:
        return "MEDIUM"

    else:
        return "LOW"


# ============================================================
# BUILD DAILY REVENUE
# ============================================================

def build_daily_metrics(df):

    daily = (
        df.assign(
            date=df["transaction_date"].dt.normalize()
        )
        .groupby("date")
        .agg(
            daily_revenue=("amount", "sum"),
            transaction_count=("customer_id", "count"),
        )
        .sort_index()
    )

    return daily


# ============================================================
# TASK 5: VISUALIZATION
# ============================================================

def create_visualization(
    daily,
    anomalies,
    mean,
    std
):
    """Create anomaly detection time-series visualization."""

    fig, ax = plt.subplots(
        figsize=(14, 6)
    )

    # Raw daily revenue
    ax.plot(
        daily.index,
        daily["daily_revenue"],
        marker="o",
        linewidth=2,
        label="Daily Revenue",
    )

    # 7-day rolling average
    rolling_avg = (
        daily["daily_revenue"]
        .rolling(window=7, min_periods=1)
        .mean()
    )

    ax.plot(
        rolling_avg.index,
        rolling_avg.values,
        linewidth=2,
        label="7-day Moving Average",
    )

    # Expected range
    if not pd.isna(std) and std > 0:

        lower = mean - 2 * std
        upper = mean + 2 * std

        ax.fill_between(
            daily.index,
            lower,
            upper,
            alpha=0.2,
            label="Expected Range ±2σ",
        )

    # Highlight anomalies
    if len(anomalies) > 0:

        ax.scatter(
            anomalies.index,
            anomalies.values,
            s=200,
            marker="X",
            zorder=5,
            label="Anomaly",
        )

        for date, value in anomalies.items():

            ax.annotate(
                "ANOMALY",
                (date, value),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontweight="bold",
            )

    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue ($)")
    ax.set_title(
        "Daily Revenue with Anomalies Flagged"
    )

    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(
        PLOT_PATH,
        dpi=150
    )

    plt.close()

    print(f"Visualization saved to: {PLOT_PATH}")


# ============================================================
# MAIN WORKFLOW
# ============================================================

def main():

    print("=" * 70)
    print("ANOMALY DETECTION & RISK IDENTIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = load_transactions()

    print("\nDATASET")
    print("-" * 70)
    print(f"Source: {DATA_PATH}")
    print(f"Transactions: {len(df)}")
    print(
        f"Date range: "
        f"{df['transaction_date'].min()} "
        f"to "
        f"{df['transaction_date'].max()}"
    )

    # --------------------------------------------------------
    # Daily metrics
    # --------------------------------------------------------

    daily = build_daily_metrics(df)

    print("\nDAILY REVENUE")
    print("-" * 70)
    print(daily)

    # --------------------------------------------------------
    # 30-day lookback
    # --------------------------------------------------------

    latest_date = daily.index.max()

    lookback_start = (
        latest_date - pd.Timedelta(days=29)
    )

    daily_30 = daily[
        daily.index >= lookback_start
    ].copy()

    print("\n30-DAY LOOKBACK")
    print("-" * 70)
    print(
        f"Lookback period: "
        f"{lookback_start.date()} "
        f"to "
        f"{latest_date.date()}"
    )

    print(
        f"Available observations: {len(daily_30)}"
    )

    # --------------------------------------------------------
    # TASK 1
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 1: THRESHOLD-BASED ANOMALY DETECTION")
    print("=" * 70)

    latest_revenue = daily_30["daily_revenue"].iloc[-1]
    latest_transactions = (
        daily_30["transaction_count"].iloc[-1]
    )

    # signup_rate is not available in transaction data.
    # It is intentionally not fabricated.
    current_metrics = {
        "daily_revenue": latest_revenue,
        "transaction_count": latest_transactions,
    }

    threshold_alerts = check_thresholds(
        current_metrics,
        ALERT_RULES
    )

    print("\nCurrent metrics:")

    for metric, value in current_metrics.items():
        print(f"  {metric}: {value}")

    print("\nThreshold alerts:")

    if threshold_alerts:

        for alert in threshold_alerts:

            print(
                f"  ⚠️ {alert['metric']} "
                f"{alert['direction']}: "
                f"{alert['value']} "
                f"(threshold: {alert['threshold']})"
            )

    else:

        print("  No threshold alerts.")

    print(
        "\nNote: signup_rate is unavailable in the "
        "transaction dataset and was not fabricated."
    )

    # --------------------------------------------------------
    # TASK 2
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 2: STATISTICAL Z-SCORE DETECTION")
    print("=" * 70)

    daily_revenue = daily_30[
        "daily_revenue"
    ]

    anomalies, z_scores, mean, std = (
        detect_anomalies_zscore(
            daily_revenue,
            threshold=2
        )
    )

    print(f"\nMean revenue: ${mean:.2f}")
    print(f"Standard deviation: ${std:.2f}")
    print(
        f"Detected {len(anomalies)} anomalies "
        f"out of {len(daily_revenue)} available days."
    )

    if len(anomalies) > 0:

        for date, value in anomalies.items():

            print(
                f"  {date.date()}: "
                f"${value:.2f} "
                f"(z-score: {z_scores[date]:.2f})"
            )

    else:

        print("  No values exceeded ±2 standard deviations.")

    # --------------------------------------------------------
    # TASK 3
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 3: SEVERITY CLASSIFICATION")
    print("=" * 70)

    severity_records = []

    for date, value in anomalies.items():

        severity = classify_severity(
            value,
            mean,
            std
        )

        severity_records.append({
            "date": date,
            "value": value,
            "z_score": z_scores[date],
            "severity": severity,
        })

    severity_df = pd.DataFrame(
        severity_records
    )

    if severity_df.empty:

        severity_df = pd.DataFrame(
            columns=[
                "date",
                "value",
                "z_score",
                "severity",
            ]
        )

    print("\nSeverity classification:")
    print(severity_df)

    high_severity = severity_df[
        severity_df["severity"].isin(
            ["CRITICAL", "HIGH"]
        )
    ]

    print(
        f"\n⚠️ High-severity anomalies requiring "
        f"investigation: {len(high_severity)}"
    )

    # --------------------------------------------------------
    # TASK 4
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 4: ANOMALY LOGGING & AUDIT TRAIL")
    print("=" * 70)

    anomaly_log = []

    expected_lower = (
        mean - 2 * std
        if not pd.isna(std)
        else np.nan
    )

    expected_upper = (
        mean + 2 * std
        if not pd.isna(std)
        else np.nan
    )

    for date, value in anomalies.items():

        severity = classify_severity(
            value,
            mean,
            std
        )

        anomaly_log.append({
            "timestamp": pd.Timestamp.now(),
            "anomaly_date": date,
            "metric": "daily_revenue",
            "value": value,
            "expected_range": (
                f"{expected_lower:.2f}-"
                f"{expected_upper:.2f}"
            ),
            "z_score": z_scores[date],
            "severity": severity,
            "status": "OPEN",
        })

    anomalies_df = pd.DataFrame(
        anomaly_log,
        columns=[
            "timestamp",
            "anomaly_date",
            "metric",
            "value",
            "expected_range",
            "z_score",
            "severity",
            "status",
        ]
    )

    anomalies_df.to_csv(
        ANOMALY_LOG_PATH,
        index=False
    )

    print(
        f"Logged {len(anomalies_df)} anomalies."
    )

    print(
        f"Audit log saved to: {ANOMALY_LOG_PATH}"
    )

    # --------------------------------------------------------
    # TASK 5
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 5: VISUALIZATION")
    print("=" * 70)

    create_visualization(
        daily_30,
        anomalies,
        mean,
        std
    )

    # --------------------------------------------------------
    # LIMITATIONS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DATA LIMITATIONS")
    print("=" * 70)

    print(
        "The available transaction dataset contains only "
        f"{len(df)} transactions."
    )

    print(
        "The available history covers fewer than 30 calendar days."
    )

    print(
        "Therefore, the 30-day monitoring window uses all "
        "available observations within the requested lookback."
    )

    print(
        "signup_rate is not present in the transaction dataset "
        "and is not fabricated."
    )

    print("\nANOMALY DETECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "data" / "raw" / "transactions.csv"
OUTPUT_DIR = ROOT / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ANOMALY_LOG_PATH = OUTPUT_DIR / "anomalies_log.csv"
PLOT_PATH = OUTPUT_DIR / "anomaly_detection.png"


# Business thresholds from the assignment
ALERT_RULES = {
    "daily_revenue": {"min": 5000, "max": 50000},
    "transaction_count": {"min": 100, "max": 10000},
    "signup_rate": {"min": 10, "max": 500},
}


# ============================================================
# LOAD DATA
# ============================================================

def load_transactions():
    """Load and validate transaction data."""
    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "customer_id",
        "transaction_date",
        "amount",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce"
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["transaction_date", "amount"]
    ).copy()

    return df


# ============================================================
# TASK 1: THRESHOLD-BASED ANOMALY DETECTION
# ============================================================

def check_thresholds(metrics, rules):
    """Alert if metrics are outside business thresholds."""

    alerts = []

    for metric_name, rule in rules.items():

        if metric_name not in metrics:
            continue

        value = metrics[metric_name]

        if value < rule["min"]:
            alerts.append({
                "metric": metric_name,
                "value": value,
                "threshold": rule["min"],
                "direction": "BELOW_MIN",
                "severity": "HIGH",
            })

        elif value > rule["max"]:
            alerts.append({
                "metric": metric_name,
                "value": value,
                "threshold": rule["max"],
                "direction": "ABOVE_MAX",
                "severity": "MEDIUM",
            })

    return alerts


# ============================================================
# TASK 2: Z-SCORE ANOMALY DETECTION
# ============================================================

def detect_anomalies_zscore(series, threshold=2):
    """
    Detect values whose absolute z-score exceeds threshold.

    The calculation is made against the available historical
    observations within the 30-day lookback window.
    """

    mean = series.mean()
    std = series.std()

    if pd.isna(std) or std == 0:
        z_scores = pd.Series(
            0.0,
            index=series.index
        )

        anomalies = series.iloc[0:0]

        return anomalies, z_scores, mean, std

    z_scores = (series - mean) / std

    anomalies = series[
        z_scores.abs() > threshold
    ]

    return anomalies, z_scores, mean, std


# ============================================================
# TASK 3: SEVERITY CLASSIFICATION
# ============================================================

def classify_severity(value, mean, std):
    """Classify anomaly severity using z-score thresholds."""

    if pd.isna(std) or std == 0:
        return "LOW"

    z_score = abs((value - mean) / std)

    if z_score > 3:
        return "CRITICAL"

    elif z_score > 2:
        return "HIGH"

    elif z_score > 1.5:
        return "MEDIUM"

    else:
        return "LOW"


# ============================================================
# BUILD DAILY REVENUE
# ============================================================

def build_daily_metrics(df):

    daily = (
        df.assign(
            date=df["transaction_date"].dt.normalize()
        )
        .groupby("date")
        .agg(
            daily_revenue=("amount", "sum"),
            transaction_count=("customer_id", "count"),
        )
        .sort_index()
    )

    return daily


# ============================================================
# TASK 5: VISUALIZATION
# ============================================================

def create_visualization(
    daily,
    anomalies,
    mean,
    std
):
    """Create anomaly detection time-series visualization."""

    fig, ax = plt.subplots(
        figsize=(14, 6)
    )

    # Raw daily revenue
    ax.plot(
        daily.index,
        daily["daily_revenue"],
        marker="o",
        linewidth=2,
        label="Daily Revenue",
    )

    # 7-day rolling average
    rolling_avg = (
        daily["daily_revenue"]
        .rolling(window=7, min_periods=1)
        .mean()
    )

    ax.plot(
        rolling_avg.index,
        rolling_avg.values,
        linewidth=2,
        label="7-day Moving Average",
    )

    # Expected range
    if not pd.isna(std) and std > 0:

        lower = mean - 2 * std
        upper = mean + 2 * std

        ax.fill_between(
            daily.index,
            lower,
            upper,
            alpha=0.2,
            label="Expected Range ±2σ",
        )

    # Highlight anomalies
    if len(anomalies) > 0:

        ax.scatter(
            anomalies.index,
            anomalies.values,
            s=200,
            marker="X",
            zorder=5,
            label="Anomaly",
        )

        for date, value in anomalies.items():

            ax.annotate(
                "ANOMALY",
                (date, value),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontweight="bold",
            )

    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue ($)")
    ax.set_title(
        "Daily Revenue with Anomalies Flagged"
    )

    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(
        PLOT_PATH,
        dpi=150
    )

    plt.close()

    print(f"Visualization saved to: {PLOT_PATH}")


# ============================================================
# MAIN WORKFLOW
# ============================================================

def main():

    print("=" * 70)
    print("ANOMALY DETECTION & RISK IDENTIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = load_transactions()

    print("\nDATASET")
    print("-" * 70)
    print(f"Source: {DATA_PATH}")
    print(f"Transactions: {len(df)}")
    print(
        f"Date range: "
        f"{df['transaction_date'].min()} "
        f"to "
        f"{df['transaction_date'].max()}"
    )

    # --------------------------------------------------------
    # Daily metrics
    # --------------------------------------------------------

    daily = build_daily_metrics(df)

    print("\nDAILY REVENUE")
    print("-" * 70)
    print(daily)

    # --------------------------------------------------------
    # 30-day lookback
    # --------------------------------------------------------

    latest_date = daily.index.max()

    lookback_start = (
        latest_date - pd.Timedelta(days=29)
    )

    daily_30 = daily[
        daily.index >= lookback_start
    ].copy()

    print("\n30-DAY LOOKBACK")
    print("-" * 70)
    print(
        f"Lookback period: "
        f"{lookback_start.date()} "
        f"to "
        f"{latest_date.date()}"
    )

    print(
        f"Available observations: {len(daily_30)}"
    )

    # --------------------------------------------------------
    # TASK 1
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 1: THRESHOLD-BASED ANOMALY DETECTION")
    print("=" * 70)

    latest_revenue = daily_30["daily_revenue"].iloc[-1]
    latest_transactions = (
        daily_30["transaction_count"].iloc[-1]
    )

    # signup_rate is not available in transaction data.
    # It is intentionally not fabricated.
    current_metrics = {
        "daily_revenue": latest_revenue,
        "transaction_count": latest_transactions,
    }

    threshold_alerts = check_thresholds(
        current_metrics,
        ALERT_RULES
    )

    print("\nCurrent metrics:")

    for metric, value in current_metrics.items():
        print(f"  {metric}: {value}")

    print("\nThreshold alerts:")

    if threshold_alerts:

        for alert in threshold_alerts:

            print(
                f"  ⚠️ {alert['metric']} "
                f"{alert['direction']}: "
                f"{alert['value']} "
                f"(threshold: {alert['threshold']})"
            )

    else:

        print("  No threshold alerts.")

    print(
        "\nNote: signup_rate is unavailable in the "
        "transaction dataset and was not fabricated."
    )

    # --------------------------------------------------------
    # TASK 2
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 2: STATISTICAL Z-SCORE DETECTION")
    print("=" * 70)

    daily_revenue = daily_30[
        "daily_revenue"
    ]

    anomalies, z_scores, mean, std = (
        detect_anomalies_zscore(
            daily_revenue,
            threshold=2
        )
    )

    print(f"\nMean revenue: ${mean:.2f}")
    print(f"Standard deviation: ${std:.2f}")
    print(
        f"Detected {len(anomalies)} anomalies "
        f"out of {len(daily_revenue)} available days."
    )

    if len(anomalies) > 0:

        for date, value in anomalies.items():

            print(
                f"  {date.date()}: "
                f"${value:.2f} "
                f"(z-score: {z_scores[date]:.2f})"
            )

    else:

        print("  No values exceeded ±2 standard deviations.")

    # --------------------------------------------------------
    # TASK 3
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 3: SEVERITY CLASSIFICATION")
    print("=" * 70)

    severity_records = []

    for date, value in anomalies.items():

        severity = classify_severity(
            value,
            mean,
            std
        )

        severity_records.append({
            "date": date,
            "value": value,
            "z_score": z_scores[date],
            "severity": severity,
        })

    severity_df = pd.DataFrame(
        severity_records
    )

    if severity_df.empty:

        severity_df = pd.DataFrame(
            columns=[
                "date",
                "value",
                "z_score",
                "severity",
            ]
        )

    print("\nSeverity classification:")
    print(severity_df)

    high_severity = severity_df[
        severity_df["severity"].isin(
            ["CRITICAL", "HIGH"]
        )
    ]

    print(
        f"\n⚠️ High-severity anomalies requiring "
        f"investigation: {len(high_severity)}"
    )

    # --------------------------------------------------------
    # TASK 4
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 4: ANOMALY LOGGING & AUDIT TRAIL")
    print("=" * 70)

    anomaly_log = []

    expected_lower = (
        mean - 2 * std
        if not pd.isna(std)
        else np.nan
    )

    expected_upper = (
        mean + 2 * std
        if not pd.isna(std)
        else np.nan
    )

    for date, value in anomalies.items():

        severity = classify_severity(
            value,
            mean,
            std
        )

        anomaly_log.append({
            "timestamp": pd.Timestamp.now(),
            "anomaly_date": date,
            "metric": "daily_revenue",
            "value": value,
            "expected_range": (
                f"{expected_lower:.2f}-"
                f"{expected_upper:.2f}"
            ),
            "z_score": z_scores[date],
            "severity": severity,
            "status": "OPEN",
        })

    anomalies_df = pd.DataFrame(
        anomaly_log,
        columns=[
            "timestamp",
            "anomaly_date",
            "metric",
            "value",
            "expected_range",
            "z_score",
            "severity",
            "status",
        ]
    )

    anomalies_df.to_csv(
        ANOMALY_LOG_PATH,
        index=False
    )

    print(
        f"Logged {len(anomalies_df)} anomalies."
    )

    print(
        f"Audit log saved to: {ANOMALY_LOG_PATH}"
    )

    # --------------------------------------------------------
    # TASK 5
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 5: VISUALIZATION")
    print("=" * 70)

    create_visualization(
        daily_30,
        anomalies,
        mean,
        std
    )

    # --------------------------------------------------------
    # LIMITATIONS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DATA LIMITATIONS")
    print("=" * 70)

    print(
        "The available transaction dataset contains only "
        f"{len(df)} transactions."
    )

    print(
        "The available history covers fewer than 30 calendar days."
    )

    print(
        "Therefore, the 30-day monitoring window uses all "
        "available observations within the requested lookback."
    )

    print(
        "signup_rate is not present in the transaction dataset "
        "and is not fabricated."
    )

    print("\nANOMALY DETECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
