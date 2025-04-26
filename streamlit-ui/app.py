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

st.set_page_config(page_title="Neurotrade Dashboard", layout="wide")
st.title("📊 Neurotrade Dashboard v4.0 (Tick Mode Enhanced)")

st_autorefresh(interval=10_000, limit=None, key="refresh")

config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
REDIS_PORT = config["redis"]["port"]
OHLCV_KEY = config["keys"]["ohlcv"]
SIGNAL_KEY = config["keys"]["signal"]
EXPERIENCE_KEY = config["keys"]["experience"]


@st.cache_resource
def get_redis_client():
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    except Exception as e:
        st.error(f"Redis connection error: {e}")
        return None

r = get_redis_client()

def patch_signals(df_signals: pd.DataFrame) -> pd.DataFrame:
    """Patch missing fields in signal dataframe dynamically for Streamlit."""
    if df_signals.empty:
        return df_signals

    # Fix datetime
    if 'timestamp' in df_signals.columns:
        df_signals['datetime'] = pd.to_datetime(df_signals['timestamp'], unit="ms", errors='coerce')

    # Add missing price from indicators['avg_price']
    if 'price' not in df_signals.columns:
        df_signals['price'] = df_signals['indicators'].apply(
            lambda x: x.get('avg_price', None) if isinstance(x, dict) else None
        )

    # Add inventory based on quantity
    if 'inventory' not in df_signals.columns:
        df_signals['inventory'] = df_signals.get('quantity', 0.0)

    # Add pnl based on unrealized_pnl_pct and equity
    if 'pnl' not in df_signals.columns:
        df_signals['pnl'] = df_signals.apply(
            lambda row: (row['indicators'].get('unrealized_pnl_pct', 0.0) / 100) * row['equity']
            if isinstance(row['indicators'], dict) else 0.0,
            axis=1
        )

    return df_signals

def highlight_signal(row):
    """Highlight BUY in green and SELL in red."""
    if row['signal'] == 'BUY':
        return ['background-color: lightgreen'] * len(row)
    elif row['signal'] == 'SELL':
        return ['background-color: salmon'] * len(row)
    else:
        return [''] * len(row)


@st.cache_data(ttl=30)
def load_data():
    if r is None:
        return pd.DataFrame(), pd.DataFrame()
    try:
        raw_ohlcv = r.lrange(OHLCV_KEY, 0, -1)
        raw_signals = r.lrange(SIGNAL_KEY, 0, -1)

        df_ohlcv = pd.DataFrame([json.loads(row) for row in raw_ohlcv]) if raw_ohlcv else pd.DataFrame()
        df_signals = pd.DataFrame([json.loads(row) for row in raw_signals]) if raw_signals else pd.DataFrame()

        if not df_ohlcv.empty:
            df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['timestamp'], unit="ms", errors='coerce')
            df_ohlcv.sort_values("datetime", inplace=True)

        # 🛠️ PATCH signals safely
        df_signals = patch_signals(df_signals)

        return df_ohlcv, df_signals

    except Exception as e:
        st.error(f"Data loading error: {e}")
        return pd.DataFrame(), pd.DataFrame()


df_ohlcv, df_signals = load_data()

st.sidebar.header("⚙️ Filters")

default_start = df_signals['datetime'].min().date() if not df_signals.empty else pd.Timestamp.today().date()
default_end = df_signals['datetime'].max().date() if not df_signals.empty else pd.Timestamp.today().date()

start_date = st.sidebar.date_input("Start Date", value=default_start)
end_date = st.sidebar.date_input("End Date", value=default_end)

start_ts = pd.Timestamp(start_date)
end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

df_signals_filtered = df_signals[(df_signals['datetime'] >= start_ts) & (df_signals['datetime'] <= end_ts)] if not df_signals.empty else pd.DataFrame()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Live Price", 
    "📋 Trade History", 
    "💰 Equity Curve", 
    "🏦 Inventory Tracker", 
    "📊 Trade PnL Histogram", 
    "🚀 Live Metrics"
])


with tab1:
    st.subheader("📈 Live Trading View")

    if not df_signals_filtered.empty:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_signals_filtered['datetime'],
            y=df_signals_filtered['price'],
            mode='lines+markers',
            name='Price',
            line=dict(color='blue')
        ))

        buys = df_signals_filtered[df_signals_filtered['signal'] == 'BUY']
        sells = df_signals_filtered[df_signals_filtered['signal'] == 'SELL']

        fig.add_trace(go.Scatter(
            x=buys['datetime'],
            y=buys['price'],
            mode='markers',
            marker=dict(color='green', size=10, symbol='triangle-up'),
            name='BUY Signals'
        ))

        fig.add_trace(go.Scatter(
            x=sells['datetime'],
            y=sells['price'],
            mode='markers',
            marker=dict(color='red', size=10, symbol='triangle-down'),
            name='SELL Signals'
        ))

        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No live tick data available yet.")


with tab2:
    st.subheader("📋 Detailed Trade Signals")
    if not df_signals_filtered.empty:
        df_show = df_signals_filtered[[
            'datetime', 'signal', 'equity', 'price', 
            'quantity', 'forced'
        ]]
        st.dataframe(df_show)
    else:
        st.info("No trades recorded yet.")


with tab3:
    st.subheader("💰 Equity Evolution")

    if not df_signals_filtered.empty:
        df_signals_filtered['net_equity'] = df_signals_filtered['equity'] + df_signals_filtered['indicators'].apply(
            lambda x: x.get('inventory', 0.0) * x.get('close', 0.0) if isinstance(x, dict) else 0.0
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_signals_filtered['datetime'],
            y=df_signals_filtered['equity'],
            mode='lines',
            name='Cash Equity',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=df_signals_filtered['datetime'],
            y=df_signals_filtered['net_equity'],
            mode='lines',
            name='Net Equity (Cash + Crypto)',
            line=dict(color='green')
        ))
        fig.update_layout(height=500, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No equity data available.")


with tab4:
    st.subheader("🏦 Inventory Over Time")

    if not df_signals_filtered.empty:
        df_signals_filtered['inventory'] = df_signals_filtered['indicators'].apply(
            lambda x: x.get('inventory', 0.0) if isinstance(x, dict) else 0.0
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_signals_filtered['datetime'],
            y=df_signals_filtered['inventory'],
            mode='lines',
            name='Inventory Held',
            line=dict(color='purple')
        ))
        fig.update_layout(height=500, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No inventory data.")

with tab5:
    st.subheader("📊 Trade Profit Histogram")

    if not df_signals_filtered.empty and 'pnl' in df_signals_filtered.columns:
        st.bar_chart(df_signals_filtered['pnl'])
    else:
        st.info("No trade PnL data yet.")


with tab6:
    st.subheader("🚀 Live Portfolio Metrics")

    if not df_signals_filtered.empty:
        # 📈 Main Metrics
        latest = df_signals_filtered.iloc[-1]
        equity = latest.get('equity', 0.0)
        price = latest.get('price', 0.0) or 0.0
        indicators = latest.get('indicators', {})
        inventory = indicators.get('inventory', 0.0) if isinstance(indicators, dict) else 0.0

        net_equity = equity + (inventory * price)

        st.metric("💵 Cash Equity", f"${equity:,.2f}")
        st.metric("🪙 Inventory BTC", f"{inventory:.6f} BTC")
        st.metric("📈 Net Equity", f"${net_equity:,.2f}")

        # 📊 Live Trade Counters
        st.subheader("📊 Live Trade Signal Counts")

        buy_count = (df_signals_filtered['signal'] == 'BUY').sum()
        sell_count = (df_signals_filtered['signal'] == 'SELL').sum()
        hold_count = (df_signals_filtered['signal'] == 'HOLD').sum()
        total_trades = buy_count + sell_count

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📈 Total BUYs", buy_count)
        col2.metric("📉 Total SELLs", sell_count)
        col3.metric("✋ Total HOLDs", hold_count)
        col4.metric("✅ Executed Trades", total_trades)

        # 📋 Inventory Over Time Table
        st.subheader("📋 Inventory Movement Timeline")

        if not df_signals_filtered.empty:
            inventory_timeline = df_signals_filtered[['datetime', 'signal', 'inventory']].copy()
            inventory_timeline = inventory_timeline.sort_values('datetime', ascending=True)
            inventory_timeline = inventory_timeline[inventory_timeline['inventory'] != 0]  # show only non-zero

            styled_table = inventory_timeline.style.apply(highlight_signal, axis=1)
            st.dataframe(styled_table, use_container_width=True)
        else:
            st.info("No inventory records available yet.")

    else:
        st.info("No live metrics available yet.")



