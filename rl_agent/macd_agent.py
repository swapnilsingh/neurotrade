from rl_agent.base import BaseAgent
from rl_agent.models.state import State

class MACDAgent(BaseAgent):
    def __init__(self, name="MACD"):
        super().__init__(name)

    def vote(self, state: State) -> str:
        macd_val = state.macd['macd'] if isinstance(state.macd, dict) else state.macd
        signal = state.macd['macd_signal'] if isinstance(state.macd, dict) else 0
        if macd_val > signal:
            return self.map_signal(1)  # BUY
        elif macd_val < signal:
            return self.map_signal(-1)  # SELL
        return self.map_signal(0)  # HOLD
