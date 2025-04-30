# dashboard/components/utils.py

import numpy as np

def calculate_sharpe(df, risk_free=0.0):
    """Calculate Sharpe ratio with error handling"""
    try:
        if df.empty or 'portfolio_value' not in df.columns:
            return 0.0
        returns = df['portfolio_value'].pct_change().dropna()
        return (returns.mean() - risk_free) / returns.std() if returns.std() != 0 else 0.0
    except Exception:
        return 0.0

def calculate_sortino(df, risk_free=0.0):
    """Calculate Sortino ratio with error handling"""
    try:
        if df.empty or 'portfolio_value' not in df.columns:
            return 0.0
        returns = df['portfolio_value'].pct_change().dropna()
        downside = returns[returns < 0].std()
        return (returns.mean() - risk_free) / downside if downside != 0 else 0.0
    except Exception:
        return 0.0

def calculate_var(df, confidence=0.95):
    """Calculate Value at Risk with error handling"""
    try:
        if df.empty or 'portfolio_value' not in df.columns:
            return 0.0
        returns = df['portfolio_value'].pct_change().dropna()
        return abs(returns.quantile(1 - confidence)) * 100
    except Exception:
        return 0.0