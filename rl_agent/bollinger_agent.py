from rl_agent.base import BaseAgent

class BollingerAgent(BaseAgent):
    def __init__(self, name="Bollinger"):
        super().__init__(name)

    def vote(self, state):
        bb = state.indicators.get("bollinger", {})
        close = state.indicators.get("close", 0)
        upper = bb.get("bollinger_hband", 0)
        lower = bb.get("bollinger_lband", 0)
        if close < lower:
            return "BUY"
        elif close > upper:
            return "SELL"
        return "HOLD"
