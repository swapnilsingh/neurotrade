### Neurotrade Project Tracker

---

## 🔁 Agile Tracker (Epics, Features, User Stories)

✅ **Updated April 7, 2025** to reflect completed system design, architecture, and folder scaffolding.

### 📦 Epic 1: Strategy Layer + Backtesting (Phase 1)
**Goal**: Build the rule-based strategy engine and integrate with a robust backtesting system.

#### 🔹 Feature 1.1: Define Strategy Rules Engine
- 📝 **User Story 1.1.1**: As a developer, I want to configure BUY/SELL/HOLD logic using JSON/YAML files so that strategies are modular and reusable.
- 📝 **User Story 1.1.2**: As a developer, I want to evaluate indicators like RSI, EMA, MACD from OHLCV data so that strategy logic has a technical basis.

#### 🔹 Feature 1.2: Implement Feature Engineering Pipeline
- 📝 **User Story 1.2.1**: As a developer, I want to extract indicators and store them in Redis/TimescaleDB so they can be reused by downstream components.
- 📝 **User Story 1.2.2**: As a developer, I want to preprocess historical OHLCV and order book data to align timestamps and remove missing values.
- 📝 **User Story 1.2.3**: 🟢As a developer, I want to stream live OHLCV and order book data using Binance's WebSocket API so that the system avoids ccxt.pro licensing costs.
- 📝 **User Story 1.2.4**: 🟢As a developer, I want to push raw OHLCV and order book data to Redis ephemeral queues (TTL 10 seconds) so that the indicator service can consume data in real-time without storage overhead.
- 📝 **User Story 1.2.5**: As a developer, I want the Indicator Service to consume raw data from the ephemeral queue, compute features, and push the results to a separate processed queue for downstream modules.
- 📝 **User Story 1.2.6**: 🟢As a developer, I want each Redis queue to be namespaced by symbol (e.g., `queue:ohlcv:BTC/USDT`) so the system can be scaled to support multiple symbols.
- 📝 **User Story 1.2.7**: 🟢As a developer, I want to maintain a dynamic list of active trading symbols in Redis or config files so that I can easily onboard new assets in the future.

#### 🔹 Feature 1.3: Build Backtesting Framework
- 📝 **User Story 1.3.1**: As a trader, I want to backtest strategies on 1-minute interval data so I can evaluate expected performance.
- 📝 **User Story 1.3.2**: As a developer, I want to simulate trades using position sizing, stop-loss, and take-profit rules to match real trading conditions.
- 📝 **User Story 1.3.3**: As a developer, I want to export metrics (P&L, drawdown, Sharpe ratio) to CSV and visual charts so I can analyze results.

#### 🔹 Feature 1.4: Validate Strategy with Simulated Runs
- 📝 **User Story 1.4.1**: As a developer, I want to run paper trades using past data and compare signals to strategy rules so I can confirm accuracy.
- 📝 **User Story 1.4.2**: As a developer, I want to track trade logs and signals in a readable format for debugging and tuning.

#### 🔹 Feature 1.5: Setup Project Infrastructure
- 📝 **User Story 1.5.1**: 🟢Scaffold base folder structure (ingestion, indicators, etc.).
- 📝 **User Story 1.5.2**: 🟢Add Docker support with `docker-compose.yml`.
- 📝 **User Story 1.5.3**: 🟢Create `.env.template` for runtime configuration.
- 📝 **User Story 1.5.4**: 🟢Add `Makefile` for CI/dev automation commands.
- 📝 **User Story 1.5.5**: 🟢Add `monitoring/` service for alerts, logging, and health.
- 📝 **User Story 1.5.6**: 🟢Setup `docs/` directory for architecture and API specs.

---

## 🧭 Tracker Usage Guidelines

- 🔁 Each **User Story** can be tagged with:
  - 🟢 for completed
  - 🟡 for in progress
  - 🔴 for not started
- 🧩 Only this file contains the full list of **Epics, Features, and User Stories**.
- 📌 Treat this as the **primary tracking and planning document** for all project phases.
- 📁 Use the accompanying **System Design** document to reference architecture, folder structure, Redis keys, and JSON schemas.
- 📅 Activity should be tracked by updating user story status tags and recording relevant commit messages or comments during each development cycle.
- 📂 Use a Git-based commit history or change logs to audit work over time.
- 🔄 Return to this file before each new planning cycle, feature update, or implementation sprint.

---

