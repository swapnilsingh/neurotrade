# inference/tick_processor.py

from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/tick_processor.yaml")
class TickProcessor:
    def __init__(self, tick_listener, min_ticks=None):
        self.tick_listener = tick_listener
        self.min_ticks = min_ticks or self.config.get("min_ticks", 3)

    def has_enough_ticks(self):
        count = len(self.tick_listener.get_recent_ticks())
        self.logger.debug(f"Tick count = {count} | Required = {self.min_ticks}")
        return count >= self.min_ticks
