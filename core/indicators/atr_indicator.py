import pandas as pd
from core.indicators.base_indicator import BaseIndicator
from core.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/indicators/atr.yaml")
class ATRIndicator(BaseIndicator):
    def compute(self, ticks):
        df = pd.DataFrame(ticks)
        high = df["price"].rolling(2).max()
        low = df["price"].rolling(2).min()
        close = df["price"]

        tr = high.combine(close.shift(), max) - low.combine(close.shift(), min)
        atr = tr.rolling(window=self.window).mean()

        return {"atr": atr.iloc[-1]}
