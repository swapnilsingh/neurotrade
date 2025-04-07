### Neurotrade System Design & Schema Reference

🔗 GitHub Repository: [https://github.com/swapnilsingh/neurotrade](https://github.com/swapnilsingh/neurotrade)

---

## 🧭 Architecture Overview

```
[Binance WebSocket Streams]
    ├─→ queue:ohlcv:<symbol>      (TTL 10s)
    └─→ queue:orderbook:<symbol>  (TTL 10s)

[Indicator Service]
    ├─ Consumes from both queues
    ├─ Computes indicators (RSI, EMA, MACD, OBI, Spread, etc.)
    └─ Pushes to: indicators:<symbol>:processed

[Strategy Service]
    ├─ Consumes from processed queue
    ├─ Applies strategy config (JSON/YAML)
    └─ Outputs signal + context to: strategy:<symbol>:signal

[ReactAI Agent & RL Model]
    ├─ Optionally override/refine signals using context (news, order book)
    └─ Output is sent to Execution Engine

[Execution Engine]
    ├─ Receives trade signals
    ├─ Performs position sizing, stop-loss, take-profit
    └─ Executes order via exchange API (CCXT)

[Monitoring + Logging]
    ├─ Tracks performance metrics (PnL, win rate, latency)
    ├─ Sends alerts via Slack/email
    └─ Supports health checks and trade auditing
```

---

## 🗂️ Recommended Project Structure

```
neurotrade/
├── ingestion/                  # WebSocket consumers (OHLCV, Order Book)
│   ├── __init__.py
│   └── binance_client.py
│
├── indicators/                # Feature engineering logic
│   ├── __init__.py
│   └── compute.py             # RSI, EMA, MACD, etc.
│
├── strategy/                  # Rule-based strategy engine
│   ├── __init__.py
│   ├── strategy_engine.py
│   └── strategies/            # Configurable strategies
│       └── default.yaml
│
├── reactai/                   # AI/Context-aware decision override
│   └── react_agent.py
│
├── execution/                 # Order placement and risk filters
│   ├── __init__.py
│   └── executor.py
│
├── rl_model/                  # RL model training and inference
│   ├── __init__.py
│   └── ppo_agent.py
│
├── monitoring/                # Logs, health checks, notifications
│   ├── __init__.py
│   └── monitor.py
│
├── backtesting/               # Strategy backtesting tools
│   ├── __init__.py
│   └── backtester.py
│
├── schemas/                   # JSON schema definitions
│   ├── ohlcv_schema.json
│   ├── orderbook_schema.json
│   └── strategy_signal_schema.json
│
├── config/                    # System configs
│   ├── symbols.yaml
│   └── redis.yaml
│
├── utils/                     # Common utilities
│   ├── redis_client.py
│   ├── logger.py
│   └── validation.py
│
├── tests/                     # Unit tests and mocks
│   ├── test_ingestion.py
│   ├── test_strategy.py
│   └── mock_streams.py
│
├── docs/                      # Design documentation and examples
│   └── architecture.md
│
├── .env.template              # Environment variable templates
├── docker-compose.yml         # Local dev environment (Redis, TimescaleDB)
├── Makefile                   # Automation commands (test, lint, run)
├── main.py                    # Orchestrator or entry point
└── requirements.txt           # Python dependencies
```

---

## 📁 Redis Queue Key Naming Convention

| Key Pattern                  | Description                                      |
|-----------------------------|--------------------------------------------------|
| `queue:ohlcv:<symbol>`      | Raw OHLCV candle data (1m), ephemeral (TTL 10s)  |
| `queue:orderbook:<symbol>`  | Raw order book snapshot, ephemeral (TTL 10s)     |
| `indicators:<symbol>:processed` | Processed features pushed by indicator service |
| `strategy:<symbol>:signal`  | Final output decision from Strategy Service      |
| `reactai:<symbol>:decision` | Final AI-refined action to execute               |

---

## 📐 Data Schemas

### 1. OHLCV (Raw Candle)
```json
{
  "symbol": "BTC/USDT",
  "timestamp": "2025-04-04T12:01:00Z",
  "open": 42000.5,
  "high": 42030.0,
  "low": 41980.0,
  "close": 42010.1,
  "volume": 152.3
}
```

### 2. Order Book Snapshot
```json
{
  "symbol": "BTC/USDT",
  "timestamp": "2025-04-04T12:01:00Z",
  "bids": [[42000.5, 1.2], [41999.0, 1.2]],
  "asks": [[42001.0, 1.0], [42002.0, 0.7]]
}
```

### 3. Composite Data Record (Merged View)
```json
{
  "symbol": "BTC/USDT",
  "timestamp": "2025-04-04T12:01:00Z",
  "ohlcv": { ... },
  "order_book_open": { ... },
  "order_book_close": { ... }
}
```

### 4. Processed Indicator Output
```json
{
  "symbol": "BTC/USDT",
  "timestamp": "2025-04-04T12:01:00Z",
  "rsi": 28.5,
  "ema_5": 42005.2,
  "macd": -12.1,
  "boll_upper": 42080.0,
  "boll_lower": 41920.0,
  "ob_imbalance": 0.34,
  "bid_ask_spread": 0.6,
  "top_of_book_delta": 0.2
}
```

### 5. Strategy Output
```json
{
  "symbol": "BTC/USDT",
  "timestamp": "2025-04-04T12:01:00Z",
  "signal": "BUY",
  "reason": "RSI < 30 and price > EMA5",
  "price": 42010.1
}
```

### 6. ReactAI Decision
```json
{
  "symbol": "BTC/USDT",
  "timestamp": "2025-04-04T12:01:00Z",
  "action": "BUY",
  "confidence": 0.92,
  "notes": "Validated signal with bullish order book"
}
```

### 7. Execution Report
```json
{
  "symbol": "BTC/USDT",
  "timestamp": "2025-04-04T12:01:00Z",
  "order_id": "abc123",
  "status": "FILLED",
  "price": 42012.0,
  "quantity": 0.05,
  "side": "BUY"
}
```

---

## 🔧 Service Breakdown

### Ingestion Service
- Subscribes to Binance WebSocket for all active symbols
- Publishes to symbol-specific ephemeral queues
- Includes timestamp normalization and retry logic

### Indicator Service
- Subscribes to raw OHLCV and order book queues
- Aggregates composite records per 1-minute window
- Computes time-aligned indicators
- Publishes processed features to `indicators:<symbol>:processed`

### Strategy Service
- Subscribes to processed indicators queue
- Loads trading logic from JSON/YAML config
- Evaluates conditions and produces `BUY`, `SELL`, or `HOLD`
- Publishes signal to strategy queue

### ReactAI Agent (optional)
- Pulls signal and surrounding context (news, book)
- Refines final decision using rule-based/AI logic
- Outputs action for execution

### Execution Engine
- Connects to exchange via CCXT
- Applies risk filters (SL, TP, position size)
- Executes market or limit order
- Publishes status to a reporting channel (logs, Telegram, UI)

---

## 📌 Notes
- All queues are ephemeral where possible to conserve resources on Raspberry Pi cluster.
- Data is symbol-specific and processed in isolation for parallel scalability.
- Composite records are used only when both OHLCV and order book snapshots are available.
- Strategy logic is modular and loaded from versioned config.
- RL and ReactAI layers are optional but enable AI augmentation.
- Add `.env` for secrets, `docker-compose.yml` for local services, `Makefile` for CI/DevOps helpers.

---

## ⏭️ Next Up
- Build ingestion and indicator services per these schemas.
- Define YAML config format for strategy rules.
- Add logging and monitoring hooks for real-time signal auditing.
- Add CI-friendly test mocks for simulated OHLCV + order book streams.
- Create reusable Python modules under `utils/` for Redis publishing, symbol management, and message validation.
- Scaffold Docker environment and `.env.template` for deployment.
- Begin auto-generating docs into `docs/` folder from schema/logic.

---

