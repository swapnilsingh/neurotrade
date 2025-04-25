import asyncio
import json
import websockets
import redis.asyncio as aioredis
from datetime import datetime, timedelta
import os

from rl_agent.ensemble_agent import EnsembleAgent
from feature_builder.builder import build_state
from feature_builder.strategy_loader import load_strategy_config
from utils.trade_logger import log_trade
from utils.reward import compute_reward  # 💡 Import reward engine
from utils.system_config import load_system_config

config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])
OHLCV_KEY = config["keys"]["ohlcv"]
SIGNAL_KEY = config["keys"]["signal"]
EXPERIENCE_KEY = config["keys"]["experience"]
CANDLE_INTERVAL = config["interval"]
MAX_CANDLES = config["max_candles"]
SYMBOL = config.get("symbol", "btcusdt")
WS_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@trade"


class CandleAggregator:
    def __init__(self, interval_seconds):
        self.interval = timedelta(seconds=interval_seconds)
        self.current_candle = None
        self.candles = []

    def add_tick(self, price, volume, timestamp):
        ts = datetime.utcfromtimestamp(timestamp / 1000)
        candle_start = ts - timedelta(seconds=ts.second % self.interval.seconds, microseconds=ts.microsecond)

        if not self.current_candle or candle_start > self.current_candle['timestamp']:
            if self.current_candle:
                self.current_candle['timestamp'] = int(self.current_candle['timestamp'].timestamp() * 1000)
                self.candles.append(self.current_candle)
            self.current_candle = {
                'timestamp': candle_start,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume,
            }
        else:
            self.current_candle['high'] = max(self.current_candle['high'], price)
            self.current_candle['low'] = min(self.current_candle['low'], price)
            self.current_candle['close'] = price
            self.current_candle['volume'] += volume

        if len(self.candles) > MAX_CANDLES:
            self.candles = self.candles[-MAX_CANDLES:]

    def get_closed_candle(self):
        if self.candles:
            return self.candles.pop(0)
        return None

async def run_inference():
    redis_conn = aioredis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    strategy_config = load_strategy_config("configs/strategy.yaml")
    reward_strategy = strategy_config.get("reward_strategy", "basic")  # 🔁 Dynamic reward strategy

    agent = EnsembleAgent()
    aggregator = CandleAggregator(CANDLE_INTERVAL)

    async with websockets.connect(WS_URL) as ws:
        print(f"✅ Connected to Binance WebSocket for {SYMBOL}")
        async for message in ws:
            data = json.loads(message)
            price = float(data["p"])
            qty = float(data["q"])
            timestamp = data["T"]

            aggregator.add_tick(price, qty, timestamp)
            candle = aggregator.get_closed_candle()

            if candle:
                # Save candle to Redis
                await redis_conn.rpush(OHLCV_KEY, json.dumps(candle))
                await redis_conn.ltrim(OHLCV_KEY, -MAX_CANDLES, -1)

                # Build state and vote
                state = build_state(candle, strategy_config)
                signal, votes = agent.vote(state)

                # Log trade info
                trade = {
                    "timestamp": candle["timestamp"],
                    "symbol": SYMBOL.upper(),
                    "signal": signal,
                    "equity": 1000.0,
                    "reason": f"majority vote={signal}",
                    "votes": votes,
                    "indicators": state.model_dump(),
                    "strategy_config": strategy_config,
                    "model_version": "v1"
                }
                log_trade(SYMBOL, trade)

                # Push trade to Redis for Streamlit
                await redis_conn.rpush(SIGNAL_KEY, json.dumps(trade))
                await redis_conn.ltrim(SIGNAL_KEY, -MAX_CANDLES, -1)

                # ➕ Compute reward using modular strategy engine
                reward = compute_reward(candle, signal, strategy=reward_strategy)

                # Push experience for trainer
                experience = {
                    "state": state.model_dump(),
                    "action": signal,
                    "reward": reward,
                    "next_state": state.model_dump(),
                    "done": False
                }
                await redis_conn.rpush(EXPERIENCE_KEY, json.dumps(experience))

                print(f"[Signal] {trade['timestamp']} {signal} | Votes: {votes} | Reward ({reward_strategy}): {reward:.4f}")

if __name__ == "__main__":
    asyncio.run(run_inference())
