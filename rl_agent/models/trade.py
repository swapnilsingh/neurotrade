from dataclasses import dataclass

@dataclass
class TradeState:
    initial_cash: float
    cash: float
    inventory: float = 0.0
    entry_price: float = 0.0
    realized_profit: float = 0.0
    signal_counter: int = 0

    @classmethod
    def from_config(cls, config: dict):
        return cls(
            initial_cash=config.get("initial_cash", 1000.0),
            cash=config.get("initial_cash", 1000.0)
        )
