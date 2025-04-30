def render_portfolio_tab(tab, data):
    from components.utils import calculate_sharpe
    import pandas as pd
    import streamlit as st

    with tab:
        summary = data.get("summary", {})
        signals_df = data.get("signals_df", pd.DataFrame())

        if summary or not signals_df.empty:
            cols = st.columns(4)
            cols[0].metric("Total Value", f"${summary.get('portfolio_value', 0):,.2f}")
            cols[1].metric("ROI", f"{summary.get('return_pct', 0):.2f}%")
            cols[2].metric("Available Cash", f"${summary.get('cash', 0):,.2f}")
            cols[3].metric("BTC Holdings", f"{summary.get('inventory_btc', 0):,.6f}")

            if 'portfolio_value' in signals_df.columns:
                st.subheader("Equity Curve")
                st.line_chart(signals_df.set_index('datetime')['portfolio_value'])

            if 'signal' in signals_df.columns and 'ind_drawdown_pct' in signals_df.columns:
                trades = signals_df[signals_df['signal'].isin(['BUY', 'SELL'])]
                if not trades.empty:
                    st.subheader("Trade Performance")
                    cols = st.columns(5)
                    cols[0].metric("Total Trades", len(trades))
                    cols[1].metric("Win Rate", f"{(len(trades[trades['ind_drawdown_pct'] > 0]) / len(trades) * 100):.1f}%")
                    cols[2].metric("Avg Profit", f"{trades['ind_drawdown_pct'].mean() * 100:.2f}%")
                    cols[3].metric("Max Drawdown", f"{signals_df['ind_drawdown_pct'].min() * 100:.2f}%")
                    cols[4].metric("Sharpe Ratio", f"{calculate_sharpe(signals_df):.2f}")
        else:
            st.info("Portfolio summary unavailable")
