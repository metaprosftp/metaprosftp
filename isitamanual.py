from google.cloud import vision
import streamlit as st
from PIL import Image

def generate_tags_with_vision(image_path):
    client = vision.ImageAnnotatorClient()

    with open(image_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.label_detection(image=image)
    labels = response.label_annotations
    tags = [label.description for label in labels]
    return tags

def main():
    st.title("Image Tagger")

    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image")

        if st.button("Generate Tags"):
            image_path = "temp.jpg"  # Save the image temporarily
            image.save(image_path)
            tags = generate_tags_with_vision(image_path)
            st.text("Tags:")
            st.text(", ".join(tags))

if __name__ == "__main__":
    main()
