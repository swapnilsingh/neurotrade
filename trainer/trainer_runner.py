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

# Load config
config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
EXPERIENCE_KEY = config["keys"]["experience"]

# Hyperparameters
BATCH_SIZE = 32
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_MIN = 0.05
EPSILON_DECAY = 0.995
TARGET_UPDATE_INTERVAL = 1000
MODEL_SAVE_INTERVAL = 500
REPLAY_BUFFER_CAPACITY = 10000

MODEL_PATH = "/app/models/model.pt"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class ReplayBuffer:
    def __init__(self):
        self.buffer = []

    def add(self, experience):
        self.buffer.append(experience)

    def sample(self, batch_size):
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[i] for i in indices]
        return batch

    def __len__(self):
        return len(self.buffer)

async def run_trainer():
    redis_conn = aioredis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

    agent = None

    # 🛡️ Check if model.pt exists
    if os.path.exists(MODEL_PATH):
        print(f"✅ [Trainer] model.pt found. Initializing Trainer from saved model...")
        agent = DQNAgent(input_dim=6, model_path=MODEL_PATH)
    else:
        print(f"⚠️ [Trainer] model.pt NOT found. Starting Trainer with fresh model...")
        agent = DQNAgent(input_dim=6)  # Start from scratch without loading

    replay_buffer = ReplayBuffer()

    TRAIN_AFTER_EXPERIENCES = 500
    MINI_BATCH_SIZE = 64
    MINI_BATCH_TRAIN_STEPS = 3

    print("✅ Trainer started. Waiting for experiences...")

    step = 0  # Training step counter

    while True:
        experience_raw = await redis_conn.lpop(EXPERIENCE_KEY)

        if experience_raw:
            experience = json.loads(experience_raw)
            replay_buffer.add(experience)

            if len(replay_buffer) >= TRAIN_AFTER_EXPERIENCES:
                for _ in range(MINI_BATCH_TRAIN_STEPS):
                    raw_batch = replay_buffer.sample(batch_size=MINI_BATCH_SIZE)

                    processed_batch = []
                    for exp in raw_batch:
                        state = np.array(exp["state"])
                        next_state = np.array(exp["next_state"])
                        quantity = exp.get("quantity", 0.001)

                        augmented_state = np.append(state, quantity)
                        augmented_next_state = np.append(next_state, quantity)

                        processed_batch.append((
                            augmented_state,
                            exp["action"],
                            exp["reward"],
                            augmented_next_state,
                            exp["done"]
                        ))

                    loss = agent.train(processed_batch)

                    # ✅ Apply epsilon decay
                    if agent.epsilon > agent.epsilon_min:
                        agent.epsilon *= agent.epsilon_decay

                    step += 1
                    print(f"📚 Training step {step} | Loss: {loss:.4f} | Epsilon: {agent.epsilon:.4f}")

                    # 💾 Save model every MODEL_SAVE_INTERVAL steps
                    if step % MODEL_SAVE_INTERVAL == 0:
                        os.makedirs("/app/models", exist_ok=True)  # Ensure folder exists
                        agent.save_model(MODEL_PATH)
                        print(f"💾 Saved model checkpoint at step {step}")

        else:
            await asyncio.sleep(0.1)  # No experiences yet, wait

if __name__ == "__main__":
    asyncio.run(run_trainer())
