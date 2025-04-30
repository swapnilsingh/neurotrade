# components/system_health.py

def render_system_health_tab(tab, ctx):
    import streamlit as st
    try:
        info = ctx.r.info()  # ✅ Corrected
        cols = st.columns(3)
        cols[0].metric("Memory Usage", info['used_memory_human'])
        cols[1].metric("Connected Clients", info['connected_clients'])
        cols[2].metric("Operations", info['total_commands_processed'])
        st.progress(info['used_memory'] / info['total_system_memory'], text="Memory Utilization")
    except Exception as e:
        st.error(f"System metrics unavailable: {str(e)}")
