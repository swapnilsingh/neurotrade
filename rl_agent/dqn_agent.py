import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os

# 🧠 Simple MLP for Q-function
class QNetwork(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(QNetwork, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def forward(self, x):
        return self.model(x)

class DQNAgent:
    def __init__(self, input_dim=7, action_space=[1, -1, 0], device='cpu', model_path="models/model.pt"):
        self.device = torch.device(device)
        self.action_space = action_space
        self.num_actions = len(action_space)
        self.input_dim = input_dim 

        self.q_net = QNetwork(self.input_dim, self.num_actions).to(self.device)
        self.target_net = QNetwork(self.input_dim, self.num_actions).to(self.device)
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=1e-4)
        self.loss_fn = nn.MSELoss()

        self.update_target_network()

        # Epsilon-Greedy Parameters
        self.epsilon = 1.0
        self.epsilon_decay = 0.99
        self.epsilon_min = 0.01

        # NEW: Model path and Auto-load
        self.model_path = model_path
        self.load_model(self.model_path)  # Auto-load if model.pt exists


    def train(self, batch, gamma=0.99):
        states, actions, rewards, next_states, dones = zip(*batch)

        # 🛡️ Handle new quantity inside state
        states = torch.from_numpy(np.stack(states)).float().to(self.device)
        next_states = torch.from_numpy(np.stack(next_states)).float().to(self.device)

        rewards = torch.tensor(rewards, dtype=torch.float32).to(self.device)
        dones = torch.tensor(dones, dtype=torch.bool).to(self.device)

        action_indices = [self.action_space.index(a) for a in actions]
        actions_tensor = torch.tensor(action_indices, dtype=torch.int64).unsqueeze(1).to(self.device)

        q_values = self.q_net(states).gather(1, actions_tensor).squeeze()

        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(1)[0]
            target_q = rewards + gamma * next_q_values * (~dones)

        loss = self.loss_fn(q_values, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def select_action(self, state, quantity=0.001):
        """
        Choose action using epsilon-greedy strategy.
        Now expects quantity as additional input.
        """
        # Ensure state includes quantity
        if isinstance(state, np.ndarray) and state.shape[-1] == self.input_dim - 1:
            # Append quantity if missing
            state = np.append(state, quantity)

        if np.random.rand() < self.epsilon:
            # Explore: Random action
            return np.random.choice(self.action_space)
        else:
            # Exploit: Choose best action
            state_tensor = torch.from_numpy(state).float().unsqueeze(0).to(self.device)
            q_values = self.q_net(state_tensor)
            best_action_idx = torch.argmax(q_values, dim=1).item()
            return self.action_space[best_action_idx]

    def update_target_network(self):
        self.target_net.load_state_dict(self.q_net.state_dict())
        print("[DQNAgent] 🔄 Target network synchronized.")

    def save_model(self, path="model.pt"):
        torch.save(self.q_net.state_dict(), path)
        print(f"[DQNAgent] 💾 Model saved to {path}")

    def load_model(self, path="model.pt"):
        if os.path.exists(path):
            self.q_net.load_state_dict(torch.load(path, map_location=self.device))
            self.update_target_network()
            print(f"[DQNAgent] ✅ Model loaded from {path}")
        else:
            print(f"[DQNAgent] ⚠️ Model path not found, starting fresh.")

