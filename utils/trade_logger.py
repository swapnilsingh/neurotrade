import json
import os

def log_trade(symbol, data, file_path="inference_log.csv"):
    log_dir = os.path.dirname(file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    with open(file_path, "a") as f:
        f.write(json.dumps(data) + "\n")
