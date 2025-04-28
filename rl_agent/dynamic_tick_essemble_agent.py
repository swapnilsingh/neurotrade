import os
import numpy as np
import torch

MODEL_PATH = "/app/models/model.pt"

class DynamicTickEnsembleAgent:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.last_action_forced = False
        self.recent_price_changes = []

        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_loaded = False

        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                checkpoint = torch.load(MODEL_PATH, map_location=self.device)
                if isinstance(checkpoint, dict):
                    print(f"⚠️ [DynamicTickEnsembleAgent] Found a model state_dict, skipping loading model for now.")
                    self.model = None
                else:
                    self.model = checkpoint
                    self.model.eval()
                    self.model_loaded = True
                    print(f"✅ [DynamicTickEnsembleAgent] Loaded model from {MODEL_PATH}")
            except Exception as e:
                print(f"⚠️ [DynamicTickEnsembleAgent] Failed to load model: {e}")
        else:
            print(f"⚠️ [DynamicTickEnsembleAgent] Model not found at {MODEL_PATH}, continuing without model.")

    def update_volatility(self):
        if len(self.recent_price_changes) >= 2:
            return np.std(self.recent_price_changes)
        else:
            return 1e-07  # Small value to avoid division by zero

    def vote(self, state):
        """
        Returns: (signal, votes, dynamic_quantity, take_profit_pct, suggestion)
        """
        if self.model_loaded and self.model is not None:
            try:
                state_array = np.array(list(state.values()), dtype=np.float32)
                state_tensor = torch.tensor(state_array).unsqueeze(0).to(self.device)

                with torch.no_grad():
                    q_values = self.model(state_tensor)
                    action = torch.argmax(q_values, dim=1).item()

                if action == 0:
                    return "HOLD", ["HOLD"], 0.0, 0.0, "Model suggests HOLD"
                elif action == 1:
                    return "BUY", ["BUY"], 0.001, 0.01, "Model suggests BUY"
                elif action == 2:
                    return "SELL", ["SELL"], 0.001, 0.01, "Model suggests SELL"
                else:
                    return "HOLD", ["HOLD"], 0.0, 0.0, "Model suggests HOLD"

            except Exception as e:
                print(f"⚠️ [DynamicTickEnsembleAgent] Model prediction failed: {e}. Falling back to rule-based.")
                self.model_loaded = False

        # 📋 Fallback to basic voting logic
        return self._rule_based_vote(state)

    def _rule_based_vote(self, state):
        votes = []

        price_change = state.get("price_change", 0)
        momentum = state.get("momentum", 0)

        self.recent_price_changes.append(price_change)
        if len(self.recent_price_changes) > self.window_size:
            self.recent_price_changes.pop(0)

        volatility = self.update_volatility()
        fallback_multiplier = 1.0  # ✅ Hardcoded fallback

        price_change_threshold = volatility * fallback_multiplier
        momentum_threshold = volatility * fallback_multiplier

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

        if buy_votes == majority:
            return "BUY", votes, 0.001, 0.01, "Rule suggests BUY"
        elif sell_votes == majority:
            return "SELL", votes, 0.001, 0.01, "Rule suggests SELL"
        else:
            return "HOLD", votes, 0.0, 0.0, "Rule suggests HOLD"
