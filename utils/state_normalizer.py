# utils/state_normalizer.py

def normalize_state(state: dict) -> dict:
    """
    Normalize each feature to a reasonable range.
    Assumes input fields are flat dictionary of scalars.
    """

    normalized = {}

    for key, value in state.items():
        if "price" in key or "pnl" in key or "relative" in key or "drawdown" in key:
            normalized[key] = float(max(min(value, 1.0), -1.0))  # Clamp to [-1, 1]
        elif "volatility" in key or "volume_spike" in key or "inventory_ratio" in key:
            normalized[key] = float(max(min(value, 1.0), 0.0))   # Clamp to [0, 1]
        elif "reward" in key or "penalty" in key or "win_rate" in key or "sharpe" in key:
            normalized[key] = float(max(min(value, 2.0), -2.0))  # Wider but controlled
        else:
            normalized[key] = float(value)  # Fallback (no-op)

    return normalized
