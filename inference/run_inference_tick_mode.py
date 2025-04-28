import asyncio
import json
import os
import redis.asyncio as aioredis
import numpy as np
import time
import logging
from datetime import datetime

from rl_agent.dynamic_tick_essemble_agent import DynamicTickEnsembleAgent as EnsembleAgent
from feature_builder.builder import build_state_from_ticks
from utils.system_config import load_system_config
from utils.trade_logger import log_trade
from utils.reward import compute_dynamic_reward
from tick_stream_listener import TickStreamListener
from cooldown_manager import CooldownManager

# 🧠 Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("inference")

# 📋 Load configuration
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

        self.INITIAL_CASH = 1000.0
        self.TRADE_FEE_RATE = 0.001
        self.SLIPPAGE_RATE = 0.0005

        self.MODEL_REFRESH_INTERVAL = 300  # seconds

    async def run(self):
        self.redis_conn = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.agent = EnsembleAgent(window_size=5)
        self.cooldown_manager = CooldownManager(enabled=True, cooldown_seconds=3)
        self.tick_listener = TickStreamListener(symbol=self.symbol, max_ticks=100)

        logger.info(f"✅ Inference started for symbol: {self.symbol.upper()}")
        asyncio.create_task(self.tick_listener.connect())

        self.cash = self.INITIAL_CASH
        self.inventory = 0.0
        self.entry_price = 0.0
        self.realized_profit = 0.0
        self.signal_counter = 0
        self.last_model_refresh_time = time.time()

        self.high_watermark = self.INITIAL_CASH
        self.previous_portfolio_value = self.INITIAL_CASH

        try:
            while True:
                await asyncio.sleep(0.5)
                ticks = self.tick_listener.get_recent_ticks()

                await self._refresh_agent_if_needed()

                if len(ticks) < 10:
                    continue

                tick = ticks[-1]
                current_price, current_timestamp = self._extract_tick_info(tick)
                if current_price is None:
                    continue

                # Build state
                state = build_state_from_ticks(
                    ticks=ticks,
                    current_price=current_price,
                    entry_price=self.entry_price,
                    position="LONG" if self.inventory > 0 else None,
                    drawdown_pct=(self.cash - self.INITIAL_CASH) / self.INITIAL_CASH
                )

                # 🚀 Full decision making
                signal, votes, dynamic_quantity, take_profit_pct, suggestion = self.agent.vote(state)

                logger.debug(f"🧠 Decision | Signal: {signal} | Quantity: {dynamic_quantity:.6f} | TP: {take_profit_pct*100:.2f}% | Suggestion: {suggestion}")

                if not self.cooldown_manager.can_trade(current_timestamp):
                    logger.debug(f"⏳ Cooldown active. Overriding signal to HOLD.")
                    signal = "HOLD"

                reason = self._process_trade(signal, current_price, dynamic_quantity, take_profit_pct)

                logger.debug(f"🛒 Trade Action: {reason}")

                # ✨ Updated Reward Calculation
                reward = self._compute_reward(current_price)

                future_ticks = self.tick_listener.get_recent_ticks()[-15:]
                future_state = build_state_from_ticks(
                    ticks=future_ticks,
                    current_price=current_price,
                    entry_price=self.entry_price,
                    position="LONG" if self.inventory > 0 else None,
                    drawdown_pct=(self.cash - self.INITIAL_CASH) / self.INITIAL_CASH
                )

                experience = self._build_experience(state, future_state, dynamic_quantity, signal, reward)
                await self._push_experience(experience, current_timestamp, signal, reason, dynamic_quantity, state, take_profit_pct, suggestion)

                await self._push_summary(current_price, current_timestamp)

                if self.signal_counter % 20 == 0:
                    logger.info(f"[Summary] Ticks: {self.signal_counter} | Cash: {self.cash:.2f} | Inventory: {self.inventory:.6f} | Realized PnL: {self.realized_profit:.2f}")

                self.signal_counter += 1

        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info("🛑 Inference stopped gracefully.")

    async def _refresh_agent_if_needed(self):
        current_time = time.time()
        if current_time - self.last_model_refresh_time >= self.MODEL_REFRESH_INTERVAL:
            logger.info(f"♻️ Refreshing agent at {datetime.utcnow()}")
            self.agent = EnsembleAgent(window_size=5)
            self.last_model_refresh_time = current_time

    def _extract_tick_info(self, tick):
        price = tick.get("price")
        ts = tick.get("timestamp", time.time())
        ts = ts / 1000 if ts > 32503680000 else ts
        return price, ts

    def _process_trade(self, signal, current_price, dynamic_quantity, take_profit_pct):
        reason = "HOLD (no action)"
        if signal == "HOLD" or dynamic_quantity <= 0:
            return reason

        fee_multiplier = 1.0

        if signal == "BUY":
            cost = current_price * dynamic_quantity * (1 + self.SLIPPAGE_RATE * fee_multiplier)
            fee = cost * self.TRADE_FEE_RATE * fee_multiplier
            total_cost = cost + fee

            if self.cash >= total_cost:
                self.inventory += dynamic_quantity
                self.cash -= total_cost
                self.entry_price = current_price
                reason = f"Bought {dynamic_quantity:.6f} BTC at {current_price:.2f} | TP: {take_profit_pct*100:.2f}%"

        elif signal == "SELL" and self.inventory >= dynamic_quantity:
            gross_revenue = current_price * dynamic_quantity * (1 - self.SLIPPAGE_RATE * fee_multiplier)
            fee = gross_revenue * self.TRADE_FEE_RATE * fee_multiplier
            net_revenue = gross_revenue - fee

            self.inventory -= dynamic_quantity
            self.cash += net_revenue
            realized = net_revenue - (self.entry_price * dynamic_quantity)
            self.realized_profit += realized

            reason = f"Sold {dynamic_quantity:.6f} BTC at {current_price:.2f}"

        return reason

    def _compute_reward(self, current_price):
        portfolio_value = self.cash + (self.inventory * current_price)

        # Update high watermark
        if portfolio_value > self.high_watermark:
            self.high_watermark = portfolio_value

        reward = compute_dynamic_reward(
            previous_portfolio_value=self.previous_portfolio_value,
            current_portfolio_value=portfolio_value,
            high_watermark=self.high_watermark,
            cash_balance=self.cash
        )

        self.previous_portfolio_value = portfolio_value

        return reward

    def _build_experience(self, state, future_state, dynamic_quantity, signal, reward):
        action_map = {"BUY": 1, "SELL": -1, "HOLD": 0}
        action = action_map.get(signal, 0)
        return {
            "state": list(state.values()) + [dynamic_quantity],
            "action": action,
            "reward": reward,
            "next_state": list(future_state.values()) + [dynamic_quantity],
            "done": False
        }

    async def _push_experience(self, experience, timestamp, signal, reason, dynamic_quantity, state, take_profit_pct, suggestion):
        await self.redis_conn.rpush(EXPERIENCE_KEY, json.dumps(experience))

        trade_record = {
            "timestamp": timestamp,
            "symbol": self.symbol.upper(),
            "signal": signal,
            "cash": self.cash,
            "inventory": self.inventory,
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
