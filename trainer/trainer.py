import os
import json
import torch
import random
import numpy as np
from collections import deque

from core.models.q_network import QNetwork
from core.experience.experience_reader import ExperienceReader
from utils.model_loader import ModelLoader
from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/trainer.yaml")
class Trainer:
    def __init__(self, redis_conn):
        self.logger.info("🧠 Initializing Trainer...")

        self.redis_conn = redis_conn
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.batch_size = self.config.get("batch_size", 64)
        self.train_after = self.config.get("train_after_experiences", 500)
        self.train_steps = self.config.get("mini_batch_train_steps", 3)
        self.gamma = self.config.get("gamma", 0.99)
        self.epsilon = self.config.get("epsilon_start", 1.0)
        self.epsilon_min = self.config.get("epsilon_min", 0.05)
        self.epsilon_decay = self.config.get("epsilon_decay", 0.995)
        self.model_path = self.config.get("model_path", "core/models/model.pt")

        # Load model
        self.model_loader = ModelLoader(QNetwork, model_path=self.model_path, device=self.device)
        self.policy_net, _ = self.model_loader.load()

        input_dim = self.model_loader.input_dim
        output_dim = self.model_loader.output_dim
        self.target_net = QNetwork(input_dim, output_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.optimizer = torch.optim.Adam(self.policy_net.parameters())

        self.buffer = deque(maxlen=10_000)
        self.reader = ExperienceReader(self.redis_conn)

    async def ingest_loop(self):
        await self.reader.ingest()
        self.buffer = self.reader.buffer

    def sample_batch(self):
        return random.sample(self.buffer, min(len(self.buffer), self.batch_size))

    def train_step(self, batch):
        states = torch.tensor([b["state"] for b in batch], dtype=torch.float32).to(self.device)
        actions = torch.tensor([b["action"] for b in batch], dtype=torch.int64).to(self.device)
        rewards = torch.tensor([b["reward"] for b in batch], dtype=torch.float32).to(self.device)
        next_states = torch.tensor([b["next_state"] for b in batch], dtype=torch.float32).to(self.device)
        dones = torch.tensor([b.get("done", False) for b in batch], dtype=torch.float32).to(self.device)

        q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q

        loss = torch.nn.functional.mse_loss(q_values, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def update_target_net(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.logger.info("🔄 Target network updated.")

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)

    def save_model(self):
        torch.save(self.policy_net.state_dict(), self.model_path)
        self.logger.info("💾 Model saved.")
