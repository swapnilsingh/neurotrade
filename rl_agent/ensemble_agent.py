from rl_agent.rsi_agent import RSIAgent
from rl_agent.models.state import State
from rl_agent.macd_agent import MACDAgent
from rl_agent.adx_agent import ADXAgent
from rl_agent.atr_agent import ATRAgent
from rl_agent.bollinger_agent import BollingerAgent

class EnsembleAgent:
    def __init__(self):
        self.agents = [
            RSIAgent(),
            MACDAgent(),
            ADXAgent(),
            ATRAgent(),
            BollingerAgent(),
        ]

    def vote(self, state: State) -> str:
        votes = [agent.vote(state) for agent in self.agents]  # ["BUY", "SELL", "HOLD", ...]
        result = max(set(votes), key=votes.count)  # majority vote
        return result, {a.name: v for a, v in zip(self.agents, votes)}
