import pandas as pd
from core.indicators.base_indicator import BaseIndicator
from core.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/indicators/adx.yaml")
class ADXIndicator(BaseIndicator):
    def compute(self, ticks):
        df = pd.DataFrame(ticks)
        high = df["price"].rolling(2).max()
        low = df["price"].rolling(2).min()
        close = df["price"]

        plus_dm = high.diff()
        minus_dm = -low.diff()
        tr = high.combine(close.shift(), max) - low.combine(close.shift(), min)
        atr = tr.rolling(window=self.window).mean()

        plus_di = 100 * plus_dm.rolling(self.window).mean() / atr
        minus_di = 100 * minus_dm.rolling(self.window).mean() / atr
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(self.window).mean()

        return {"adx": adx.iloc[-1]}
