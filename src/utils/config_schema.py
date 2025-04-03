import json
from jsonschema import validate, ValidationError

# Define the strategy config schema
config_schema = {
    "type": "object",
    "properties": {
        "strategy_id": {"type": "string"},
        "indicators": {
            "type": "object",
            "properties": {
                "macd": {
                    "type": "object",
                    "properties": {
                        "fast_length": {"type": "integer"},
                        "slow_length": {"type": "integer"},
                        "signal_smooth": {"type": "integer"}
                    },
                    "required": ["fast_length", "slow_length", "signal_smooth"]
                },
                "rsi": {
                    "type": "object",
                    "properties": {
                        "length": {"type": "integer"},
                        "overbought": {"type": "integer"},
                        "oversold": {"type": "integer"}
                    },
                    "required": ["length", "overbought", "oversold"]
                }
            },
            "required": ["macd", "rsi"]
        },
        "trade_parameters": {
            "type": "object",
            "properties": {
                "position_size": {"type": "integer"},
                "stop_loss_pct": {"type": "number"},
                "take_profit_pct": {"type": "number"}
            },
            "required": ["position_size", "stop_loss_pct", "take_profit_pct"]
        },
        "slippage": {"type": "number"},
        "risk": {
            "type": "object",
            "properties": {
                "max_drawdown": {"type": "number"},
                "max_position_size": {"type": "number"}
            },
            "required": ["max_drawdown", "max_position_size"]
        },
        "evaluation": {
            "type": "object",
            "properties": {
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["metrics"]
        }
    },
    "required": ["strategy_id", "indicators", "trade_parameters", "slippage", "risk", "evaluation"]
}

# Save schema as a JSON file for easy reference
with open('config_schema.json', 'w') as f:
    json.dump(config_schema, f, indent=4)

# Print the schema to verify
print(json.dumps(config_schema, indent=4))
