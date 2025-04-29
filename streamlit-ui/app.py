# neurotrade_dashboard.py (v8.7 Config Integrated)
import streamlit as st
import pandas as pd
import redis
import os
import json
from datetime import datetime
from utils.system_config import load_system_config
import plotly.express as px
import plotly.graph_objects as go

# Utility functions at the TOP
def calculate_sharpe(df, risk_free=0.0):
    """Calculate Sharpe ratio with error handling"""
    try:
        if df.empty or 'portfolio_value' not in df.columns:
            return 0.0
        returns = df['portfolio_value'].pct_change().dropna()
        return (returns.mean() - risk_free) / returns.std() if returns.std() != 0 else 0.0
    except:
        return 0.0

def calculate_sortino(df, risk_free=0.0):
    """Calculate Sortino ratio with error handling"""
    try:
        if df.empty or 'portfolio_value' not in df.columns:
            return 0.0
        returns = df['portfolio_value'].pct_change().dropna()
        downside = returns[returns < 0].std()
        return (returns.mean() - risk_free) / downside if downside != 0 else 0.0
    except:
        return 0.0

def calculate_var(df, confidence=0.95):
    """Calculate Value at Risk with error handling"""
    try:
        if df.empty or 'portfolio_value' not in df.columns:
            return 0.0
        returns = df['portfolio_value'].pct_change().dropna()
        return abs(returns.quantile(1 - confidence)) * 100
    except:
        return 0.0

# 🛠️ Config Setup
st.set_page_config(page_title="Neurotrade Dashboard v8.7 — Live + Optimized", layout="wide")
st.title("📊 Neurotrade Dashboard v8.7 — Full Visibility Suite")

# Load config
config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
REDIS_PORT = config["redis"]["port"]
SIGNAL_KEY = config["keys"]["signal"]
SUMMARY_KEY = "trading:summary"
EXPERIENCE_KEY = "experience_queue"

# Rest of your existing code remains the same below...
# [Keep all other code unchanged from this point]

@st.cache_resource
def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

r = get_redis_client()

@st.cache_data(ttl=10)
def fetch_data():
    """Fetch and process all Redis data with config-based keys"""
    data = {
        "signals": [],
        "summary": {},
        "experience": []
    }
    
    try:
        # Fetch trading signals using configured key
        signals = r.lrange(SIGNAL_KEY, 0, -1)
        if signals:
            data["signals"] = [json.loads(s) for s in signals]
            signals_df = pd.DataFrame(data["signals"])
            
            # Process timestamps
            if 'timestamp' in signals_df.columns:
                signals_df['datetime'] = pd.to_datetime(signals_df['timestamp'], unit='ms')
                signals_df = signals_df.sort_values('datetime', ascending=False)
            
            # Flatten indicators
            if 'indicators' in signals_df.columns:
                indicators_df = pd.json_normalize(signals_df['indicators']).add_prefix('ind_')
                signals_df = pd.concat([signals_df.drop('indicators', axis=1), indicators_df], axis=1)
            
            data["signals_df"] = signals_df

        # Fetch trading summary
        summary = r.get(SUMMARY_KEY)
        if summary:
            data["summary"] = json.loads(summary)

        # Fetch experience replay data
        exp = r.lrange(EXPERIENCE_KEY, 0, 99)  # Last 100 experiences
        data["experience"] = [json.loads(e) for e in exp]

    except Exception as e:
        st.error(f"Data error: {str(e)}")
    
    return data

# Tabs setup
tabs = st.tabs([
    "🚦 Trading Signals", 
    "💰 Portfolio", 
    "🧠 AI Training", 
    "⚙️ System"
])

# Load data
data = fetch_data()

# Trading Signals Tab
with tabs[0]:
    if data.get("signals_df") is not None and not data["signals_df"].empty:
        df = data["signals_df"]
        
        # Real-time metrics
        latest = df.iloc[0]
        cols = st.columns(4)
        cols[0].metric("Price", f"${latest.get('price', 0):,.2f}")
        cols[1].metric("Signal", latest.get('signal', 'N/A'))
        cols[2].metric("Model", latest.get('model_version', 'v2'))
        cols[3].metric("Confidence", f"{latest.get('ind_band_position', 0)*100:.1f}%")
        
        # Visualizations
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Price Action")
            if 'price' in df.columns:
                st.line_chart(df.set_index('datetime')['price'])
        
        with col2:
            st.subheader("Signal Distribution")
            if 'signal' in df.columns:
                st.bar_chart(df['signal'].value_counts())
        
        # Indicator analysis
        st.subheader("Technical Indicators")
        indicator_cols = [c for c in df.columns if c.startswith('ind_')]
        if indicator_cols:
            selected_indicator = st.selectbox("Choose indicator", indicator_cols)
            st.line_chart(df.set_index('datetime')[selected_indicator])

    else:
        st.warning("No trading signals found")

# Portfolio Tab
# Portfolio Tab (Enhanced Performance Analytics)
with tabs[1]:
    summary = data.get("summary", {})
    signals_df = data.get("signals_df", pd.DataFrame())
    
    if summary or not signals_df.empty:
        st.subheader("💰 Portfolio Analytics")
        
        # Key Metrics Row
        cols = st.columns(4)
        cols[0].metric("Total Equity", f"${summary.get('portfolio_value', 0):,.2f}")
        cols[1].metric("ROI", f"{summary.get('return_pct', 0):.2f}%")
        cols[2].metric("Current Cash", f"${summary.get('cash', 0):,.2f}")
        cols[3].metric("BTC Holdings", f"{summary.get('inventory_btc', 0):,.6f}")
        
        # Equity Curve Visualization
        if 'portfolio_value' in signals_df.columns:
            st.subheader("Equity Curve")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=signals_df['datetime'],
                y=signals_df['portfolio_value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#1f77b4')
            ))
            fig.update_layout(height=400, xaxis_title='Date', yaxis_title='Value')
            st.plotly_chart(fig, use_container_width=True)
        
        # Trade Performance Metrics
        if not signals_df.empty and 'signal' in signals_df.columns:
            st.subheader("Trade Statistics")
            
            # Calculate trade metrics
            trades = signals_df[signals_df['signal'].isin(['BUY', 'SELL'])]
            total_trades = len(trades)
            winning_trades = len(trades[trades['ind_drawdown_pct'] > 0])  # Using drawdown as profit proxy
            
            # Metrics columns
            stat_cols = st.columns(5)
            stat_cols[0].metric("Total Trades", total_trades)
            stat_cols[1].metric("Win Rate", 
                               f"{(winning_trades/total_trades)*100:.1f}%" if total_trades > 0 else "N/A",
                               help="Percentage of profitable trades")
            stat_cols[2].metric("Avg Profit", 
                               f"{trades['ind_drawdown_pct'].mean()*100:.2f}%" if total_trades > 0 else "N/A")
            stat_cols[3].metric("Max Drawdown", 
                               f"{signals_df['ind_drawdown_pct'].min()*100:.2f}%")
            stat_cols[4].metric("Sharpe Ratio", 
                               f"{calculate_sharpe(signals_df):.2f}" if not signals_df.empty else "N/A",
                               help="Risk-adjusted returns metric")
            
            # Trade Signal Distribution
            st.subheader("Signal Performance")
            col1, col2 = st.columns(2)
            with col1:
                if not trades.empty:
                    fig = px.pie(
                        trades,
                        names='signal',
                        values='price',
                        hole=0.4,
                        color_discrete_sequence=['#2ca02c', '#d62728']
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'price' in trades.columns:
                    st.metric("Avg Buy Price", 
                             f"${trades[trades['signal'] == 'BUY']['price'].mean():,.2f}" 
                             if any(trades['signal'] == 'BUY') else "N/A")
                    st.metric("Avg Sell Price", 
                             f"${trades[trades['signal'] == 'SELL']['price'].mean():,.2f}" 
                             if any(trades['signal'] == 'SELL') else "N/A")
        
        # Advanced Risk Metrics
        st.subheader("Risk Analysis")
        risk_cols = st.columns(3)
        risk_cols[0].metric("Volatility (24h)", 
                           f"{signals_df['price'].pct_change().std()*100:.2f}%" 
                           if not signals_df.empty else "N/A")
        risk_cols[1].metric("Value at Risk (95%)", 
                           f"{calculate_var(signals_df):.2f}%" 
                           if not signals_df.empty else "N/A")
        risk_cols[2].metric("Sortino Ratio", 
                           f"{calculate_sortino(signals_df):.2f}" 
                           if not signals_df.empty else "N/A")
        
        # ROI Breakdown
        st.subheader("ROI Composition")
        roi_cols = st.columns(2)
        roi_cols[0].metric("Realized P&L", f"${summary.get('net_profit', 0):,.2f}")
        roi_cols[1].metric("Unrealized P&L", 
                          f"${summary.get('portfolio_value', 0) - summary.get('cash', 0) - summary.get('net_profit', 0):,.2f}")
    else:
        st.info("Portfolio summary unavailable")

# AI Training Tab
# AI Training Tab
with tabs[2]:
    if data["experience"]:
        exp_df = pd.DataFrame(data["experience"])
        
        st.subheader("Training Metrics")
        cols = st.columns(3)
        cols[0].metric("Experiences", len(exp_df))
        
        # Enhanced reward handling
        if 'reward' in exp_df.columns:
            try:
                # Convert to numeric and drop NA
                exp_df['reward'] = pd.to_numeric(exp_df['reward'], errors='coerce')
                valid_rewards = exp_df['reward'].dropna()
                
                cols[1].metric("Avg Reward", f"{valid_rewards.mean():.2f}")
                cols[2].metric("Max Reward", f"{valid_rewards.max():.2f}")
                
                st.subheader("Reward Distribution")
                if not valid_rewards.empty:
                    st.bar_chart(valid_rewards.value_counts(bins=10))
                else:
                    st.warning("No valid reward values found")
                    
            except Exception as e:
                st.error(f"Reward processing error: {str(e)}")
        else:
            st.warning("Reward data not found in experience buffer")
        
        # State analysis
        st.subheader("State Analysis")
        if 'state' in exp_df.columns and not exp_df.empty:
            st.write("Sample State Vector:", exp_df.iloc[0]['state'])
    else:
        st.warning("Training buffer empty")

# System Tab
with tabs[3]:
    st.subheader("Redis Health")
    try:
        info = r.info()
        cols = st.columns(3)
        cols[0].metric("Memory", info['used_memory_human'])
        cols[1].metric("Connections", info['connected_clients'])
        cols[2].metric("Ops", info['total_commands_processed'])
        
        st.progress(info['used_memory'] / info['total_system_memory'],
                   text="Memory Utilization")
    except Exception as e:
        st.error(f"System metrics unavailable: {str(e)}")

# Debug panel
with st.expander("🔍 Data Inspector"):
    st.write("### Signals Structure")
    if data.get("signals_df") is not None:
        st.write(data["signals_df"].columns.tolist())
    
    st.write("### Experience Sample")
    if data["experience"]:
        st.json(data["experience"][0], expanded=False)