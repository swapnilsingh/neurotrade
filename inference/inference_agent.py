import time
import torch

from core.models.q_network import QNetwork
from utils.model_loader import ModelLoader
from inference.input_preprocessor import InputPreprocessor
from inference.signal_decider import SignalDecider
from core.decorators.decorators import inject_logger, inject_config


@inject_logger()
@inject_config("configs/inference_agent.yaml")
class InferenceAgent:
    def __init__(self):
        # Injected from config
        device_str = self.config.get("device", "cpu")
        self.device = torch.device(device_str)

        fallback_tensor_values = self.config.get("fallback_tensor", [0.0, 0.0, 0.0])
        self.fallback_tensor = torch.tensor([fallback_tensor_values], dtype=torch.float32)

        self.model_path = self.config.get("model_path")
        self.refresh_interval = self.config.get("refresh_interval", 30)

        # Modules
        self.model_loader = ModelLoader(QNetwork, model_path=self.model_path, device=self.device)
        self.input_preprocessor = InputPreprocessor()
        self.signal_decider = SignalDecider()

        # Model state
        self.model = self.model_loader.load()
        self.last_refresh_time = 0

    def auto_refresh_model(self):
        now = time.time()
        if now - self.last_refresh_time >= self.refresh_interval:
            self.last_refresh_time = now
            if self.model_loader.auto_refresh():
                self.model = self.model_loader.model

    def vote(self, state: dict):
        if not self.model_loader.model_loaded or self.model is None:
            return self.signal_decider.decide(self.fallback_tensor)

        try:
            tensor_input = self.input_preprocessor.prepare_tensor(
                state, expected_input_dim=self.model_loader.input_dim, device=self.device
            )
            with torch.no_grad():
                q_values = self.model(tensor_input)
            return self.signal_decider.decide(q_values)

        except Exception as e:
            self.logger.exception(f"❌ Inference failed during vote: {e}")
            return self.signal_decider.decide(self.fallback_tensor)
