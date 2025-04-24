from rl_agent.base import BaseAgent

class ATRAgent(BaseAgent):
    def __init__(self, name="ATR"):
        super().__init__(name)

    def vote(self, state):
        atr = state.indicators.get("atr", 0)
        return "BUY" if atr > 1.0 else "HOLD"
