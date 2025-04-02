# Neurotrade Usage Guide

## ▶️ Running the Application Locally

```bash
streamlit run src/app.py
```

Navigate to `http://localhost:8501` to interact with the backtesting dashboard.

## ⚙️ Adjusting Parameters via UI

- Set trading symbol, timeframe, capital, and indicators
- Upload a strategy JSON config
- Start backtesting

## 🧪 Viewing Backtest Results

Tabs in the dashboard include:
- **Summary**: Final capital, drawdown, win rate, Sharpe ratio
- **Trades**: Detailed trade logs (entry/exit, PnL)
- **Charts**: Buy/sell points, equity curve, indicator overlays

## 💾 Exporting Results

- Export configuration as JSON
- Export results as ZIP: logs, trade history, config

## 🕹️ Headless Mode (optional)

To run backtests programmatically:

```bash
python scripts/backtest.py --config configs/sample_config.json
```

## 💡 Tips

- Use smaller timeframes for more trades in backtest
- Tune slippage and trading fees for realism

