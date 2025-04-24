from rl_agent.ensemble_agent import EnsembleAgent
from rl_agent.models.state import State

def test_ensemble_vote():
    agent = EnsembleAgent()
    state = State(indicators={"rsi": 25, "macd": {"macd": 1, "macd_signal": 0}, "adx": 30, "atr": 2, "bollinger": {}, "close": 8000})
    signal, votes = agent.vote(state)
    assert signal in ["BUY", "SELL", "HOLD"]
    assert isinstance(votes, dict)
