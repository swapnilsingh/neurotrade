import os
import time
import numpy as np
import torch
import logging
from rl_agent.dqn_agent import QNetwork
from utils.config_loader import load_config

logger = logging.getLogger("DynamicTickEnsembleAgent")

class DynamicTickEnsembleAgent:
    def __init__(self, config=None):
        self.config = config or load_config("configs/ensemble_agent.yaml")

        # 🔧 Configurable Parameters
        self.window_size = self.config.get("window_size")
        self.refresh_interval = self.config.get("refresh_interval")
        self.model_path = self.config.get("model_path")
        self.default_dynamic_quantity = self.config.get("default_dynamic_quantity", 0.001)
        self.fallback_action = self.config.get("fallback_action", "HOLD")

        # 💻 Force CPU for inference
        self.device = torch.device("cpu")

        self.input_dim = None
        self.model = None
        self.model_loaded = False
        self.last_refresh_time = 0
        self.last_model_mtime = None

        self.action_space = ["BUY", "SELL", "HOLD"]
        self.num_actions = len(self.action_space)

        self.load_model()

    def load_model(self):
        logger.debug(f"🔍 Checking for model at {self.model_path}")
        if not os.path.exists(self.model_path):
            logger.warning("⚠️ Model file not found. Fallback to HOLD.")
            self.model_loaded = False
            return

        try:
            state_dict = torch.load(self.model_path, map_location=self.device)
            for key, value in state_dict.items():
                if "weight" in key and len(value.shape) == 2:
                    self.input_dim = value.shape[1]
                    break

            if self.input_dim is None:
                raise ValueError("❌ Could not infer input_dim from model.")

            self.model = QNetwork(self.input_dim, self.num_actions).to(self.device)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self.model_loaded = True
            logger.info(f"✅ Model loaded successfully with input_dim={self.input_dim}")

        except Exception as e:
            logger.exception(f"❌ Model loading failed: {e}")
            self.model_loaded = False

    def auto_refresh_model(self):
        current_time = time.time()
        if current_time - self.last_refresh_time >= self.refresh_interval:
            self.last_refresh_time = current_time
            if os.path.exists(self.model_path):
                mtime = os.path.getmtime(self.model_path)
                if self.last_model_mtime is None or mtime > self.last_model_mtime:
                    logger.info("♻️ Model file updated. Reloading model...")
                    self.load_model()
                    self.last_model_mtime = mtime

    def vote(self, state):
        if self.model_loaded and self.model is not None:
            try:
                state_array = np.array(list(state.values()), dtype=np.float32)

                if self.input_dim and state_array.shape[0] == self.input_dim - 1:
                    state_array = np.append(state_array, self.default_dynamic_quantity)

                if state_array.shape[0] != self.input_dim:
                    raise ValueError(f"⚠️ Expected {self.input_dim} features, got {state_array.shape[0]}")

                state_tensor = torch.tensor(state_array).unsqueeze(0).to(self.device)

                with torch.no_grad():
                    q_values = self.model(state_tensor)
                    action_idx = torch.argmax(q_values, dim=1).item()

                logger.debug(f"[Q-values] {q_values.tolist()} | Action Index: {action_idx}")

                if action_idx >= len(self.action_space):
                    raise ValueError(f"Invalid action index: {action_idx}")

                signal = self.action_space[action_idx]
                quantity = self.default_dynamic_quantity if signal != "HOLD" else 0.0
                take_profit = 0.01 if signal != "HOLD" else 0.0
                reason = f"Model suggests {signal}"

                return signal, [signal], quantity, take_profit, reason

            except Exception as e:
                logger.exception(f"❌ Inference failed: {e}")

        # ➖ Fallback Mode
        return self.fallback_action, [self.fallback_action], 0.0, 0.0, f"Fallback: {self.fallback_action}"

