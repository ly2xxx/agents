import streamlit as st

def render_file_picker(support_types):
    uploaded_files = []
    num_files = st.number_input("Pick your file(s) - files for Retrieval Augmented Query", min_value=1, value=1, step=1)
    for i in range(num_files):
        file = st.file_uploader(f"Choose file {i+1}", type=support_types, key=f"file_{i}")
        if file:
            uploaded_files.append(file)
    return uploaded_files
