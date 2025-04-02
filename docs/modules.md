# Modules Overview

## 1. Data Ingestion
- **Purpose:** Collect real-time market data
- **Interfaces:** Binance via CCXT, Redis caching

## 2. Feature Engineering
- **Purpose:** Compute indicators and predictive features
- **Techniques:** RSI, MACD, Bollinger Bands, ADX, ATR, GPU acceleration

## 3. Strategies
- **Purpose:** Define trading strategies and triggers
- **Configuration:** JSON/YAML based configurations, modular logic

## 4. AI Agents
- **Purpose:** Apply machine learning models for trading decisions
- **Models Supported:** LSTM, XGBoost, ensemble voting

## 5. OMS (Order Management System)
- **Purpose:** Track and manage positions
- **Features:** Trade simulation, risk management, slippage modeling, fee simulation
