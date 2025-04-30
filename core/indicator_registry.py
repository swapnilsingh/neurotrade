import importlib
import logging
import yaml

logger = logging.getLogger("IndicatorRegistry")

def load_indicator_agents(config_path):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    agents = []
    for item in config.get("indicators", []):
        class_path = item["class"]
        module_name, class_name = class_path.rsplit(".", 1)

        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)

        # 🚀 No config/name passed — decorators handle that
        instance = cls()
        agents.append(instance)
        logger.info(f"✅ Loaded indicator: {class_name} from {class_path}")

    return agents
