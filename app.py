import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# ------------------------------
# Simulate Base Data
# ------------------------------
months = pd.date_range(start="2024-01-01", periods=12, freq="M")
np.random.seed(42)

arpu = np.random.uniform(4.5, 6.5, 12)                      # base ARPU ($)
churn_rate = np.random.uniform(2, 5, 12)                    # base churn %
customer_base = 500_000                                     # starting customers

customers = [customer_base]
for i in range(1, 12):
    churned = customers[i-1] * (churn_rate[i-1] / 100)
    customers.append(customers[i-1] - churned)

revenue = [arpu[i] * customers[i] for i in range(12)]

base_data = pd.DataFrame({
    "Month": months.strftime("%b-%Y"),
    "ARPU ($)": arpu.round(2),
    "Churn Rate (%)": churn_rate.round(2),
    "Customers": np.round(customers).astype(int),
    "Revenue ($)": np.round(revenue, 2)
})

# ------------------------------
# App layout
# ------------------------------
st.set_page_config(page_title="Telco Executive Dashboard", layout="wide")
st.title("📊 Telco Executive Dashboard: ARPU, Churn & Revenue Impact")
st.markdown("Interactive tool to show how **small changes** in ARPU or Churn affect customers & revenue.")

tab1, tab2 = st.tabs(["🎛 Interactive What-If", "📈 Scenario Comparison & Export"])

# ------------------------------
# Tab 1: Interactive What-If (Churn + ARPU sliders)
# ------------------------------
with tab1:
    st.subheader("Adjust ARPU and Churn (Live What-If)")
    col1, col2 = st.columns(2)
    with col1:
        churn_adjust = st.slider("Adjust Churn Rate (%)  (add/subtract)", -2.0, 2.0, 0.0, 0.1)
    with col2:
        arpu_adjust_pct = st.slider("Adjust ARPU (%)  (increase/decrease)", -20.0, 20.0, 0.0, 0.5)

    data = base_data.copy()
    # apply ARPU change
    data["Adj ARPU ($)"] = (data["ARPU ($)"] * (1 + arpu_adjust_pct / 100)).round(2)
    # apply churn change
    data["Adj Churn Rate (%)"] = (data["Churn Rate (%)"] + churn_adjust).clip(lower=0).round(2)

    # compute customers and revenue under adjusted churn & ARPU
    customers_adj = [customer_base]
    for i in range(1, 12):
        churned = customers_adj[i-1] * (data["Adj Churn Rate (%)"].iloc[i-1] / 100)
        customers_adj.append(customers_adj[i-1] - churned)
    data["Adj Customers"] = np.round(customers_adj).astype(int)
    data["Adj Revenue ($)"] = (data["Adj ARPU ($)"] * data["Adj Customers"]).round(2)

    # Interactive Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["Month"], y=data["Adj ARPU ($)"],
                             mode='lines+markers', name='Adj ARPU ($)', yaxis='y1'))
    fig.add_trace(go.Scatter(x=data["Month"], y=data["Adj Churn Rate (%)"],
                             mode='lines+markers', name='Adj Churn Rate (%)', yaxis='y2'))
    # revenue as bubble sizes
    fig.add_trace(go.Scatter(x=data["Month"], y=data["Adj ARPU ($)"],
                             mode='markers',
                             marker=dict(size=(data["Adj Revenue ($)"] / data["Adj Revenue ($)"].max()) * 40 + 5,
                                         opacity=0.5),
                             name='Adj Revenue ($)',
                             text=[f"Revenue: ${r:,.0f}<br>Customers: {c:,}" for r, c in zip(data["Adj Revenue ($)"], data["Adj Customers"])],
                             hoverinfo="text"))

    fig.update_layout(
        title="What-If: Adj ARPU vs Adj Churn (Revenue shown as bubbles)",
        xaxis=dict(title="Month"),
        yaxis=dict(title="Adj ARPU ($)", side='left', color='blue'),
        yaxis2=dict(title="Adj Churn Rate (%)", overlaying='y', side='right', color='red'),
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Data (Adjusted)")
    st.dataframe(data[["Month", "Adj ARPU ($)", "Adj Churn Rate (%)", "Adj Customers", "Adj Revenue ($)"]], use_container_width=True)

# ------------------------------
# Tab 2: Scenario Comparison + Export
# ------------------------------
with tab2:
    st.subheader("Compare Churn Scenarios (with ARPU scenario)")
    # allow a simple ARPU scenario to be superimposed
    arpu_scenario = st.selectbox("Apply ARPU scenario to all churn scenarios:",
                                options=["Base (No change)", "ARPU +5%", "ARPU -5%"],
                                index=0)
    arpu_scenario_map = {"Base (No change)": 0.0, "ARPU +5%": 5.0, "ARPU -5%": -5.0}
    arpu_scenario_pct = arpu_scenario_map[arpu_scenario]

    # churn scenarios
    scenarios = {
        "Low Churn (-1%)": -1.0,
        "Base (No Change)": 0.0,
        "High Churn (+1.5%)": 1.5
    }

    scenario_frames = []
    fig2 = go.Figure()
    colors = ["green", "blue", "red"]

    for (name, churn_adj), color in zip(scenarios.items(), colors):
        df = base_data.copy()
        df["Adj ARPU ($)"] = (df["ARPU ($)"] * (1 + arpu_scenario_pct / 100)).round(2)
        df["Adj Churn Rate (%)"] = (df["Churn Rate (%)"] + churn_adj).clip(lower=0).round(2)

        customers_adj = [customer_base]
        for i in range(1, 12):
            churned = customers_adj[i-1] * (df["Adj Churn Rate (%)"].iloc[i-1] / 100)
            customers_adj.append(customers_adj[i-1] - churned)
        df["Adj Customers"] = np.round(customers_adj).astype(int)
        df["Adj Revenue ($)"] = (df["Adj ARPU ($)"] * df["Adj Customers"]).round(2)

        df_out = df[["Month", "Adj ARPU ($)", "Adj Churn Rate (%)", "Adj Customers", "Adj Revenue ($)"]].copy()
        df_out["Scenario"] = name
        scenario_frames.append(df_out)

        fig2.add_trace(go.Scatter(x=df_out["Month"], y=df_out["Adj Revenue ($)"],
                                  mode="lines+markers", name=name, line=dict(color=color)))

    fig2.update_layout(title=f"Revenue Trajectories by Churn Scenario (ARPU scenario: {arpu_scenario})",
                       xaxis=dict(title="Month"), yaxis=dict(title="Adj Revenue ($)"), template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)

    combined = pd.concat(scenario_frames, ignore_index=True)

    st.subheader("Scenario Data")
    st.dataframe(combined, use_container_width=True)

    # ------------------------------
    # Exports: Excel & HTML
    # ------------------------------
    st.subheader("Export Results")

    def to_excel_bytes(df: pd.DataFrame) -> bytes:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Scenarios")
            writer.save()
        return output.getvalue()

    excel_bytes = to_excel_bytes(combined)
    st.download_button(
        label="📊 Download Excel (.xlsx)",
        data=excel_bytes,
        file_name="telco_scenario_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # HTML export (easy way to then Print -> Save as PDF locally)
    html_report = combined.to_html(index=False)
    st.download_button(
        label="📄 Download HTML report (open in browser, Print → Save as PDF)",
        data=html_report,
        file_name="telco_scenario_data.html",
        mime="text/html"
    )

    st.markdown("**Tip:** To create a PDF: open the downloaded HTML file in a browser and choose *Print → Save as PDF*.")
