import streamlit as st
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import pandas as pd
import redis
import os
import json
import warnings

from utils.system_config import load_system_config

warnings.filterwarnings("ignore", category=RuntimeWarning)

# 🚀 Streamlit Setup
st.set_page_config(page_title="Neurotrade Dashboard", layout="wide")
st.title("📊 Neurotrade Dashboard v5.1 (Cash-based + Model Suggestions)")

st_autorefresh(interval=10_000, limit=None, key="refresh")

# 🛠️ Load config and Redis
config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
REDIS_PORT = config["redis"]["port"]
SIGNAL_KEY = config["keys"]["signal"]
SUMMARY_KEY = "trading:summary"

@st.cache_resource
def get_redis_client():
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    except Exception as e:
        st.error(f"Redis connection error: {e}")
        return None

r = get_redis_client()

# 📥 Load live summary
def load_summary():
    if r is None:
        return None
    try:
        summary_data = r.get(SUMMARY_KEY)
        if summary_data:
            return json.loads(summary_data)
        else:
            return None
    except Exception as e:
        st.error(f"Error loading summary: {e}")
        return None

# 📥 Load trade history
def load_signals():
    if r is None:
        return pd.DataFrame()
    try:
        raw_signals = r.lrange(SIGNAL_KEY, 0, -1)
        df_signals = pd.DataFrame([json.loads(row) for row in raw_signals]) if raw_signals else pd.DataFrame()

        if not df_signals.empty and 'timestamp' in df_signals.columns:
            df_signals['datetime'] = pd.to_datetime(df_signals['timestamp'], unit="ms", errors='coerce')
            df_signals.sort_values("datetime", inplace=True)
        return df_signals
    except Exception as e:
        st.error(f"Error loading signals: {e}")
        return pd.DataFrame()

summary = load_summary()
df_signals = load_signals()

# 🖥️ Tabs Layout
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Live Portfolio", "📈 Equity Growth", "📋 Trade History", "📊 Signal Metrics", "🧠 Model Suggestions"])

# 🚀 LIVE SUMMARY
with tab1:
    st.subheader("🚀 Live Portfolio Status")
    if summary:
        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Cash", f"${summary['cash']:,.2f}")
        col2.metric("🪙 Inventory (BTC)", f"{summary['inventory_btc']:.6f} BTC")
        col3.metric("₿ BTC Price", f"${summary['btc_price']:,.2f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("💰 Portfolio Value", f"${summary['portfolio_value']:,.2f}")
        col5.metric("📈 Net Profit", f"${summary['net_profit']:,.2f}")
        col6.metric("📈 Return %", f"{summary['return_pct']:.2f}%")
    else:
        st.warning("No live summary available yet.")

# 📈 CASH EQUITY & PORTFOLIO CURVE
with tab2:
    st.subheader("📈 Equity and Portfolio Evolution")
    if not df_signals.empty:
        fig = go.Figure()

        if 'cash' in df_signals.columns:
            fig.add_trace(go.Scatter(
                x=df_signals['datetime'],
                y=df_signals['cash'],
                mode='lines',
                name='Cash Equity',
                line=dict(color='blue')
            ))

        if 'inventory' in df_signals.columns and 'price' in df_signals.columns:
            df_signals['portfolio_value'] = df_signals['cash'] + (df_signals['inventory'] * df_signals['price'])
            fig.add_trace(go.Scatter(
                x=df_signals['datetime'],
                y=df_signals['portfolio_value'],
                mode='lines',
                name='Total Portfolio Value',
                line=dict(color='green')
            ))

        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No equity/portfolio data available yet.")

# 📋 TRADE HISTORY
with tab3:
    st.subheader("📋 Detailed Trade Signals")
    if not df_signals.empty:
        expected_cols = ['datetime', 'signal', 'cash', 'inventory', 'quantity', 'forced', 'take_profit_pct', 'suggestion']
        available_cols = [col for col in expected_cols if col in df_signals.columns]

        df_show = df_signals[available_cols].copy()

        for col in expected_cols:
            if col not in df_show.columns:
                if col == 'forced':
                    df_show[col] = False
                elif col == 'suggestion':
                    df_show[col] = "-"
                else:
                    df_show[col] = 0.0

        st.dataframe(df_show, use_container_width=True)
    else:
        st.info("No trade signals recorded yet.")

# 📊 SIGNAL METRICS
with tab4:
    st.subheader("📊 Trade Metrics")
    if not df_signals.empty:
        buy_count = (df_signals['signal'] == 'BUY').sum()
        sell_count = (df_signals['signal'] == 'SELL').sum()
        hold_count = (df_signals['signal'] == 'HOLD').sum()
        total_trades = buy_count + sell_count

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Executed Trades", total_trades)
        col2.metric("📈 BUY Signals", buy_count)
        col3.metric("📉 SELL Signals", sell_count)
        col4.metric("✋ HOLDs", hold_count)
    else:
        st.info("No trades executed yet.")

# 🧠 MODEL SUGGESTIONS
with tab5:
    st.subheader("🧠 Model Suggestions")
    if not df_signals.empty and 'suggestion' in df_signals.columns:
        latest_suggestion = df_signals['suggestion'].dropna().iloc[-1] if not df_signals['suggestion'].dropna().empty else "-"
        st.info(f"Latest Model Suggestion: {latest_suggestion}")
    else:
        st.info("No suggestions available.")
