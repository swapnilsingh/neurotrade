from rl_agent.models.state import State

class BaseAgent:
    def __init__(self, name="BaseAgent"):
        self.name = name

    def vote(self, state: State) -> int:
        raise NotImplementedError("Subclasses must implement this method")
    
    def map_signal(self, signal: int) -> str:
        return {1: "BUY", -1: "SELL", 0: "HOLD"}.get(signal, "HOLD")
