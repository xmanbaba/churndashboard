# =========================================================
# Telco Executive Dashboard - AI-Driven Forecasting
# =========================================================
# This Streamlit app demonstrates how executives in a Telco
# can use AI + Data-driven insights to simulate ARPU and
# churn rate scenarios, and understand their revenue impact.
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# --------------------------
# Page Configuration
# --------------------------
st.set_page_config(
    page_title="AI-Driven Telco Dashboard",
    layout="wide"
)

# --------------------------
# Title and Introduction
# --------------------------
st.title("📊 Telco Executive Dashboard: ARPU & Churn Forecasting")

st.markdown("""
Welcome to the **AI-Driven Telco Dashboard**.  
This interactive tool is designed for executives to:
- Understand the **impact of ARPU and Churn on revenue**
- Simulate **different business scenarios**
- Download results for **boardroom reporting**

💡 This demo is an example of how **AI leadership** can enable faster, data-driven decision-making.
""")

# =========================================================
# SIDEBAR - Simulation Controls
# =========================================================
st.sidebar.header("⚙️ Simulation Controls")

# Forecast horizon
months = st.sidebar.slider(
    "Forecast Horizon (Months)",
    min_value=6,
    max_value=36,
    value=12
)

# Base ARPU and growth
base_arpu = st.sidebar.number_input(
    "Base ARPU ($)",
    min_value=2.0,
    max_value=50.0,
    value=8.0,
    step=0.5
)

arpu_growth = st.sidebar.slider(
    "ARPU Monthly Growth Rate (%)",
    min_value=-5.0,
    max_value=10.0,
    value=2.0
)

# Churn assumptions
base_churn = st.sidebar.slider(
    "Base Monthly Churn Rate (%)",
    min_value=1.0,
    max_value=15.0,
    value=5.0
)

churn_trend = st.sidebar.slider(
    "Churn Monthly Change (bps)",
    min_value=-50,
    max_value=50,
    value=-10
)

# Subscriber base
starting_subs = st.sidebar.number_input(
    "Starting Subscribers (Millions)",
    min_value=0.1,
    max_value=50.0,
    value=5.0
)

# =========================================================
# FORECAST MODEL
# =========================================================
months_range = np.arange(1, months + 1)

# ARPU projection
arpu = [
    base_arpu * ((1 + arpu_growth / 100) ** (m - 1))
    for m in months_range
]

# Churn projection (bps = basis points, 0.01%)
churn = [
    max(0.1, base_churn + (m - 1) * (churn_trend / 100))
    for m in months_range
]

# Subscriber base evolution
subscribers = [starting_subs * 1_000_000]
for m in range(1, months):
    prev_subs = subscribers[-1]
    retained = prev_subs * (1 - churn[m - 1] / 100)
    subscribers.append(retained)

# Revenue calculation
revenue = [
    subscribers[i] * arpu[i]
    for i in range(months)
]

# Assemble into DataFrame
df = pd.DataFrame({
    "Month": months_range,
    "ARPU ($)": np.round(arpu, 2),
    "Churn Rate (%)": np.round(churn, 2),
    "Subscribers": np.round(subscribers, 0),
    "Revenue ($)": np.round(revenue, 0)
})

# =========================================================
# VISUALIZATIONS
# =========================================================
st.markdown("## 📈 Forecast Visualizations")

# Chart 1: ARPU
fig1 = px.line(
    df, x="Month", y="ARPU ($)",
    title="ARPU Forecast",
    markers=True
)

# Chart 2: Churn Rate
fig2 = px.line(
    df, x="Month", y="Churn Rate (%)",
    title="Churn Rate Forecast",
    markers=True
)

# Chart 3: Revenue
fig3 = px.line(
    df, x="Month", y="Revenue ($)",
    title="Revenue Forecast",
    markers=True
)

# Display charts in columns
col1, col2, col3 = st.columns(3)
col1.plotly_chart(fig1, use_container_width=True)
col2.plotly_chart(fig2, use_container_width=True)
col3.plotly_chart(fig3, use_container_width=True)

# =========================================================
# FORECAST DATA TABLE
# =========================================================
st.markdown("## 📑 Forecast Data Table")

st.dataframe(df, use_container_width=True)

# =========================================================
# EXCEL EXPORT
# =========================================================
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """
    Convert DataFrame into Excel bytes for download.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Scenarios")
    output.seek(0)
    return output.getvalue()

excel_bytes = to_excel_bytes(df)

st.download_button(
    label="📥 Download Forecast Data (Excel)",
    data=excel_bytes,
    file_name="telco_forecast.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================================================
# EXECUTIVE INSIGHTS
# =========================================================
st.markdown("## 🔎 Executive Insights")

st.markdown(f"""
- **Starting Subscribers:** {starting_subs:.1f}M  
- **Final Subscribers after {months} months:** {df['Subscribers'].iloc[-1]:,.0f}  
- **Final ARPU:** ${df['ARPU ($)'].iloc[-1]:.2f}  
- **Total Revenue:** ${df['Revenue ($)'].sum():,.0f}  

💡 *Observation:*  
Even small changes in **ARPU growth** or **Churn rate** have a massive 
impact on revenue. This dashboard shows how executives can test different 
scenarios and adjust **pricing, promotions, and retention strategies** 
to sustain growth.
""")

# =========================================================
# END OF APP
# =========================================================
