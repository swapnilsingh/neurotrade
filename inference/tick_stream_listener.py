import asyncio
import websockets
import json
from collections import deque

class TickStreamListener:
    def __init__(self, symbol="btcusdt", max_ticks=100):
        self.symbol = symbol.lower()
        self.max_ticks = max_ticks
        self.ticks = deque(maxlen=max_ticks)
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@trade"

    async def connect(self):
        async with websockets.connect(self.ws_url) as ws:
            print(f"✅ Connected to Binance Trade Stream for {self.symbol.upper()}")
            async for message in ws:
                data = json.loads(message)
                tick = {
                    "price": float(data["p"]),
                    "qty": float(data["q"]),
                    "timestamp": int(data["T"])
                }
                self.ticks.append(tick)

    def get_recent_ticks(self):
        return list(self.ticks)