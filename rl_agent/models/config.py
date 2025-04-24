from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class StrategyConfig:
    indicators: List[str]
    trading: Dict[str, float]
    oms: Dict[str, float]
