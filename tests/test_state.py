from rl_agent.models.state import State

def test_state_creation():
    state = State(indicators={"rsi": 45, "macd": {}, "atr": 1.5}, timestamp=123456789)
    assert state.indicators["rsi"] == 45
    assert state.timestamp == 123456789
