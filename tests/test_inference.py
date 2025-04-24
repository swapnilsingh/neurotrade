from feature_builder.builder import build_state
from feature_builder.strategy_loader import load_strategy_config
from rl_agent.ensemble_agent import EnsembleAgent

def test_inference_single_tick():
    row = {
        "timestamp": 1714023000000,
        "rsi": 25, "macd": {"macd": 1, "macd_signal": 0},
        "adx": 28, "atr": 1.5, "bollinger": {}, "close": 9200
    }
    config = {"indicators": ["rsi", "macd", "adx", "atr", "bollinger", "close"]}
    state = build_state(row, config)
    agent = EnsembleAgent()
    signal, votes = agent.vote(state)
    assert signal in ["BUY", "SELL", "HOLD"]
    assert isinstance(votes, dict)
