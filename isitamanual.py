import os
import streamlit as st
import google.generativeai as genai

# Configuring the API key securely
api_key = os.environ.get("AIzaSyDboqGrsG04ifpcwvDoXuylYKJKnPFFptk")

genai.configure(api_key=api_key)

# Generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Streamlit app header
st.title("Generative AI Chat with Gemini")
st.write("Powered by Google Generative AI")

# User input
user_input = st.text_area("Enter your message here:", placeholder="Type your input...")

# Send button
if st.button("Send"):
    if user_input.strip() == "":
        st.warning("Please enter a valid input.")
    else:
        try:
            # Generate a response
            response = genai.generate_text(
                prompt=user_input,
                **generation_config
            )
            
            # Display the response
            st.subheader("Response:")
            st.write(response.text)
        except Exception as e:
            st.error(f"An error occurred: {e}")
