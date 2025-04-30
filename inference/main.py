import asyncio
import json
import logging
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
from inference.summary_publisher import SummaryPublisher
from inference.state_tracker import StateTracker
from core.experience.experience_writer import ExperienceWriter
from utils.trade_logger import log_trade

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
        self.state_builder = StateBuilder(self.evaluator, self.state_tracker, self.tick_listener)
        self.trade_executor = TradeExecutor(self.state_tracker)
        self.reward_evaluator = RewardEvaluator(self.reward_agent, self.tick_listener, self.state_tracker)
        self.experience_writer = ExperienceWriter(self.redis_conn)
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

        await self.experience_writer.push(
            state=list(state.values()),
            next_state=list(future_state.values()),
            action={"BUY": 1, "SELL": -1, "HOLD": 0}.get(signal, 0),
            reward=reward,
            done=False,
            ts=ts,
            reason=reason
        )

        trade = {
            "timestamp": int(ts),
            "signal": signal,
            "price": current_price,
            "quantity": qty,
            "reason": reason,
            "model_version": self.experience_writer.model_version,
            "take_profit_pct": tp_pct,
            "suggestion": suggestion,
            "indicators": state
        }

        log_trade("BTCUSDT", trade)
        await self.redis_conn.rpush(self.experience_writer.signal_key, json.dumps(trade))
        await self.redis_conn.ltrim(self.experience_writer.signal_key, -self.experience_writer.max_signal_history, -1)

        await self.summary_publisher.publish(current_price, ts)

if __name__ == "__main__":
    asyncio.run(InferenceRunner().run())
