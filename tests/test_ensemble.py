from rl_agent.ensemble_agent import EnsembleAgent
from rl_agent.models.state import State

def test_ensemble_vote():
    agent = EnsembleAgent()
    state = State(
        timestamp=1714023000000,
        rsi={"rsi": 25},
        macd={"macd": 1, "macd_signal": 0},
        atr={"atr": 2},
        adx={"adx": 30},
        bollinger={
            "bollinger_hband": 110,
            "bollinger_lband": 90,
            "bollinger_mavg": 100
        },
        close=8000
    )
    signal, votes = agent.vote(state)
    assert signal in ["BUY", "SELL", "HOLD"]
    assert isinstance(votes, dict)
