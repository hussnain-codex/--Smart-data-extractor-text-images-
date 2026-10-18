"""Upload a receipt image and see the extracted JSON.

Run: streamlit run streamlit_app.py
"""

import tempfile
from pathlib import Path

import streamlit as st

from image_extractor import analyze_image, extract_invoice_from_image

st.set_page_config(page_title="Smart Data Extractor", page_icon="🧾")
st.title("Smart Data Extractor")

mode = st.radio("Extract as", ["Invoice / receipt", "Any image"], horizontal=True)
upload = st.file_uploader(
    "Upload an image", type=["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"]
)

if upload:
    st.image(upload, width=320)

    if st.button("Extract", type="primary"):
        suffix = Path(upload.name).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as file:
            file.write(upload.getvalue())
            image_path = file.name

        try:
            with st.spinner("Sending image to Gemini..."):
                if mode == "Invoice / receipt":
                    result = extract_invoice_from_image(image_path)
                else:
                    result = analyze_image(image_path)
            st.success("Extraction complete.")
            st.json(result.model_dump(mode="json"))
        except (RuntimeError, ValueError, OSError) as error:
            st.error(f"{type(error).__name__}: {error}")
        finally:
            Path(image_path).unlink(missing_ok=True)
