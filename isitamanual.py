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
import unicodedata
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import paramiko

st.title('Image Captioning and Tagging')

# File uploader for images
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

# API Key input field
API_KEY = st.text_input("Enter your API Key:", type="password", help="Get your Google API key from [here](https://makersuite.google.com/app/apikey)")

# Process the uploaded image
if uploaded_file is not None:
    if st.button('Upload'):
        if API_KEY.strip() == '':
            st.error('Enter a valid API key')
        else:
            # Save the uploaded file temporarily
            file_path = os.path.join("temp", uploaded_file.name)
            os.makedirs("temp", exist_ok=True)  # Ensure the temp directory exists
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Open the image
            img = Image.open(file_path)

            # Configure Generative AI with the new API key
            try:
                genai.configure(api_key=API_KEY)
                
                # Use the updated model for generating content
                model = genai.GenerativeModel('gemini-1.5-flash')

                # Generate caption
                caption_response = model.generate_content({"parts": [{"text": "Write a caption for this image in English"}]})
                st.write("Caption Response Debugging:", caption_response)  # Debug response
                caption = caption_response  # Replace with correct attribute once identified

                # Generate tags
                tags_response = model.generate_content({"parts": [{"text": "Generate 5 hashtags for this image"}]})
                st.write("Tags Response Debugging:", tags_response)  # Debug response
                tags = tags_response  # Replace with correct attribute once identified

                # Display the image and results
                st.image(img, caption=f"Caption: {caption}")
                st.write(f"Tags: {tags}")
            
            except Exception as e:
                error_msg = str(e)
                st.error(f"An error occurred: {error_msg}")
            
            # Cleanup the temp directory
            os.remove(file_path)

# Footer
footer = """
<style>
    a:link, a:visited {
        color: blue;
        text-decoration: none;
    }
    a:hover, a:active {
        color: skyblue;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: black;
        color: white;
        text-align: center;
        padding: 10px 0;
    }
</style>
<div class="footer">
    <p>Developed with ❤ by <a href="https://www.linkedin.com/in/sgvkamalakar" target="_blank">sgvkamalakar</a></p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
