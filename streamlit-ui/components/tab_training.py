import streamlit as st
def render_training_tab(tab, data):
    import pandas as pd
    with tab:
        if data.get("experience"):
            exp_df = pd.DataFrame(data["experience"])
            cols = st.columns(3)
            cols[0].metric("Experience Buffer", len(exp_df))
            cols[1].metric("Avg Reward", f"{exp_df.get('reward', 0).mean():.2f}")
            cols[2].metric("Max Reward", f"{exp_df.get('reward', 0).max():.2f}")
            st.subheader("Reward Distribution")
            st.bar_chart(exp_df['reward'].value_counts(bins=10))
        else:
            st.warning("Training buffer empty")