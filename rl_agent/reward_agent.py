import numpy as np
from utils.reward import compute_reward_from_ticks
class RewardAgent:
    def __init__(self, evaluator_agent, use_dynamic_volatility=True):
        self.evaluator_agent = evaluator_agent
        self.use_dynamic_volatility = use_dynamic_volatility

    def compute(self, ticks, signal, quantity, current_price, entry_price, position, inventory_ratio):
        

        # Base reward purely from price movement
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

        # 🚀 Add exploration reward for non-HOLD actions
        exploration_bonus = 0.001 if signal in ["BUY", "SELL"] else 0.0

        # 🛠️ Final shaped reward
        shaped_reward = (base_reward + exploration_bonus)
        shaped_reward *= feedback.get("reward_bonus_booster", 1.0)
        shaped_reward /= feedback.get("penalty_aggressiveness", 1.0)

        reward_info = {
            "base_reward": base_reward,
            "exploration_bonus": exploration_bonus,
            "shaped_reward": shaped_reward,
            "sharpe_ratio_hint": feedback.get("sharpe_ratio_hint", 0.0),
            "drawdown_hint": feedback.get("drawdown_hint", 0.0),
            "reward_bonus_booster": feedback.get("reward_bonus_booster", 1.0),
            "penalty_aggressiveness": feedback.get("penalty_aggressiveness", 1.0)
        }

        return shaped_reward, reward_info

