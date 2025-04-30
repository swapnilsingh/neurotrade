from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/trade_executor.yaml")
class TradeExecutor:
    def __init__(self, state_tracker, config=None):
        self.state_tracker = state_tracker
        self.config = config or {}
        self.trade_fee_rate = self.config.get("trade_fee_rate", 0.001)
        self.slippage_rate = self.config.get("slippage_rate", 0.0005)

    def execute(self, signal, current_price, quantity):
        reason = "HOLD (no action)"
        inventory = self.state_tracker.get_inventory()
        cash = self.state_tracker.get_cash()
        entry_price = self.state_tracker.get_entry_price()

        if signal == "BUY":
            cost = current_price * quantity * (1 + self.slippage_rate)
            total_cost = cost + cost * self.trade_fee_rate
            if cash >= total_cost:
                total_value = entry_price * inventory + current_price * quantity
                inventory += quantity
                new_entry_price = total_value / max(inventory, 1e-8)
                cash -= total_cost

                self.state_tracker.update_position(
                    cash=cash,
                    inventory=inventory,
                    entry_price=new_entry_price,
                    realized_profit=0.0
                )
                reason = f"Bought {quantity:.6f} BTC at {current_price:.2f}"
            else:
                reason = "Skipped BUY - Insufficient Cash"

        elif signal == "SELL" and inventory > 0:
            sell_qty = min(quantity, inventory)
            gross_revenue = current_price * sell_qty * (1 - self.slippage_rate)
            net_revenue = gross_revenue - gross_revenue * self.trade_fee_rate
            realized = (current_price - entry_price) * sell_qty
            cash += net_revenue
            inventory -= sell_qty
            new_entry_price = entry_price if inventory > 0 else 0.0

            self.state_tracker.update_position(
                cash=cash,
                inventory=inventory,
                entry_price=new_entry_price,
                realized_profit=realized
            )
            reason = f"Sold {sell_qty:.6f} BTC at {current_price:.2f} | Realized {realized:.2f}"

        self.logger.debug(f"[Trade Execution] {reason}")
        return reason
