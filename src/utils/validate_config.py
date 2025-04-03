import json
from jsonschema import validate, ValidationError

# Load the config schema from the config_schema.json file
with open('config_schema.json', 'r') as f:
    config_schema = json.load(f)

# Sample strategy config to validate
strategy_config = {
    "strategy_id": "macd_rsi_strategy",
    "indicators": {
        "macd": {
            "fast_length": 12,
            "slow_length": 26,
            "signal_smooth": 9
        },
        "rsi": {
            "length": 14,
            "overbought": 70,
            "oversold": 30
        }
    },
    "trade_parameters": {
        "position_size": 1000,
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.05
    },
    "slippage": 0.001,
    "risk": {
        "max_drawdown": 0.2,
        "max_position_size": 0.1
    },
    "evaluation": {
        "metrics": ["roi", "sharpe", "win_rate"]
    }
}

# Validate the strategy config
try:
    validate(instance=strategy_config, schema=config_schema)
    print("Config is valid.")
except ValidationError as e:
    print(f"Config is invalid: {e.message}")
