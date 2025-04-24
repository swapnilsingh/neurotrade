from utils.reward import compute_reward

def test_reward_computation():
    assert round(compute_reward(100, 110), 2) == 0.1
    assert round(compute_reward(100, 90), 2) == -0.1
