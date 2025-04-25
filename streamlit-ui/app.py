import streamlit as st
import pandas as pd
import redis
import json
import os
from datetime import datetime

st.set_page_config(page_title="Neurotrade Dashboard", layout="wide")
st.title("📊 Neurotrade Performance Dashboard")

from utils.system_config import load_system_config
config = load_system_config()

REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
EXPERIENCE_KEY = config["keys"]["experience"]
SIGNAL_KEY = config["keys"]["signal"]

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

@st.cache_data(ttl=5)
def load_from_redis():
    raw = r.lrange(SIGNAL_KEY, -500, -1)
    parsed = [json.loads(row) for row in raw]
    df = pd.DataFrame(parsed)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.sort_values("timestamp", inplace=True)
    return df

df = load_from_redis()

if df.empty:
    st.warning("No trading data found.")
else:
    st.subheader("💼 Equity Curve")
    df["pnl"] = df["equity"].diff().fillna(0)
    st.line_chart(df.set_index("timestamp")[["equity"]])

    st.subheader("📊 Agent Votes")
    st.json(df["votes"].iloc[-1])

    st.subheader("🧠 Explain Last Trade")
    last_trade = df.iloc[-1]
    st.markdown(f"**Symbol:** {last_trade['symbol']}")
    st.markdown(f"**Signal:** `{last_trade['signal']}`")
    st.markdown(f"**Reason:** {last_trade['reason']}")
    st.markdown(f"**Equity:** ${last_trade['equity']:.2f}")
    st.markdown(f"**Timestamp:** {last_trade['timestamp']}")
