import redis.asyncio as aioredis
from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/redis.yaml")
class RedisClientFactory:
    def __init__(self):
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 6379)
        self.decode_responses = self.config.get("decode_responses", True)

        self.logger.debug(f"🔌 Connecting to Redis at {self.host}:{self.port} (decode_responses={self.decode_responses})")

    def create(self):
        return aioredis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=self.decode_responses
        )
