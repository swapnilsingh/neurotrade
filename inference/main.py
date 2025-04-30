"""
main.py — Inference Orchestration Entry Point

This script is responsible for:
✅ Connecting to the live Binance WebSocket stream (via TickStreamListener)
✅ Building live market state from tick data (via StateBuilder)
✅ Delegating trading decisions to InferenceAgent (Q-network-based signal generator)
✅ Executing trades using TradeExecutor
✅ Evaluating trade outcomes via RewardAgent and RewardEvaluator
✅ Logging trades to Redis and maintaining performance summary (via SummaryPublisher)
✅ Managing trade cooldowns and retry intervals

All internal logic is modular and driven by configuration:
- Model loading, input preprocessing, and action decoding are handled by InferenceAgent
- Configs are injected via @inject_config decorators
- Logs are tagged via @inject_logger decorators
"""

import asyncio
from core.decorators.decorators import inject_logger
from utils.redis_factory import RedisClientFactory
from inference.inference_agent import InferenceAgent
from inference.reward_evaluator import RewardEvaluator
from inference.reward_agent import RewardAgent
from inference.evaluator_agent import EvaluatorAgent
from inference.tick_stream_listener import TickStreamListener
from inference.cooldown_manager import CooldownManager
from inference.tick_processor import TickProcessor
from inference.state_builder import StateBuilder
from inference.trade_executor import TradeExecutor
from inference.experience_manager import ExperienceManager
from inference.summary_publisher import SummaryPublisher
from inference.state_tracker import StateTracker
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)


@inject_logger()
class InferenceRunner:
    def __init__(self):
        self.symbol = "btcusdt"
        self.redis_conn = RedisClientFactory().create()

        self.evaluator = EvaluatorAgent()
        self.reward_agent = RewardAgent(self.evaluator)
        self.inference_agent = InferenceAgent()
        self.tick_listener = TickStreamListener()
        self.cooldown_manager = CooldownManager()
        self.state_tracker = StateTracker()
        self.tick_processor = TickProcessor(self.tick_listener)
        self.state_builder = StateBuilder(self.evaluator, self.state_tracker,self.tick_listener)
        self.trade_executor = TradeExecutor(self.state_tracker)
        self.reward_evaluator = RewardEvaluator(self.reward_agent, self.tick_listener, self.state_tracker)
        self.experience_manager = ExperienceManager(self.redis_conn)
        self.summary_publisher = SummaryPublisher(self.redis_conn, self.state_tracker)

        self.logger.info(f"✅ InferenceRunner initialized for {self.symbol.upper()}")

    async def run(self):
        self.logger.info("🚀 Starting inference loop...")
        asyncio.create_task(self.tick_listener.connect())

        try:
            while True:
                await asyncio.sleep(0.5)
                await self.run_tick_cycle()
        except (asyncio.CancelledError, KeyboardInterrupt):
            self.logger.info("🛑 Inference stopped gracefully.")

    async def run_tick_cycle(self):
        if not self.tick_processor.has_enough_ticks():
            return

        self.inference_agent.auto_refresh_model()

        state, current_price, ts = self.state_builder.build()
        signal, votes, qty, tp_pct, suggestion = self.inference_agent.vote(state)

        self.logger.info(f"🧠 Signal: {signal} | Price: {current_price:.2f} | Reason: {suggestion}")

        if self.cooldown_manager.enabled and not self.cooldown_manager.can_trade(ts):
            self.logger.debug("⏳ Cooldown active. Overriding signal to HOLD.")
            signal = "HOLD"

        reason = self.trade_executor.execute(signal, current_price, qty)
        reward = self.reward_evaluator.compute(current_price, signal, qty)
        future_state = self.state_builder.build_future()

        await self.experience_manager.push(
            state, future_state, qty, signal, reward,
            ts, reason, tp_pct, suggestion, current_price
        )

        await self.summary_publisher.publish(current_price, ts)


if __name__ == "__main__":
    asyncio.run(InferenceRunner().run())
