import asyncio
import logging
from trainer import Trainer
from utils.redis_factory import RedisClientFactory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

async def main():
    redis_conn = RedisClientFactory().create()
    trainer = Trainer(redis_conn)

    asyncio.create_task(trainer.ingest_loop())
    step = 0

    while True:
        if len(trainer.buffer) < trainer.train_after:
            await asyncio.sleep(1)
            continue

        for _ in range(trainer.train_steps):
            batch = trainer.sample_batch()
            loss = trainer.train_step(batch)
            trainer.logger.info(f"🧠 Step {step} | Loss={loss:.4f} | Epsilon={trainer.epsilon:.3f}")
            step += 1

        trainer.update_target_net()
        trainer.save_model()
        trainer.decay_epsilon()
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
