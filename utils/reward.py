# utils/reward.py

def compute_reward(candle: dict, signal: int, strategy: str = "basic") -> float:
    """
    Compute reward based on selected reward strategy.

    Args:
        candle (dict): OHLCV candle.
        signal (int): 1 = BUY, -1 = SELL, 0 = HOLD.
        strategy (str): Reward strategy ("basic", "sharpe", "penalty").

    Returns:
        float: Clipped and normalized reward.
    """
    open_price = candle['open']
    close_price = candle['close']

    if strategy == "basic":
        if signal == 1:  # BUY
            reward = ((close_price - open_price) / open_price) * 100
        elif signal == -1:  # SELL
            reward = ((open_price - close_price) / open_price) * 100
        else:  # HOLD
            reward = -abs(close_price - open_price) / open_price * 100

    elif strategy == "sharpe":
        price_range = candle['high'] - candle['low']
        volatility = price_range / open_price
        if signal == 1:  # BUY
            ret = ((close_price - open_price) / open_price)
        elif signal == -1:  # SELL
            ret = ((open_price - close_price) / open_price)
        else:  # HOLD
            ret = -abs(close_price - open_price) / open_price

        if volatility > 0:
            reward = (ret / volatility) * 10  # Sharpe-style scaling
        else:
            reward = ret * 10

    elif strategy == "penalty":
        if signal == 1 and close_price < open_price:
            reward = -2.0
        elif signal == -1 and close_price > open_price:
            reward = -2.0
        elif signal == 0 and abs(close_price - open_price) > 0.001 * open_price:
            reward = -1.0
        else:
            reward = 1.0

    else:
        raise ValueError(f"Unknown reward strategy: {strategy}")

    # Clip reward to safe range
    reward = max(min(reward, 10.0), -10.0)

    # Normalize reward
    reward /= 5.0

    return reward
