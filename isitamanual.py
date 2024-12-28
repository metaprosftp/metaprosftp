import streamlit as st
import google.generativeai as genai
from PIL import Image

# Ganti dengan API key Anda
genai.configure(api_key="AIzaSyDboqGrsG04ifpcwvDoXuylYKJKnPFFptk")

def generate_tags(image_path):
  with open(image_path, "rb") as image_file:
    image = image_file.read()
  response = genai.generate_text(
      model="gemini-pro",
      prompt="Describe this image:",
      image=image
  )
  return response.text

def main():
  st.title("Image Tagger")

  uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

  if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image")

    if st.button("Generate Tags"):
      image_path = "temp.jpg"  # Simpan gambar sementara
      image.save(image_path)
      tags = generate_tags(image_path)
      st.text("Tags:")
      st.text(tags)

if __name__ == "__main__":
  main()
