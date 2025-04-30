# dashboard/components/tabs.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from components.utils import calculate_sharpe, calculate_sortino, calculate_var


def render_all_tabs(data, redis_client):
    tabs = st.tabs([
        "🚦 Trading Signals", 
        "💰 Portfolio", 
        "🧠 AI Training", 
        "⚙️ System Health",
        "📤 Export Data"
    ])

    from components.tab_signals import render_signals_tab
    from components.tab_portfolio import render_portfolio_tab
    from components.tab_training import render_training_tab
    from components.tab_system import render_system_tab
    from components.tab_export import render_export_tab

    render_signals_tab(tabs[0], data)
    render_portfolio_tab(tabs[1], data)
    render_training_tab(tabs[2], data)
    render_system_tab(tabs[3], redis_client)
    render_export_tab(tabs[4], data, redis_client)