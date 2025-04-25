from rl_agent.base import BaseAgent
from rl_agent.models.state import State

class ADXAgent(BaseAgent):
    def __init__(self, name="ADX"):
        super().__init__(name)

    def vote(self, state: State) -> int:
        adx_val = state.adx['adx'] if isinstance(state.adx, dict) else state.adx
        return self.map_signal(1) if adx_val > 25 else self.map_signal(0)    # BUY if strong trend, else HOLD
