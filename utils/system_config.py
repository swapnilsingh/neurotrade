import yaml
import os

_config_cache = None  # ✅ Add this global cache

def load_system_config():
    global _config_cache
    if _config_cache:
        return _config_cache

    path = os.path.join(os.getenv("PYTHONPATH", "/app"), "configs", "system.yaml")
    print(f"📂 Loading config from: {path}")
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    symbol = config.get("symbol", "btcusdt").upper()
    interval = config.get("interval", 3)

    config["keys"]["ohlcv"] = config["keys"]["ohlcv"].format(symbol=symbol, interval=interval)
    config["keys"]["signal"] = config["keys"]["signal"].format(symbol=symbol)

    _config_cache = config  # ✅ Store in cache
    return config
