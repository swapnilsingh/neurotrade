# rl_agent/tick_ensemble_agent.py

class TickEnsembleAgent:
    def __init__(self, price_change_threshold=0.0002, momentum_threshold=0.0001):
        self.price_change_threshold = price_change_threshold
        self.momentum_threshold = momentum_threshold
        self.last_action_forced = False

    def vote(self, state):
        votes = []

        # Basic simple rule agents
        if state.price_change > self.price_change_threshold:
            votes.append("BUY")
        elif state.price_change < -self.price_change_threshold:
            votes.append("SELL")
        else:
            votes.append("HOLD")

        if state.momentum > self.momentum_threshold:
            votes.append("BUY")
        elif state.momentum < -self.momentum_threshold:
            votes.append("SELL")
        else:
            votes.append("HOLD")

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
            self.last_action_forced = True
            return "HOLD", votes
