# core/indicators/base_indicator.py

from abc import ABC, abstractmethod
from core.decorators import inject_logger, inject_config

@inject_logger()
@inject_config()  # Path will be passed by subclasses dynamically
class BaseIndicator(ABC):
    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def compute(self, ticks):
        pass

    def safe_compute(self, ticks):
        try:
            if len(ticks) < getattr(self, "window", 14):  # fallback to 14 if window not injected
                self.logger.warning(f"{self.name}: Not enough ticks ({len(ticks)}) to compute.")
                return {self.name.lower(): None}
            return self.compute(ticks)
        except Exception as e:
            self.logger.exception(f"{self.name}: Exception during computation: {e}")
            return {self.name.lower(): None}
