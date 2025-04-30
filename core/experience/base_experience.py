from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/experience_manager.yaml")
class BaseExperience:
    def __init__(self):
        self.logger.info("🔌 BaseExperience initialized with config.")
        self.model_version = self.config.get("model_version", "v1")
        self.max_signal_history = self.config.get("max_signal_history", 1000)
        symbol = self.config.get("symbol", "btcusdt").upper()

        keys = self.config.get("keys", {})
        self.experience_key = keys.get("experience", "experience_queue")
        self.signal_key = keys.get("signal", f"signal_history:{{symbol}}").replace("{symbol}", symbol)
