# neurotrade_dashboard.py (Final Integrated Version)
import streamlit as st
import pandas as pd
import numpy as np
import redis
import os
import json
import io
import zipfile
from datetime import datetime
from utils.system_config import load_system_config
import plotly.express as px
import plotly.graph_objects as go

# Utility Functions
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

# Configuration and Setup
st.set_page_config(page_title="Neurotrade Dashboard", layout="wide")
st.title("📊 Neurotrade Dashboard — Live Trading Analytics")

# Redis Configuration
config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
REDIS_PORT = config["redis"]["port"]
SIGNAL_KEY = config["keys"]["signal"]
SUMMARY_KEY = "trading:summary"
EXPERIENCE_KEY = "experience_queue"

@st.cache_resource
def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

r = get_redis_client()

# Data Fetching
@st.cache_data(ttl=10)
def fetch_data():
    """Fetch and process all Redis data"""
    data = {"signals": [], "summary": {}, "experience": []}
    
    try:
        # Trading Signals
        signals = r.lrange(SIGNAL_KEY, 0, -1)
        if signals:
            data["signals"] = [json.loads(s) for s in signals]
            signals_df = pd.DataFrame(data["signals"])
            
            if 'timestamp' in signals_df.columns:
                signals_df['datetime'] = pd.to_datetime(signals_df['timestamp'], unit='ms')
                signals_df = signals_df.sort_values('datetime', ascending=False)
            
            if 'indicators' in signals_df.columns:
                indicators_df = pd.json_normalize(signals_df['indicators']).add_prefix('ind_')
                signals_df = pd.concat([signals_df.drop('indicators', axis=1), indicators_df], axis=1)
            
            data["signals_df"] = signals_df

        # Portfolio Summary
        summary = r.get(SUMMARY_KEY)
        if summary:
            data["summary"] = json.loads(summary)

        # Experience Data
        data["experience"] = [json.loads(e) for e in r.lrange(EXPERIENCE_KEY, 0, 99)]

    except Exception as e:
        st.error(f"Data error: {str(e)}")
    
    return data

# Tabs Setup
tabs = st.tabs([
    "🚦 Trading Signals", 
    "💰 Portfolio", 
    "🧠 AI Training", 
    "⚙️ System Health",
    "📤 Export Data"
])

data = fetch_data()

# Trading Signals Tab
with tabs[0]:
    if data.get("signals_df") is not None and not data["signals_df"].empty:
        df = data["signals_df"]
        
        # Real-time Metrics
        latest = df.iloc[0]
        cols = st.columns(4)
        cols[0].metric("Price", f"${latest.get('price', 0):,.2f}")
        cols[1].metric("Signal", latest.get('signal', 'N/A'))
        cols[2].metric("Model", latest.get('model_version', 'v2'))
        cols[3].metric("Confidence", f"{latest.get('ind_band_position', 0)*100:.1f}%")
        
        # Price Chart with Signals
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['datetime'], y=df['price'], 
            mode='lines', name='Price',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Buy/Sell Markers
        buys = df[df['signal'] == 'BUY']
        sells = df[df['signal'] == 'SELL']
        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=buys['datetime'], y=buys['price'],
                mode='markers', name='BUY',
                marker=dict(symbol='triangle-up', size=10, color='#2ca02c')
            ))
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=sells['datetime'], y=sells['price'],
                mode='markers', name='SELL',
                marker=dict(symbol='triangle-down', size=10, color='#d62728')
            ))
        
        fig.update_layout(height=500, xaxis_title='Time', yaxis_title='Price (USD)')
        st.plotly_chart(fig, use_container_width=True)

        # Signal Stats
        cols = st.columns(3)
        cols[0].metric("Total Buys", len(buys))
        cols[1].metric("Total Sells", len(sells))
        cols[2].metric("Signal Frequency", 
                      f"{len(df)/((df['datetime'].max() - df['datetime'].min()).total_seconds()/3600):.1f}/hour" 
                      if len(df) > 1 else "N/A")
    else:
        st.warning("No trading signals found")

# Portfolio Tab
with tabs[1]:
    summary = data.get("summary", {})
    signals_df = data.get("signals_df", pd.DataFrame())
    
    if summary or not signals_df.empty:
        # Key Metrics
        cols = st.columns(4)
        cols[0].metric("Total Value", f"${summary.get('portfolio_value', 0):,.2f}")
        cols[1].metric("ROI", f"{summary.get('return_pct', 0):.2f}%")
        cols[2].metric("Available Cash", f"${summary.get('cash', 0):,.2f}")
        cols[3].metric("BTC Holdings", f"{summary.get('inventory_btc', 0):,.6f}")
        
        # Equity Curve
        if 'portfolio_value' in signals_df.columns:
            st.subheader("Equity Curve")
            st.line_chart(signals_df.set_index('datetime')['portfolio_value'])
        
        # Trade Statistics
        trades = signals_df[signals_df['signal'].isin(['BUY', 'SELL'])]
        if not trades.empty:
            st.subheader("Trade Performance")
            cols = st.columns(5)
            cols[0].metric("Total Trades", len(trades))
            cols[1].metric("Win Rate", f"{(len(trades[trades['ind_drawdown_pct'] > 0])/len(trades)*100):.1f}%")
            cols[2].metric("Avg Profit", f"{trades['ind_drawdown_pct'].mean()*100:.2f}%")
            cols[3].metric("Max Drawdown", f"{signals_df['ind_drawdown_pct'].min()*100:.2f}%")
            cols[4].metric("Sharpe Ratio", f"{calculate_sharpe(signals_df):.2f}")
    else:
        st.info("Portfolio summary unavailable")

# AI Training Tab
with tabs[2]:
    if data["experience"]:
        exp_df = pd.DataFrame(data["experience"])
        
        # Training Metrics
        cols = st.columns(3)
        cols[0].metric("Experience Buffer", len(exp_df))
        cols[1].metric("Avg Reward", f"{exp_df.get('reward', 0).mean():.2f}")
        cols[2].metric("Max Reward", f"{exp_df.get('reward', 0).max():.2f}")
        
        # Reward Distribution
        st.subheader("Reward Distribution")
        st.bar_chart(exp_df['reward'].value_counts(bins=10))
    else:
        st.warning("Training buffer empty")

# System Health Tab
with tabs[3]:
    try:
        info = r.info()
        cols = st.columns(3)
        cols[0].metric("Memory Usage", info['used_memory_human'])
        cols[1].metric("Connected Clients", info['connected_clients'])
        cols[2].metric("Operations", info['total_commands_processed'])
        st.progress(info['used_memory'] / info['total_system_memory'], text="Memory Utilization")
    except Exception as e:
        st.error(f"System metrics unavailable: {str(e)}")

# Data Export Tab
with tabs[4]:
    st.subheader("Data Export")
    
    # Export Configuration
    col1, col2 = st.columns(2)
    with col1:
        export_format = st.selectbox("File Format", ["CSV", "JSON", "Parquet"])
        date_range = st.date_input("Date Range", [])
    with col2:
        selected_columns = st.multiselect("Columns", 
                                        options=data["signals_df"].columns.tolist(),
                                        default=["datetime", "signal", "price"])
        include_debug = st.checkbox("Include Debug Info")
    
    # Export Logic
    if st.button("📦 Generate Export Package"):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            try:
                # Signals Data
                signals_export = data["signals_df"]
                if date_range and len(date_range) == 2:
                    signals_export = signals_export[
                        (signals_export['datetime'].dt.date >= date_range[0]) & 
                        (signals_export['datetime'].dt.date <= date_range[1])
                    ]
                if selected_columns:
                    signals_export = signals_export[selected_columns]
                
                if export_format == "CSV":
                    z.writestr("signals.csv", signals_export.to_csv(index=False))
                elif export_format == "JSON":
                    z.writestr("signals.json", signals_export.to_json(orient="records"))
                elif export_format == "Parquet":
                    z.writestr("signals.parquet", signals_export.to_parquet())
                
                # Debug Info
                if include_debug:
                    debug_data = {
                        "redis_info": r.info(),
                        "data_stats": {
                            "signals": signals_export.shape,
                            "experience": len(data["experience"])
                        }
                    }
                    z.writestr("debug_info.json", json.dumps(debug_data))
                
                st.success("Export package created successfully!")
                
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
        
        # Download Button
        st.download_button(
            label="⬇️ Download Export",
            data=buffer.getvalue(),
            file_name=f"neurotrade_export_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip"
        )

# Debug Panel
with st.expander("🔍 Debug Information"):
    st.write("### Signals Data Structure")
    if data.get("signals_df") is not None:
        st.write(data["signals_df"].columns.tolist())
    
    st.write("### Latest Signal")
    if data.get("signals"):
        st.json(data["signals"][0])