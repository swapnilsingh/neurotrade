# inference/reward_evaluator.py

from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/reward_evaluator.yaml")
class RewardEvaluator:
    def __init__(self, reward_agent, tick_listener, state_tracker):
        self.reward_agent = reward_agent
        self.tick_listener = tick_listener
        self.state_tracker = state_tracker

    def compute(self, current_price, signal, quantity):
        ticks = self.tick_listener.get_recent_ticks()[-15:]
        inventory_value = self.state_tracker.get_inventory() * current_price
        portfolio_value = self.state_tracker.get_cash() + inventory_value
        inventory_ratio = inventory_value / max(portfolio_value, 1e-8)

        reward, info = self.reward_agent.compute(
            ticks=ticks,
            signal=signal,
            quantity=quantity,
            current_price=current_price,
            entry_price=self.state_tracker.get_entry_price(),
            position=self.state_tracker.get_inventory(),
            inventory_ratio=inventory_ratio
        )

        self.logger.debug(f"✅ Reward Evaluated: {reward} | Info: {info}")
        return reward
