# utils/config_helpers.py

def format_redis_keys(config):
    symbol = config.get("symbol", "btcusdt").upper()
    interval = config.get("interval", 3)
    keys = config.get("keys", {})

    if "ohlcv" in keys:
        keys["ohlcv"] = keys["ohlcv"].format(symbol=symbol, interval=interval)
    if "signal" in keys:
        keys["signal"] = keys["signal"].format(symbol=symbol)

    config["keys"] = keys
    return config
