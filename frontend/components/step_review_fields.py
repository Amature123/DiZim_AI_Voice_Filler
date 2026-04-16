import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"


def render():
    st.write("Edit extracted information:")

    fields = st.session_state.extracted_fields
    if not fields:
        st.warning("No fields to display")
        return

    # Display as editable key-value pairs
    keys = list(fields.keys())
    values = [fields[k] for k in keys]

    edited = st.data_editor(
        {"Field": keys, "Value": values},
        column_config={
            "Field": st.column_config.TextColumn(disabled=True),
            "Value": st.column_config.TextColumn(),
        },
        hide_index=True,
        num_rows="fixed",
    )

    # Convert back to dict
    updated_fields = {row["Field"]: row["Value"] for _, row in edited.iterrows()}

    # Convert numeric strings back to numbers
    for k, v in updated_fields.items():
        if isinstance(v, str):
            try:
                updated_fields[k] = int(v)
            except ValueError:
                try:
                    updated_fields[k] = float(v)
                except ValueError:
                    pass

    st.session_state.extracted_fields = updated_fields

    col1, col2 = st.columns(2)
    with col1:
        fmt = st.radio("Format:", options=["docx", "pdf"], horizontal=True)
        st.session_state.download_format = fmt

    with col2:
        if st.button("Generate Document"):
            with st.spinner("Generating document..."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/api/generate-doc",
                        json={
                            "fields": updated_fields,
                            "templateType": st.session_state.template_type,
                            "format": fmt,
                        },
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        st.session_state.generated_file = resp.content
                        ext = "pdf" if fmt == "pdf" else "docx"
                        st.session_state.generated_filename = f"{st.session_state.template_type}.{ext}"
                        st.session_state.step = 3
                        st.rerun()
                    else:
                        st.error(f"Error: {resp.text}")
                except Exception as e:
                    st.error(f"Cannot connect to backend: {e}")

    if st.button("Back"):
        st.session_state.step = 1
        st.rerun()
