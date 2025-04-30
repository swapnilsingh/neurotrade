import pandas as pd
from core.indicators.base_indicator import BaseIndicator
from core.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/indicators/bollinger.yaml")
class BollingerBandsIndicator(BaseIndicator):
    def compute(self, ticks):
        prices = pd.Series([tick["price"] for tick in ticks])
        mean = prices.rolling(window=self.window).mean()
        std = prices.rolling(window=self.window).std()

        upper = mean + (self.num_std * std)
        lower = mean - (self.num_std * std)
        return {
            "bollinger_upper": upper.iloc[-1],
            "bollinger_lower": lower.iloc[-1],
            "bollinger_mean": mean.iloc[-1]
        }
