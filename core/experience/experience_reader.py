import json
import asyncio
from collections import deque
from core.experience.base_experience import BaseExperience

class ExperienceReader(BaseExperience):
    def __init__(self, redis_conn, maxlen=10000):
        super().__init__()
        self.redis = redis_conn
        self.buffer = deque(maxlen=maxlen)

    async def ingest(self):
        while True:
            raw = await self.redis.lpop(self.experience_key)
            if raw:
                try:
                    experience = json.loads(raw)
                    self.buffer.append(experience)
                except Exception as e:
                    self.logger.warning(f"❌ Failed to parse experience: {e}")
            else:
                await asyncio.sleep(0.05)

    def sample(self, batch_size):
        import random
        return random.sample(self.buffer, min(len(self.buffer), batch_size))
