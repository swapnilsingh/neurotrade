import random
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
        self.last_action_forced = False  # 🧠 Track if forced

    def vote(self, state):
        votes = []
        for agent in self.agents:
            agent_vote = agent.vote(state)
            votes.append(agent_vote)

        # Tally votes
        buy_votes = votes.count("BUY")
        sell_votes = votes.count("SELL")
        hold_votes = votes.count("HOLD")

        majority = max(buy_votes, sell_votes, hold_votes)

        if majority == buy_votes and buy_votes > len(votes) // 2:
            self.last_action_forced = False
            return "BUY", votes
        elif majority == sell_votes and sell_votes > len(votes) // 2:
            self.last_action_forced = False
            return "SELL", votes
        else:
            # No strong majority -> HOLD
            self.last_action_forced = True
            return "HOLD", votes

