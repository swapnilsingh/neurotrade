from core.decorators.decorators import inject_logger, inject_config
from utils.reward import compute_reward_from_ticks

@inject_logger()
@inject_config("configs/reward_agent.yaml")
class RewardAgent:
    def __init__(self, evaluator_agent):
        self.evaluator_agent = evaluator_agent
        self.use_dynamic_volatility = self.config.get("use_dynamic_volatility", True)
        self.exploration_bonus = self.config.get("exploration_bonus", 0.001)
        self.default_reward_bonus_booster = self.config.get("default_reward_bonus_booster", 1.0)
        self.default_penalty_aggressiveness = self.config.get("default_penalty_aggressiveness", 1.0)

        self.logger.debug(f"🔧 RewardAgent config: {self.config}")

    def compute(self, ticks, signal, quantity, current_price, entry_price, position, inventory_ratio):
        base_reward = compute_reward_from_ticks(
            ticks=ticks,
            signal=signal,
            quantity=quantity,
            current_price=current_price,
            entry_price=entry_price,
            position=position,
            use_dynamic_volatility=self.use_dynamic_volatility,
            inventory_ratio=inventory_ratio
        )

        feedback = self.evaluator_agent.generate_feedback()
        bonus = self.exploration_bonus if signal in ["BUY", "SELL"] else 0.0

        shaped_reward = (base_reward + bonus)
        shaped_reward *= feedback.get("reward_bonus_booster", self.default_reward_bonus_booster)
        shaped_reward /= feedback.get("penalty_aggressiveness", self.default_penalty_aggressiveness)

        self.logger.debug(
            f"[RewardAgent] Reward={shaped_reward:.5f}, Base={base_reward:.5f}, Bonus={bonus:.4f}, "
            f"Booster={feedback.get('reward_bonus_booster')}, Penalty={feedback.get('penalty_aggressiveness')}"
        )
        return shaped_reward, feedback

