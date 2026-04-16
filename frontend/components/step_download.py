import streamlit as st


def render():
    st.success("Document successfully generated!")

    if st.session_state.generated_file:
        st.download_button(
            label=f"Download {st.session_state.generated_filename}",
            data=st.session_state.generated_file,
            file_name=st.session_state.generated_filename,
        )

    if st.button("Start Over"):
        st.session_state.step = 0
        st.session_state.template_type = None
        st.session_state.transcribed_text = None
        st.session_state.extracted_fields = None
        st.session_state.generated_file = None
        st.session_state.generated_filename = None
        st.rerun()
