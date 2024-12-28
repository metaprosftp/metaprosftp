import streamlit as st
import os
from PIL import Image
import google.generativeai as genai

# App title
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

            try:
                # Configure Generative AI with the new API key
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')

                # Generate caption
                caption_response = model.generate_content({"parts": [{"text": "Write a caption for this image in English"}]})
                st.write("Caption Response Debug:", caption_response)  # Debug: check response structure
                caption = caption_response.candidates[0].text  # Adjust according to response structure

                # Generate tags
                tags_response = model.generate_content({"parts": [{"text": "Generate 5 hashtags for this image"}]})
                st.write("Tags Response Debug:", tags_response)  # Debug: check response structure
                tags = tags_response.candidates[0].text  # Adjust according to response structure

                # Display the image and results
                st.image(img, caption=f"Caption: {caption}")
                st.write(f"Tags: {tags}")
            
            except Exception as e:
                st.error(f"An error occurred: {e}")
            
            finally:
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
