class PaperExecutor:
    def __init__(self):
        self.position = None
        self.equity = 1000.0
        self.last_price = 0

    def execute(self, price, signal):
        if signal == "BUY" and self.position is None:
            self.position = price
        elif signal == "SELL" and self.position:
            profit = price - self.position
            self.equity += profit
            self.position = None
        return self.equity

class BinanceExecutor:
    def __init__(self, api_key=None, api_secret=None):
        # placeholder for live execution
        self.api_key = api_key
        self.api_secret = api_secret

    def execute(self, symbol, signal):
        print(f"[LIVE MODE] Executing {signal} on {symbol}")
