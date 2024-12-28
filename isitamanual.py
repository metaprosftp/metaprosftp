import streamlit as st
import os
from PIL import Image
import google.generativeai as genai

# Streamlit app title
st.title('Image Captioning, Tagging, and Metadata Generation')

# File uploader for image input
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

# Input field for API key
API_KEY = st.text_input("Enter your API Key: Get your Google Studio API key from [here](https://makersuite.google.com/app/apikey)", type="password")

# Initialize prompts for metadata generation
if 'title_prompt' not in st.session_state:
    st.session_state['title_prompt'] = (
        "Create a descriptive title in English up to 12 words long. Ensure the keywords accurately reflect the subject matter, context, and main elements of the image, using precise terms that capture unique aspects like location, activity, or theme for specificity. Maintain variety and consistency in keywords relevant to the image content. Avoid using brand names or copyrighted elements in the title."
    )

if 'tags_prompt' not in st.session_state:
    st.session_state['tags_prompt'] = (
        "Generate up to 49 keywords relevant to the image (each keyword must be one word, separated by commas). Avoid using brand names or copyrighted elements in the keywords."
    )

# Function to generate metadata for images using AI model
def generate_metadata(model, img):
    # Generate a caption
    caption_response = model.generate_content(["Write a caption for the image in English.", img])
    caption = caption_response.text if caption_response else "No caption generated."

    # Generate tags
    tags_response = model.generate_content(["Generate 5 hashtags for the image in English.", img])
    tags = tags_response.text if tags_response else "No tags generated."

    # Generate title
    title_response = model.generate_content([st.session_state['title_prompt'], img])
    title = title_response.text if title_response else "No title generated."

    # Generate keywords
    keywords_response = model.generate_content([st.session_state['tags_prompt'], img])
    keywords = keywords_response.text if keywords_response else "No keywords generated."

    return caption, tags, title, keywords

# Main logic for file upload and API interaction
if uploaded_file is not None:
    if st.button('Upload'):
        if API_KEY.strip() == '':
            st.error('Enter a valid API key.')
        else:
            # Save uploaded file temporarily
            file_path = os.path.join("temp", uploaded_file.name)
            os.makedirs("temp", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # Open and display the uploaded image
            img = Image.open(file_path)
            st.image(img, caption="Uploaded Image")

            try:
                # Configure the generative AI model
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model

                # Generate metadata
                caption, tags, title, keywords = generate_metadata(model, img)

                # Display the results
                st.write(f"### Caption: {caption}")
                st.write(f"### Tags: {tags}")
                st.write(f"### Title: {title}")
                st.write(f"### Keywords: {keywords}")

            except Exception as e:
                error_msg = str(e)
                if "API_KEY_INVALID" in error_msg:
                    st.error("Invalid API Key. Please enter a valid API Key.")
                else:
                    st.error(f"An error occurred: {error_msg}")

# Footer with credits
footer = """
<style>
    a:link, a:visited {
        color: blue;
        text-decoration: dotted;
    }
    a:hover, a:active {
        color: skyblue;
    }
    .footer p {
        font-size: 15px;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #333;
        color: white;
        text-align: center;
        padding: 10px 0;
    }
    .footer a:hover {
        color: white;
    }
</style>

<div class="footer">
    <p>Developed with ❤ by <a href="https://www.linkedin.com/in/sgvkamalakar" target="_blank">sgvkamalakar</a></p>
</div>
"""

st.markdown(footer, unsafe_allow_html=True)
