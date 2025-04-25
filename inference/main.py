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

    print(f"🧠 Running inference on {len(df)} rows...")

    for idx, row in df.iterrows():
        state = build_state(row, config)
        signal, votes = agent.vote(state)

        trade = {
            "timestamp": int(row["timestamp"]),
            "symbol": row.get("symbol", "BTCUSDT"),
            "signal": signal,
            "equity": 1000.0,
            "reason": f"majority vote={signal}",
            "votes": votes,
            "indicators": state.model_dump(include={"rsi", "macd", "bollinger", "atr", "adx", "close"}),
            "strategy_config": config,
            "model_version": "v1"
        }

        log_trade(trade["symbol"], trade)

        # 👇 Add this line for feedback
        print(f"[{idx}] ✅ Signal: {signal} | Votes: {votes}")

    print("🎉 Inference complete.")

if __name__ == "__main__":
    run_inference()
