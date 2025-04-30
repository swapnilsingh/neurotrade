# core/decorators.py
import logging
from functools import wraps
from utils.config_loader import load_config

def inject_logger(name_attr="logger_name", level_attr="log_level"):
    def decorator(cls):
        orig_init = cls.__init__

        @wraps(orig_init)
        def wrapped(self, *args, **kwargs):
            # 💡 Inject logger early BEFORE __init__()
            logger_name = getattr(self, name_attr, cls.__name__) if hasattr(self, name_attr) else cls.__name__
            log_level = getattr(self, level_attr, "INFO").upper() if hasattr(self, level_attr) else "INFO"

            self.logger = logging.getLogger(logger_name)
            self.logger.setLevel(getattr(logging, log_level, logging.INFO))

            orig_init(self, *args, **kwargs)

        cls.__init__ = wrapped
        return cls
    return decorator


def inject_config(config_path=None):
    def decorator(cls):
        orig_init = cls.__init__

        @wraps(orig_init)
        def wrapped(self, *args, **kwargs):
            normalized = config_path
            if config_path and config_path.startswith("configs/"):
                normalized = config_path.replace("configs/", "")

            self_config = load_config(normalized) if normalized else {}
            self.config = self_config

            for key, value in self_config.items():
                setattr(self, key, value)

            orig_init(self, *args, **kwargs)

        cls.__init__ = wrapped
        return cls
    return decorator
