import streamlit as st


def render():
    template = st.radio(
        "Select document type:",
        options=[
            ("VAT Invoice", "hoa-don-gtgt"),
            ("Personal Income Tax Return", "to-khai-tncn"),
        ],
        format_func=lambda x: x[0],
        index=0,
    )

    if st.button("Continue"):
        st.session_state.template_type = template[1]
        st.session_state.step = 1
        st.rerun()
