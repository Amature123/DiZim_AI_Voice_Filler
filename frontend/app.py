import streamlit as st
import requests

st.set_page_config(page_title="DiZim AI Financial Assistant", layout="wide")

st.title("DiZim AI Financial Assistant")

# Sidebar - History
with st.sidebar:
    st.header("History")
    try:
        resp = requests.get("http://localhost:8000/api/history")
        if resp.status_code == 200:
            docs = resp.json()
            if docs:
                for doc in docs[:10]:
                    with st.expander(f"{doc['template_id']} - {doc['created_at'][:10]}"):
                        st.write(f"ID: {doc['id'][:8]}...")
                        st.write(f"File: {doc.get('output_path', 'N/A')}")
            else:
                st.info("No documents yet")
        else:
            st.warning("Cannot connect to backend")
    except Exception:
        st.warning("Backend not started (localhost:8000)")

# State initialization
if "step" not in st.session_state:
    st.session_state.step = 0
if "template_type" not in st.session_state:
    st.session_state.template_type = None
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = None
if "extracted_fields" not in st.session_state:
    st.session_state.extracted_fields = None
if "generated_file" not in st.session_state:
    st.session_state.generated_file = None
if "generated_filename" not in st.session_state:
    st.session_state.generated_filename = None

# Steps
steps = ["Select Template", "Record Voice", "Review", "Download"]

# Progress bar
st.progress((st.session_state.step + 1) / 4)
st.caption(f"Step {st.session_state.step + 1}/4: {steps[st.session_state.step]}")

if st.session_state.step == 0:
    from components.step_select_template import render
    render()
elif st.session_state.step == 1:
    from components.step_voice_record import render
    render()
elif st.session_state.step == 2:
    from components.step_review_fields import render
    render()
elif st.session_state.step == 3:
    from components.step_download import render
    render()
