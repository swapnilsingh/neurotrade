# utils/config_loader.py

import yaml
import os

def load_config(*files, base_path="configs"):
    """
    Generic loader to merge one or more YAML config files.
    
    Args:
        *files: Filenames to load and merge (e.g., "system.yaml", "inference.yaml").
        base_path (str): Path where config files are located.

    Returns:
        dict: Merged config dictionary.
    """
    config = {}

    for filename in files:
        path = os.path.join(base_path, filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            if data:
                config.update(data)

    return config
