import streamlit as st
from PIL import Image
import fitz  # PyMuPDF for PDF previews
import pandas as pd
import io

def render_file_picker(support_types):
    with st.sidebar:
        uploaded_files = []
        num_files = st.number_input("Pick your file(s) - files for Retrieval Augmented Query", min_value=1, value=1, step=1, key="num_files")
        for i in range(num_files):
            file = st.file_uploader(f"Choose file {i+1}", type=support_types, key=f"file_{i}")
            if file:
                uploaded_files.append(file)
                
                # Image previews
                if file.type == "image/png" or file.type == "image/jpeg" or file.name.lower().endswith(('.jpg', '.jpeg')):
                    image = Image.open(file)
                    image.thumbnail((100, 100))
                    st.image(image, caption=f"Preview of {file.name}")
                
                # PDF preview (first page)
                elif file.name.lower().endswith('.pdf'):
                    pdf = fitz.open(stream=file.read(), filetype="pdf")
                    page = pdf[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.image(img, caption=f"First page of {file.name}", width=100)
                
                # Text preview
                elif file.name.lower().endswith(('.txt', '.md')):
                    text_preview = file.read().decode('utf-8')[:200] + '...'
                    st.text_area(f"Preview of {file.name}", text_preview, height=100)
                
                # Excel preview
                elif file.name.lower().endswith('.xlsx'):
                    df = pd.read_excel(file)
                    st.dataframe(df.head(3), height=100)

                file.seek(0)
    # Reset all file pointers before returning
    for file in uploaded_files:
        file.seek(0)
               
    return uploaded_files