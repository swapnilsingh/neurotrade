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
from utils.reward import compute_reward
from utils.system_config import load_system_config

config = load_system_config()
REDIS_HOST = os.getenv("REDIS_HOST", config["redis"]["host"])

symbol = config.get("symbol", "btcusdt").lower()
interval = config.get("interval", 3)
MAX_CANDLES = config.get("max_candles", 500)
CANDLE_INTERVAL = config["interval"]
OHLCV_KEY = config["keys"]["ohlcv"].replace("{symbol}", symbol).replace("{interval}", str(interval))
SIGNAL_KEY = config["keys"]["signal"].replace("{symbol}", symbol).replace("{interval}", str(interval))
EXPERIENCE_KEY = config["keys"]["experience"]
SYMBOL = symbol
WS_URL = f"wss://stream.binance.com:9443/ws/{symbol}@trade"

# 📈 Virtual Wallet Parameters
INITIAL_EQUITY = 1000.0
TRADE_FEE_RATE = 0.001  # 0.1% fee
SLIPPAGE_RATE = 0.0005  # 0.05% slippage

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
    reward_strategy = strategy_config.get("reward_strategy", "basic")

    agent = EnsembleAgent()
    aggregator = CandleAggregator(CANDLE_INTERVAL)

    # 🏦 Virtual Wallet
    equity = INITIAL_EQUITY
    position = None
    entry_price = 0.0
    last_buy_timestamp = None  # ⏱️ Track when we last opened a position
    MIN_HOLD_SECONDS = 15  # ⏱️ Minimum seconds to hold before selling

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
                await redis_conn.rpush(OHLCV_KEY, json.dumps(candle))
                await redis_conn.ltrim(OHLCV_KEY, -MAX_CANDLES, -1)

                state = build_state(candle, strategy_config)
                signal, votes = agent.vote(state)

                # 🛡️ Enforce Cooldown Logic
                if position == "LONG" and last_buy_timestamp is not None:
                    hold_duration = (candle["timestamp"] - last_buy_timestamp) / 1000  # ms to seconds
                    if hold_duration < MIN_HOLD_SECONDS:
                        signal = "HOLD"

                reason = "HOLD (no action)"
                pnl = 0.0
                holding_duration_sec = 0

                if signal == "BUY" and position is None:
                    # 🛒 Open long
                    position = "LONG"
                    entry_price = price * (1 + SLIPPAGE_RATE)  # Slippage on buy
                    fee = equity * TRADE_FEE_RATE
                    equity -= fee
                    reason = f"Opened LONG at {entry_price:.2f} | Fee: {fee:.2f}"
                    last_buy_timestamp = candle["timestamp"]  # ⏱️ Mark buy time

                elif signal == "SELL" and position == "LONG":
                    # 💰 Close long
                    exit_price = price * (1 - SLIPPAGE_RATE)  # Slippage on sell
                    pnl = exit_price - entry_price
                    equity += pnl
                    fee = equity * TRADE_FEE_RATE
                    equity -= fee
                    reason = f"Closed LONG at {exit_price:.2f} | PnL: {pnl:.2f} | Fee: {fee:.2f}"

                    if last_buy_timestamp is not None:
                        holding_duration_sec = (candle["timestamp"] - last_buy_timestamp) / 1000

                    position = None
                    entry_price = 0.0
                    last_buy_timestamp = None  # ⏱️ Reset on sell

                # 🧠 Extend candle dict with trading meta-info
                candle["pnl"] = pnl
                candle["holding_duration_sec"] = holding_duration_sec

                trade = {
                    "timestamp": candle["timestamp"],
                    "symbol": SYMBOL.upper(),
                    "signal": signal,
                    "equity": equity,
                    "reason": reason,
                    "votes": votes,
                    "indicators": state.model_dump(),
                    "strategy_config": strategy_config,
                    "model_version": "v1",
                    "forced": agent.last_action_forced,
                    "pnl": pnl,
                    "holding_duration_sec": holding_duration_sec
                }
                log_trade(SYMBOL, trade)

                await redis_conn.rpush(SIGNAL_KEY, json.dumps(trade))
                await redis_conn.ltrim(SIGNAL_KEY, -MAX_CANDLES, -1)

                # 🧠 Now reward gets correct pnl and hold duration inside candle
                reward = compute_reward(candle, signal, strategy=reward_strategy)

                experience = {
                    "state": state.indicators_vector(),
                    "action": signal,
                    "reward": reward,
                    "next_state": state.indicators_vector(),
                    "done": False
                }
                await redis_conn.rpush(EXPERIENCE_KEY, json.dumps(experience))

                print(f"[Signal] {trade['timestamp']} {signal} | Reason: {reason} | Equity: {equity:.2f} | Reward: {reward:.4f}")

if __name__ == "__main__":
    asyncio.run(run_inference())
