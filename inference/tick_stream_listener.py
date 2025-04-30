import asyncio
import websockets
import json
from collections import deque
from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/tick_stream_listener.yaml")
class TickStreamListener:
    def __init__(self):
        self.symbol = self.config.get("symbol", "btcusdt").lower()
        self.max_ticks = self.config.get("max_ticks", 100)
        self.base_url = self.config.get("websocket_base_url", "wss://stream.binance.com:9443/ws")
        self.ws_url = f"{self.base_url}/{self.symbol}@trade"
        self.ticks = deque(maxlen=self.max_ticks)
        self._connected = False

    async def connect(self):
        try:
            self.logger.info(f"Connecting to WebSocket: {self.ws_url}")
            async with websockets.connect(self.ws_url) as ws:
                self._connected = True
                self.logger.info(f"✅ Connected to Binance stream for {self.symbol.upper()}")
                async for message in ws:
                    data = json.loads(message)
                    tick = {
                        "price": float(data["p"]),
                        "qty": float(data["q"]),
                        "timestamp": int(data["T"])
                    }
                    self.ticks.append(tick)
        except Exception as e:
            self.logger.exception(f"WebSocket connection failed: {e}")
        finally:
            self._connected = False
            self.logger.warning("🔌 WebSocket connection closed.")

    def get_recent_ticks(self):
        return list(self.ticks)

    def is_connected(self):
        return self._connected
