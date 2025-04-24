import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Neurotrade Dashboard", layout="wide")

st.title("📊 Neurotrade Performance Dashboard")

@st.cache_data
def load_data():
    if not os.path.exists("inference_log.csv"):
        return pd.DataFrame()
    with open("inference_log.csv", "r") as f:
        lines = [json.loads(line) for line in f]
    df = pd.DataFrame(lines)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.sort_values("timestamp", inplace=True)
    return df

df = load_data()

if df.empty:
    st.warning("No trading data found.")
else:
    st.subheader("💼 Equity Curve")
    df["pnl"] = df["equity"].diff().fillna(0)
    fig = df.plot(x="timestamp", y="equity", title="Equity Over Time", legend=False)
    st.line_chart(df.set_index("timestamp")[["equity"]])

    st.subheader("📊 Agent Votes")
    st.json(df["votes"].iloc[-1] if not df.empty else {})

    st.subheader("🧠 Explain Last Trade")
    last_trade = df.iloc[-1]
    st.markdown(f"**Symbol:** {last_trade['symbol']}")
    st.markdown(f"**Signal:** `{last_trade['signal']}`")
    st.markdown(f"**Reason:** {last_trade['reason']}")
    st.markdown(f"**Equity:** ${last_trade['equity']:.2f}")
    st.markdown(f"**Timestamp:** {last_trade['timestamp']}")
