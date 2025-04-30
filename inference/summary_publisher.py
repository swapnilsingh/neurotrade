# inference/summary_publisher.py

import json
import time
from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/summary_publisher.yaml")
class SummaryPublisher:
    def __init__(self, redis_conn, state_tracker, config=None):
        self.redis_conn = redis_conn
        self.state_tracker = state_tracker
        self.summary_key = self.config.get("keys", {}).get("summary", "trading:summary")
        self.publish_interval = self.config.get("publish_interval", 1)  # seconds
        self.last_publish_time = 0

    async def publish(self, current_price, timestamp):
        now = time.time()
        if now - self.last_publish_time < self.publish_interval:
            return

        cash = self.state_tracker.get_cash()
        inventory = self.state_tracker.get_inventory()
        portfolio_value = cash + (inventory * current_price)
        net_profit = portfolio_value - self.state_tracker.initial_cash
        return_pct = (net_profit / self.state_tracker.initial_cash) * 100

        summary = {
            "timestamp": timestamp,
            "cash": cash,
            "inventory_btc": inventory,
            "btc_price": current_price,
            "portfolio_value": portfolio_value,
            "net_profit": net_profit,
            "return_pct": return_pct
        }

        await self.redis_conn.set(self.summary_key, json.dumps(summary))
        self.last_publish_time = now
        self.logger.debug(f"[Summary] Published: {summary}")
