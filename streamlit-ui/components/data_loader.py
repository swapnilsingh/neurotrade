# dashboard/components/data_loader.py

import redis
import os
import json
import pandas as pd
import streamlit as st
from utils.config_loader import load_config

@st.cache_resource
def get_redis_client():
    config = load_config("streamlit_dashboard.yaml")
    host = os.getenv("REDIS_HOST", config["REDIS_HOST"])
    port = config["REDIS_PORT"]
    return redis.Redis(host=host, port=port, decode_responses=True)

@st.cache_data(ttl=10)
def fetch_data(self):
    data = {"signals": [], "summary": {}, "experience": []}

    try:
        symbol = self.config.get("symbol", "btcusdt").upper()
        signal_key = self.config["keys"]["signal"].replace("{symbol}", symbol)
        raw_signals = self.r.lrange(signal_key, 0, -1)

        if raw_signals:
            data["signals"] = [json.loads(s) for s in raw_signals]
            df = pd.DataFrame(data["signals"])
            if not df.empty and "timestamp" in df.columns:
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
                df = df.sort_values("datetime", ascending=False)

                if "indicators" in df.columns:
                    indicators_df = pd.json_normalize(df["indicators"]).add_prefix("ind_")
                    df = pd.concat([df.drop("indicators", axis=1), indicators_df], axis=1)

            data["signals_df"] = df
        else:
            data["signals_df"] = pd.DataFrame()

    except Exception as e:
        self.logger.warning(f"Signal data fetch failed: {e}")
        data["signals_df"] = pd.DataFrame()

    return data


