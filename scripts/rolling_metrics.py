"""
Time-Series Trend & Rolling Metrics Analysis
Project: HirePulse

This script:
1. Resamples offer salary data weekly and monthly
2. Calculates 7-day and 30-day rolling averages
3. Calculates month-over-month percentage changes
4. Calculates cumulative offer salary value
5. Identifies the overall trend
6. Generates visualizations
7. Saves a business interpretation report
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/offers.csv"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 1. LOAD AND PREPARE DATA
# ============================================================

print("=" * 70)
print("TIME-SERIES TREND & ROLLING METRICS ANALYSIS")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

# Convert date column to datetime
df["offer_date"] = pd.to_datetime(df["offer_date"])

# Sort chronologically
df = df.sort_values("offer_date").reset_index(drop=True)

print("\nDATA OVERVIEW")
print("-" * 70)
print(f"Rows: {len(df)}")
print(f"Date range: {df['offer_date'].min().date()} to "
      f"{df['offer_date'].max().date()}")
print(f"Total offer salary value: ${df['salary'].sum():,.0f}")


# ============================================================
# 2. CREATE DAILY TIME SERIES
# ============================================================

# Aggregate multiple offers occurring on the same day
daily = (
    df.groupby("offer_date")
    .agg(
        offer_salary_value=("salary", "sum"),
        offer_count=("candidate_id", "count"),
        average_offer_salary=("salary", "mean")
    )
    .sort_index()
)

# Create a continuous daily index so missing dates are represented
full_dates = pd.date_range(
    start=daily.index.min(),
    end=daily.index.max(),
    freq="D"
)

daily = daily.reindex(full_dates)

daily.index.name = "date"

# No offer on a date = zero offer activity
daily["offer_salary_value"] = daily["offer_salary_value"].fillna(0)
daily["offer_count"] = daily["offer_count"].fillna(0)

# Average salary should remain missing when there were no offers
# because there is no average to calculate on those dates.
daily["average_offer_salary"] = daily["average_offer_salary"].fillna(0)


# ============================================================
# TASK 1: RESAMPLE DATA BY TIME PERIOD
# ============================================================

print("\n" + "=" * 70)
print("TASK 1: RESAMPLING")
print("=" * 70)

# Weekly aggregation
weekly_revenue = daily["offer_salary_value"].resample("W").sum()
weekly_count = daily["offer_count"].resample("W").sum()
weekly_avg = daily["offer_salary_value"].resample("W").mean()

# Monthly aggregation
monthly_revenue = daily["offer_salary_value"].resample("ME").sum()
monthly_count = daily["offer_count"].resample("ME").sum()
monthly_avg = daily["offer_salary_value"].resample("ME").mean()

print("\nWEEKLY OFFER SALARY VALUE")
print(weekly_revenue)

print("\nWEEKLY OFFER COUNT")
print(weekly_count)

print("\nWEEKLY AVERAGE DAILY OFFER SALARY VALUE")
print(weekly_avg)

print("\nMONTHLY OFFER SALARY VALUE")
print(monthly_revenue)

print("\nMONTHLY OFFER COUNT")
print(monthly_count)

# Highest-revenue periods
highest_week = weekly_revenue.idxmax()
highest_week_value = weekly_revenue.max()

highest_month = monthly_revenue.idxmax()
highest_month_value = monthly_revenue.max()

print("\nHIGHEST REVENUE PERIODS")
print(
    f"Highest week: {highest_week.date()} - "
    f"${highest_week_value:,.0f}"
)
print(
    f"Highest month: {highest_month.strftime('%B %Y')} - "
    f"${highest_month_value:,.0f}"
)


# ============================================================
# TASK 2: ROLLING WINDOW AVERAGES
# ============================================================

print("\n" + "=" * 70)
print("TASK 2: ROLLING WINDOW AVERAGES")
print("=" * 70)

# 7-day rolling average
daily["revenue_ma7"] = (
    daily["offer_salary_value"]
    .rolling(window=7, min_periods=7)
    .mean()
)

# 30-day rolling average
daily["revenue_ma30"] = (
    daily["offer_salary_value"]
    .rolling(window=30, min_periods=30)
    .mean()
)

print("\nLatest 7-day rolling average:")
print(f"${daily['revenue_ma7'].iloc[-1]:,.2f}")

print("\nLatest 30-day rolling average:")
print(f"${daily['revenue_ma30'].iloc[-1]:,.2f}")

# Plot raw data vs rolling averages
plt.figure(figsize=(14, 7))

plt.plot(
    daily.index,
    daily["offer_salary_value"],
    label="Raw Daily Offer Salary",
    alpha=0.35
)

plt.plot(
    daily.index,
    daily["revenue_ma7"],
    label="7-Day Rolling Average",
    linewidth=2
)

plt.plot(
    daily.index,
    daily["revenue_ma30"],
    label="30-Day Rolling Average",
    linewidth=2
)

plt.title("Daily Offer Salary Value vs Rolling Averages")
plt.xlabel("Date")
plt.ylabel("Offer Salary Value ($)")
plt.legend()
plt.grid(alpha=0.25)
plt.tight_layout()

plt.savefig(
    os.path.join(OUTPUT_DIR, "rolling_avg.png"),
    dpi=150
)

plt.close()

print("\nSaved: output/rolling_avg.png")


# ============================================================
# TASK 3: MONTH-OVER-MONTH PERCENTAGE CHANGE
# ============================================================

print("\n" + "=" * 70)
print("TASK 3: MONTH-OVER-MONTH CHANGE")
print("=" * 70)

mom_change = monthly_revenue.pct_change() * 100

print("\nMONTHLY PERCENTAGE CHANGE")
print(mom_change)

# Positive-growth months
growth_months = mom_change[mom_change > 0]

# Negative-growth months
decline_months = mom_change[mom_change < 0]

# Stable months
stable_months = mom_change[mom_change == 0]

print("\nMONTHS WITH POSITIVE GROWTH")
if len(growth_months) > 0:
    for date, change in growth_months.items():
        print(f"{date.strftime('%B %Y')}: +{change:.2f}%")
else:
    print("None")

print("\nMONTHS WITH DECLINE")
if len(decline_months) > 0:
    for date, change in decline_months.items():
        print(f"{date.strftime('%B %Y')}: {change:.2f}%")
else:
    print("None")

print("\nSTABLE MONTHS")
if len(stable_months) > 0:
    for date, change in stable_months.items():
        print(f"{date.strftime('%B %Y')}: {change:.2f}%")
else:
    print("None")


# ============================================================
# TASK 4: CUMULATIVE SUM
# ============================================================

print("\n" + "=" * 70)
print("TASK 4: CUMULATIVE SUM")
print("=" * 70)

daily["cumulative_revenue"] = (
    daily["offer_salary_value"].cumsum()
)

total_accumulated = daily["cumulative_revenue"].iloc[-1]

print(
    f"\nTotal accumulated offer salary value: "
    f"${total_accumulated:,.0f}"
)

# Cumulative plot
plt.figure(figsize=(14, 7))

plt.plot(
    daily.index,
    daily["cumulative_revenue"],
    linewidth=2
)

plt.title("Cumulative Offer Salary Value Over Time")
plt.xlabel("Date")
plt.ylabel("Cumulative Offer Salary Value ($)")
plt.grid(alpha=0.25)
plt.tight_layout()

plt.savefig(
    os.path.join(OUTPUT_DIR, "cumulative.png"),
    dpi=150
)

plt.close()

print("Saved: output/cumulative.png")


# ============================================================
# TASK 5: TREND ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("TASK 5: TREND ANALYSIS")
print("=" * 70)

# Use the latest 30 available days
recent_ma30 = daily["revenue_ma30"].dropna().tail(30)

first_ma = recent_ma30.iloc[0]
last_ma = recent_ma30.iloc[-1]

trend_difference = last_ma - first_ma

if first_ma == 0:
    trend_magnitude = 0
else:
    trend_magnitude = (trend_difference / first_ma) * 100

# Determine trend direction
threshold = 1.0

if trend_magnitude > threshold:
    trend_direction = "up"
elif trend_magnitude < -threshold:
    trend_direction = "down"
else:
    trend_direction = "flat"


# Latest MoM value
latest_mom = mom_change.dropna().iloc[-1]

# Daily volatility
daily_volatility = daily["offer_salary_value"].std()

# Identify strongest growth and decline months
if len(growth_months) > 0:
    strongest_growth_month = growth_months.idxmax()
    strongest_growth_value = growth_months.max()
else:
    strongest_growth_month = None
    strongest_growth_value = None

if len(decline_months) > 0:
    strongest_decline_month = decline_months.idxmin()
    strongest_decline_value = decline_months.min()
else:
    strongest_decline_month = None
    strongest_decline_value = None


# Business implication
if trend_direction == "up":
    business_implication = (
        "The smoothed offer salary trend is increasing. "
        "This indicates that offer-value activity is growing over "
        "the recent period rather than the increase being caused "
        "only by isolated daily spikes."
    )
    suggested_action = (
        "Review the recruiting pipeline and capacity to determine "
        "what is driving the increase. If the increase is sustainable, "
        "maintain sufficient recruiting and onboarding capacity."
    )

elif trend_direction == "down":
    business_implication = (
        "The smoothed offer salary trend is decreasing. "
        "This indicates weakening offer-value activity across "
        "the recent period."
    )
    suggested_action = (
        "Investigate candidate volume, interview throughput, offer "
        "acceptance, and recruiting bottlenecks before making changes "
        "to hiring strategy."
    )

else:
    business_implication = (
        "The smoothed offer salary trend is relatively stable. "
        "Daily fluctuations exist, but there is no strong sustained "
        "direction in the recent 30-day rolling metric."
    )
    suggested_action = (
        "Maintain the current process while monitoring the rolling "
        "average and monthly changes for signs of acceleration or decline."
    )


# ============================================================
# SAVE TREND ANALYSIS
# ============================================================

analysis = f"""
TIME-SERIES TREND ANALYSIS
==========================

Dataset:
HirePulse offers.csv

Analysis period:
{daily.index.min().date()} to {daily.index.max().date()}

Total accumulated offer salary value:
${total_accumulated:,.0f}

Highest weekly offer salary value:
{highest_week.date()} -> ${highest_week_value:,.0f}

Highest monthly offer salary value:
{highest_month.strftime('%B %Y')} -> ${highest_month_value:,.0f}


ROLLING METRICS
---------------

Latest 7-day rolling average:
${daily['revenue_ma7'].iloc[-1]:,.2f}

Latest 30-day rolling average:
${daily['revenue_ma30'].iloc[-1]:,.2f}

Recent 30-day rolling-average trend:
{trend_direction.upper()}

Change in 30-day rolling average:
{trend_magnitude:.2f}%


MONTH-OVER-MONTH ANALYSIS
-------------------------

Latest month-over-month change:
{latest_mom:.2f}%

Positive-growth months:
{len(growth_months)}

Declining months:
{len(decline_months)}

Stable months:
{len(stable_months)}

Strongest positive month-over-month change:
{(
    strongest_growth_month.strftime('%B %Y')
    + ' -> +' + f'{strongest_growth_value:.2f}%'
    if strongest_growth_month is not None
    else 'None'
)}

Strongest negative month-over-month change:
{(
    strongest_decline_month.strftime('%B %Y')
    + ' -> ' + f'{strongest_decline_value:.2f}%'
    if strongest_decline_month is not None
    else 'None'
)}


VOLATILITY
----------

Daily offer salary-value standard deviation:
${daily_volatility:,.2f}


BUSINESS INTERPRETATION
-----------------------

{business_implication}

Suggested action:
{suggested_action}


TIME-SERIES OBSERVATION
-----------------------

Raw daily data contains gaps and fluctuations because offers do not
occur every day. Resampling converts these observations into weekly
and monthly summaries. The 7-day rolling average smooths short-term
daily noise, while the 30-day rolling average provides a broader view
of the underlying direction.

A positive .pct_change() means the current month's offer salary value
increased compared with the previous month. A negative value means it
decreased.

Missing calendar dates were explicitly added to the time series and
their offer activity was represented as zero. This prevents gaps in
the date index from being ignored during rolling-window calculations.

IMPORTANT:
This analysis uses "offer salary value" as the business metric because
HirePulse is a recruitment dataset and does not contain actual revenue.
Salary values represent the total salary attached to offers, not company
revenue.
"""

with open(
    os.path.join(OUTPUT_DIR, "trend_analysis.txt"),
    "w",
    encoding="utf-8"
) as file:
    file.write(analysis.strip())

print("\nSaved: output/trend_analysis.txt")


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

print(f"Trend direction: {trend_direction.upper()}")
print(f"Trend magnitude: {trend_magnitude:.2f}%")
print(f"Latest MoM change: {latest_mom:.2f}%")
print(f"Total accumulated: ${total_accumulated:,.0f}")
print(f"Daily volatility: ${daily_volatility:,.2f}")

print("\nGenerated files:")
print("  output/rolling_avg.png")
print("  output/cumulative.png")
print("  output/trend_analysis.txt")

print("\nAnalysis complete.")