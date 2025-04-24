import torch
from utils.model_utils import save_model, load_model, get_model_version
from rl_agent.dqn_agent import DQNModel

def test_model_save_load_version():
    model = DQNModel(input_dim=10, output_dim=3)
    save_model(model, path="/tmp/test_model.pt")
    loaded = load_model(lambda: DQNModel(10, 3), path="/tmp/test_model.pt")
    assert isinstance(loaded, DQNModel)
    version = get_model_version("/tmp/test_model.pt")
    assert isinstance(version, str) and len(version) == 64
