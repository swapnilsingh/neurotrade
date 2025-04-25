from rl_agent.base import BaseAgent
from rl_agent.models.state import State

class ATRAgent(BaseAgent):
    def __init__(self, name="ATR"):
        super().__init__(name)

    def vote(self, state: State) -> int:
        atr_val = state.atr['atr'] if isinstance(state.atr, dict) else state.atr
        return self.map_signal(1) if atr_val > 1.0 else self.map_signal(0)  # BUY if volatility is high
