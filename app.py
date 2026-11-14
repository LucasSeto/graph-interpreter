import streamlit as st


st.set_page_config(page_title="Photo Viewer")
st.title("Photo Viewer")

photo = st.file_uploader(
    "Choose a photo",
    type=["jpg", "jpeg", "png", "webp", "bmp", "gif", "tif", "tiff"],
)

if photo is not None:
    st.image(photo, caption=photo.name, use_container_width=True)
