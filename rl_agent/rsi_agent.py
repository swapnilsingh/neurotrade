from rl_agent.base import BaseAgent

class RSIAgent(BaseAgent):
    def __init__(self, name="RSI"):
        super().__init__(name)

    def vote(self, state):
        rsi = state.indicators.get("rsi", 50)
        if rsi < 30:
            return "BUY"
        elif rsi > 70:
            return "SELL"
        return "HOLD"
