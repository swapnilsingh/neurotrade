from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/cooldown_manager.yaml")
class CooldownManager:
    def __init__(self):
        self.enabled = self.config.get("enabled", True)
        self.cooldown_seconds = self.config.get("cooldown_seconds", 2)
        self.last_trade_time = 0

        self.logger.debug(f"⏱️ CooldownManager initialized: enabled={self.enabled}, cooldown_seconds={self.cooldown_seconds}")

    def can_trade(self, timestamp):
        if not self.enabled:
            return True

        elapsed = timestamp - self.last_trade_time
        if elapsed >= self.cooldown_seconds * 1000:
            self.last_trade_time = timestamp
            self.logger.debug(f"✅ Cooldown passed: {elapsed}ms elapsed")
            return True

        self.logger.debug(f"⛔ Cooldown active: only {elapsed}ms elapsed")
        return False
