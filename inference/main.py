import pandas as pd
import json
from rl_agent.ensemble_agent import EnsembleAgent
from feature_builder.builder import build_state
from feature_builder.strategy_loader import load_strategy_config
from utils.trade_logger import log_trade

def run_inference(file_path="sample_ohlcv.csv", strategy_path="configs/strategy.yaml"):
    df = pd.read_csv(file_path)
    config = load_strategy_config(strategy_path)
    agent = EnsembleAgent()

    for _, row in df.iterrows():
        state = build_state(row, config)
        signal, votes = agent.vote(state)

        trade = {
            "timestamp": int(row["timestamp"]),
            "symbol": row.get("symbol", "BTCUSDT"),
            "signal": signal,
            "equity": 1000.0,
            "reason": f"majority vote={signal}",
            "votes": votes,
            "indicators": state.indicators,
            "strategy_config": config,
            "model_version": "v1"
        }
        log_trade(trade["symbol"], trade)

if __name__ == "__main__":
    run_inference()
