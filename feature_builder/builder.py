from rl_agent.models.state import State

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

def build_state_from_ticks(ticks, current_price, entry_price, position):
    prices = [tick['price'] for tick in ticks]
    qtys = [tick['qty'] for tick in ticks]

    price_change = (prices[-1] - prices[0]) / prices[0] if prices[0] != 0 else 0
    avg_price = sum(prices) / len(prices)
    avg_qty = sum(qtys) / len(qtys)
    momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 and prices[-5] != 0 else 0

    # 🧠 New: Unrealized PnL%
    if position == "LONG" and entry_price > 0:
        unrealized_pnl_pct = (current_price - entry_price) / entry_price
    else:
        unrealized_pnl_pct = 0.0

    state = {
        "price_change": price_change,
        "momentum": momentum,
        "avg_price": avg_price,
        "avg_qty": avg_qty,
        "unrealized_pnl_pct": unrealized_pnl_pct   # ✅ NEW
    }
    return state

