import os
import redis.asyncio as aioredis
from utils.config_loader import load_config

class RedisClient:
    def __init__(self, config=None):
        self.config = config or load_config("configs/redis.yaml")
        self.host = os.getenv("REDIS_HOST", self.config.get("host", "localhost"))
        self.port = self.config.get("port", 6379)

    def connect(self):
        return aioredis.Redis(host=self.host, port=self.port, decode_responses=True)
