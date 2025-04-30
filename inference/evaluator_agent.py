import numpy as np
from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/evaluator_agent.yaml")
class EvaluatorAgent:
    def __init__(self):
        self.short_window = self.config.get("short_window", 10)
        self.long_window = self.config.get("long_window", 100)

        # 🗂️ History Buffers
        self.trade_pnls = []
        self.portfolio_values = []
        self.trade_durations = []
        self.trade_volatilities = []
        self.slippage_costs = []
        self.fee_costs = []

        self.logger.debug(f"🧠 EvaluatorAgent initialized with short={self.short_window}, long={self.long_window}")

    def record_trade(self, realized_pnl, portfolio_value, trade_duration_sec, volatility_at_trade, slippage_cost=0.0, fee_cost=0.0):
        self.trade_pnls.append(realized_pnl)
        self.portfolio_values.append(portfolio_value)
        self.trade_durations.append(trade_duration_sec)
        self.trade_volatilities.append(volatility_at_trade)
        self.slippage_costs.append(slippage_cost)
        self.fee_costs.append(fee_cost)
        self._trim_buffers()

    def _trim_buffers(self):
        for buf in [self.trade_pnls, self.portfolio_values, self.trade_durations,
                    self.trade_volatilities, self.slippage_costs, self.fee_costs]:
            while len(buf) > self.long_window:
                buf.pop(0)

    def generate_feedback(self):
        if len(self.trade_pnls) < 2:
            return self._default_feedback()

        recent_pnls = self.trade_pnls[-self.short_window:]
        win_rate = np.mean([1 if pnl > 0 else 0 for pnl in recent_pnls])
        avg_pnl = np.mean(recent_pnls)
        avg_duration = np.mean(self.trade_durations[-self.short_window:]) if self.trade_durations else 0.0
        avg_slippage = np.mean(self.slippage_costs[-self.short_window:]) if self.slippage_costs else 0.0
        avg_fee = np.mean(self.fee_costs[-self.short_window:]) if self.fee_costs else 0.0
        volatility_success = self._calculate_volatility_success()
        sharpe_ratio = self._calculate_sharpe_ratio()

        max_value = max(self.portfolio_values or [1])
        current_value = self.portfolio_values[-1] if self.portfolio_values else 1
        drawdown = (max_value - current_value) / max(max_value, 1e-8)

        feedback = {
            "reward_bonus_booster": 1.0 + min(max(avg_pnl, 0.0), 0.01) * 10,
            "penalty_aggressiveness": 1.0 + drawdown * 5,
            "win_rate_hint": win_rate,
            "drawdown_hint": drawdown,
            "average_trade_duration_sec": avg_duration,
            "average_slippage_cost": avg_slippage,
            "average_fee_cost": avg_fee,
            "volatility_success_rate": volatility_success,
            "sharpe_ratio_hint": sharpe_ratio
        }

        self.logger.debug(f"[EvaluatorAgent] Feedback: {feedback}")
        return feedback

    def _default_feedback(self):
        return {
            "reward_bonus_booster": 1.0,
            "penalty_aggressiveness": 1.0,
            "win_rate_hint": 0.5,
            "drawdown_hint": 0.0,
            "average_trade_duration_sec": 0.0,
            "average_slippage_cost": 0.0,
            "average_fee_cost": 0.0,
            "volatility_success_rate": 0.5,
            "sharpe_ratio_hint": 0.0
        }

    def _calculate_volatility_success(self):
        if not self.trade_pnls or not self.trade_volatilities:
            return 0.5
        pairs = zip(self.trade_pnls[-self.short_window:], self.trade_volatilities[-self.short_window:])
        return np.mean([1 for pnl, vol in pairs if pnl > 0 and vol > 0.002]) or 0.5

    def _calculate_sharpe_ratio(self):
        if len(self.portfolio_values) < 2:
            return 0.0
        returns = np.diff(self.portfolio_values) / np.maximum(self.portfolio_values[:-1], 1e-8)
        return_std = np.std(returns)
        return (np.mean(returns) / return_std) * np.sqrt(252) if return_std else 0.0
