from rl_agent.base import BaseAgent
from rl_agent.models.state import State

class RSIAgent(BaseAgent):
    def __init__(self, name="RSI"):
        super().__init__(name)

    def vote(self, state: State) -> str:
        rsi_val = state.rsi['rsi'] if isinstance(state.rsi, dict) else state.rsi
        if rsi_val < 30:
            return self.map_signal(1)  # BUY
        elif rsi_val > 70:
            return self.map_signal(-1)  # SELL
        return self.map_signal(0)  # HOLD
