from feature_builder.builder import build_state

def test_build_state_valid():
    ohlcv_row = {
        "timestamp": 1714023000000,
        "rsi": 25, "macd": {"macd": 0.5}, "atr": 1.0
    }
    config = {"indicators": ["rsi", "macd", "atr"]}
    state = build_state(ohlcv_row, config)
    assert isinstance(state.rsi, (float, dict))
    assert isinstance(state.macd, (float, dict))
    assert state.timestamp == 1714023000000
