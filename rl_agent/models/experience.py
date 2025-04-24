from dataclasses import dataclass
from typing import Any

@dataclass
class Experience:
    state: Any
    action: str
    reward: float
    next_state: Any
    done: bool
