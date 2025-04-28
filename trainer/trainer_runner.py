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

# 📋 Load config
config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
EXPERIENCE_KEY = config["keys"]["experience"]

# ⚙️ Hyperparameters
BATCH_SIZE = 32
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_MIN = 0.05
EPSILON_DECAY = 0.995
TRAIN_AFTER_EXPERIENCES = 500
MINI_BATCH_SIZE = 64
MINI_BATCH_TRAIN_STEPS = 3
MODEL_SAVE_INTERVAL = 500

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

    await redis_conn.delete(EXPERIENCE_KEY)
    print(f"🧹 Cleared old experiences in {EXPERIENCE_KEY} before starting training.")

    if os.path.exists(MODEL_PATH):
        print(f"✅ [Trainer] model.pt found. Loading existing model...")
        agent = DQNAgent(input_dim=10, model_path=MODEL_PATH)
    else:
        print(f"⚠️ [Trainer] model.pt NOT found. Starting fresh model...")
        agent = DQNAgent(input_dim=10)

    replay_buffer = ReplayBuffer()

    print("✅ Trainer started. Waiting for experiences...")

    step = 0

    while True:
        experience_raw = await redis_conn.lpop(EXPERIENCE_KEY)

        if experience_raw:
            experience = json.loads(experience_raw)
            replay_buffer.add(experience)

            if len(replay_buffer) >= TRAIN_AFTER_EXPERIENCES:
                for _ in range(MINI_BATCH_TRAIN_STEPS):
                    raw_batch = replay_buffer.sample(MINI_BATCH_SIZE)

                    processed_batch = []
                    for exp in raw_batch:
                        state = np.array(exp["state"], dtype=np.float32)
                        next_state = np.array(exp["next_state"], dtype=np.float32)

                        # ✅ Safe-padding if shape mismatch
                        if state.shape[-1] < agent.input_dim:
                            pad_size = agent.input_dim - state.shape[-1]
                            state = np.pad(state, (0, pad_size))
                        if next_state.shape[-1] < agent.input_dim:
                            pad_size = agent.input_dim - next_state.shape[-1]
                            next_state = np.pad(next_state, (0, pad_size))

                        processed_batch.append((
                            state,
                            exp["action"],
                            exp["reward"],
                            next_state,
                            exp["done"]
                        ))

                    loss = agent.train(processed_batch)

                    if agent.epsilon > EPSILON_MIN:
                        agent.epsilon *= EPSILON_DECAY

                    step += 1
                    print(f"📚 Training Step {step} | Loss: {loss:.5f} | Epsilon: {agent.epsilon:.5f}")

                    if step % MODEL_SAVE_INTERVAL == 0:
                        os.makedirs("/app/models", exist_ok=True)
                        agent.save_model(MODEL_PATH)
                        print(f"💾 Model checkpoint saved at step {step}")

        else:
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(run_trainer())
