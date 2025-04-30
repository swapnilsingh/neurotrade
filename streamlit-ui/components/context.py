# components/context.py

from core.decorators import inject_logger, inject_config
import pandas as pd
import json

@inject_logger()
@inject_config("configs/streamlit_dashboard.yaml")
class DashboardContext:
    def __init__(self):
        import redis
        import os
        self.redis_host = os.getenv("REDIS_HOST", self.config["redis"]["host"])
        self.redis_port = self.config["redis"]["port"]
        self.r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)

    def fetch_data(self):
        data = {"signals": [], "summary": {}, "experience": []}

        try:
            # Signal history
            raw_signals = self.r.lrange(self.config["keys"]["signal"].replace("{symbol}", "BTCUSDT"), 0, -1)
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
        except Exception as e:
            self.logger.warning(f"Signal data fetch failed: {e}")
            data["signals_df"] = pd.DataFrame()

        # other fields...
        return data
