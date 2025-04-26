import os
import numpy as np
import torch

MODEL_PATH = "/app/models/model.pt"

class DynamicTickEnsembleAgent:
    def __init__(self, window_size=10, volatility_multiplier=1.5):
        self.window_size = window_size
        self.volatility_multiplier = volatility_multiplier
        self.last_action_forced = False
        self.recent_price_changes = []

        # 🧠 Load model if available (for future extension, even though now voting is rule-based)
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                # Assuming a simple torch model structure
                self.model = torch.load(MODEL_PATH, map_location=self.device)
                print(f"✅ [DynamicTickEnsembleAgent] Loaded model from {MODEL_PATH}")
            except Exception as e:
                print(f"⚠️ [DynamicTickEnsembleAgent] Failed to load model: {e}")
        else:
            print(f"⚠️ [DynamicTickEnsembleAgent] Model not found at {MODEL_PATH}, continuing without model.")

    def update_volatility(self):
        if len(self.recent_price_changes) >= 2:
            return np.std(self.recent_price_changes)
        else:
            return 1e-07  # Small default to avoid division by zero

    def vote(self, state):
        votes = []

        # 🛠️ State features extraction
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
