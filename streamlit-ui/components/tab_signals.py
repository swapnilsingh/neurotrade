# dashboard/components/tab_signals.py

def render_signals_tab(tab, data):
    import plotly.graph_objects as go
    import streamlit as st
    with tab:
        df = data.get("signals_df", None)
        if df is not None and not df.empty:
            latest = df.iloc[0]
            cols = st.columns(4)
            cols[0].metric("Price", f"${latest.get('price', 0):,.2f}")
            cols[1].metric("Signal", latest.get('signal', 'N/A'))
            cols[2].metric("Model", latest.get('model_version', 'v2'))
            cols[3].metric("Confidence", f"{latest.get('ind_band_position', 0)*100:.1f}%")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['datetime'], y=df['price'], mode='lines', name='Price'))

            buys = df[df['signal'] == 'BUY']
            sells = df[df['signal'] == 'SELL']

            if not buys.empty:
                fig.add_trace(go.Scatter(x=buys['datetime'], y=buys['price'], mode='markers', name='BUY'))
            if not sells.empty:
                fig.add_trace(go.Scatter(x=sells['datetime'], y=sells['price'], mode='markers', name='SELL'))

            fig.update_layout(height=500, xaxis_title='Time', yaxis_title='Price (USD)')
            st.plotly_chart(fig, use_container_width=True)

            cols = st.columns(3)
            cols[0].metric("Total Buys", len(buys))
            cols[1].metric("Total Sells", len(sells))
            cols[2].metric("Signal Frequency", f"{len(df)/((df['datetime'].max() - df['datetime'].min()).total_seconds()/3600):.1f}/hour" if len(df) > 1 else "N/A")
        else:
            st.warning("No trading signals found")