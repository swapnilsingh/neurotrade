# 🧠 Neurotrade: Real-Time AI Cryptocurrency Trading System

Neurotrade is a modular, scalable, real-time AI-powered cryptocurrency trading framework. It leverages deep reinforcement learning and rule-based ensemble agents to simulate, monitor, and automate trading decisions on live or historical data.

This platform is designed for traders, researchers, and developers seeking:
- A modular architecture to plug in different strategies or agents
- Real-time data streaming and dashboarding
- Explainable and testable AI trading flows
- Compatibility with Docker and Kubernetes-based deployments

---

## 🚀 Features

- **Real-Time + Backtest Modes**  
  Trade live using Binance WebSocket data or run backtests using historical OHLCV CSV files.
  
- **Modular Multi-Agent Architecture**  
  Plug-and-play agents like RSI, MACD, Bollinger Bands, DQN, PPO, and LSTM. Agents vote on every tick/candle and can be extended or tuned independently.

- **Explainability by Design**  
  Every vote is logged with context, indicators, and model version to help analyze what decisions were made and why.

- **Replay and Audit Trail**  
  Each trade and signal is saved with metadata (votes, strategy config, reward, equity) to allow re-simulation and forensic debugging.

- **Streamlit Dashboard**  
  Real-time equity curve, trade insights, vote explanations, and performance summaries.

- **Cross-Environment Compatible**  
  Run locally, in Docker, or deploy at scale using Kubernetes (K3s ready).

- **Comprehensive Test Suite**  
  Unit tests cover agents, reward logic, logging, inference flow, and state handling.

---

## 🛠️ Local Setup

This project requires Python 3.11 or later.

1. Clone and enter the project:
```bash
git clone https://github.com/your-org/neurotrade.git
cd neurotrade
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. Install dependencies (per module or unified):
```bash
pip install -r inference/requirements.txt
pip install -r trainer/requirements.txt
pip install -r streamlit-ui/requirements.txt
```

---

## 🧪 Testing & Code Coverage

### Run all unit tests:
```bash
pytest tests
```

### Run with test coverage:
```bash
pip install coverage
coverage run -m pytest tests
coverage report -m
coverage html  # Generates HTML report at htmlcov/index.html
```

Tests cover:
- Agent votes and ensemble aggregation
- Reward shaping (profit-based and percentage-based)
- Model version hashing
- State object creation and serialization
- Logger output validation
- Trainer experience replay memory

---

## 📊 Running a Backtest

Backtests simulate trades using a CSV file of OHLCV data (`sample_ohlcv.csv`) and produce a log of decisions.

```bash
python scripts/backtest_from_csv.py
```

This will:
- Use `configs/strategy.yaml` to select active indicators
- Build state objects for each row
- Feed them to the ensemble agent
- Simulate execution using a paper trading engine
- Log results to `inference_log.csv`

---

## 📺 Streamlit Dashboard

Run the dashboard to visualize trading activity in real time or from log files:

```bash
cd streamlit-ui
streamlit run app.py
```

Features:
- Dynamic equity curve
- Per-symbol dashboard tabbing (e.g. BTCUSDT, ETHUSDT)
- Display of final signal and all agent votes
- Real-time updates and replayable UI
- Signal explainability and strategy metadata view

---

## 📦 Docker & Kubernetes Deployment

### Docker (Example for `inference`)
```bash
cd inference
docker build -t neurotrade/inference .
docker run -p 8000:8000 neurotrade/inference
```

Each module includes its own `Dockerfile` and `requirements.txt`.

### Kubernetes (via K3s)
```bash
kubectl apply -f deployment/k3s/inference-deployment.yaml
kubectl apply -f deployment/k3s/inference-service.yaml
```

You can customize:
- Node affinity
- CPU/GPU resource limits
- Persistent volume mounts for Redis, models, logs

---

## 🧱 Project Structure (Overview)

```
rl_agent/
│   base.py                  - Abstract interface for all agents
│   rsi_agent.py             - Rule-based RSI agent
│   dqn_agent.py             - Deep Q Network agent (PyTorch)
│   ensemble_agent.py        - Aggregates votes from all agents
│
├── models/
│   state.py                 - Structured indicator state
│   experience.py            - Experience replay structure
│   config.py                - YAML strategy config model

trainer/
│   trainer.py               - DQN optimizer loop, replay memory

inference/
│   main.py                  - Loads model + emits trade signals

feature_builder/
│   builder.py               - Converts OHLCV to state
│   strategy_loader.py       - Loads YAML config for indicators

executor/
│   exchange_executor.py     - Paper/live mode trading executor

streamlit-ui/
│   app.py                   - Real-time dashboard + explainability

utils/
│   reward.py                - Reward shaping and equity-based logic
│   model_utils.py           - Model versioning, save/load
│   trade_logger.py          - JSON line logger for trades

tests/
│   test_*.py                - Unit tests for each module

deployment/k3s/
│   inference-deployment.yaml
│   inference-service.yaml

configs/
│   strategy.yaml            - Strategy + indicator config

sample_ohlcv.csv            - Sample BTCUSDT test data
README.md                   - This file
.gitignore                  - Excludes logs, models, coverage, etc
pytest.ini                  - Pytest configuration
```

---

## 🪪 License

MIT License — free for personal and commercial use. Attribution appreciated.

---

# ✅ You're Ready to Trade

Whether you're backtesting a strategy, deploying to production, or training a live DQN model — Neurotrade gives you all the tools.

Let us know if you'd like to contribute, extend the agent pool, or scale up with multi-GPU training.

Happy Trading! 🚀

---

## 📋 Business Requirements

Neurotrade is designed to support:
- Real-time cryptocurrency trading decisions at low latency
- Modular plug-and-play agent development (RL + rule-based)
- Configurable and testable strategies using YAML/JSON
- Scalable architecture for training, inference, and visualization
- Seamless switching between paper trading and live mode
- Explainability and auditing per trade decision

---

## 🧠 Architectural Decisions & Rationale

| Decision | Rationale |
|----------|-----------|
| Use of Reinforcement Learning (DQN) | Adaptive to changing market patterns, learns from reward signals |
| Modular multi-agent system | Promotes experimentation, allows rule + AI mix |
| Redis decoupling | Avoids state retention and promotes stateless microservices |
| YAML-configurable strategies | Easy for non-devs to modify indicator settings |
| Use of Streamlit | Lightweight dashboard for real-time and replay visualization |
| Kubernetes-native deployment (K3s) | Supports cloud-native, node-affinity, multi-agent scale-out |

---

## ⚠️ Risks, Assumptions, and Considerations

**Risks**
- Market volatility may render some strategies obsolete
- Overfitting during training can reduce live performance
- Misconfiguration of YAML strategy can silently affect performance

**Assumptions**
- Redis or another message store will be available and low latency
- WebSocket feed (Binance) is stable and responds in near real-time
- Single-symbol inference per pod is sufficient in early iterations

**Considerations**
- Each agent or symbol can be containerized independently
- GPU acceleration is optional and can be node-affinity bound
- Redis is used only for transient data, not long-term storage

---

## 🔄 Fallback Scenarios

| Failure | Fallback |
|---------|----------|
| WebSocket connection drops | Auto reconnect and restore stream |
| No model file on inference | Run in observation-only mode (log signals but no trades) |
| Indicator API fails | Use cached OHLCV or fallback to REST API fetch |
| Inference module crash | Pod auto-restarts with saved state |
| Trainer overwhelmed | Reduce training frequency or decouple experience pushing |

---

## 🔁 System Flow and Component Interaction

1. **Data Ingestion**  
   - Tick or 1min OHLCV from Binance → Redis buffer or direct

2. **Feature Builder**  
   - Converts OHLCV + strategy.yaml → State vector

3. **Agent Layer**  
   - Multiple agents vote using State
   - EnsembleAgent aggregates final signal

4. **Executor**  
   - Executes trade in paper or live mode based on signal

5. **Logger**  
   - Trade decisions and agent votes written to `inference_log.csv`

6. **Streamlit Dashboard**  
   - Reads `inference_log.csv` for visualization
   - Displays equity curve, agent votes, strategy metadata

---

## 🧭 Architectural Diagrams (Markdown Format)

### System Overview

```
+------------------------+
| Binance OHLCV / Tick   |
+-----------+------------+
            |
            v
+------------------------+
| Feature Builder (State)|
+-----------+------------+
            |
            v
+------------------------+
| Ensemble Agent Layer   |
| (RSI, MACD, DQN, etc)  |
+-----------+------------+
            |
            v
+------------------------+
| Trade Executor (OMS)   |
+-----------+------------+
            |
            v
+------------------------+
| Streamlit UI Dashboard |
+------------------------+
```

---

## 🪪 License

MIT License — open for personal and commercial use. Attribution appreciated.
