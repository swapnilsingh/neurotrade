import pytest
from rl_agent.models.state import State
from rl_agent.rsi_agent import RSIAgent
from rl_agent.macd_agent import MACDAgent
from rl_agent.bollinger_agent import BollingerAgent
from rl_agent.adx_agent import ADXAgent
from rl_agent.atr_agent import ATRAgent
from rl_agent.ensemble_agent import EnsembleAgent

def mock_state(**kwargs):
    return State(
        rsi={"rsi": kwargs.get("rsi", 50)},
        macd={"macd": kwargs.get("macd", 0), "macd_signal": kwargs.get("macd_signal", 0)},
        bollinger={
            "bollinger_mavg": kwargs.get("mavg", 100),
            "bollinger_hband": kwargs.get("upper", 110),
            "bollinger_lband": kwargs.get("lower", 90)
        },
        atr={"atr": kwargs.get("atr", 0.5)},
        adx={"adx": kwargs.get("adx", 20)},
        close=kwargs.get("close", 100)
    )

def test_rsi_agent():
    agent = RSIAgent()
    assert agent.vote(mock_state(rsi=25)) == "BUY"
    assert agent.vote(mock_state(rsi=75)) == "SELL"
    assert agent.vote(mock_state(rsi=50)) == "HOLD"

def test_macd_agent():
    agent = MACDAgent()
    assert agent.vote(mock_state(macd=1, macd_signal=0)) == "BUY"
    assert agent.vote(mock_state(macd=0, macd_signal=1)) == "SELL"
    assert agent.vote(mock_state(macd=0.5, macd_signal=0.5)) == "HOLD"

def test_bollinger_agent():
    agent = BollingerAgent()
    assert agent.vote(mock_state(close=85, lower=90)) == "BUY"
    assert agent.vote(mock_state(close=115, upper=110)) == "SELL"
    assert agent.vote(mock_state(close=100)) == "HOLD"

def test_adx_agent():
    agent = ADXAgent()
    assert agent.vote(mock_state(adx=30)) == "BUY"
    assert agent.vote(mock_state(adx=15)) == "HOLD"

def test_atr_agent():
    agent = ATRAgent()
    assert agent.vote(mock_state(atr=1.5)) == "BUY"
    assert agent.vote(mock_state(atr=0.5)) == "HOLD"

def test_ensemble_agent():
    agent = EnsembleAgent()
    state = mock_state(rsi=25, macd=1, macd_signal=0, adx=30, atr=2, close=85, lower=90)
    signal, votes = agent.vote(state)
    assert signal in ["BUY", "SELL", "HOLD"]
    assert isinstance(votes, dict)
