# utils/reward.py

import numpy as np

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
        quantity = 0.001

    try:
        position = float(position)
    except (ValueError, TypeError):
        position = 0.0

    return current_price, entry_price, quantity, position

def calculate_dynamic_volatility(ticks, window_size=10):
    """
    Calculate rolling volatility (standard deviation of price returns).
    """
    if len(ticks) < window_size + 1:
        return 0.002  # Default fallback threshold (0.2%)

    prices = [tick["price"] for tick in ticks[-(window_size + 1):]]
    returns = [(prices[i+1] - prices[i]) / max(prices[i], 1e-8) for i in range(len(prices) - 1)]

    rolling_volatility = np.std(returns)

    return max(0.0005, min(rolling_volatility, 0.01))  # Clamp between 0.05% and 1%


def compute_reward_from_ticks(
    ticks,
    signal,
    quantity,
    current_price,
    entry_price,
    position,
    slippage=0.0005,
    trading_fee=0.001,
    drawdown_penalty_factor=0.3,
    hold_penalty_base=-0.001,
    big_move_penalty_base=-0.015,
    bonus_multiplier_base=2.0,
    use_dynamic_volatility=True,
    inventory_ratio=None
):
    """
    Enhanced reward function with volatility, inventory, dynamic penalties,
    and small profitable trade encouragement.
    """
    current_price, entry_price, quantity, position = sanitize_inputs(
        current_price, entry_price, quantity, position
    )

    if not ticks:
        return -0.002  # fallback penalty if no future ticks

    reward = 0.0

    # 🔥 Dynamic volatility threshold
    volatility = calculate_dynamic_volatility(ticks) if use_dynamic_volatility else 0.002
    volatility_threshold = volatility

    # 📈 Calculate future price and price change
    future_price = float(ticks[-1]["price"])
    price_change_pct = (future_price - current_price) / max(current_price, 1e-8)

    # ➡️ HOLD case
    if signal == "HOLD":
        dynamic_hold_penalty = hold_penalty_base - (0.3 * volatility)
        reward = dynamic_hold_penalty
        if abs(price_change_pct) >= volatility_threshold:
            reward += big_move_penalty_base - (volatility * 4)

    # ➡️ BUY/SELL case
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

        # 🎯 Tiny profitable exit bonus
        if net_pnl > 0:
            reward += 0.001

        # 🎯 Big move bonus
        if abs(price_change_pct) >= volatility_threshold and reward > 0:
            reward *= bonus_multiplier_base + (volatility * 4)

    # ➡️ Drawdown penalty if open position
    if position != 0:
        unrealized_pnl = (current_price - entry_price) * position
        if unrealized_pnl < 0:
            drawdown_penalty = drawdown_penalty_factor * abs(unrealized_pnl) / max(abs(entry_price), 1e-8)
            reward -= drawdown_penalty

    # ➡️ Inventory overload penalty
    if inventory_ratio is not None and inventory_ratio > 0.6:
        reward -= (inventory_ratio - 0.6) * 0.015

    # ➡️ Nonlinear reward shaping
    if reward > 0:
        reward = reward ** 0.85  # smoother positive rewards
    else:
        reward = reward * 1.3   # lighter negative amplification

    return reward


def compute_dynamic_reward(
    previous_portfolio_value,
    current_portfolio_value,
    high_watermark,
    cash_balance,
    config=None
) -> float:
    """
    Dynamic portfolio-based reward function.
    """
    reward = 0.0

    growth_scaling_factor = 10.0
    drawdown_penalty_factor = 20.0
    ath_bonus = 50.0
    low_cash_threshold = 0.1
    cash_penalty = 10.0

    portfolio_growth = current_portfolio_value - previous_portfolio_value
    reward += portfolio_growth * growth_scaling_factor

    if current_portfolio_value < high_watermark:
        drawdown = (high_watermark - current_portfolio_value) / max(high_watermark, 1e-8)
        reward -= drawdown * drawdown_penalty_factor

    if current_portfolio_value > high_watermark:
        reward += ath_bonus

    if cash_balance < low_cash_threshold * previous_portfolio_value:
        reward -= cash_penalty

    return reward

def compute_reward(candle, signal, strategy="basic"):
    """
    Basic reward based on PnL and holding time.
    """
    pnl = candle.get("pnl", 0.0)
    holding_duration_sec = candle.get("holding_duration_sec", 0.0)

    slippage_penalty_rate = 0.0005
    min_holding_sec = 15
    early_exit_penalty = 1.0

    reward = 0.0

    if strategy == "basic":
        if signal == "SELL":
            reward = pnl
        else:
            reward = 0.0
    elif strategy == "smart":
        if signal == "SELL":
            reward = pnl
            reward -= slippage_penalty_rate * abs(pnl)
            if holding_duration_sec < min_holding_sec:
                reward -= early_exit_penalty
        else:
            reward = 0.0

    return reward
