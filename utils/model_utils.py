import hashlib
import torch

def save_model(model, path="model.pt"):
    torch.save(model.state_dict(), path)

def load_model(model_class, path="model.pt"):
    model = model_class()
    model.load_state_dict(torch.load(path, map_location=torch.device("cpu")))
    return model

def get_model_version(path="model.pt"):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
