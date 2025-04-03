import json
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
class BacktestRunner:
    def __init__(self, config_file, data):
        # Check if config_file is a dictionary
        if isinstance(config_file, dict):
            self.strategy_config = config_file  # If it's a dict, use it directly
        else:
            self.strategy_config = self.load_config(config_file)  # strategy config (from file)

        self.data = data  # historical data (OHLCV)
        self.initial_capital = 10000  # initial capital for backtest
        self.position = 0  # current position (0 = no position)
        self.balance = self.initial_capital  # current balance
        self.equity_curve = []  # Start equity curve as an empty list
        self.trade_logs = []  # list to track trade logs

    def apply_indicators(self):
        """
        This method applies technical indicators like SMA, MACD, RSI, etc.
        based on the strategy configuration.
        """
        # Add SMA (Simple Moving Average)
        self.data['SMA'] = self.data['close'].rolling(window=3).mean()  # 3-day SMA for testing

        # Add MACD (Moving Average Convergence Divergence)
        exp12 = self.data['close'].ewm(span=12, adjust=False).mean()
        exp26 = self.data['close'].ewm(span=26, adjust=False).mean()
        self.data['MACD'] = exp12 - exp26

        # Add RSI (Relative Strength Index)
        delta = self.data['close'].diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

    def execute_strategy(self):
        """
        This method will loop through the historical data, apply the
        strategy logic, and execute buy/sell signals.
        """
        for index, row in self.data.iterrows():
            # Only append to the equity curve after the first iteration
            if index == 0:
                self.equity_curve.append(self.balance)

            # Check if price crosses the SMA and execute buy/sell
            if row['close'] > row['SMA'] and self.position == 0:  # Buy Signal
                self.buy(row['close'], index)
            elif row['close'] < row['SMA'] and self.position > 0:  # Sell Signal
                self.sell(row['close'], index)

            # Track equity curve after each trade
            self.equity_curve.append(self.balance + self.position * row['close'])

    def buy(self, price, date):
        """Simulate a buy order."""
        self.position = self.balance // price  # calculate how many units we can buy
        self.balance -= self.position * price  # deduct the cost from balance
        self.trade_logs.append({'date': date, 'action': 'BUY', 'price': price, 'position': self.position})

    def sell(self, price, date):
        """Simulate a sell order."""
        self.balance += self.position * price  # add the money from selling
        self.trade_logs.append({'date': date, 'action': 'SELL', 'price': price, 'position': 0})
        self.position = 0  # reset position after selling




    
    def load_config(self, config_file):
        """
        Load the strategy config from a JSON or YAML file.
        """
        with open(config_file, 'r') as f:
            if config_file.endswith('.json'):
                return json.load(f)
            elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
                return yaml.safe_load(f)
            else:
                raise ValueError("Unsupported config file format")

    def plot_equity_curve(self):
        """Plot the equity curve over time."""
        plt.plot(self.equity_curve)
        plt.title('Equity Curve')
        plt.xlabel('Time')
        plt.ylabel('Portfolio Value')
        plt.show()

    def generate_report(self):
        """Generate performance report (ROI, Sharpe, etc.)"""
        # For simplicity, we will just print the final equity
        final_equity = self.balance + self.position * self.data.iloc[-1]['close']
        print(f"Final equity: {final_equity}")
        print(f"Total return: {((final_equity - self.initial_capital) / self.initial_capital) * 100:.2f}%")
        print(f"Number of trades: {len(self.trade_logs)}")

        # Additional metrics like Sharpe ratio can be added here
