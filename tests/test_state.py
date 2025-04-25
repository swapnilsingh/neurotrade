from rl_agent.models.state import State

def test_state_creation():
    state = State(
        timestamp=123456789,
        rsi={"rsi": 45},
        macd={"macd": 0.0, "macd_signal": 0.0},
        atr={"atr": 1.5},
        adx={"adx": 0},
        bollinger={
            "bollinger_hband": 110,
            "bollinger_lband": 90,
            "bollinger_mavg": 100
        },
        close=100
    )
    assert state.rsi["rsi"] == 45
    assert state.timestamp == 123456789
