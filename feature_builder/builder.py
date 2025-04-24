from rl_agent.models.state import State

def build_state(ohlcv_row, config):
    indicators = {}
    for name in config["indicators"]:
        if name in ohlcv_row:
            indicators[name] = ohlcv_row[name]
    return State(indicators=indicators, timestamp=int(ohlcv_row["timestamp"]))
