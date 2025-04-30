import numpy as np
import torch
from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/input_preprocessor.yaml")
class InputPreprocessor:
    def __init__(self):
        self.default_dynamic_quantity = self.config.get("default_dynamic_quantity", 0.001)

    def prepare_tensor(self, state: dict, expected_input_dim: int, device=torch.device("cpu")):
        try:
            state_array = np.array(list(state.values()), dtype=np.float32)

            # Append dynamic quantity if off by one
            if state_array.shape[0] == expected_input_dim - 1:
                state_array = np.append(state_array, self.default_dynamic_quantity)

            if state_array.shape[0] != expected_input_dim:
                raise ValueError(f"⚠️ Expected {expected_input_dim} features, got {state_array.shape[0]}")

            state_tensor = torch.tensor(state_array).unsqueeze(0).to(device)
            return state_tensor

        except Exception as e:
            self.logger.exception(f"❌ Failed to preprocess state: {e}")
            raise
