import os
import streamlit as st
import google.generativeai as genai

# Konfigurasi API
genai.configure(api_key=os.environ.get("AIzaSyDffy1dlvuaQXBaa1Yjo7hz1P8rppM3aMU"))

# Konfigurasi model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Inisialisasi model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Header aplikasi
st.title("Generative AI Chat with Gemini")
st.write("Powered by Google Generative AI")

# Input pengguna
user_input = st.text_area("Enter your message here:", placeholder="Type your input...")

# Tombol untuk mengirim pesan
if st.button("Send"):
    if user_input.strip() == "":
        st.warning("Please enter a valid input.")
    else:
        # Mulai sesi chat
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(user_input)
        
        # Tampilkan hasil
        st.subheader("Response:")
        st.write(response.text)
