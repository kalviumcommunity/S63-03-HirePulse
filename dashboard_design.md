# Executive Business Performance Dashboard — Design Documentation

## 1. Executive Summary & Overview
The **Executive Business Performance Dashboard** is an analytics application built using **Streamlit**, **Pandas**, and **Matplotlib**. It organizes business performance indicators into a strict **4-level information hierarchy** following the principle of **Progressive Disclosure** (summary metrics at the top, granular customer records at the bottom).

---

## 2. Information Hierarchy Architecture

The dashboard is structured into four distinct analytical levels:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 1 — STATUS (Top 5 KPI Cards)                                     │
│ Executive high-level health summary: Revenue, Customers, AOV, Churn    │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 2 — TRENDS (Time-Series Charts)                                  │
│ 12-Month trends with target reference lines & annotations              │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 3 — SEGMENTS (Horizontal Bar Breakdown)                          │
│ Customer tier revenue contributions & strategic composition            │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 4 — DETAIL / PROGRESSIVE DISCLOSURE (Data Explorer)             │
│ Interactive filtering by segment & date range with CSV export         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Level 1: Key Performance Indicators (KPI Selection & Rationale)

| KPI Card | Current Value | Delta | Selection Rationale |
| :--- | :--- | :--- | :--- |
| **Revenue** | `$5.2M` | `+12.5%` | Primary top-line financial indicator assessing overall business scale and growth trajectory. |
| **Active Customers** | `2,500` | `+5.2%` | Core customer base health metric reflecting customer acquisition and retention momentum. |
| **Average Order Value (AOV)** | `$145` | `+3.1%` | Measures customer purchasing power and cross-selling / up-selling effectiveness. |
| **Churn Rate** | `4.8%` | `-1.2%` | Critical customer health metric; lowering churn directly preserves recurring revenue. |
| **NPS Score** | `72` | `+4` | Leading indicator of customer satisfaction, product-market fit, and organic brand advocacy. |

---

## 4. Level 2: Business Trend Analysis

### Chart 1: Monthly Revenue Trend (2024)
* **Visual Format**: Line chart with `$5.0M` target reference line.
* **Key Findings**: Revenue grew from `$4.2M` in January to peak at `$5.5M` in November. Surpassed the target threshold in May 2024 (`$5.0M`), demonstrating accelerating H2 performance.
* **Saved Image**: `output/revenue_trend.png`

### Chart 2: Active vs. Churned Customers (2024)
* **Visual Format**: Dual-axis line chart tracking Active Customer volume against Monthly Churn count with a `2,500` active account target line.
* **Key Findings**: Active customer count steadily expanded from `2,350` to meet the `2,500` target in December. Monthly churn volume remained controlled between `105` and `130` accounts.
* **Saved Image**: `output/customer_metrics.png`

### Chart 3: Average Order Value Trend (2024)
* **Visual Format**: Time-series line chart with `$150` target benchmark line.
* **Key Findings**: AOV steadily increased from `$132` in January to `$145` by year-end, narrowing the gap to the `$150` strategic milestone.
* **Saved Image**: `output/aov_trend.png`

---

## 5. Level 3: Segment Analysis

* **Visual Format**: Horizontal bar chart with explicit data labels.
* **Data Breakdown**:
  * **Enterprise**: `$2.1M` (40.4%)
  * **Mid-Market**: `$1.5M` (28.8%)
  * **SMB**: `$1.0M` (19.2%)
  * **Starter**: `$0.6M` (11.5%)
* **Strategic Value**: Identifies Enterprise and Mid-Market tiers as the primary revenue engines, contributing **69.2%** of total commercial revenue.
* **Saved Image**: `output/revenue_by_segment.png`

---

## 6. Level 4: Progressive Disclosure & Detail Explorer

The **Detailed Data Explorer** section fulfills the requirement of progressive disclosure by allowing analysts to inspect row-level customer data only when deep investigation is needed.

### Features:
1. **Dynamic Segment Filtering**: Filter records by Enterprise, Mid-Market, SMB, or Starter.
2. **Date Range Filtering**: Filter by customer `last_activity` date across 2024.
3. **Live Metrics**: Displays dynamic record counts (`X / 40`) and filtered revenue totals.
4. **CSV Export**: `st.download_button` exports exactly the filtered table subset to `filtered_customer_records.csv`.

---

## 7. Core Design Principles & Palette

1. **Progressive Disclosure**: High-level summaries first, granular operational details on demand.
2. **Spatial Organization**: Top-level executive metrics occupy prime screen real estate at the very top.
3. **Consistent Visual Language**:
   * **Primary Accent (Tech Blue)**: `#1E88E5` (Main metric trends, active counts)
   * **Secondary Accent (Sky Blue)**: `#0EA5E9` (AOV metrics)
   * **Success Green**: `#10B981` (Positive deltas and growth indicators)
   * **Warning / Churn Red**: `#EF4444` (Churn rate, churned account counts)
   * **Target / Reference Gray**: `#64748B` (Dashed reference lines for target goals)
4. **Context Over Raw Numbers**: Every metric and chart includes period-over-period delta comparisons or reference target benchmarks.

---

## 8. Target Audience & Stakeholder Mapping

| Target Audience | Dashboard Level | Primary Usage & Value |
| :--- | :--- | :--- |
| **CEO / Executive Team** | Level 1 & Level 2 | Instant high-level business health check via 5 status cards and revenue trend performance against annual targets. |
| **VP of Sales & Marketing** | Level 2 & Level 3 | Evaluates customer acquisition growth vs. churn and assesses segment revenue contribution to guide budget allocation. |
| **Data Analysts & Operations** | Level 4 | Filters customer records by date and tier to investigate churn risk or export datasets for deeper modeling. |

---

## 9. Data Sources & Schema

* **Type**: Synthesized business performance sample datasets (reproducible without external API dependencies or database credentials).
* **Granularity**: Monthly aggregated metrics for trend lines and row-level customer dataset (40 records with `customer_id`, `segment`, `revenue`, `last_activity`, `churn_risk`).
