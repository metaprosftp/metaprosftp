import streamlit as st
import os
import tempfile
from PIL import Image
import iptcinfo3
import zipfile
import time
import traceback
import unicodedata
import pytz
import genai  # Assuming genai SDK is installed
from datetime import datetime

# Set the timezone to UTC+7 Jakarta
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')

def normalize_text(text):
    """Normalize and clean text."""
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    return normalized

def embed_metadata(image_path, metadata, new_filename):
    """Embed metadata into the image and rename it."""
    try:
        # Open the image file
        img = Image.open(image_path)

        # Load existing IPTC data (if any)
        iptc_data = iptcinfo3.IPTCInfo(image_path, force=True)

        # Clear existing IPTC metadata
        for tag in iptc_data._data:
            iptc_data._data[tag] = []

        # Update IPTC data with new metadata
        iptc_data['keywords'] = [metadata.get('Tags', '')]
        iptc_data['caption/abstract'] = [metadata.get('Title', '')]

        # Save the image with embedded metadata
        iptc_data.save()

        # Rename the file
        renamed_path = os.path.join(os.path.dirname(image_path), new_filename)
        os.rename(image_path, renamed_path)

        return renamed_path
    except Exception as e:
        st.error(f"An error occurred while embedding metadata: {e}")
        st.error(traceback.format_exc())

def main():
    """Main function for the Streamlit app."""
    st.title("Image Captioning and Metadata Editor")

    # Toggle workflow
    workflow = st.radio("Choose a workflow:", options=["Metadata Embedding", "AI Captioning"], horizontal=True)

    if workflow == "Metadata Embedding":
        title_input = st.text_input("Enter Title for Images")
        tags_input = st.text_area("Enter Tags (comma-separated)")

        uploaded_files = st.file_uploader("Upload Images (JPG/JPEG only)", accept_multiple_files=True, type=["jpg", "jpeg"])

        if uploaded_files and title_input and tags_input:
            if st.button("Process Images"):
                with tempfile.TemporaryDirectory() as temp_dir:
                    image_paths = []
                    for file in uploaded_files:
                        temp_image_path = os.path.join(temp_dir, file.name)
                        with open(temp_image_path, 'wb') as f:
                            f.write(file.read())
                        image_paths.append(temp_image_path)

                    processed_files = []
                    for idx, image_path in enumerate(image_paths):
                        metadata = {'Title': normalize_text(title_input), 'Tags': normalize_text(tags_input)}
                        new_filename = f"{normalize_text(title_input)}_{idx + 1}.jpg"
                        updated_image_path = embed_metadata(image_path, metadata, new_filename)
                        if updated_image_path:
                            processed_files.append(updated_image_path)

                    # Zip processed files
                    zip_filename = os.path.join(temp_dir, "processed_images.zip")
                    with zipfile.ZipFile(zip_filename, 'w') as zipf:
                        for file_path in processed_files:
                            zipf.write(file_path, os.path.basename(file_path))

                    with open(zip_filename, "rb") as f:
                        st.download_button("Download Processed Images", f, "processed_images.zip", "application/zip")
                    st.success(f"Processed {len(processed_files)} images successfully!")

    elif workflow == "AI Captioning":
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])
        api_key = st.text_input("Enter your API Key:", type="password")

        if uploaded_file and api_key:
            if st.button("Generate Caption and Tags"):
                file_path = os.path.join("temp", uploaded_file.name)
                os.makedirs("temp", exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                img = Image.open(file_path)

                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')  # Replace with appropriate model
                    caption = model.generate_content(["Write a caption for the image in English.", img])
                    tags = model.generate_content(["Generate 5 hashtags for the image in English.", img])
                    st.image(img, caption=f"Caption: {caption.text}")
                    st.write(f"Tags: {tags.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
