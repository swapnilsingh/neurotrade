import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os

class QNetwork(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(QNetwork, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )
    def forward(self, x):
        return self.model(x)

class DQNAgent:
    def __init__(self, input_dim=None, action_space=[1, -1, 0], device='cpu', model_path="models/model.pt"):
        self.device = torch.device(device) if isinstance(device, str) else device
        self.action_space = action_space
        self.num_actions = len(self.action_space)
        self.model_path = model_path

        self.epsilon = 1.0
        self.epsilon_decay = 0.997
        self.epsilon_min = 0.02

        self.q_net = None
        self.target_net = None
        self.optimizer = None
        self.loss_fn = None

        if input_dim is not None:
            self.initialize_networks(input_dim)

            # 🔥 New Safe Load: only load if model matches input_dim
            if os.path.exists(model_path):
                try:
                    checkpoint = torch.load(model_path, map_location=self.device)
                    model_input_dim = None
                    for k, v in checkpoint.items():
                        if "weight" in k and len(v.shape) == 2:
                            model_input_dim = v.shape[1]
                            break

                    if model_input_dim is None:
                        raise ValueError("Cannot infer input_dim from model checkpoint!")

                    if model_input_dim != input_dim:
                        print(f"⚠️ Model input_dim mismatch in checkpoint: found {model_input_dim}, expected {input_dim}. Training from scratch.")
                    else:
                        self.q_net.load_state_dict(checkpoint)
                        self.update_target_network()
                        print(f"✅ DQNAgent loaded model successfully from {model_path}")
                except Exception as e:
                    print(f"⚠️ Failed to load model checkpoint: {e}. Training from scratch.")

    def initialize_networks(self, input_dim):
        """Build Q-network and target-network and optimizer."""
        self.input_dim = input_dim
        self.q_net = QNetwork(self.input_dim, self.num_actions).to(self.device)
        self.target_net = QNetwork(self.input_dim, self.num_actions).to(self.device)
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=1e-4)
        self.loss_fn = nn.MSELoss()
        self.update_target_network()

    def train(self, batch, gamma=0.99):
        # If not initialized, infer input_dim from the first state's size
        if self.q_net is None:
            first_state = batch[0][0]
            state_array = np.array(first_state, dtype=np.float32)
            self.initialize_networks(len(state_array))
            self.load_model(self.model_path)

        states, actions, rewards, next_states, dones = zip(*batch)
        # Convert to tensors of correct dtype
        states = torch.from_numpy(np.stack(states)).float().to(self.device)
        next_states = torch.from_numpy(np.stack(next_states)).float().to(self.device)
        rewards = torch.tensor(rewards, dtype=torch.float32).to(self.device)
        dones = torch.tensor(dones, dtype=torch.bool).to(self.device)

        # Convert actions to indices in action space
        action_indices = [self.action_space.index(a) for a in actions]
        actions_tensor = torch.tensor(action_indices, dtype=torch.int64).unsqueeze(1).to(self.device)

        # Compute current Q-values and target Q-values
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
        # Convert state dict to array if needed
        if isinstance(state, dict):
            state = np.array(list(state.values()), dtype=np.float32)
        # Append dynamic quantity if state is one feature short
        if isinstance(state, np.ndarray) and state.shape[-1] == getattr(self, 'input_dim', state.shape[-1]) - 1:
            state = np.append(state, quantity)

        if np.random.rand() < self.epsilon:
            return np.random.choice(self.action_space)  # explore
        else:
            state_tensor = torch.from_numpy(state).float().unsqueeze(0).to(self.device)
            q_values = self.q_net(state_tensor)
            best_action_idx = torch.argmax(q_values, dim=1).item()
            return self.action_space[best_action_idx]

    def update_target_network(self):
        """Copy Q-network weights to target network."""
        if self.target_net is not None:
            self.target_net.load_state_dict(self.q_net.state_dict())
            print("[DQNAgent] 🔄 Target network synchronized.")

    def save_model(self, path="model.pt"):
        torch.save(self.q_net.state_dict(), path)
        print(f"[DQNAgent] 💾 Model saved to {path}")

    def load_model(self, path="model.pt"):
        if self.q_net is None:
            return  # Cannot load if uninitialized
        if os.path.exists(path):
            try:
                checkpoint = torch.load(path, map_location=self.device)
                model_state_dict = self.q_net.state_dict()
                # Load only if shapes match
                if all(key in checkpoint and checkpoint[key].shape == model_state_dict[key].shape
                       for key in model_state_dict.keys()):
                    self.q_net.load_state_dict(checkpoint)
                    self.update_target_network()
                    print(f"[DQNAgent] ✅ Model loaded from {path}")
                else:
                    print(f"[DQNAgent] ⚠️ Model shape mismatch. Fresh model initialized.")
            except Exception as e:
                print(f"[DQNAgent] ⚠️ Model load failed ({e}). Fresh model initialized.")
        else:
            print(f"[DQNAgent] ⚠️ No model found at {path}. Using fresh model.")
