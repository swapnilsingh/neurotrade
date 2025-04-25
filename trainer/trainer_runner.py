import asyncio
import os
import redis.asyncio as aioredis
import json
from trainer_class import DQNTrainer
from rl_agent.models.state import State
from rl_agent.models.experience import Experience
from utils.system_config import load_system_config

config = load_system_config()
redis_cfg = config["redis"]
REDIS_HOST = redis_cfg["host"]
REDIS_PORT = redis_cfg.get("port", 6379)
EXPERIENCE_KEY = "experience_queue"

INPUT_DIM = 9
OUTPUT_DIM = 3

async def run_trainer():
    redis_conn = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    trainer = DQNTrainer(input_dim=INPUT_DIM, output_dim=OUTPUT_DIM)

    print("📡 Trainer connected to Redis. Listening for experiences...")

    while True:
        raw = await redis_conn.lpop(EXPERIENCE_KEY)
        if raw:
            data = json.loads(raw)
            state = State(**data["state"])
            next_state = State(**data["next_state"])
            exp = Experience(state=state, action=data["action"], reward=data["reward"], next_state=next_state, done=data["done"])
            trainer.remember(exp)
            trainer.replay()
            trainer.save_model()
        else:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_trainer())
