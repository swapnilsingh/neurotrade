# 🏗️ Neurotrade Architecture

This document provides a high-level and modular breakdown of the system architecture powering **Neurotrade** — an AI-powered cryptocurrency trading framework.

---

## 🧠 High-Level Architecture

```text
[ Binance / CCXT ]
       ↓
[ Data Ingestion Module ]
       ↓
[ Feature Engineering Node (GPU optional) ]
       ↓
[ Strategy Framework ]  <-------------------
       ↓                                  ↑
[ Multi-Agent AI Layer ]                 |
       ↓                                  |
[ Order Management System (OMS) ] ------→
       ↓
[ Dashboard / Backtesting UI (Streamlit) ]
```

---

## 🔌 Technology Stack

| Layer                      | Tech                                      |
|---------------------------|-------------------------------------------|
| Data Ingestion            | Python, CCXT                              |
| Feature Engineering       | Pandas, NumPy, TA-Lib, Custom GPU Code    |
| Strategy Engine           | Rule Engine, JSON/YAML Configuration      |
| AI Agent Layer            | LSTM, XGBoost, Sklearn                    |
| Order Management System   | Custom Python OMS                         |
| UI                        | Streamlit                                 |
| Storage                   | Local/NFS, PostgreSQL (future), Redis     |
| Deployment                | Docker, Docker Compose, Kubernetes (K3s)  |
| CI/CD                     | GitHub Actions                            |

---

## 🧩 Modular Components

### 1. **Data Ingestion Module (`src/ingestion/`)**
- Fetches OHLCV data from Binance or other exchanges
- Uses Redis to deduplicate and temporarily cache data
- Supports historical + live streaming modes

### 2. **Feature Engineering Module (`src/feature_engineering/`)**
- Computes technical indicators (RSI, MACD, etc.)
- Supports batch and streaming modes
- Optimized for GPU acceleration (Jetson Orin Nano, etc.)

### 3. **Strategy Framework (`src/strategies/`)**
- Loads trading logic from JSON/YAML config
- Evaluates rule-based conditions for buy/sell
- Communicates decisions to AI layer and OMS

### 4. **Multi-Agent AI Layer (`src/ai_agents/`)**
- Each agent can independently approve, reject, or vote on a trade
- Uses ML models for predictive analytics and validation
- Modular agent plug-in support

### 5. **Order Management System (OMS) (`src/oms/`)**
- Simulates or places trades
- Handles position tracking, PnL, slippage, fees, inventory
- Sends inventory and trade states to UI

### 6. **Dashboard & Monitoring (`Streamlit`, `src/app.py`)**
- Backtesting visualizations
- Strategy performance metrics
- Live trade visualization (optional)

---

## 🗃️ Data Flow Summary

1. Ingest OHLCV data from Binance (via CCXT)
2. Engineer features and technical indicators
3. Evaluate rules or ML signals for trade decisions
4. AI agents validate and vote on actions
5. OMS executes trades or simulates them
6. Dashboard shows trades, metrics, and visual indicators

---

This modular and container-ready architecture ensures flexibility for research, backtesting, live trading, and future integration with multiple AI strategies.

