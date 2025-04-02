# API and Configuration Reference

## 🔧 Strategy Configuration Format (JSON)

Neurotrade strategies are defined via JSON files.

### 📄 Sample Strategy Configuration

```json
{
  "start_date": "2023-01-01",
  "end_date": "2023-06-01",
  "symbol": "BTC/USDT",
  "timeframe": "15m",
  "capital": 1000,
  "indicators": {
    "rsi": {"enabled": true, "period": 14},
    "macd": {"enabled": true, "fast": 12, "slow": 26, "signal": 9},
    "bollinger_bands": {"enabled": true, "period": 20, "stddev": 2}
  },
  "trading": {
    "buy_condition": "rsi < 30 and macd > signal",
    "sell_condition": "rsi > 70 or macd < signal",
    "trade_size_pct": 10,
    "slippage_pct": 0.05,
    "trading_fee_pct": 0.1
  },
  "oms": {
    "trailing_stop": true,
    "trailing_pct": 0.03,
    "risk_per_trade": 0.02
  }
}
```

## 📤 Future API Endpoints (Optional)

If REST APIs are added later for live trading, document the endpoints here:

| Endpoint | Method | Description               |
|----------|--------|---------------------------|
| /trade   | POST   | Trigger a trade execution |
| /status  | GET    | Check bot or agent status |

