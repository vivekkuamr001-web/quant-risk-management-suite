import streamlit as st
import plotly.graph_objects as go
import risk_engine as re

st.set_page_config(page_title="Quantitative Risk Management Suite", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    div.metric-container { background-color: #161B22; border: 1px solid #30363D; padding: 10px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Risk Management Dashboard & Portfolio Simulator")

tab1, tab2 = st.tabs(["Trade Execution & Risk Sizer", "Monte Carlo Portfolio Simulator"])

# TAB 1: Position Sizer & Compounding Engine
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Strategy Input Parameters")
        asset = st.selectbox("Asset Symbol", ["BTC/USD", "XAU/USD"])
        balance = st.number_input("Account Balance ($)", value=10000, step=500)
        risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.4, 0.1)
        win_rate = st.slider("Win Rate (%)", 10, 90, 25, 1)
        rrr = st.slider("Risk-to-Reward Ratio (1:X)", 0.5, 10.0, 6.5, 0.1)
        daily_drawdown_pct = st.slider("Max Daily Drawdown Limit (%)", 1.0, 10.0, 2.0, 0.5)
        
        entry_price = st.number_input("Entry Price ($)", value=65000.0 if asset == "BTC/USD" else 2650.0)
        stop_price = st.number_input("Stop Loss Price ($)", value=63600.0 if asset == "BTC/USD" else 2635.0)

    # Compute calculations
    calc = re.calculate_position_size(asset, balance, risk_pct, entry_price, stop_price, rrr, win_rate)
    comp_df = re.simulate_trade_compounding(balance, risk_pct, win_rate, rrr, num_trades=40)
    circuit_floor = balance * (1.0 - daily_drawdown_pct / 100.0)

    with col2:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Position Size", f"{calc['position_size']} {calc['unit_label']}")
        m2.metric("Max Risk ($)", f"${calc['max_risk_dollars']:,.2f}")
        m3.metric("Expected Value (EV)", f"${calc['ev_dollars']:,.2f}")
        m4.metric("Circuit Status", "Active", delta_color="normal")

        # Compounding Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=comp_df["Trade"], y=comp_df["Equity"], mode='lines+markers', name='Projected Equity', line=dict(color='#38BDF8', width=3)))
        fig.add_hline(y=circuit_floor, line_dash="dash", line_color="#F87171", annotation_text="Daily Drawdown Floor")
        fig.update_layout(title="Projected Equity Curve (40 Sequential Trades)", template="plotly_dark", height=420)
        st.plotly_chart(fig, use_container_width=True)

# TAB 2: Monte Carlo Risk Simulator
with tab2:
    st.subheader("Bounded Monte Carlo Trajectory Simulator")
    mc_c1, mc_c2 = st.columns([1, 2])
    
    with mc_c1:
        deposit = st.number_input("Initial Deposit ($)", value=10000, step=1000)
        max_risk = st.slider("Max Portfolio Risk (%)", 1, 50, 10)
        target_profit = st.slider("Target Profit (%)", 5, 100, 20)
        volatility = st.slider("Asset Volatility (%)", 5, 60, 19)
        
    paths_df, stop_floor, profit_cap = re.simulate_monte_carlo(deposit, max_risk, target_profit, volatility)
    
    with mc_c2:
        mc_fig = go.Figure()
        for col in paths_df.columns:
            mc_fig.add_trace(go.Scatter(x=paths_df.index, y=paths_df[col], mode='lines', opacity=0.7))
            
        mc_fig.add_hline(y=profit_cap, line_dash="dash", line_color="#4ADE80", annotation_text=f"Profit Target (${profit_cap:,.0f})")
        mc_fig.add_hline(y=stop_floor, line_dash="dash", line_color="#F87171", annotation_text=f"Stop-Loss Floor (${stop_floor:,.0f})")
        mc_fig.update_layout(title="Monte Carlo Path Simulation (Bounded)", template="plotly_dark", height=450, showlegend=False)
        st.plotly_chart(mc_fig, use_container_width=True)