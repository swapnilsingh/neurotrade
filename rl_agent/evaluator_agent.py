# rl_agent/evaluator_agent.py

import numpy as np

class EvaluatorAgent:
    def __init__(self, short_window=10, long_window=100):
        """
        Initialize the Evaluator Agent.

        Parameters:
        - short_window: number of recent trades for short-term feedback
        - long_window: number of trades for long-term trend evaluation
        """
        self.short_window = short_window
        self.long_window = long_window

        # 🗂️ History Buffers
        self.trade_pnls = []
        self.portfolio_values = []
        self.trade_durations = []
        self.trade_volatilities = []
        self.slippage_costs = []
        self.fee_costs = []

    def record_trade(self, realized_pnl, portfolio_value, trade_duration_sec, volatility_at_trade, slippage_cost=0.0, fee_cost=0.0):
        """
        Record the outcome of a trade.

        Parameters:
        - realized_pnl: profit or loss from the trade
        - portfolio_value: portfolio value after trade
        - trade_duration_sec: how long the trade was held
        - volatility_at_trade: volatility when trade occurred
        - slippage_cost: cost from slippage
        - fee_cost: trading fee cost
        """
        self.trade_pnls.append(realized_pnl)
        self.portfolio_values.append(portfolio_value)
        self.trade_durations.append(trade_duration_sec)
        self.trade_volatilities.append(volatility_at_trade)
        self.slippage_costs.append(slippage_cost)
        self.fee_costs.append(fee_cost)

        # 🧹 Maintain history sizes
        self._trim_buffers()

    def _trim_buffers(self):
        buffers = [
            self.trade_pnls,
            self.portfolio_values,
            self.trade_durations,
            self.trade_volatilities,
            self.slippage_costs,
            self.fee_costs
        ]
        for buffer in buffers:
            if len(buffer) > self.long_window:
                buffer.pop(0)

    def generate_feedback(self):
        """
        Analyze the history and generate feedback for the RL agent.

        Returns:
        A dictionary of dynamic tuning hints.
        """
        if len(self.trade_pnls) < 2:
            return self._default_feedback()

        # --- Compute Short-Term Metrics ---
        recent_pnls = self.trade_pnls[-self.short_window:]
        avg_pnl = np.mean(recent_pnls)
        win_rate = np.mean([1 if pnl > 0 else 0 for pnl in recent_pnls])

        avg_duration = np.mean(self.trade_durations[-self.short_window:]) if self.trade_durations else 0.0
        avg_slippage = np.mean(self.slippage_costs[-self.short_window:]) if self.slippage_costs else 0.0
        avg_fee = np.mean(self.fee_costs[-self.short_window:]) if self.fee_costs else 0.0

        volatility_success_rate = self._calculate_volatility_success()

        # --- Compute Risk Metrics ---
        max_portfolio = max(self.portfolio_values) if self.portfolio_values else 1
        current_portfolio = self.portfolio_values[-1] if self.portfolio_values else 1
        drawdown = (max_portfolio - current_portfolio) / max(max_portfolio, 1e-8)

        sharpe_ratio = self._calculate_sharpe_ratio()

        # --- Final Feedback Dictionary ---
        feedback = {
            "reward_bonus_booster": 1.0 + min(max(avg_pnl, 0.0), 0.01) * 10,
            "penalty_aggressiveness": 1.0 + drawdown * 5,
            "win_rate_hint": win_rate,
            "drawdown_hint": drawdown,
            "average_trade_duration_sec": avg_duration,
            "average_slippage_cost": avg_slippage,
            "average_fee_cost": avg_fee,
            "volatility_success_rate": volatility_success_rate,
            "sharpe_ratio_hint": sharpe_ratio
        }

        return feedback

    def _default_feedback(self):
        """
        Provide neutral feedback if insufficient data.
        """
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
        """
        Measure how well the agent handles volatility.
        """
        if not self.trade_pnls or not self.trade_volatilities:
            return 0.5

        successes = []
        for pnl, vol in zip(self.trade_pnls[-self.short_window:], self.trade_volatilities[-self.short_window:]):
            if vol > 0.002:  # define high volatility
                if pnl > 0:
                    successes.append(1)
                else:
                    successes.append(0)

        return np.mean(successes) if successes else 0.5

    def _calculate_sharpe_ratio(self):
        """
        Calculate a simple Sharpe Ratio.
        """
        if len(self.portfolio_values) < 2:
            return 0.0

        returns = np.diff(self.portfolio_values) / np.maximum(self.portfolio_values[:-1], 1e-8)
        avg_return = np.mean(returns)
        return_std = np.std(returns)

        if return_std == 0:
            return 0.0

        sharpe_ratio = (avg_return / return_std) * np.sqrt(252)  # Assuming daily returns
        return sharpe_ratio
