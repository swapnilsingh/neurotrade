# 📦 Modules Overview - Neurotrade

This document outlines all core modules of the Neurotrade architecture, describing their responsibilities, input/output interfaces, and interaction patterns.

---

## 1. 📨 Data Ingestion Module (`src/ingestion/`)
- **Purpose:** Retrieve historical and live OHLCV data from crypto exchanges.
- **Input:** Ticker symbol, timeframe, start/end dates
- **Output:** Cleaned DataFrame or JSON with OHLCV data
- **Key Features:**
  - Integrates with CCXT
  - Caches data in Redis (if enabled)
  - Supports resampling, deduplication, and retry logic

---

## 2. 📊 Feature Engineering Module (`src/feature_engineering/`)
- **Purpose:** Compute technical indicators and statistical features
- **Input:** OHLCV data from ingestion
- **Output:** Feature-enriched DataFrame (includes indicators)
- **Key Features:**
  - Supports RSI, MACD, Bollinger Bands, ADX, ATR
  - Can run on GPU if supported (Jetson Orin Nano, CUDA)
  - Handles NA values, feature normalization, and windowing

---

## 3. 📈 Strategy Framework (`src/strategies/`)
- **Purpose:** Define and execute rule-based strategies loaded from config files
- **Input:** Feature-enriched data + strategy config (JSON/YAML)
- **Output:** Trading signals (buy/sell/hold)
- **Key Features:**
  - Modular rule evaluation engine
  - Post-profit trade blocking logic
  - Supports slippage, fees, and position sizing logic

---

## 4. 🧠 AI Agents (`src/ai_agents/`)
- **Purpose:** Use ML models to validate or override strategy signals
- **Input:** Data + signals
- **Output:** Final signal decision (per agent or ensemble)
- **Key Features:**
  - Plug-and-play agent architecture
  - Supports LSTM, XGBoost, Scikit-learn models
  - Ensemble voting and prediction confidence filters

---

## 5. 🧾 Order Management System (OMS) (`src/oms/`)
- **Purpose:** Manage capital, simulate execution, track positions
- **Input:** Final trade signals
- **Output:** Executed trades, updated portfolio
- **Key Features:**
  - Inventory tracking, slippage modeling
  - Realistic trade execution simulation
  - Exportable trade log and stats

---

## 6. 📺 Visualization & Backtesting UI (`src/app.py`)
- **Purpose:** Provide an interactive UI to configure, run, and visualize backtests
- **Input:** Strategy config, timeframe, indicators
- **Output:** Charts, summary metrics, trade log
- **Key Features:**
  - Tabs for performance, trades, equity curve, indicators
  - Upload/export JSON configs
  - Headless backtest support via CLI

---

## 7. 🧪 Testing Framework (`tests/`)
- **Purpose:** Validate functionality via unit and integration tests
- **Tools:** Pytest, pytest-cov, mock
- **Scope:**
  - Ingestion, feature pipelines, strategy logic, AI agents, OMS
  - Coverage and performance testing

---

Each module in Neurotrade is designed to be stateless, testable, and replaceable. This modular structure ensures flexibility and scalability for future features, live trading, and production deployment.

