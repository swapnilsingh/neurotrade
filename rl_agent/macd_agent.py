from rl_agent.base import BaseAgent

class MACDAgent(BaseAgent):
    def __init__(self, name="MACD"):
        super().__init__(name)

    def vote(self, state):
        macd = state.indicators.get("macd", {})
        macd_val = macd.get("macd", 0)
        signal = macd.get("macd_signal", 0)
        if macd_val > signal:
            return "BUY"
        elif macd_val < signal:
            return "SELL"
        return "HOLD"
