import pytest
import pandas as pd
import numpy as np
from strategies.backtest_runner import BacktestRunner

# Sample data for testing (OHLCV) with guaranteed behavior (price crossing SMA)
sample_data = {
    'date': pd.date_range(start='2022-01-01', periods=10, freq='D'),
    'open': [1000, 1010, 1020, 1030, 1040, 1050, 1040, 1030, 1020, 1010],  # Increasing then decreasing prices
    'high': [1010, 1020, 1030, 1040, 1050, 1060, 1050, 1040, 1030, 1020],
    'low': [990, 1000, 1010, 1020, 1030, 1040, 1030, 1020, 1010, 1000],
    'close': [1005, 1015, 1025, 1035, 1045, 1055, 1045, 1035, 1025, 1015],  # Values crossing above and below SMA
    'volume': np.random.randint(1, 1000, 10)
}

data = pd.DataFrame(sample_data)

# Sample strategy config for testing
strategy_config = {
    "strategy_id": "simple_sma_strategy",
    "indicators": {
        "macd": {"fast_length": 12, "slow_length": 26, "signal_smooth": 9},
        "rsi": {"length": 14, "overbought": 70, "oversold": 30}
    },
    "trade_parameters": {
        "position_size": 1000,
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.05
    },
    "slippage": 0.001,
    "risk": {"max_drawdown": 0.2, "max_position_size": 0.1},
    "evaluation": {"metrics": ["roi", "sharpe", "win_rate"]}
}

# Unit test to check the application of SMA
def test_apply_indicators():
    backtest = BacktestRunner(strategy_config, data)
    backtest.apply_indicators()
    assert 'SMA' in backtest.data.columns  # Ensure the SMA column was added

# Unit test to check if buy and sell logic works as expected
def test_buy_sell_logic():
    backtest = BacktestRunner(strategy_config, data)
    backtest.apply_indicators()
    
    # Execute strategy
    backtest.execute_strategy()
    
    # Check if buy and sell actions were logged
    assert len(backtest.trade_logs) > 0  # Ensure some trades occurred
    assert backtest.trade_logs[0]['action'] in ['BUY', 'SELL']  # Check action is either BUY or SELL

# Unit test to check if equity curve is generated correctly
def test_equity_curve():
    backtest = BacktestRunner(strategy_config, data)
    backtest.apply_indicators()
    backtest.execute_strategy()
    
    # Check if equity curve is being tracked
    assert len(backtest.equity_curve) == len(data)  # Ensure the equity curve length matches data length
    assert backtest.equity_curve[0] == backtest.balance  # The first equity curve value should equal initial balance
