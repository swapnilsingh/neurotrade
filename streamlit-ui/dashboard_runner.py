# dashboard_runner.py

import streamlit as st
from components.context import DashboardContext
from components.tab_signals import render_signals_tab
from components.tab_portfolio import render_portfolio_tab
from components.tab_training import render_training_tab
from components.tab_system import render_system_health_tab
from components.tab_export import render_export_tab
from components.tab_trading import render_trade_performance_tab
from components.utils import calculate_sharpe
import pandas as pd

# Streamlit Page Setup
st.set_page_config(page_title="Neurotrade Dashboard", layout="wide")
st.title("📊 Neurotrade Dashboard — Live Trading Analytics")

# Context and Data
ctx = DashboardContext()
data = ctx.fetch_data()

# Sanitize signal_df for downstream tabs
if "signals_df" in data and isinstance(data["signals_df"], pd.DataFrame):
    signals_df = data["signals_df"]
    available_columns = signals_df.columns.tolist()
    default_columns = [col for col in ["datetime", "signal", "price"] if col in available_columns]
    data["available_columns"] = available_columns
    data["default_columns"] = default_columns

    # Avoid ZeroDivisionError for signal frequency
    if len(signals_df) > 1:
        time_span = (signals_df["datetime"].max() - signals_df["datetime"].min()).total_seconds()
        data["signal_frequency"] = f"{len(signals_df)/(time_span/3600):.1f}/hour" if time_span > 0 else "N/A"
    else:
        data["signal_frequency"] = "N/A"
else:
    data["signals_df"] = pd.DataFrame()
    data["available_columns"] = []
    data["default_columns"] = []
    data["signal_frequency"] = "N/A"

# Tabs Setup
tabs = st.tabs([
    "🚦 Trading Signals", 
    "💰 Portfolio", 
    "🧠 AI Training", 
    "⚙️ System Health",
    "📤 Export Data",
    "📈 Trade Performance"
])

# Render Each Tab
render_signals_tab(tabs[0], data)
render_portfolio_tab(tabs[1], data)
render_training_tab(tabs[2], data)
render_system_health_tab(tabs[3], ctx)
render_export_tab(tabs[4], data, ctx)
render_trade_performance_tab(tabs[5], data)
