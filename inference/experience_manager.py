# inference/experience_manager.py

import json
from core.decorators.decorators import inject_logger, inject_config
from utils.trade_logger import log_trade

@inject_logger()
@inject_config("configs/experience_manager.yaml")
class ExperienceManager:
    def __init__(self, redis_conn):
        self.redis_conn = redis_conn
        self.model_version = self.config.get("model_version", "v1")
        self.max_signal_history = self.config.get("max_signal_history", 1000)

        keys = self.config.get("keys", {})
        symbol = self.config.get("symbol", "btcusdt").upper()
        self.experience_key = keys.get("experience", "experience_queue")
        self.signal_key = keys.get("signal", "signal_history:{symbol}").replace("{symbol}", symbol)

    async def push(self, state, future_state, qty, signal, reward,
                   ts, reason, tp_pct, suggestion, price):
        experience = {
            "state": list(state.values()),
            "action": {"BUY": 1, "SELL": -1, "HOLD": 0}.get(signal, 0),
            "reward": reward,
            "next_state": list(future_state.values()),
            "done": False
        }

        await self.redis_conn.rpush(self.experience_key, json.dumps(experience))

        trade = {
            "timestamp": int(ts),
            "signal": signal,
            "price": price,
            "quantity": qty,
            "reason": reason,
            "model_version": self.model_version,
            "take_profit_pct": tp_pct,
            "suggestion": suggestion,
            "indicators": state
        }

        log_trade("BTCUSDT", trade)
        await self.redis_conn.rpush(self.signal_key, json.dumps(trade))
        await self.redis_conn.ltrim(self.signal_key, -self.max_signal_history, -1)
        self.logger.debug(f"[Experience] Logged {signal} | Reward={reward:.4f}")
