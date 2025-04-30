import pandas as pd
from core.indicators.base_indicator import BaseIndicator
from core.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/indicators/rsi.yaml")
class RSIIndicator(BaseIndicator):
    def compute(self, ticks):
        prices = [tick["price"] for tick in ticks]
        series = pd.Series(prices)
        delta = series.diff()

        gain = delta.clip(lower=0).rolling(window=self.window).mean()
        loss = -delta.clip(upper=0).rolling(window=self.window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return {"rsi": rsi.iloc[-1]}
