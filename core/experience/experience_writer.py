import json
from core.experience.base_experience import BaseExperience

class ExperienceWriter(BaseExperience):
    def __init__(self, redis_conn):
        super().__init__()
        self.redis = redis_conn

    async def push(self, state, next_state, action, reward, done, ts, reason, model_version=None):
        experience = {
            "state": state,
            "next_state": next_state,
            "action": action,
            "reward": reward,
            "done": done,
            "timestamp": ts,
            "reason": reason,
            "model_version": model_version or self.model_version
        }

        try:
            await self.redis.rpush(self.experience_key, json.dumps(experience))
            self.logger.info(f"📝 Experience pushed at {ts}")
        except Exception as e:
            self.logger.error(f"❌ Failed to push experience: {e}")
