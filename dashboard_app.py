"""
Executive Business Performance Dashboard
A 4-level progressive disclosure dashboard built with Streamlit, Pandas, and Matplotlib.

Level 1: Status (Top KPIs)
Level 2: Trends (Time-series line charts with targets)
Level 3: Segments (Breakdown by customer tier)
Level 4: Detail / Progressive Disclosure (Dynamic data explorer with filtering & export)
"""

import os
from pathlib import Path
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Executive Business Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Output directory setup
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Custom Styling & Colors
COLOR_PRIMARY = "#1E88E5"     # Tech Blue for primary metrics & lines
COLOR_SECONDARY = "#0EA5E9"   # Light Blue for secondary metrics
COLOR_SUCCESS = "#10B981"     # Emerald Green for positive trends
COLOR_WARNING = "#EF4444"     # Rose Red for churn / negative metrics
COLOR_TARGET = "#64748B"      # Slate Gray for reference/target lines
COLOR_BG_LIGHT = "#F8FAFC"

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

# ==============================================================================
# SAMPLE DATA GENERATION
# ==============================================================================

@st.cache_data
def get_trend_data():
    months = pd.date_range('2024-01-01', periods=12, freq='MS')
    revenue = [4.2, 4.5, 4.8, 4.6, 5.0, 5.1, 4.9, 4.7, 5.2, 5.4, 5.5, 5.2]
    active_customers = [2350, 2380, 2410, 2390, 2430, 2450, 2440, 2420, 2460, 2480, 2510, 2500]
    churned_customers = [125, 120, 115, 130, 118, 112, 122, 128, 115, 110, 105, 120]
    aov = [132, 135, 138, 136, 140, 142, 141, 139, 143, 144, 146, 145]
    
    df_trends = pd.DataFrame({
        'month': months,
        'revenue': revenue,
        'active_customers': active_customers,
        'churned_customers': churned_customers,
        'aov': aov
    })
    return df_trends

@st.cache_data
def get_segment_data():
    segments = ['Enterprise', 'Mid-Market', 'SMB', 'Starter']
    segment_revenue = [2.1, 1.5, 1.0, 0.6]
    return pd.DataFrame({'segment': segments, 'revenue': segment_revenue})

@st.cache_data
def get_customer_dataset():
    np.random.seed(42)
    segments = ['Enterprise', 'Mid-Market', 'SMB', 'Starter']
    churn_risks = ['Low', 'Medium', 'High']
    
    records = []
    start_date = datetime.date(2024, 1, 1)
    end_date = datetime.date(2024, 12, 31)
    date_range_days = (end_date - start_date).days
    
    for i in range(1, 41):
        seg = np.random.choice(segments, p=[0.25, 0.30, 0.30, 0.15])
        if seg == 'Enterprise':
            rev = np.random.randint(50000, 150000)
        elif seg == 'Mid-Market':
            rev = np.random.randint(15000, 50000)
        elif seg == 'SMB':
            rev = np.random.randint(3000, 15000)
        else:
            rev = np.random.randint(500, 3000)
            
        random_days = np.random.randint(0, date_range_days)
        last_act = start_date + datetime.timedelta(days=int(random_days))
        risk = np.random.choice(churn_risks, p=[0.6, 0.25, 0.15])
        
        records.append({
            'customer_id': f'CUST-{1000 + i}',
            'segment': seg,
            'revenue': rev,
            'last_activity': last_act,
            'churn_risk': risk
        })
        
    return pd.DataFrame(records)

# ==============================================================================
# CHART GENERATION & EXPORT FUNCTIONS
# ==============================================================================

def create_revenue_trend_chart(df_trends):
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    ax.plot(df_trends['month'], df_trends['revenue'], marker='o', color=COLOR_PRIMARY, linewidth=2.5, label='Monthly Revenue ($M)')
    
    # Reference/Target line
    ax.axhline(5.0, color=COLOR_TARGET, linestyle='--', linewidth=1.8, label='Target ($5.0M)')
    
    # Annotations
    max_idx = df_trends['revenue'].idxmax()
    max_month = df_trends.loc[max_idx, 'month']
    max_rev = df_trends.loc[max_idx, 'revenue']
    ax.annotate(f'Peak: ${max_rev:.1f}M', xy=(max_month, max_rev), xytext=(max_month, max_rev + 0.25),
                arrowprops=dict(facecolor=COLOR_PRIMARY, shrink=0.08, width=1, headwidth=6),
                fontsize=9, fontweight='bold', ha='center')
    
    ax.set_title('Monthly Revenue Trend (2024)', fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Month', fontsize=10, labelpad=8)
    ax.set_ylabel('Revenue ($ Millions)', fontsize=10, labelpad=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.set_ylim(3.5, 6.0)
    ax.legend(loc='lower right', frameon=True)
    plt.tight_layout()
    
    # Save chart image to output folder
    fig.savefig(OUTPUT_DIR / "revenue_trend.png")
    return fig

def create_customer_metrics_chart(df_trends):
    fig, ax1 = plt.subplots(figsize=(10, 4.5), dpi=150)
    
    ax1.plot(df_trends['month'], df_trends['active_customers'], marker='s', color=COLOR_PRIMARY, linewidth=2.5, label='Active Customers')
    ax1.set_xlabel('Month', fontsize=10, labelpad=8)
    ax1.set_ylabel('Active Customers', fontsize=10, color=COLOR_PRIMARY, labelpad=8)
    ax1.tick_params(axis='y', labelcolor=COLOR_PRIMARY)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax1.set_ylim(2200, 2600)
    
    # Target Line for Active Customers
    ax1.axhline(2500, color=COLOR_TARGET, linestyle='--', linewidth=1.5, label='Target (2,500 Active)')
    
    ax2 = ax1.twinx()
    ax2.plot(df_trends['month'], df_trends['churned_customers'], marker='^', color=COLOR_WARNING, linewidth=2, linestyle=':', label='Churned Customers')
    ax2.set_ylabel('Churned Customers', fontsize=10, color=COLOR_WARNING, labelpad=8)
    ax2.tick_params(axis='y', labelcolor=COLOR_WARNING)
    ax2.set_ylim(80, 150)
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)
    
    plt.title('Active vs. Churned Customers (2024)', fontsize=13, fontweight='bold', pad=12)
    plt.tight_layout()
    
    fig.savefig(OUTPUT_DIR / "customer_metrics.png")
    return fig

def create_aov_trend_chart(df_trends):
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    ax.plot(df_trends['month'], df_trends['aov'], marker='d', color=COLOR_SECONDARY, linewidth=2.5, label='Average Order Value ($)')
    
    # Target Line
    ax.axhline(150, color=COLOR_TARGET, linestyle='--', linewidth=1.8, label='Target ($150)')
    
    # Annotation
    latest_aov = df_trends['aov'].iloc[-1]
    latest_month = df_trends['month'].iloc[-1]
    ax.annotate(f'Dec AOV: ${latest_aov}', xy=(latest_month, latest_aov), xytext=(latest_month, latest_aov - 4),
                arrowprops=dict(facecolor=COLOR_SECONDARY, shrink=0.08, width=1, headwidth=6),
                fontsize=9, fontweight='bold', ha='center')
    
    ax.set_title('Average Order Value (AOV) Trend (2024)', fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Month', fontsize=10, labelpad=8)
    ax.set_ylabel('Average Order Value ($)', fontsize=10, labelpad=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.set_ylim(120, 160)
    ax.legend(loc='lower right', frameon=True)
    plt.tight_layout()
    
    fig.savefig(OUTPUT_DIR / "aov_trend.png")
    return fig

def create_segment_revenue_chart(df_segment):
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    bars = ax.barh(df_segment['segment'], df_segment['revenue'], color=COLOR_PRIMARY, height=0.55)
    
    ax.set_title('Revenue by Customer Segment', fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Revenue ($ Millions)', fontsize=10, labelpad=8)
    ax.set_ylabel('Customer Segment', fontsize=10, labelpad=8)
    ax.invert_yaxis()  # Highest revenue on top
    ax.set_xlim(0, 2.5)
    
    # Data labels on bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, f'${width:.1f}M',
                ha='left', va='center', fontsize=10, fontweight='bold', color='#1E293B')
        
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "revenue_by_segment.png")
    return fig

# Pre-generate & save all charts to disk for requirements compliance
df_trends_data = get_trend_data()
df_segment_data = get_segment_data()
create_revenue_trend_chart(df_trends_data)
create_customer_metrics_chart(df_trends_data)
create_aov_trend_chart(df_trends_data)
create_segment_revenue_chart(df_segment_data)

# ==============================================================================
# DASHBOARD LAYOUT & RENDER
# ==============================================================================

# Sidebar Filters
st.sidebar.title("🎛️ Data Explorer Filters")
st.sidebar.markdown("Filter customer records in **Level 4 Detail Explorer**.")

customer_df = get_customer_dataset()

segment_options = ["All"] + list(customer_df['segment'].unique())
selected_segment = st.sidebar.selectbox("Customer Segment", segment_options, index=0)

min_date = customer_df['last_activity'].min()
max_date = customer_df['last_activity'].max()

selected_date_range = st.sidebar.date_input(
    "Last Activity Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# App Title & Header
st.title("📈 Executive Business Performance Dashboard")
st.markdown("""
This dashboard provides a structured 4-level overview of annual performance metrics, time-series trends, customer segment breakdowns, and detailed customer record exploration.
""")
st.divider()

# ------------------------------------------------------------------------------
# LEVEL 1 — STATUS (5 KPI Cards)
# ------------------------------------------------------------------------------
st.header("Level 1 — Executive Status (KPIs)")
st.caption("Top-level summary metrics showing current operational state and period-over-period percentage changes.")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Revenue", value="$5.2M", delta="+12.5%")
with col2:
    st.metric(label="Active Customers", value="2,500", delta="+5.2%")
with col3:
    st.metric(label="Average Order Value", value="$145", delta="+3.1%")
with col4:
    st.metric(label="Churn Rate", value="4.8%", delta="-1.2%", delta_color="inverse")
with col5:
    st.metric(label="NPS Score", value="72", delta="+4")

st.divider()

# ------------------------------------------------------------------------------
# LEVEL 2 — TRENDS (3 Trend Charts)
# ------------------------------------------------------------------------------
st.header("Level 2 — Business Trends (2024)")
st.caption("Time-series tracking of key indicators against strategic target reference lines.")

tab1, tab2, tab3 = st.tabs(["📉 Revenue Trend", "👥 Customer Dynamics", "🛒 Average Order Value"])

with tab1:
    st.subheader("Monthly Revenue vs. $5.0M Target")
    fig_rev = create_revenue_trend_chart(df_trends_data)
    st.pyplot(fig_rev, width="stretch")
    st.info("💡 **Insight**: Monthly revenue surpassed the $5.0M target in May 2024 and peaked in November at $5.5M driven by Q4 promotional campaigns.")

with tab2:
    st.subheader("Active Customer Growth vs. Churn Volume")
    fig_cust = create_customer_metrics_chart(df_trends_data)
    st.pyplot(fig_cust, width="stretch")
    st.info("💡 **Insight**: Active customers steadily expanded to reach the 2,500 target in December, while monthly churn stabilized between 105–130 accounts.")

with tab3:
    st.subheader("Average Order Value (AOV) Progression")
    fig_aov = create_aov_trend_chart(df_trends_data)
    st.pyplot(fig_aov, width="stretch")
    st.info("💡 **Insight**: AOV expanded from $132 in Jan to $145 in Dec, approaching the $150 strategic benchmark as cross-selling adoption grew.")

st.divider()

# ------------------------------------------------------------------------------
# LEVEL 3 — SEGMENTS (Horizontal Bar Chart)
# ------------------------------------------------------------------------------
st.header("Level 3 — Customer Segment Performance")
st.caption("Breakdown of total revenue contributions by customer tier.")

fig_seg = create_segment_revenue_chart(df_segment_data)
st.pyplot(fig_seg, width="stretch")

st.markdown("""
> 📌 **Key Takeaway**: The **Enterprise** segment is the largest revenue driver ($2.1M out of $5.2M total revenue, accounting for ~40.4%), followed by **Mid-Market** ($1.5M). Enterprise and Mid-Market combined deliver over 69% of overall commercial revenue.
""")

st.divider()

# ------------------------------------------------------------------------------
# LEVEL 4 — DETAIL / PROGRESSIVE DISCLOSURE (Filtered Data Explorer)
# ------------------------------------------------------------------------------
st.header("Level 4 — Detailed Data Explorer")
st.caption("Drill down into individual customer records with interactive filters and data export.")

# Apply Sidebar Filters
filtered_df = customer_df.copy()

if selected_segment != "All":
    filtered_df = filtered_df[filtered_df['segment'] == selected_segment]

if isinstance(selected_date_range, (list, tuple)) and len(selected_date_range) == 2:
    start_filter, end_filter = selected_date_range
    filtered_df = filtered_df[
        (filtered_df['last_activity'] >= start_filter) & 
        (filtered_df['last_activity'] <= end_filter)
    ]

# Summary statistics of filtered view
col_count1, col_count2, col_export = st.columns([2, 2, 2])
with col_count1:
    st.metric(label="Filtered Records", value=f"{len(filtered_df)} / {len(customer_df)}")
with col_count2:
    total_filt_rev = filtered_df['revenue'].sum()
    st.metric(label="Filtered Revenue Total", value=f"${total_filt_rev:,.2f}")
with col_export:
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Filtered CSV",
        data=csv_data,
        file_name="filtered_customer_records.csv",
        mime="text/csv",
        width="stretch"
    )

st.subheader("Customer Records Table")
st.dataframe(
    filtered_df.style.format({'revenue': '${:,.2f}'}),
    width="stretch",
    height=350
)


# Footer
st.markdown("---")
st.caption("Executive Business Performance Dashboard v1.0 | Built with Streamlit & Matplotlib")
