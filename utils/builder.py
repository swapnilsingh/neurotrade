def build_state_from_ticks(
    ticks,
    current_price,
    entry_price=None,
    position=None,
    drawdown_pct=0.0,
    inventory=0.0,
    cash_balance=500.0,
    evaluator_feedback=None,
    trade_duration_sec=10.0,
    extra_indicators=None  # 🔥 New input from indicator agents
):
    """
    Builds a normalized state dictionary from recent ticks, trade context, and dynamic indicators.
    All features are scaled between [-1, 1] or [0, 1] as applicable.
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

    price_change_pct = (current_price - prev_price) / max(prev_price, 1e-8)
    state["price_change_pct"] = price_change_pct

    momentum_pct = (current_price - price_n_ticks_ago) / max(price_n_ticks_ago, 1e-8)
    state["momentum_pct"] = momentum_pct

    prices = [tick["price"] for tick in ticks[-10:]]
    price_mean = sum(prices) / len(prices) if prices else current_price
    price_std = (sum((p - price_mean)**2 for p in prices) / len(prices))**0.5 if prices else 0
    upper_band = price_mean + 2 * price_std
    lower_band = price_mean - 2 * price_std
    state["band_position"] = (current_price - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5

    # --- Evaluator Hints ---
    evaluator_feedback = evaluator_feedback or {}
    state["rsi_scaled"] = (evaluator_feedback.get("rsi", {"rsi": 50}).get("rsi", 50) - 50) / 50
    macd = evaluator_feedback.get("macd", {"macd": 0, "macd_signal": 0})
    state["macd_diff"] = macd.get("macd", 0) - macd.get("macd_signal", 0)
    state["atr_pct"] = evaluator_feedback.get("atr", {"atr": 0}).get("atr", 0) / max(current_price, 1e-8)
    state["adx_scaled"] = evaluator_feedback.get("adx", {"adx": 20}).get("adx", 20) / 100

    # --- Trade Context ---
    inventory_value = inventory * current_price
    portfolio_value = cash_balance + inventory_value
    state["inventory_ratio"] = inventory_value / max(portfolio_value, 1e-8)
    state["drawdown_pct"] = drawdown_pct
    state["trade_duration_norm"] = min(trade_duration_sec / 3600, 1.0)

    # --- Extra Indicator Injection ---
    if extra_indicators:
        for key, val in extra_indicators.items():
            state[key] = val

    return state
