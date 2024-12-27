import streamlit as st
import os
import tempfile
from PIL import Image
import iptcinfo3
import zipfile
import time
import traceback
import unicodedata
from datetime import datetime, timedelta
import pytz

# Set the timezone to UTC+7 Jakarta
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')

def normalize_text(text):
    """Normalize and clean text."""
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    return normalized

def embed_metadata(image_path, metadata, new_filename, progress_placeholder, files_processed, total_files):
    """Embed metadata into the image and rename it."""
    try:
        time.sleep(1)

        # Open the image file
        img = Image.open(image_path)

        # Load existing IPTC data (if any)
        iptc_data = iptcinfo3.IPTCInfo(image_path, force=True)

        # Clear existing IPTC metadata
        for tag in iptc_data._data:
            iptc_data._data[tag] = []

        # Update IPTC data with new metadata
        iptc_data['keywords'] = [metadata.get('Tags', '')]  # Tags
        iptc_data['caption/abstract'] = [metadata.get('Title', '')]  # Title

        # Save the image with the embedded metadata
        iptc_data.save()

        # Rename the file
        renamed_path = os.path.join(os.path.dirname(image_path), new_filename)
        os.rename(image_path, renamed_path)

        # Update progress text
        files_processed += 1
        progress_placeholder.text(f"Processing images... {files_processed}/{total_files}")

        return renamed_path

    except Exception as e:
        st.error(f"An error occurred while embedding metadata: {e}")
        st.error(traceback.format_exc())

def main():
    """Main function for the Streamlit app."""
    st.title("Image Metadata Editor")

    # Login functionality
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == "dian" and password == "trial":
                st.session_state['logged_in'] = True
                st.success("Login successful!")
            else:
                st.error("Invalid credentials. Please try again.")
        return

    # Metadata input fields
    title_input = st.text_input("Enter Title for Images")
    tags_input = st.text_area("Enter Tags (comma-separated)")

    # File uploader
    uploaded_files = st.file_uploader("Upload Images (JPG/JPEG only)", accept_multiple_files=True, type=["jpg", "jpeg"])

    if uploaded_files and title_input and tags_input:
        if st.button("Process Images"):
            with st.spinner("Processing images..."):
                try:
                    # Create a temporary directory for processing
                    with tempfile.TemporaryDirectory() as temp_dir:
                        image_paths = []
                        for idx, file in enumerate(uploaded_files):
                            temp_image_path = os.path.join(temp_dir, file.name)
                            with open(temp_image_path, 'wb') as f:
                                f.write(file.read())
                            image_paths.append(temp_image_path)

                        total_files = len(image_paths)
                        files_processed = 0

                        # Progress placeholder
                        progress_placeholder = st.empty()

                        # Process and embed metadata
                        processed_files = []
                        for idx, image_path in enumerate(image_paths):
                            metadata = {
                                'Title': normalize_text(title_input),
                                'Tags': normalize_text(tags_input)
                            }
                            new_filename = f"{normalize_text(title_input)}_{idx + 1}.jpg"
                            updated_image_path = embed_metadata(image_path, metadata, new_filename, progress_placeholder, files_processed, total_files)
                            if updated_image_path:
                                processed_files.append(updated_image_path)

                        # Create a zip file of the processed images
                        zip_filename = os.path.join(temp_dir, "processed_images.zip")
                        with zipfile.ZipFile(zip_filename, 'w') as zipf:
                            for file_path in processed_files:
                                zipf.write(file_path, os.path.basename(file_path))

                        # Provide download link
                        with open(zip_filename, "rb") as f:
                            st.download_button(
                                label="Download Processed Images",
                                data=f,
                                file_name="processed_images.zip",
                                mime="application/zip"
                            )

                        st.success(f"Processed {len(processed_files)} images successfully!")

                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.error(traceback.format_exc())

if __name__ == "__main__":
    main()
