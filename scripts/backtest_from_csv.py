import pandas as pd
from rl_agent.ensemble_agent import EnsembleAgent
from utils.builder import build_state
from feature_builder.strategy_loader import load_strategy_config
from executor.exchange_executor import PaperExecutor
from utils.trade_logger import log_trade

def run_backtest(csv_path="sample_ohlcv.csv", strategy_path="configs/strategy.yaml"):
    df = pd.read_csv(csv_path)
    df.sort_values("timestamp", inplace=True)
    config = load_strategy_config(strategy_path)
    agent = EnsembleAgent()
    executor = PaperExecutor()

    for _, row in df.iterrows():
        state = build_state(row, config)
        signal, votes = agent.vote(state)
        equity = executor.execute(row["close"], signal)

        trade = {
            "timestamp": int(row["timestamp"]),
            "symbol": row.get("symbol", "BTCUSDT"),
            "signal": signal,
            "equity": equity,
            "reason": f"majority vote={signal}",
            "votes": votes,
            "indicators": state.indicators,
            "strategy_config": config,
            "model_version": "v1"
        }
        log_trade(trade["symbol"], trade)

if __name__ == "__main__":
    run_backtest()
