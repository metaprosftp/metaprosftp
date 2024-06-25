import streamlit as st
import os
import tempfile
from PIL import Image
import google.generativeai as genai
import iptcinfo3
import time
import traceback
import re
import unicodedata
from datetime import datetime, timedelta
import pytz
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

if 'sftp_username' not in st.session_state:
    st.session_state['sftp_username'] = "209940897"

if 'title_prompt' not in st.session_state:
    st.session_state['title_prompt'] = ("Create a descriptive and accurate title in English, up to 12 words long. Ensure the title introduces the content clearly and is relevant, descriptive, and precise. Avoid formal sentence structures and the use of brand names, product names, or people's names. The title should highlight the main features of the image and suggest potential uses in various contexts.")

# Function to generate metadata for images using AI model
def generate_metadata(model, img):
    title_prompt = st.session_state['title_prompt']

    # Generate the title
    title_response = model.generate_content([title_prompt, img])
    title = title_response.text.strip()  # Strip leading/trailing whitespace from title

    # Define the prompt for generating tags based on the generated title
    tags_prompt = f"Generate up to 49 keywords relevant to the image (each keyword must be one word, separated by commas). The image contains \"{title}\, Focus on keywords related to the Subject Matter, Key Concepts, Contextual Keywords, Contextual Keywords, Related Terms, Audience and Perspective, Industry or Field-Specific Terms. ")

    # Generate the tags
    tags_response = model.generate_content([tags_prompt, img])
    tags_text = tags_response.text

    # Prepare metadata dictionary
    metadata = {
        'Title': title,
        'Tags': tags_text.split(',')
    }
    return metadata

# Function to embed metadata into images
def embed_metadata(image_path, metadata, progress_placeholder, files_processed, total_files):
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
        iptc_data['keywords'] = metadata.get('Tags', [])  # Keywords
        iptc_data['caption/abstract'] = metadata.get('Title', '')  # Title

        # Save the image with the embedded metadata
        iptc_data.save()

        # Update progress text
        files_processed += 1
        progress_placeholder.text(f"Processing images to generate titles, tags, and embed metadata {files_processed}/{total_files}")

        # Return the updated image path for further processing
        return image_path

    except Exception as e:
        st.error(f"An error occurred while embedding metadata: {e}")
        st.error(traceback.format_exc())  # Print detailed error traceback for debugging

def sftp_upload(image_path, sftp_username, sftp_password, progress_placeholder, files_processed, total_files):
    # SFTP connection details
    sftp_host = "sftp.contributor.adobestock.com"
    sftp_port = 22

    # Initialize SFTP connection
    transport = paramiko.Transport((sftp_host, sftp_port))
    transport.connect(username=sftp_username, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        filename = os.path.basename(image_path)
        sftp.put(image_path, f"/your/remote/directory/path/{filename}")  # Replace with your remote directory path
        progress_placeholder.text(f"Uploaded {files_processed + 1}/{total_files} files to SFTP server.")

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

    # Display "About" button at the top
    if st.button("About"):
        st.markdown("""
        ### Why Choose MetaPro?
        """)

    # Check logout at the end
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
        # Read start date from license file
        with open(license_file, 'r') as file:
            start_date_str = file.read().strip()
            start_date = datetime.fromisoformat(start_date_str)

        # Calculate the expiration date
        expiration_date = start_date + timedelta(days=31)
        current_date = datetime.now(JAKARTA_TZ)

        if current_date > expiration_date:
            st.error("Your license has expired. Please contact support for a new license key.")
            return
        else:
            days_remaining = (expiration_date - current_date).days
            st.success(f"License valid. You have {days_remaining} days remaining.")

        # API Key input
        api_key = st.text_input('Enter your API Key', value=st.session_state['api_key'] or '')

        # Save API key in session state
        if api_key:
            st.session_state['api_key'] = api_key

        # SFTP Username input
        sftp_username = st.text_input('SFTP Username', value=st.session_state['sftp_username'])

        # Save SFTP username in session state
        if sftp_username:
            st.session_state['sftp_username'] = sftp_username

        # SFTP Password input
        sftp_password = st.text_input('SFTP Password', type='password')

        # Commented out the Title and tags prompts input
        # title_prompt = st.text_area('Title Prompt', value=st.session_state['title_prompt'], height=100)
        # tags_prompt = st.text_area('Tags Prompt', value=st.session_state['tags_prompt'], height=100)

        # Save prompts in session state
        # st.session_state['title_prompt'] = title_prompt
        # st.session_state['tags_prompt'] = tags_prompt

        # Upload image files
        uploaded_files = st.file_uploader('Upload Images (Only JPG and JPEG supported)', accept_multiple_files=True)

        if uploaded_files:
            valid_files = [file for file in uploaded_files if file.type in ['image/jpeg', 'image/jpg']]
            invalid_files = [file for file in uploaded_files if file not in valid_files]

            if invalid_files:
                st.error("Only JPG and JPEG files are supported.")

            if valid_files and st.button("Process"):
                with st.spinner("Processing..."):
                    try:
                        # Check and update upload count for the current date
                        if st.session_state['upload_count']['date'] != current_date.date():
                            st.session_state['upload_count'] = {
                                'date': current_date.date(),
                                'count': 0
                            }

                        # Check if remaining uploads are available
                        if st.session_state['upload_count']['count'] + len(valid_files) > 1000:
                            remaining_uploads = 1000 - st.session_state['upload_count']['count']
                            st.warning(f"You have exceeded the upload limit. Remaining uploads for today: {remaining_uploads}")
                            return
                        else:
                            st.session_state['upload_count']['count'] += len(valid_files)
                            st.success(f"Uploads successful. Remaining uploads for today: {1000 - st.session_state['upload_count']['count']}")

                        genai.configure(api_key=api_key)  # Configure AI model with API key
                        model = genai.GenerativeModel('gemini-pro-vision')

                        # Create a temporary directory to store the uploaded images
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Save the uploaded images to the temporary directory
                            image_paths = []
                            for file in valid_files:
                                temp_image_path = os.path.join(temp_dir, file.name)
                                with open(temp_image_path, 'wb') as f:
                                    f.write(file.read())
                                image_paths.append(temp_image_path)

                            total_files = len(image_paths)
                            files_processed = 0

                            # Progress placeholder for embedding metadata
                            embed_progress_placeholder = st.empty()
                            # Progress placeholder for SFTP upload
                            upload_progress_placeholder = st.empty()

                            # Process each image one by one
                            for image_path in image_paths:
                                try:
                                    # Open image
                                    img = Image.open(image_path)

                                    # Generate metadata
                                    metadata = generate_metadata(model, img)

                                    # Embed metadata
                                    if metadata:
                                        updated_image_path = embed_metadata(image_path, metadata, embed_progress_placeholder, files_processed, total_files)
                                        
                                        # Upload via SFTP
                                        if updated_image_path:
                                            sftp_upload(updated_image_path, sftp_username, sftp_password, upload_progress_placeholder, files_processed, total_files)
                                            files_processed += 1

                                except Exception as e:
                                    st.error(f"An error occurred while processing {os.path.basename(image_path)}: {e}")
                                    st.error(traceback.format_exc())
                                    continue

                            st.success(f"Successfully processed and transferred {files_processed} files to the SFTP server.")

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        st.error(traceback.format_exc())  # Print detailed error traceback for debugging

if __name__ == '__main__':
    main()
