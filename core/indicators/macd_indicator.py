import pandas as pd
from core.indicators.base_indicator import BaseIndicator
from core.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/indicators/macd.yaml")
class MACDIndicator(BaseIndicator):
    def compute(self, ticks):
        prices = [tick["price"] for tick in ticks]
        series = pd.Series(prices)

        fast_ema = series.ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = series.ewm(span=self.slow_period, adjust=False).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=self.signal_period, adjust=False).mean()

        return {
            "macd": macd.iloc[-1],
            "macd_signal": signal.iloc[-1]
        }
