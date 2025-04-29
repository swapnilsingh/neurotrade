import os
import time
import numpy as np
import torch
from rl_agent.dqn_agent import QNetwork

MODEL_PATH = "/app/models/model.pt"

class DynamicTickEnsembleAgent:
    def __init__(self, window_size=10, refresh_interval=300):
        self.window_size = window_size
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.model_loaded = False

        self.input_dim = None
        self.action_space = [1, -1, 0]
        self.num_actions = len(self.action_space)

        self.refresh_interval = refresh_interval  # seconds
        self.last_refresh_time = 0
        self.last_model_mtime = None

        self.load_model()

    def load_model(self):
        print(f"🔎 [DynamicTickEnsembleAgent] Checking for model at: {MODEL_PATH}")

        if not os.path.exists(MODEL_PATH):
            print(f"⚠️ [DynamicTickEnsembleAgent] Model file does not exist. Skipping model load. Fallback to HOLD.")
            self.model_loaded = False
            return

        try:
            state_dict = torch.load(MODEL_PATH, map_location=self.device)

            # 🔥 Dynamically infer input_dim every time
            inferred_input_dim = None
            for key, value in state_dict.items():
                if "weight" in key and len(value.shape) == 2:
                    inferred_input_dim = value.shape[1]
                    break

            if inferred_input_dim is None:
                raise ValueError("❌ Could not infer input_dim from model state_dict.")

            if self.input_dim is not None and self.input_dim != inferred_input_dim:
                print(f"⚡ Detected model input_dim change: {self.input_dim} ➔ {inferred_input_dim}. Adapting agent.")
            
            self.input_dim = inferred_input_dim  # ✅ Update input_dim

            self.model = QNetwork(self.input_dim, self.num_actions).to(self.device)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self.model_loaded = True
            print(f"✅ [DynamicTickEnsembleAgent] Successfully loaded model with input_dim={self.input_dim} from {MODEL_PATH}")
        
        except Exception as e:
            print(f"⚠️ [DynamicTickEnsembleAgent] Model load failed: {e}. Using fallback HOLD mode.")
            self.model = None
            self.model_loaded = False


    def auto_refresh_model(self):
        """Auto refresh model if new model is detected."""
        current_time = time.time()
        if current_time - self.last_refresh_time >= self.refresh_interval:
            self.last_refresh_time = current_time
            if os.path.exists(MODEL_PATH):
                mtime = os.path.getmtime(MODEL_PATH)
                if self.last_model_mtime is None or mtime > self.last_model_mtime:
                    print(f"♻️ [DynamicTickEnsembleAgent] New model detected. Reloading model...")
                    self.load_model()

    def vote(self, state):
        if self.model_loaded and self.model is not None:
            try:
                # ➡️ Patch: Always append dynamic_quantity = 0.001 if missing
                state_array = np.array(list(state.values()), dtype=np.float32)

                # 🛡 Safely check and fix state length
                if state_array.shape[0] == self.input_dim - 1:
                    # append dummy quantity if missing
                    state_array = np.append(state_array, 0.001)

                if state_array.shape[0] != self.input_dim:
                    raise ValueError(f"State feature count ({state_array.shape[0]}) != model input_dim ({self.input_dim})")

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
                print(f"⚠️ [DynamicTickEnsembleAgent] Inference failed: {e}. Switching to fallback.")
                self.model_loaded = False

        # Fallback
        return "HOLD", ["HOLD"], 0.0, 0.0, "Fallback: HOLD (no model)"

