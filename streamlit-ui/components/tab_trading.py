# components/trade_performance.py

import streamlit as st
import pandas as pd
from components.utils import calculate_sharpe

def render_trade_performance_tab(tab, data):
    with tab:
        st.subheader("📈 Trade Performance")

        signals_df = data.get("signals_df", pd.DataFrame())

        if 'signal' in signals_df.columns and 'ind_drawdown_pct' in signals_df.columns:
            trades = signals_df[signals_df['signal'].isin(['BUY', 'SELL'])]

            if not trades.empty:
                cols = st.columns(5)
                cols[0].metric("Total Trades", len(trades))
                cols[1].metric("Win Rate", f"{(len(trades[trades['ind_drawdown_pct'] > 0]) / len(trades) * 100):.1f}%")
                cols[2].metric("Avg Profit", f"{trades['ind_drawdown_pct'].mean() * 100:.2f}%")
                cols[3].metric("Max Drawdown", f"{signals_df['ind_drawdown_pct'].min() * 100:.2f}%")
                cols[4].metric("Sharpe Ratio", f"{calculate_sharpe(signals_df):.2f}")
            else:
                st.warning("No executed trades found.")
        else:
            st.info("Insufficient trade data to compute metrics.")
