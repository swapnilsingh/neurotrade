from rl_agent.base import BaseAgent

class ADXAgent(BaseAgent):
    def __init__(self, name="ADX"):
        super().__init__(name)

    def vote(self, state):
        adx = state.indicators.get("adx", 0)
        return "BUY" if adx > 25 else "HOLD"
