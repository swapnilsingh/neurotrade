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

def sanitize_inputs(current_price, entry_price, quantity, position):
    """
    Ensure all inputs are floats to prevent type errors during reward computation.
    """
    try:
        current_price = float(current_price)
    except (ValueError, TypeError):
        current_price = 0.0

    try:
        entry_price = float(entry_price)
    except (ValueError, TypeError):
        entry_price = 0.0

    try:
        quantity = float(quantity)
    except (ValueError, TypeError):
        quantity = 0.001  # Safe small value

    try:
        position = float(position)
    except (ValueError, TypeError):
        position = 0.0

    return current_price, entry_price, quantity, position


def compute_reward_from_ticks(ticks, signal, quantity, current_price, entry_price, position,
                                          slippage=0.0005, trading_fee=0.001,
                                          drawdown_penalty_factor=0.2,
                                          volatility_threshold=0.002,  # 0.2% move
                                          hold_penalty=-0.002,
                                          big_move_penalty=-0.01,
                                          bonus_multiplier=1.5):
    """
    Booster Reward Function with Big Move Detector:
    - Penalizes inactivity during big market movements.
    - Encourages capturing volatile swings.
    """

    # 🛡 Sanitize inputs
    current_price, entry_price, quantity, position = sanitize_inputs(
        current_price, entry_price, quantity, position
    )

    if not ticks:
        return -0.001  # General penalty if no ticks available

    reward = 0.0

    # Estimate future price
    future_price = float(ticks[-1]["price"])

    # Price change percentage
    price_change_pct = (future_price - current_price) / current_price

    # === CASE 1: HOLD signal ===
    if signal == "HOLD":
        reward = hold_penalty  # Penalty for inactivity
        
        # ➡️ If BIG move happened and agent held, punish harder
        if abs(price_change_pct) >= volatility_threshold:
            reward += big_move_penalty  # Add extra negative reward

    # === CASE 2: BUY or SELL signal ===
    else:
        if signal == "BUY":
            pnl_pct = price_change_pct
        elif signal == "SELL":
            pnl_pct = -price_change_pct
        else:
            pnl_pct = 0.0

        gross_pnl = pnl_pct * quantity * current_price
        cost = current_price * quantity * (trading_fee + slippage)
        net_pnl = gross_pnl - cost

        reward = net_pnl

        # ➡️ Volatility bonus if captured big move
        if abs(price_change_pct) >= volatility_threshold and reward > 0:
            reward *= bonus_multiplier

    # ➡️ Drawdown Penalty if open position
    if position != 0:
        unrealized_pnl = (current_price - entry_price) * position
        if unrealized_pnl < 0:
            drawdown_penalty = drawdown_penalty_factor * abs(unrealized_pnl) / max(abs(entry_price), 1e-8)
            reward -= drawdown_penalty

    # ➡️ Gentle Nonlinear Amplification
    if reward > 0:
        reward = reward ** 0.7
    else:
        reward = reward * 1.2

    return reward


def compute_dynamic_reward(
    previous_portfolio_value,
    current_portfolio_value,
    high_watermark,
    cash_balance,
    config=None
) -> float:

    reward = 0.0

    # Parameters (or load from config later)
    growth_scaling_factor = 10.0
    drawdown_penalty_factor = 20.0
    ath_bonus = 50.0
    low_cash_threshold = 0.1  # 10% of initial cash
    cash_penalty = 10.0

    # 1. Portfolio Growth Reward
    portfolio_growth = current_portfolio_value - previous_portfolio_value
    reward += portfolio_growth * growth_scaling_factor

    # 2. Drawdown Penalty
    if current_portfolio_value < high_watermark:
        drawdown = (high_watermark - current_portfolio_value) / high_watermark
        reward -= drawdown * drawdown_penalty_factor

    # 3. New All Time High Bonus
    if current_portfolio_value > high_watermark:
        reward += ath_bonus

    # 4. Low Cash Penalty
    if cash_balance < low_cash_threshold * previous_portfolio_value:
        reward -= cash_penalty

    return reward





