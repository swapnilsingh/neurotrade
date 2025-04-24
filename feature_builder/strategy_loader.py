import yaml

def load_strategy_config(path="configs/strategy.yaml"):
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return config
