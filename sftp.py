import streamlit as st
import os
import tempfile
from PIL import Image
import google.generativeai as genai
import iptcinfo3
import re
import time
import traceback
import unicodedata
from datetime import datetime, timedelta
import pytz

# Set the timezone to UTC+7 Jakarta
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')

# Function to check if lock file exists and its content
def check_lock():
    lock_file = "lock.txt"
    if os.path.exists(lock_file):
        with open(lock_file, 'r') as file:
            content = file.read().strip()
            return content == "logged_in"
    return False

# Function to set lock file
def set_lock(status):
    lock_file = "lock.txt"
    with open(lock_file, 'w') as file:
        file.write(status)

# Initialize session state for login and license validation
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'license_validated' not in st.session_state:
    st.session_state['license_validated'] = False

if 'upload_count' not in st.session_state:
    st.session_state['upload_count'] = {
        'date': None,
        'count': 0
    }

if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None

if 'title_prompt' not in st.session_state:
    st.session_state['title_prompt'] = ("Create a descriptive title in English up to 12 words long. Ensure the keywords accurately reflect the subject matter, context, and main elements of the image, using precise terms that capture unique aspects like location, activity, or theme for specificity. Maintain variety and consistency in keywords relevant to the image content. Avoid using brand names or copyrighted elements in the title.")

if 'tags_prompt' not in st.session_state:
    st.session_state['tags_prompt'] = ("Generate up to 49 keywords relevant to the image (each keyword must be one word, separated by commas). Avoid using brand names or copyrighted elements in the keywords.")

# Function to generate metadata for images using AI model
def generate_metadata(model, img):
    title_prompt = st.session_state['title_prompt']
    tags_prompt = st.session_state['tags_prompt']

    caption = model.generate_content([title_prompt, img])
    tags = model.generate_content([tags_prompt, img])

    keywords = re.findall(r'\w+', tags.text)
    keywords = [word.lower() for word in keywords]
    unique_keywords = list(set(keywords))[:49]
    trimmed_tags = ','.join(unique_keywords)

    return {
        'Title': caption.text.strip(),
        'Tags': trimmed_tags
    }

# Function to embed metadata into images
def embed_metadata(image_path, metadata, progress_placeholder, files_processed, total_files):
    try:
        time.sleep(1)
        img = Image.open(image_path)
        iptc_data = iptcinfo3.IPTCInfo(image_path, force=True)

        for tag in iptc_data._data:
            iptc_data._data[tag] = []

        iptc_data['keywords'] = [metadata.get('Tags', '')]
        iptc_data['caption/abstract'] = [metadata.get('Title', '')]

        iptc_data.save()

        files_processed += 1
        progress_placeholder.text(f"Processing images to generate titles, tags, and embed metadata {files_processed}/{total_files}")

        return image_path

    except Exception as e:
        st.error(f"An error occurred while embedding metadata: {e}")
        st.error(traceback.format_exc())


def main():
    st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        section[data-testid="stSidebar"] div:first-child {top: 0; height: 100vh;}
    </style>
    """, unsafe_allow_html=True)

    if not st.session_state['logged_in']:
        st.markdown("""
        <style>
        .small-title {
            font-size: 1.5em;
        }
        </style>
        <h1 class="small-title">Login</h1>
        """, unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            correct_username = "dian"
            correct_password = "trial"

            if username == correct_username and password == correct_password:
                if check_lock():
                    st.error("Another user is currently logged in. Please try again later.")
                else:
                    st.session_state['logged_in'] = True
                    set_lock("logged_in")
                    st.success("Login successful! Please click the login button once more.")
            else:
                st.error("Invalid username or password.")
        return

    if st.button("About"):
        st.markdown("""### Why Choose MetaPro?""")

    if st.button("Logout"):
        st.session_state['logged_in'] = False
        set_lock("")
        st.success("Logged out successfully.")
        return

    if not check_lock():
        st.error("Access denied. Your MetaPro Basic Plan subscription is limited to only one device.")
        return

    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <a href="https://wa.me/6285328007533" target="_blank">
            <button style="background-color: #1976d2; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                MetaPro
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    license_file = "license.txt"
    if not st.session_state['license_validated']:
        if os.path.exists(license_file):
            with open(license_file, 'r') as file:
                start_date_str = file.read().strip()
                start_date = datetime.fromisoformat(start_date_str)
                st.session_state['license_validated'] = True
        else:
            validation_key = st.text_input('License Key', type='password')

    correct_key = "31days"

    if not st.session_state['license_validated'] and validation_key:
        if validation_key == correct_key:
            st.session_state['license_validated'] = True
            start_date = datetime.now(JAKARTA_TZ)
            with open(license_file, 'w') as file:
                file.write(start_date.isoformat())
        else:
            st.error("Invalid validation key. Please enter the correct key.")

    if st.session_state['license_validated']:
        with open(license_file, 'r') as file:
            start_date_str = file.read().strip()
            start_date = datetime.fromisoformat(start_date_str)

        expiration_date = start_date + timedelta(days=31)
        current_date = datetime.now(JAKARTA_TZ)

        if current_date > expiration_date:
            st.error("Your license has expired. Please contact support for a new license key.")
            return
        else:
            days_remaining = (expiration_date - current_date).days
            st.success(f"License valid. You have {days_remaining} days remaining.")

        api_key = st.text_input('Enter your API Key', value=st.session_state['api_key'] or '')

        if api_key:
            st.session_state['api_key'] = api_key

        uploaded_files = st.file_uploader('Upload Images (Only JPG and JPEG supported)', accept_multiple_files=True)

        if uploaded_files:
            valid_files = [file for file in uploaded_files if file.type in ['image/jpeg', 'image/jpg']]
            invalid_files = [file for file in uploaded_files if file not in valid_files]

            if invalid_files:
                st.error("Only JPG and JPEG files are supported.")

            if valid_files and st.button("Process"):
                with st.spinner("Processing..."):
                    try:
                        if st.session_state['upload_count']['date'] != current_date.date():
                            st.session_state['upload_count'] = {
                                'date': current_date.date(),
                                'count': 0
                            }

                        if st.session_state['upload_count']['count'] + len(valid_files) > 1000:
                            remaining_uploads = 1000 - st.session_state['upload_count']['count']
                            st.warning(f"You have exceeded the upload limit. Remaining uploads for today: {remaining_uploads}")
                            return
                        else:
                            st.session_state['upload_count']['count'] += len(valid_files)
                            st.success(f"Uploads successful. Remaining uploads for today: {1000 - st.session_state['upload_count']['count']}")

                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-pro-vision')

                        with tempfile.TemporaryDirectory() as temp_dir:
                            image_paths = []
                            for file in valid_files:
                                temp_image_path = os.path.join(temp_dir, file.name)
                                with open(temp_image_path, 'wb') as f:
                                    f.write(file.read())
                                image_paths.append(temp_image_path)

                            total_files = len(image_paths)
                            files_processed = 0
                            progress_placeholder = st.empty()

                            for image_path in image_paths:
                                try:
                                    img = Image.open(image_path)
                                    metadata = generate_metadata(model, img)
                                    embed_metadata(image_path, metadata, progress_placeholder, files_processed, total_files)
                                    files_processed += 1

                                except Exception as e:
                                    st.error(f"An error occurred while processing {os.path.basename(image_path)}: {e}")
                                    st.error(traceback.format_exc())
                                    continue

                            st.success(f"Successfully processed {files_processed} files.")

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        st.error(traceback.format_exc())

if __name__ == '__main__':
    main()
