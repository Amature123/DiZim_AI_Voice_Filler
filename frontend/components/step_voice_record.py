import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"


def render():
    st.write(f"Template: **{st.session_state.template_type}**")

    audio_file = st.audio_input("Record or upload audio file:")

    if audio_file:
        with st.spinner("Transcribing audio to text..."):
            try:
                filename = getattr(audio_file, "name", "recording.wav")
                files = {"audio": (filename, audio_file, "audio/wav")}
                resp = requests.post(f"{BACKEND_URL}/api/transcribe", files=files, timeout=60)
                if resp.status_code == 200:
                    st.session_state.transcribed_text = resp.json()["text"]
                    st.success("Audio transcription successful!")
                else:
                    st.error(f"Error: {resp.text}")
            except Exception as e:
                st.error(f"Cannot connect to backend: {e}")

    if st.session_state.transcribed_text:
        st.text_area("Transcribed text:", value=st.session_state.transcribed_text, height=150)

        if st.button("Continue - Extract fields"):
            with st.spinner("Extracting fields from text..."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/api/extract",
                        json={
                            "text": st.session_state.transcribed_text,
                            "templateType": st.session_state.template_type,
                        },
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        st.session_state.extracted_fields = resp.json()["fields"]
                        st.session_state.step = 2
                        st.rerun()
                    else:
                        st.error(f"Error: {resp.text}")
                except Exception as e:
                    st.error(f"Cannot connect to backend: {e}")

    if st.button("Back"):
        st.session_state.step = 0
        st.rerun()
