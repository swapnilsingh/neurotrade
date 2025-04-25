from typing import Union, Dict
from pydantic import BaseModel

class State(BaseModel):
    timestamp: int = 0  # 👈 ADD THIS LINE
    rsi: Union[float, Dict[str, float]] = 50.0
    macd: Union[float, Dict[str, float]] = 0.0
    bollinger: Union[float, Dict[str, float]] = 0.0
    atr: Union[float, Dict[str, float]] = 0.0
    adx: Union[float, Dict[str, float]] = 0.0
    close: float = 0.0

    def indicators_vector(self) -> list:
        def get_val(val, key=None):
            if isinstance(val, dict) and key:
                return val.get(key, 0)
            return val if isinstance(val, (int, float)) else 0

        return [
            get_val(self.rsi, "rsi"),
            get_val(self.macd, "macd"),
            get_val(self.macd, "macd_signal"),
            get_val(self.bollinger, "bollinger_mavg"),
            get_val(self.bollinger, "bollinger_hband"),
            get_val(self.bollinger, "bollinger_lband"),
            get_val(self.atr, "atr"),
            get_val(self.adx, "adx"),
            self.close
        ]
