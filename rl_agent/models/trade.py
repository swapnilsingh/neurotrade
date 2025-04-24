from dataclasses import dataclass

@dataclass
class Trade:
    timestamp: int
    symbol: str
    signal: str
    equity: float
    reason: str
    votes: dict
    indicators: dict
    strategy_config: dict
    model_version: str
