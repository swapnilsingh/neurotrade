from rl_agent.models.state import State
import numpy as np
import yaml
import os

# 🛡️ Load Reward Config
reward_config_path = os.getenv("REWARD_CONFIG_PATH", "/app/configs/reward.yaml")

try:
    with open(reward_config_path, "r") as f:
        reward_config = yaml.safe_load(f)["reward"]
except Exception as e:
    raise Exception(f"Failed to load reward config in builder: {e}")


def build_state(ohlcv_row, config):
    indicators = {}
    close_price = ohlcv_row.get("close", 1.0)  # fallback in case missing

    for name in config["indicators"]:
        if name in ohlcv_row:
            value = ohlcv_row[name]
            if name == "rsi":
                indicators[name] = value / 100.0
            elif name == "adx":
                indicators[name] = value / 100.0
            elif name == "atr":
                indicators[name] = value / 50000.0  # fixed scale divisor
            elif name == "close":
                indicators[name] = value / 100000.0
            else:  # macd, bollinger, others assumed small
                indicators[name] = value

    return State(indicators=indicators)

def build_state_from_ticks(
    ticks,
    current_price,
    entry_price=None,
    position=None,
    drawdown_pct=0.0,
    inventory=0.0,
    cash_balance=500.0,
    evaluator_feedback=None,
    trade_duration_sec=10.0
):
    """
    Builds a normalized state dictionary from recent ticks and trade context.
    All features are scaled either between [-1, 1] or [0, 1] where applicable.
    """

    state = {}

    if not ticks:
        return state  # Defensive fallback

    # --- Price-based features ---
    try:
        prev_price = ticks[-2]["price"]
        price_n_ticks_ago = ticks[-10]["price"] if len(ticks) >= 10 else prev_price
    except Exception:
        prev_price = price_n_ticks_ago = current_price

    # Price change %
    price_change_pct = (current_price - prev_price) / max(prev_price, 1e-8)
    state["price_change_pct"] = price_change_pct

    # Momentum %
    momentum_pct = (current_price - price_n_ticks_ago) / max(price_n_ticks_ago, 1e-8)
    state["momentum_pct"] = momentum_pct

    # Relative Price in Band (use last 10 prices)
    prices = [tick["price"] for tick in ticks[-10:]]
    price_mean = sum(prices) / len(prices) if prices else current_price
    price_std = (sum((p - price_mean)**2 for p in prices) / len(prices))**0.5 if prices else 0
    upper_band = price_mean + 2 * price_std
    lower_band = price_mean - 2 * price_std
    if upper_band != lower_band:
        band_position = (current_price - lower_band) / (upper_band - lower_band)
    else:
        band_position = 0.5  # Neutral
    state["band_position"] = band_position

    # --- Indicators ---
    if evaluator_feedback is None:
        evaluator_feedback = {}

    # RSI scaling
    rsi_val = evaluator_feedback.get("rsi", {"rsi": 50}).get("rsi", 50)
    state["rsi_scaled"] = (rsi_val - 50) / 50

    # MACD diff
    macd = evaluator_feedback.get("macd", {"macd": 0, "macd_signal": 0})
    macd_diff = macd.get("macd", 0) - macd.get("macd_signal", 0)
    state["macd_diff"] = macd_diff  # Optionally divide by price to normalize if unstable

    # ATR percentage
    atr_val = evaluator_feedback.get("atr", {"atr": 0}).get("atr", 0)
    state["atr_pct"] = atr_val / max(current_price, 1e-8)

    # ADX scaling
    adx_val = evaluator_feedback.get("adx", {"adx": 20}).get("adx", 20)
    state["adx_scaled"] = adx_val / 100

    # --- Trade context ---
    inventory_value = inventory * current_price
    portfolio_value = cash_balance + inventory_value

    # Inventory ratio
    state["inventory_ratio"] = inventory_value / max(portfolio_value, 1e-8)

    # Drawdown percentage (already passed)
    state["drawdown_pct"] = drawdown_pct

    # Trade Duration (optional normalized by 1 hour cap)
    state["trade_duration_norm"] = min(trade_duration_sec / 3600, 1.0)

    return state
