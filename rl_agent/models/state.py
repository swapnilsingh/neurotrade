from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class State:
    indicators: Dict[str, Any]
    timestamp: int = 0
