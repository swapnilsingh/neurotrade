from typing import List
from pydantic import BaseModel

class State(BaseModel):
    rsi: float = 0.5         # Normalized (rsi / 100)
    macd: float = 0.0
    bollinger: float = 0.0
    atr: float = 0.0         # Normalized (atr / 50000)
    adx: float = 0.5         # Normalized (adx / 100)
    close: float = 0.0       # Normalized (close / 100000)

    def indicators_vector(self) -> List[float]:
        return [
            self.rsi,
            self.macd,
            self.bollinger,
            self.atr,
            self.adx,
            self.close
        ]
