#!/bin/bash

mkdir -p configs

cat <<EOF > configs/logging.yaml
# ... [logging.yaml content here]
EOF

cat <<EOF > configs/inference.yaml
symbol: "btcusdt"
interval: 3
max_candles: 1000
min_ticks_for_state: 3
cooldown:
  enabled: true
EOF

cat <<EOF > configs/ensemble_agent.yaml
window_size: 5
refresh_interval: 300
EOF

cat <<EOF > configs/reward_agent.yaml
use_dynamic_volatility: true
reward_scaling_factor: 1.0
drawdown_penalty_weight: 0.5
EOF

cat <<EOF > configs/evaluator_agent.yaml
short_window: 10
long_window: 100
EOF

cat <<EOF > configs/trainer.yaml
batch_size: 32
gamma: 0.99
epsilon_start: 1.0
epsilon_min: 0.05
epsilon_decay: 0.995
train_after_experiences: 500
mini_batch_size: 64
mini_batch_train_steps: 3
model_save_interval: 500
model_path: "/app/models/model.pt"
EOF

cat <<EOF > configs/streamlit.yaml
refresh_interval_sec: 10
enable_dark_mode: true
display_tabs:
  - summary
  - trades
  - equity
  - sharpe_ratio
  - drawdown
EOF

cat <<EOF > configs/meta_strategy.yaml
agents:
  - RSI
  - MACD
  - PPO
aggregation_method: "majority_vote"
confidence_threshold: 0.6
EOF

cat <<EOF > configs/redis.yaml
host: "redis"
port: 6379
EOF
