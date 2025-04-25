import yaml
import os
def load_system_config():
    path = os.path.join(os.getenv("PYTHONPATH", "/app"), "configs", "system.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)
    
    symbol = config.get("symbol", "btcusdt").upper()
    interval = config.get("interval", 3)

    # Auto-format Redis keys with symbol and interval
    config["keys"]["ohlcv"] = config["keys"]["ohlcv"].format(symbol=symbol, interval=interval)
    config["keys"]["signal"] = config["keys"]["signal"].format(symbol=symbol)

    return config
