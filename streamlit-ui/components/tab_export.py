def render_export_tab(tab, data, redis_client):
    import io, json, zipfile
    from datetime import datetime
    import pandas as pd
    import streamlit as st

    with tab:
        st.subheader("Data Export")
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("File Format", ["CSV", "JSON", "Parquet"])
            date_range = st.date_input("Date Range", [])
        with col2:
            available_columns = data.get("available_columns", [])
            default_columns = data.get("default_columns", [])
            selected_columns = st.multiselect(
                "Columns",
                options=available_columns,
                default=default_columns
            )
            include_debug = st.checkbox("Include Debug Info")

        if st.button("📦 Generate Export Package"):
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as z:
                try:
                    signals_export = data["signals_df"]
                    if date_range and len(date_range) == 2:
                        signals_export = signals_export[
                            (signals_export['datetime'].dt.date >= date_range[0]) &
                            (signals_export['datetime'].dt.date <= date_range[1])
                        ]
                    if selected_columns:
                        signals_export = signals_export[selected_columns]

                    if export_format == "CSV":
                        z.writestr("signals.csv", signals_export.to_csv(index=False))
                    elif export_format == "JSON":
                        z.writestr("signals.json", signals_export.to_json(orient="records"))
                    elif export_format == "Parquet":
                        z.writestr("signals.parquet", signals_export.to_parquet())

                    if include_debug:
                        debug_data = {
                            "redis_info": redis_client.info(),
                            "data_stats": {
                                "signals": signals_export.shape,
                                "experience": len(data.get("experience", []))
                            }
                        }
                        z.writestr("debug_info.json", json.dumps(debug_data))

                    st.success("Export package created successfully!")

                except Exception as e:
                    st.error(f"Export failed: {str(e)}")

            st.download_button(
                label="⬇️ Download Export",
                data=buffer.getvalue(),
                file_name=f"neurotrade_export_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip"
            )
