import asyncio
import json
import os
import redis.asyncio as aioredis
import numpy as np
import time
import logging
from datetime import datetime

from rl_agent.dynamic_tick_essemble_agent import DynamicTickEnsembleAgent
from feature_builder.builder import build_state_from_ticks
from utils.system_config import load_system_config
from utils.trade_logger import log_trade
from utils.state_normalizer import normalize_state
from rl_agent.models.state import State
from rl_agent.evaluator_agent import EvaluatorAgent
from rl_agent.reward_agent import RewardAgent
from cooldown_manager import CooldownManager
from tick_stream_listener import TickStreamListener

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("inference")

# Load configuration
config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
REDIS_PORT = config["redis"]["port"]
EXPERIENCE_KEY = config["keys"]["experience"]
SIGNAL_KEY = config["keys"]["signal"]
SUMMARY_KEY = "trading:summary"

class InferenceRunner:
    def __init__(self):
        self.symbol = config.get("symbol", "btcusdt").lower()
        self.interval = config.get("interval", 3)
        self.MAX_CANDLES = config.get("max_candles", 500)

        self.evaluator = EvaluatorAgent(short_window=10, long_window=100)
        self.reward_agent = RewardAgent(self.evaluator, use_dynamic_volatility=True)

        self.INITIAL_CASH = 500.0
        self.TRADE_FEE_RATE = 0.001
        self.SLIPPAGE_RATE = 0.0005

    async def run(self):
        self.redis_conn = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.dqn_agent = DynamicTickEnsembleAgent(window_size=5)
        self.cooldown_manager = CooldownManager(enabled=True, cooldown_seconds=2)
        self.tick_listener = TickStreamListener(symbol=self.symbol, max_ticks=100)

        self.cash = self.INITIAL_CASH
        self.inventory = 0.0
        self.entry_price = 0.0
        self.realized_profit = 0.0
        self.signal_counter = 0

        logger.info(f"✅ Inference started for {self.symbol.upper()}")
        asyncio.create_task(self.tick_listener.connect())

        try:
            while True:
                await asyncio.sleep(0.5)

                ticks = self.tick_listener.get_recent_ticks()
                if len(ticks) < 10:
                    continue

                current_price, current_timestamp = self._extract_tick_info(ticks[-1])
                if current_price is None:
                    continue

                raw_state = build_state_from_ticks(
                    ticks=ticks,
                    current_price=current_price,
                    entry_price=self.entry_price,
                    position="LONG" if self.inventory > 0 else None,
                    drawdown_pct=(self.cash - self.INITIAL_CASH) / self.INITIAL_CASH,
                    inventory=self.inventory,
                    cash_balance=self.cash,
                    evaluator_feedback=self.evaluator.generate_feedback(),
                    trade_duration_sec=10.0
                )
                normalized_state = normalize_state(raw_state)
                normalized_state["dynamic_quantity"] = 0.001

                signal, votes, dynamic_quantity, take_profit_pct, suggestion = self.dqn_agent.vote(normalized_state)
                logger.debug(f"🧠 DQN Signal: {signal} | Price: {current_price:.2f}")

                if not self.cooldown_manager.can_trade(current_timestamp):
                    logger.debug("⏳ Cooldown active. Overriding to HOLD.")
                    signal = "HOLD"

                reason = self._process_trade(signal, current_price, dynamic_quantity)
                reward = self._compute_reward(current_price, signal, dynamic_quantity)

                future_ticks = self.tick_listener.get_recent_ticks()[-15:]
                future_price = future_ticks[-1]["price"] if future_ticks else current_price

                future_raw = build_state_from_ticks(
                    ticks=future_ticks,
                    current_price=future_price,
                    entry_price=self.entry_price,
                    position="LONG" if self.inventory > 0 else None,
                    drawdown_pct=(self.cash - self.INITIAL_CASH) / self.INITIAL_CASH,
                    inventory=self.inventory,
                    cash_balance=self.cash,
                    evaluator_feedback=self.evaluator.generate_feedback(),
                    trade_duration_sec=10.0
                )
                future_state = normalize_state(future_raw)
                future_state["dynamic_quantity"] = 0.001

                experience = self._build_experience(normalized_state, future_state, dynamic_quantity, signal, reward)
                await self._push_experience(experience, current_timestamp, signal, reason, dynamic_quantity, normalized_state, take_profit_pct, suggestion, current_price)
                await self._push_summary(current_price, current_timestamp)

                if self.signal_counter % 20 == 0:
                    logger.info(f"[Summary] Ticks: {self.signal_counter} | Cash: {self.cash:.2f} | Inventory: {self.inventory:.6f} | RealizedPnL: {self.realized_profit:.2f}")
                self.signal_counter += 1

        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info("🛑 Inference stopped gracefully.")

    def _extract_tick_info(self, tick):
        price = tick.get("price")
        ts = tick.get("timestamp", time.time() * 1000)
        return price, ts

    def _process_trade(self, signal, current_price, dynamic_quantity):
        reason = "HOLD (no action)"
        if signal == "BUY":
            cost = current_price * dynamic_quantity * (1 + self.SLIPPAGE_RATE)
            total_cost = cost + cost * self.TRADE_FEE_RATE
            if self.cash >= total_cost:
                total_value = self.entry_price * self.inventory + current_price * dynamic_quantity
                self.inventory += dynamic_quantity
                self.entry_price = total_value / max(self.inventory, 1e-8)
                self.cash -= total_cost
                reason = f"Bought {dynamic_quantity:.6f} BTC at {current_price:.2f}"
            else:
                reason = "Skipped BUY - Insufficient Cash"
        elif signal == "SELL" and self.inventory > 0:
            sell_quantity = min(dynamic_quantity, self.inventory)
            gross_revenue = current_price * sell_quantity * (1 - self.SLIPPAGE_RATE)
            net_revenue = gross_revenue - gross_revenue * self.TRADE_FEE_RATE
            realized = (current_price - self.entry_price) * sell_quantity
            self.cash += net_revenue
            self.inventory -= sell_quantity
            self.realized_profit += realized
            if self.inventory == 0:
                self.entry_price = 0.0
            reason = f"Sold {sell_quantity:.6f} BTC at {current_price:.2f} | Realized {realized:.2f}"
        return reason

    def _compute_reward(self, current_price, signal, dynamic_quantity):
        future_ticks = self.tick_listener.get_recent_ticks()[-15:]
        inventory_value = self.inventory * current_price
        portfolio_value = self.cash + inventory_value
        inventory_ratio = inventory_value / (portfolio_value + 1e-8)
        shaped_reward, _ = self.reward_agent.compute(
            ticks=future_ticks,
            signal=signal,
            quantity=dynamic_quantity,
            current_price=current_price,
            entry_price=self.entry_price,
            position=self.inventory,
            inventory_ratio=inventory_ratio
        )
        return shaped_reward

    def _build_experience(self, state, future_state, dynamic_quantity, signal, reward):
        action_map = {"BUY": 1, "SELL": -1, "HOLD": 0}
        return {
            "state": list(state.values()),
            "action": action_map.get(signal, 0),
            "reward": reward,
            "next_state": list(future_state.values()),
            "done": False
        }

    async def _push_experience(self, experience, timestamp, signal, reason, dynamic_quantity, state, take_profit_pct, suggestion, current_price):
        await self.redis_conn.rpush(EXPERIENCE_KEY, json.dumps(experience))
        trade_record = {
            "timestamp": int(timestamp),
            "symbol": self.symbol.upper(),
            "signal": signal,
            "cash": self.cash,
            "inventory": self.inventory,
            "price": current_price,
            "reason": reason,
            "model_version": "v2",
            "quantity": dynamic_quantity,
            "take_profit_pct": take_profit_pct,
            "suggestion": suggestion,
            "indicators": state
        }
        log_trade(self.symbol, trade_record)
        await self.redis_conn.rpush(SIGNAL_KEY, json.dumps(trade_record))
        await self.redis_conn.ltrim(SIGNAL_KEY, -self.MAX_CANDLES, -1)

    async def _push_summary(self, current_price, timestamp):
        portfolio_value = self.cash + (self.inventory * current_price)
        net_profit = portfolio_value - self.INITIAL_CASH
        return_pct = (net_profit / self.INITIAL_CASH) * 100
        summary = {
            "timestamp": timestamp,
            "cash": self.cash,
            "inventory_btc": self.inventory,
            "btc_price": current_price,
            "portfolio_value": portfolio_value,
            "net_profit": self.realized_profit,
            "return_pct": return_pct
        }
        await self.redis_conn.set(SUMMARY_KEY, json.dumps(summary))

if __name__ == "__main__":
    runner = InferenceRunner()
    asyncio.run(runner.run())
