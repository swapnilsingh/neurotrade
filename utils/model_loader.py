import os
import torch
from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("model_loader.yaml")
class ModelLoader:
    def __init__(self, model_class, model_path=None, output_dim=None, device=torch.device("cpu")):
        self.model_class = model_class
        self.device = device
        self.model_path = model_path or self.config.get("model_path")
        self.output_dim = output_dim or self.config.get("output_dim")
        self.hidden_layers = self.config.get("hidden_layers", [128, 128])

        self.model = None
        self.input_dim = None
        self.last_mtime = None
        self.model_loaded = False

    def load(self):
        if not os.path.exists(self.model_path):
            self.logger.warning(f"⚠️ Model file not found at {self.model_path}. Fallback mode enabled.")
            return None, None

        try:
            state_dict = torch.load(self.model_path, map_location=self.device)
            inferred_input_dim = self._infer_input_dim(state_dict)

            model = self.model_class(
                input_dim=inferred_input_dim,
                output_dim=self.output_dim,
                hidden_layers=self.hidden_layers
            ).to(self.device)

            model.load_state_dict(state_dict)
            model.eval()

            self.input_dim = inferred_input_dim
            self.model_loaded = True
            self.logger.info(f"✅ Loaded model with input_dim={self.input_dim}, output_dim={self.output_dim}")
            return model, self.input_dim

        except Exception as e:
            self.logger.exception(f"❌ Failed to load model: {e}")
            return None, None

    def auto_refresh(self, refresh_interval_sec=30):
        if not os.path.exists(self.model_path):
            return False

        current_mtime = os.path.getmtime(self.model_path)
        if self.last_mtime is None or current_mtime > self.last_mtime:
            self.logger.info("♻️ Detected updated model file. Reloading...")
            self.load()
            self.last_mtime = current_mtime
            return True
        return False

    def _infer_input_dim(self, state_dict):
        for key, value in state_dict.items():
            if "weight" in key and len(value.shape) == 2:
                return value.shape[1]
        raise ValueError("❌ Could not infer input_dim from model weights.")
