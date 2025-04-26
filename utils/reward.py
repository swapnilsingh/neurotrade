# utils/reward.py

def compute_reward(candle, signal, strategy="basic"):
    """
    Calculate reward based on PnL, holding time, and trading costs.

    Parameters:
    - candle: dict containing the latest closed candle + trade info
    - signal: action taken ("BUY", "SELL", "HOLD")
    - strategy: "basic" or "smart" reward logic
    """

    pnl = candle.get("pnl", 0.0)
    holding_duration_sec = candle.get("holding_duration_sec", 0.0)

    slippage_penalty_rate = 0.0005  # 0.05% assumed slippage
    min_holding_sec = 15            # Minimum holding time threshold
    early_exit_penalty = 1.0         # Penalty if sold too early

    reward = 0.0

    if strategy == "basic":
        if signal == "SELL":
            reward = pnl
        else:
            reward = 0.0

    elif strategy == "smart":
        if signal == "SELL":
            reward = pnl

            # Apply slippage penalty
            reward -= slippage_penalty_rate * abs(pnl)

            # Penalize if exited too early
            if holding_duration_sec < min_holding_sec:
                reward -= early_exit_penalty

        else:
            reward = 0.0  # HOLD or BUY gets neutral reward

    return reward

# utils/reward.py

def compute_reward_from_ticks(ticks, signal, quantity, current_price, entry_price, position,
                               slippage=0.0005, trading_fee=0.001):
    """
    Reward based on profit/loss after executing action, simulating slippage and trading fee.
    """

    if not ticks or signal == "HOLD":
        return -0.001  # small penalty for inactivity to encourage trading when needed

    reward = 0.0

    if signal == "BUY":
        # BUY action: Penalize wrong buys if price doesn't go up
        future_price = ticks[-1]["price"]
        price_diff = future_price - current_price
        gross_profit = price_diff * quantity
        reward = gross_profit
    elif signal == "SELL":
        # SELL action: Reward if price drops after selling
        future_price = ticks[-1]["price"]
        price_diff = current_price - future_price
        gross_profit = price_diff * quantity
        reward = gross_profit
    else:
        reward = -0.001  # HOLD again small penalty

    # Simulate fee + slippage cost
    cost = current_price * quantity * (trading_fee + slippage)
    reward = reward - cost

    # Boost positive rewards, punish losses harder
    if reward > 0:
        reward = reward ** 1.5
    else:
        reward = reward * 2

    return reward






