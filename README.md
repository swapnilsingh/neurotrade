# 🧠 Neurotrade

> **Modular. Scalable. AI-Powered.**

[![License](https://img.shields.io/github/license/swapnilsingh/neurotrade)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/swapnilsingh/neurotrade/ci-cd.yml)](https://github.com/swapnilsingh/neurotrade/actions)

---

## 📌 Overview

**Neurotrade** is a modular, scalable, AI-powered cryptocurrency trading framework. It supports real-time data ingestion, feature engineering, configurable rule-based or AI-driven strategies, and streamlined deployment using Docker and Kubernetes.

---

## 🚀 Features

- Real-time OHLCV crypto data ingestion via CCXT
- Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Configurable strategies using JSON or YAML
- AI agent integration (LSTM, XGBoost)
- Streamlit-based visualization and backtesting dashboard
- Docker + Kubernetes deployment ready
- CI/CD pipeline using GitHub Actions

---

## 🏗️ Project Structure

```bash
neurotrade/
├── data/                # Raw and processed market data
├── src/                 # Core source code (modular components)
├── models/              # Trained ML models
├── tests/               # Unit and integration tests
├── configs/             # Strategy and system configs
├── notebooks/           # Research and experimentation
├── docs/                # Project documentation
├── scripts/             # Utility scripts
├── logs/                # Runtime logs
├── Dockerfile           # Container build file
├── docker-compose.yml   # Local container orchestration
├── requirements.txt     # Python dependencies
└── README.md            # Project info (this file)
```

---

## ⚙️ Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/swapnilsingh/neurotrade.git
cd neurotrade
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Dashboard
```bash
streamlit run src/app.py
```

---

## 🐳 Docker Setup

### Local Container Run
```bash
docker-compose up -d --build
```

---

## ☸️ Kubernetes Deployment

Apply manifests from the `k8s/` directory:
```bash
kubectl apply -f k8s/
```

---

## 🧪 Running Tests
```bash
pytest tests/
```

---

## 📚 Documentation

Complete documentation is available in the `docs/` directory:
- [Overview](docs/overview.md)
- [Architecture](docs/architecture.md)
- [Setup](docs/setup.md)
- [Usage](docs/usage.md)
- [API Reference](docs/api.md)
- [Modules](docs/modules.md)
- [Testing](docs/testing.md)
- [Deployment](docs/deployment.md)
- [Contributing](docs/contributing.md)

---

## 🤝 Contributing
We welcome contributions! See [CONTRIBUTING.md](docs/contributing.md) for guidelines.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

