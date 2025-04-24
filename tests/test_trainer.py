import torch
from trainer.trainer import DQNTrainer
from rl_agent.models.state import State
from rl_agent.models.experience import Experience

class DummyState(State):
    def indicators_vector(self):
        return [0.1] * 10

def test_trainer_memory_and_replay():
    trainer = DQNTrainer(input_dim=10, output_dim=3)
    for _ in range(100):
        exp = Experience(
            state=DummyState(indicators={}),
            action="BUY",
            reward=1.0,
            next_state=DummyState(indicators={}),
            done=False
        )
        trainer.remember(exp)
    assert len(trainer.memory) == 100
    trainer.replay()  # Should not raise
    trainer.save_model("/tmp/test_model.pt")
    assert torch.load("/tmp/test_model.pt")
