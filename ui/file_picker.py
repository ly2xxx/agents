import streamlit as st
from PIL import Image

def render_file_picker(support_types):
    with st.sidebar:
        uploaded_files = []
        num_files = st.number_input("Pick your file(s) - files for Retrieval Augmented Query", min_value=1, value=1, step=1, key="num_files")
        for i in range(num_files):
            file = st.file_uploader(f"Choose file {i+1}", type=support_types, key=f"file_{i}")
            if file:
                uploaded_files.append(file)
                # Add thumbnail preview for PNG and JPG files
                if file.type == "image/png" or file.type == "image/jpeg" or file.name.lower().endswith(('.jpg', '.jpeg')):
                    image = Image.open(file)
                    # Create thumbnail with max size 100x100 while maintaining aspect ratio
                    image.thumbnail((100, 100))
                    st.image(image, caption=f"Preview of {file.name}")
    return uploaded_files