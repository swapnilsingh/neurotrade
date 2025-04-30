# inference/state_tracker.py

from core.decorators.decorators import inject_logger, inject_config

@inject_logger()
@inject_config("configs/state_tracker.yaml")
class StateTracker:
    def __init__(self, config=None):
        self.initial_cash = self.config.get("initial_cash", 1000.0)
        self.trade_fee_rate = self.config.get("trade_fee_rate", 0.001)
        self.slippage_rate = self.config.get("slippage_rate", 0.0005)

        self.cash = self.initial_cash
        self.inventory = 0.0
        self.entry_price = 0.0
        self.realized_profit = 0.0

        self.logger.debug(f"Initialized with cash={self.cash}, fee={self.trade_fee_rate}, slippage={self.slippage_rate}")

    def get_cash(self):
        return self.cash

    def get_inventory(self):
        return self.inventory

    def get_entry_price(self):
        return self.entry_price

    def get_realized_profit(self):
        return self.realized_profit

    def update_after_buy(self, price, qty):
        """Update internal state after a buy order."""
        cost = price * qty * (1 + self.slippage_rate)
        total_cost = cost + cost * self.trade_fee_rate
        if self.cash >= total_cost:
            prev_value = self.entry_price * self.inventory
            self.inventory += qty
            self.entry_price = (prev_value + price * qty) / max(self.inventory, 1e-8)
            self.cash -= total_cost
            self.logger.debug(f"BUY: qty={qty}, price={price}, new_cash={self.cash}, new_entry={self.entry_price}")
            return f"Bought {qty:.6f} BTC at {price:.2f}"
        return "Skipped BUY - Insufficient Cash"

    def update_after_sell(self, price, qty):
        """Update internal state after a sell order."""
        sell_qty = min(qty, self.inventory)
        revenue = price * sell_qty * (1 - self.slippage_rate)
        net_revenue = revenue - revenue * self.trade_fee_rate
        realized = (price - self.entry_price) * sell_qty

        self.cash += net_revenue
        self.inventory -= sell_qty
        self.realized_profit += realized

        if self.inventory == 0:
            self.entry_price = 0.0

        self.logger.debug(f"SELL: qty={sell_qty}, price={price}, cash={self.cash}, realized_pnl={realized}")
        return f"Sold {sell_qty:.6f} BTC at {price:.2f} | Realized PnL: {realized:.2f}"
    
    def update_position(self, cash, inventory, entry_price, realized_profit=0.0):
        self.cash = cash
        self.inventory = inventory
        self.entry_price = entry_price
        self.realized_profit += realized_profit
        self.logger.debug(f"[State Updated] 💰 Cash={self.cash}, 🧮 Inventory={self.inventory}, 🎯 Entry={self.entry_price}, 📈 Realized={self.realized_profit}")

