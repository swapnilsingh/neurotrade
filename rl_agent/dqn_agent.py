import torch
import torch.nn as nn
import numpy as np
from rl_agent.base import BaseAgent
from rl_agent.models.state import State

class DQNModel(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQNModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def forward(self, x):
        return self.net(x)

class DQNAgent(BaseAgent):
    def __init__(self, input_dim=10, output_dim=3, name="DQN", model_path="model.pt"):
        super().__init__(name)
        self.model = DQNModel(input_dim, output_dim)
        self.model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
        self.model.eval()

    def vote(self, state: State) -> str:
        x = torch.tensor(state.indicators_vector(), dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            q_values = self.model(x)
        action_idx = torch.argmax(q_values).item()
        signal = [1, -1, 0][action_idx]  # numeric mapping
        return self.map_signal(signal)  # string output: "BUY", "SELL", "HOLD"
