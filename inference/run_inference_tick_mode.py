import asyncio
import json
import os
import websockets
import redis.asyncio as aioredis
from datetime import datetime
import numpy as np
import time

from rl_agent.dynamic_tick_essemble_agent import DynamicTickEnsembleAgent as EnsembleAgent
from feature_builder.builder import build_state_from_ticks
from feature_builder.strategy_loader import load_strategy_config
from utils.trade_logger import log_trade
from utils.reward import compute_reward_from_ticks
from utils.system_config import load_system_config
from tick_stream_listener import TickStreamListener
from cooldown_manager import CooldownManager

config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
REDIS_PORT = config["redis"]["port"]

symbol = config.get("symbol", "btcusdt").lower()
interval = config.get("interval", 3)
MAX_CANDLES = config.get("max_candles", 500)
CANDLE_INTERVAL = config["interval"]
OHLCV_KEY = config["keys"]["ohlcv"].replace("{symbol}", symbol).replace("{interval}", str(interval))
SIGNAL_KEY = config["keys"]["signal"].replace("{symbol}", symbol).replace("{interval}", str(interval))
EXPERIENCE_KEY = config["keys"]["experience"]
SYMBOL = symbol
WS_URL = f"wss://stream.binance.com:9443/ws/{symbol}@trade"

MODEL_PATH = "/app/models/model.pt"
MODEL_CHECK_INTERVAL = 300  # 5 minutes

INITIAL_EQUITY = 1000.0
TRADE_FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
BASE_TRADE_QUANTITY = 0.001
MAX_TRADE_QUANTITY = 0.01

async def run_inference():
    redis_conn = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    agent = EnsembleAgent(window_size=5, volatility_multiplier=1.0)
    cooldown_manager = CooldownManager(enabled=True, cooldown_seconds=3)
    tick_listener = TickStreamListener(symbol=SYMBOL, max_ticks=100)

    # Track model modification time
    last_model_mtime = os.path.getmtime(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
    last_model_check_time = time.time()

    asyncio.create_task(tick_listener.connect())

    cash = INITIAL_EQUITY
    inventory = 0.0
    position = None
    entry_price = 0.0

    while True:
        await asyncio.sleep(0.5)
        ticks = tick_listener.get_recent_ticks()

        # 🔥 Model Hot Reload Check
        current_time = time.time()
        if current_time - last_model_check_time >= MODEL_CHECK_INTERVAL:
            if os.path.exists(MODEL_PATH):
                current_mtime = os.path.getmtime(MODEL_PATH)
                if last_model_mtime is None or current_mtime != last_model_mtime:
                    print(f"♻️ [Inference] New model detected. Reloading model...")
                    agent.load_model(MODEL_PATH)
                    last_model_mtime = current_mtime
            last_model_check_time = current_time

        if len(ticks) < 10:
            continue

        current_price = ticks[-1]["price"]
        current_timestamp = ticks[-1]["timestamp"]

        state = build_state_from_ticks(
            ticks=ticks,
            current_price=current_price,
            entry_price=entry_price,
            position=position
        )

        signal, votes = agent.vote(state)

        buy_votes = votes.count('BUY')
        sell_votes = votes.count('SELL')
        total_votes = len(votes)

        confidence = max(buy_votes, sell_votes) / total_votes if total_votes > 0 else 0
        dynamic_quantity = BASE_TRADE_QUANTITY * (1 + confidence)
        dynamic_quantity = min(dynamic_quantity, MAX_TRADE_QUANTITY)

        if not cooldown_manager.can_trade(current_timestamp):
            signal = "HOLD"

        reason = "HOLD (no action)"

        if signal == "BUY":
            cost = current_price * dynamic_quantity * (1 + SLIPPAGE_RATE)
            fee = cost * TRADE_FEE_RATE
            total_cost = cost + fee

            if cash >= total_cost:
                inventory += dynamic_quantity
                cash -= total_cost
                entry_price = current_price * (1 + SLIPPAGE_RATE)
                position = "LONG"
                reason = f"Bought {dynamic_quantity:.6f} BTC at {current_price:.2f} | Cost: {total_cost:.2f}"
            else:
                signal = "HOLD"
                reason = "HOLD: Not enough cash to BUY"

        elif signal == "SELL":
            revenue = current_price * dynamic_quantity * (1 - SLIPPAGE_RATE)
            fee = revenue * TRADE_FEE_RATE
            net_revenue = revenue - fee

            if inventory >= dynamic_quantity:
                inventory -= dynamic_quantity
                cash += net_revenue
                position = None
                entry_price = 0.0
                reason = f"Sold {dynamic_quantity:.6f} BTC at {current_price:.2f} | Revenue: {net_revenue:.2f}"
            else:
                signal = "HOLD"
                reason = "HOLD: Not enough inventory to SELL"

        equity = cash + inventory * current_price

        trade = {
            "timestamp": current_timestamp,
            "symbol": SYMBOL.upper(),
            "signal": signal,
            "equity": equity,
            "reason": reason,
            "votes": votes,
            "indicators": state,
            "model_version": "v1",
            "forced": agent.last_action_forced,
            "quantity": dynamic_quantity
        }

        log_trade(SYMBOL, trade)
        await redis_conn.rpush(SIGNAL_KEY, json.dumps(trade))
        await redis_conn.ltrim(SIGNAL_KEY, -MAX_CANDLES, -1)

        reward = compute_reward_from_ticks(
            ticks,
            signal,
            quantity=dynamic_quantity,
            current_price=current_price,
            entry_price=entry_price,
            position=position
        )

        signal_to_action_value = {"BUY": 1, "SELL": -1, "HOLD": 0}
        mapped_action = signal_to_action_value.get(signal, 0)

        future_ticks = tick_listener.get_recent_ticks()[-15:]

        future_state = build_state_from_ticks(
            ticks=future_ticks,
            current_price=current_price,
            entry_price=entry_price,
            position=position
        )

        experience = {
            "state": list(state.values()),
            "action": mapped_action,
            "reward": reward,
            "next_state": list(future_state.values()),
            "done": False
        }

        await redis_conn.rpush(EXPERIENCE_KEY, json.dumps(experience))

        print(f"[Signal] {current_timestamp} {signal} | {reason} | Equity: {equity:.2f} | Reward: {reward:.4f}")

if __name__ == "__main__":
    asyncio.run(run_inference())
