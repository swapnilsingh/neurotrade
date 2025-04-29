import asyncio
import json
import os
import random
import time
import torch
import redis.asyncio as aioredis
import numpy as np

from rl_agent.dqn_agent import DQNAgent
from utils.system_config import load_system_config

# Load configuration
config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
REDIS_PORT = config["redis"]["port"]
EXPERIENCE_KEY = config["keys"]["experience"]

# Training Hyperparameters
BATCH_SIZE = 64
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_MIN = 0.05
EPSILON_DECAY = 0.995
TRAIN_AFTER_EXPERIENCES = 500
TARGET_UPDATE_INTERVAL = 500
MODEL_SAVE_INTERVAL = 500
MODEL_PATH = "/app/models/model.pt"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class ReplayBuffer:
    def __init__(self):
        self.buffer = []

    def add(self, experience):
        self.buffer.append(experience)

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)

async def run_trainer():
    redis_conn = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    replay_buffer = ReplayBuffer()

    dqn_agent = None
    epsilon = EPSILON_START
    training_step = 0

    print("✅ Trainer started. Waiting for experiences...")

    while True:
        await asyncio.sleep(0.5)

        # Fetch new experience from Redis
        experience_raw = await redis_conn.lpop(EXPERIENCE_KEY)
        if experience_raw is None:
            continue

        try:
            experience = json.loads(experience_raw)
            state = experience["state"]
            action = experience["action"]
            reward = experience["reward"]
            next_state = experience["next_state"]
            done = experience.get("done", False)
        except Exception as e:
            print(f"⚠️ Invalid experience format. Skipping. Error: {e}")
            continue

        replay_buffer.add((state, action, reward, next_state, done))

        # Initialize DQNAgent if not initialized
        if dqn_agent is None and len(state) > 0:
            dqn_agent = DQNAgent(input_dim=len(state), device=device, model_path=MODEL_PATH)
            print(f"✅ DQNAgent initialized with input_dim = {len(state)}")

        if dqn_agent is None or len(replay_buffer) < TRAIN_AFTER_EXPERIENCES:
            continue

        batch = replay_buffer.sample(BATCH_SIZE)

        loss = dqn_agent.train(batch, gamma=GAMMA)
        training_step += 1

        print(f"📚 Training Step {training_step} | Loss: {loss:.5f} | Epsilon: {epsilon:.4f}")

        # Update epsilon (exploration decay)
        epsilon = max(EPSILON_MIN, epsilon * EPSILON_DECAY)
        dqn_agent.epsilon = epsilon

        # Periodically update target network
        if training_step % TARGET_UPDATE_INTERVAL == 0:
            dqn_agent.update_target_network()
            print("🔄 Target network updated.")

        # Periodically save model
        if training_step % MODEL_SAVE_INTERVAL == 0:
            dqn_agent.save_model(MODEL_PATH)
            print(f"💾 Model saved at step {training_step}")

if __name__ == "__main__":
    asyncio.run(run_trainer())
