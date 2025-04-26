import torch
import random
from collections import deque
from rl_agent.dqn_agent import DQNModel
from rl_agent.models.experience import Experience

class DQNTrainer:
    def __init__(self, input_dim, output_dim, device=None, gamma=0.99, lr=0.001):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🚀 Using device: {self.device}")

        self.model = DQNModel(input_dim, output_dim).to(self.device)
        self.target_model = DQNModel(input_dim, output_dim).to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = torch.nn.MSELoss()
        self.gamma = gamma
        self.memory = deque(maxlen=10000)
        self.batch_size = 64

    def remember(self, experience: Experience):
        self.memory.append(experience)

    def replay(self):
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        for exp in batch:
            state = torch.tensor(exp.state.indicators_vector(), dtype=torch.float32).unsqueeze(0).to(self.device)
            next_state = torch.tensor(exp.next_state.indicators_vector(), dtype=torch.float32).unsqueeze(0).to(self.device)

            target = self.model(state).detach()
            next_q = self.target_model(next_state).detach()
            reward = torch.tensor([exp.reward], dtype=torch.float32).to(self.device)
            done = exp.done
            action_map = {'BUY': 1, 'SELL': -1, 'HOLD': 0}
            action_idx = [1, -1, 0].index(action_map[exp.action])


            if done:
                target[0][action_idx] = reward
            else:
                target[0][action_idx] = reward + self.gamma * torch.max(next_q)

            output = self.model(state)
            loss = self.criterion(output, target)

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def save_model(self, path="model.pt"):
        torch.save(self.model.state_dict(), path)
