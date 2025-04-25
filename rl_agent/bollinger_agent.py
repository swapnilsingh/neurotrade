from rl_agent.base import BaseAgent
from rl_agent.models.state import State

class BollingerAgent(BaseAgent):
    def __init__(self, name="Bollinger"):
        super().__init__(name)

    def vote(self, state: State) -> int:
        close = state.close
        if isinstance(state.bollinger, dict):
            upper = state.bollinger.get('bollinger_hband', 0)
            lower = state.bollinger.get('bollinger_lband', 0)
        else:
            upper = lower = 0

        if close < lower:
            return self.map_signal(1)    # BUY
        elif close > upper:
            return self.map_signal(-1)   # SELL
        return self.map_signal(0)    # HOLD
