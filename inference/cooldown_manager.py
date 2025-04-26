class CooldownManager:
    def __init__(self, enabled=True, cooldown_seconds=3):
        self.enabled = enabled
        self.cooldown_seconds = cooldown_seconds
        self.last_trade_timestamp = None

    def can_trade(self, current_timestamp):
        if not self.enabled:
            return True
        if self.last_trade_timestamp is None:
            return True
        elapsed = (current_timestamp - self.last_trade_timestamp) / 1000  # ms to seconds
        return elapsed >= self.cooldown_seconds

    def record_trade(self, current_timestamp):
        self.last_trade_timestamp = current_timestamp