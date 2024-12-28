import os
import streamlit as st
import google.generativeai as genai

# Konfigurasi API key
api_key = os.getenv("AIzaSyDboqGrsG04ifpcwvDoXuylYKJKnPFFptk")

genai.configure(api_key=api_key)

# Konfigurasi model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(history=[])
except Exception as e:
    st.error(f"Gagal menginisialisasi model: {e}")
    st.stop()

# Antarmuka Streamlit
st.title("Gemini Chatbot dengan Streamlit")
st.write("Masukkan teks Anda dan dapatkan respons dari model Gemini.")

# Input dari pengguna
user_input = st.text_input("Masukkan teks Anda:")

if st.button("Kirim"):
    if user_input.strip():
        with st.spinner("Sedang memproses..."):
            try:
                response = chat_session.send_message(user_input)
                st.success("Respons dari model:")
                st.write(response.text)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat mengirim pesan: {e}")
    else:
        st.warning("Input tidak boleh kosong.")
