import numpy as np

class DynamicTickEnsembleAgent:
    def __init__(self, window_size=10, volatility_multiplier=1.5):
        self.window_size = window_size
        self.volatility_multiplier = volatility_multiplier
        self.last_action_forced = False
        self.recent_price_changes = []

    def update_volatility(self):
        if len(self.recent_price_changes) >= 2:
            return np.std(self.recent_price_changes)
        else:
            return 1e-07  # Small default to avoid division by zero

    def vote(self, state):
        votes = []

        # 🛠️ FIX: Treat 'state' as a dictionary
        price_change = state.get("price_change", 0)
        momentum = state.get("momentum", 0)

        self.recent_price_changes.append(price_change)

        # Keep only last N
        if len(self.recent_price_changes) > self.window_size:
            self.recent_price_changes.pop(0)

        volatility = self.update_volatility()

        price_change_threshold = volatility * self.volatility_multiplier
        momentum_threshold = volatility * self.volatility_multiplier

        if price_change > price_change_threshold and momentum > momentum_threshold:
            votes.append("BUY")
        elif price_change < -price_change_threshold and momentum < -momentum_threshold:
            votes.append("SELL")
        else:
            votes.append("HOLD")

        buy_votes = votes.count("BUY")
        sell_votes = votes.count("SELL")
        hold_votes = votes.count("HOLD")

        majority = max(buy_votes, sell_votes, hold_votes)

        if majority == buy_votes:
            self.last_action_forced = False
            return "BUY", votes
        elif majority == sell_votes:
            self.last_action_forced = False
            return "SELL", votes
        else:
            self.last_action_forced = True
            return "HOLD", votes
