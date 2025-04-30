import torch
from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/signal_decider.yaml")
class SignalDecider:
    def __init__(self):
        self.action_space = self.config.get("action_space", ["BUY", "SELL", "HOLD"])
        self.default_quantity = self.config.get("default_dynamic_quantity", 0.001)
        self.default_take_profit = self.config.get("default_take_profit", 0.01)
        self.fallback_action = self.config.get("fallback_action", "HOLD")

    def decide(self, q_values: torch.Tensor):
        try:
            action_idx = torch.argmax(q_values, dim=1).item()
            if action_idx >= len(self.action_space):
                raise ValueError(f"Invalid action index: {action_idx}")

            signal = self.action_space[action_idx]
            quantity = self.default_quantity if signal != "HOLD" else 0.0
            take_profit = self.default_take_profit if signal != "HOLD" else 0.0
            reason = f"Model suggests {signal}"

            self.logger.debug(f"[Decision] Q-values: {q_values.tolist()} → {signal}")
            return signal, [signal], quantity, take_profit, reason

        except Exception as e:
            self.logger.exception(f"❌ Failed to decide signal: {e}")
            return self.fallback_action, [self.fallback_action], 0.0, 0.0, f"Fallback: {self.fallback_action}"
