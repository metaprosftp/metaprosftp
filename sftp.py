import streamlit as st
import os
import tempfile
from PIL import Image
import google.generativeai as genai
import iptcinfo3
import zipfile
import time
import traceback
import re
import unicodedata
from datetime import datetime, timedelta
import pytz
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import paramiko

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

# Function to normalize and clean text
def normalize_text(text):
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    return normalized

# Function to generate metadata for images using AI model
def generate_metadata(model, img, start_time):
    caption = model.generate_content([
        "Generate a descriptive title in English up to 12 words long, identifying the main elements of the image. Describe the primary subjects, objects, activities, and context. Refine the title to include relevant keywords for SEO and ensure it is engaging and informative, but avoid mentioning human names, brand names, product names, or company names.",
        img
    ])
    
    # Check elapsed time and pause if necessary
    elapsed_time = time.time() - start_time
    if elapsed_time > 10:
       #  st.info("Pausing for 5 seconds...")
        time.sleep(8)
        start_time = time.time()  # Reset the start time after pausing

    tags = model.generate_content([
        "Generate up to 45 keywords in English that are relevant to the image (Ensure each keyword is a single word, separated by commas).",
        img
    ])

    # Check elapsed time and pause if necessary
    elapsed_time = time.time() - start_time
    if elapsed_time > 10:
       # st.info("Pausing for 5 seconds...")
        time.sleep(5)
        start_time = time.time()  # Reset the start time after pausing

    # Filter out undesirable characters from the generated tags
    filtered_tags = re.sub(r'[^\w\s,]', '', tags.text)
    
    # Trim the generated keywords if they exceed 49 words
    keywords = filtered_tags.split(',')[:49]  # Limit to 49 words
    trimmed_tags = ','.join(keywords)
    
    return {
        'Title': caption.text.strip(),  # Remove leading/trailing whitespace
        'Tags': trimmed_tags.strip()
    }

# Function to embed metadata into images
def embed_metadata(image_path, metadata, progress_bar, files_processed, total_files):
    try:
        # Simulate delay
        time.sleep(1)

        # Open the image file
        img = Image.open(image_path)

        # Load existing IPTC data (if any)
        iptc_data = iptcinfo3.IPTCInfo(image_path, force=True)

        # Clear existing IPTC metadata
        for tag in iptc_data._data:
            iptc_data._data[tag] = []

        # Update IPTC data with new metadata
        iptc_data['keywords'] = [metadata.get('Tags', '')]  # Keywords
        iptc_data['caption/abstract'] = [metadata.get('Title', '')]  # Title

        # Save the image with the embedded metadata
        iptc_data.save()

        # Update progress bar
        files_processed += 1
        progress_bar.progress(files_processed / total_files)
        progress_bar.text(f"Embedding metadata for image {files_processed}/{total_files}")

        # Return the updated image path for further processing
        return image_path

    except Exception as e:
        st.error(f"An error occurred while embedding metadata: {e}")
        st.error(traceback.format_exc())  # Print detailed error traceback for debugging

def sftp_upload(image_paths, sftp_password, progress_placeholder):
    # SFTP connection details
    sftp_host = "sftp.contributor.adobestock.com"
    sftp_port = 22
    sftp_username = "209940897"

    # Initialize SFTP connection
    transport = paramiko.Transport((sftp_host, sftp_port))
    transport.connect(username=sftp_username, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        for i, image_path in enumerate(image_paths, start=1):
            filename = os.path.basename(image_path)
            sftp.put(image_path, f"/your/remote/directory/path/{filename}")  # Replace with your remote directory path
            progress_placeholder.text(f"Uploaded {i}/{len(image_paths)} files to SFTP server.")

    except Exception as e:
        st.error(f"Error during SFTP upload: {e}")
        st.error(traceback.format_exc())

    finally:
        sftp.close()
        transport.close()

def main():
    """Main function for the Streamlit app."""
    
    # Apply custom styling
    st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        section[data-testid="stSidebar"] div:first-child {top: 0; height: 100vh;}
    </style>
    """, unsafe_allow_html=True)

    # Check if user is logged in
    if not st.session_state['logged_in']:
        # Display login form
        # Use custom HTML and CSS to style the title
        st.markdown("""
    <style>
    .small-title {
        font-size: 1.5em; /* Adjust the size as needed */
    }
    </style>
    <h1 class="small-title">Login</h1>
    """, unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            # Validate login credentials
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

    # Display logout button
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        set_lock("")
        st.success("Logged out successfully.")
        return

    # Check lock file before proceeding
    if not check_lock():
        st.error("Access denied. Your MetaPro Basic Plan subscription is limited to only one device.")
        return

    # Display WhatsApp chat link
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <a href="https://wa.me/6285328007533" target="_blank">
            <button style="background-color: #1976d2; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                MetaPro
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # Check if license has already been validated
    license_file = "license.txt"
    if not st.session_state['license_validated']:
        if os.path.exists(license_file):
            with open(license_file, 'r') as file:
                start_date_str = file.read().strip()
                start_date = datetime.fromisoformat(start_date_str)
                st.session_state['license_validated'] = True
        else:
            # License key input
            validation_key = st.text_input('License Key', type='password')

    # Check if validation key is correct
    correct_key = "A1B2-C3D4-E5F6-G7H8"

    if not st.session_state['license_validated'] and validation_key:
        if validation_key == correct_key:
            st.session_state['license_validated'] = True
            start_date = datetime.now(JAKARTA_TZ)
            with open(license_file, 'w') as file:
                file.write(start_date.isoformat())
        else:
            st.error("Invalid validation key. Please enter the correct key.")

    if st.session_state['license_validated']:
        # Check the license file for the start date
        with open(license_file, 'r') as file:
            start_date_str = file.read().strip()
            start_date = datetime.fromisoformat(start_date_str)

        # Display license status and expiration information
        days_remaining = 30 - (datetime.now(JAKARTA_TZ) - start_date).days
        st.info(f"License validated. Days remaining: {days_remaining}")

        # Check if the license has expired
        if days_remaining <= 0:
            st.error("Your license has expired. Please contact support to renew your license.")
            return

        # Display the rest of your application here
        st.title("Image Metadata Generator")

        api_key = st.text_input('Enter your API Key', value=st.session_state['api_key'] or '')
        if api_key:
            st.session_state['api_key'] = api_key

        uploaded_files = st.file_uploader('Upload Images (Only JPG and JPEG supported)', accept_multiple_files=True)

        if uploaded_files and st.button("Process"):
            with st.spinner("Processing..."):
                try:
                    genai.configure(api_key=api_key)  # Configure AI model with API key
                    model = genai.GenerativeModel('gemini-pro-vision')

                    temp_dir = tempfile.mkdtemp()

                    image_paths = []
                    for file in uploaded_files:
                        temp_image_path = os.path.join(temp_dir, file.name)
                        with open(temp_image_path, 'wb') as f:
                            f.write(file.read())
                        image_paths.append(temp_image_path)

                    metadata_list = []
                    process_placeholder = st.empty()
                    start_time = time.time()  # Initialize the start time

                    for i, image_path in enumerate(image_paths):
                        process_placeholder.text(f"Processing Generate Titles and Tags {i + 1}/{len(image_paths)}")
                        try:
                            img = Image.open(image_path)
                            metadata = generate_metadata(model, img, start_time)
                            metadata_list.append(metadata)
                        except Exception as e:
                            st.error(f"An error occurred while generating metadata for {os.path.basename(image_path)}: {e}")
                            st.error(traceback.format_exc())
                            continue

                    # Display progress bar for embedding metadata
                    progress_bar = st.progress(0)
                    progress_bar_text = st.empty()
                    total_files = len(image_paths)
                    files_processed = 0

                    # Embed metadata into images and create a zip file
                    updated_image_paths = []
                    for image_path, metadata in zip(image_paths, metadata_list):
                        updated_image_path = embed_metadata(image_path, metadata, progress_bar, files_processed, total_files)
                        updated_image_paths.append(updated_image_path)

                    # Update the upload count for the day
                    current_date = datetime.now(JAKARTA_TZ).date()
                    if st.session_state['upload_count']['date'] == current_date:
                        st.session_state['upload_count']['count'] += len(updated_image_paths)
                    else:
                        st.session_state['upload_count']['date'] = current_date
                        st.session_state['upload_count']['count'] = len(updated_image_paths)

                    # Prompt user for SFTP password
                    sftp_password = st.text_input("Enter your SFTP password", type='password')

                    if st.button("Upload to SFTP"):
                        progress_placeholder = st.empty()
                        sftp_upload(updated_image_paths, sftp_password, progress_placeholder)

                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.error(traceback.format_exc())

if __name__ == '__main__':
    main()
