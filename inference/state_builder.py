from core.decorators.decorators import inject_logger, inject_config
from utils.builder import build_state_from_ticks

@inject_logger()
@inject_config("state_builder.yaml")
class StateBuilder:
    def __init__(self, evaluator_agent, state_tracker, tick_listener, indicator_agents=None):
        self.evaluator = evaluator_agent
        self.state_tracker = state_tracker
        self.tick_listener = tick_listener
        self.indicator_agents = indicator_agents or []

        self.trade_duration_sec = self.config.get("trade_duration_sec", 10.0)
        self.logger.debug(f"📐 Initialized with trade_duration_sec = {self.trade_duration_sec}")

    def build(self):
        ticks = self.tick_listener.get_recent_ticks()
        if not ticks:
            return {}, 0.0, 0

        current_price = ticks[-1]["price"]
        ts = ticks[-1]["timestamp"]

        indicator_outputs = {}
        for agent in self.indicator_agents:
            try:
                result = agent.compute(ticks)
                if isinstance(result, dict):
                    indicator_outputs.update(result)
            except Exception as e:
                self.logger.warning(f"[IndicatorError] {agent.__class__.__name__} failed: {e}")

        state = build_state_from_ticks(
            ticks=ticks,
            current_price=current_price,
            entry_price=self.state_tracker.get_entry_price(),
            position="LONG" if self.state_tracker.get_inventory() > 0 else None,
            drawdown_pct=self._drawdown(),
            inventory=self.state_tracker.get_inventory(),
            cash_balance=self.state_tracker.get_cash(),
            evaluator_feedback=self.evaluator.generate_feedback(),
            trade_duration_sec=self.trade_duration_sec,
            extra_indicators=indicator_outputs
        )

        return state, current_price, ts

    def build_future(self):
        ticks = self.tick_listener.get_recent_ticks()[-15:]
        future_price = ticks[-1]["price"] if ticks else 0.0

        indicator_outputs = {}
        for agent in self.indicator_agents:
            try:
                result = agent.compute(ticks)
                if isinstance(result, dict):
                    indicator_outputs.update(result)
            except Exception as e:
                self.logger.warning(f"[IndicatorError] {agent.__class__.__name__} failed on future: {e}")

        state = build_state_from_ticks(
            ticks=ticks,
            current_price=future_price,
            entry_price=self.state_tracker.get_entry_price(),
            position="LONG" if self.state_tracker.get_inventory() > 0 else None,
            drawdown_pct=self._drawdown(),
            inventory=self.state_tracker.get_inventory(),
            cash_balance=self.state_tracker.get_cash(),
            evaluator_feedback=self.evaluator.generate_feedback(),
            trade_duration_sec=self.trade_duration_sec,
            extra_indicators=indicator_outputs
        )

        return state

    def _drawdown(self):
        cash = self.state_tracker.get_cash()
        initial = self.state_tracker.initial_cash
        return (cash - initial) / max(initial, 1e-8)
