import streamlit as st
from PIL import Image
import tweepy
import os
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twitter API credentials
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# Tweepy authentication
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

# Predefined sizes
IMAGE_SIZES = {
    "300x250": (300, 250),
    "728x90": (728, 90),
    "160x600": (160, 600),
    "300x600": (300, 600),
}

# Streamlit UI
st.title("Image Resizer & X (Twitter) Auto Post")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Original Image", use_column_width=True)

    resized_images = []
    
    # Resize images
    for size_name, dimensions in IMAGE_SIZES.items():
        resized_img = img.resize(dimensions)
        resized_images.append((size_name, resized_img))

    # Display resized images
    st.subheader("Resized Images")
    for name, img in resized_images:
        st.image(img, caption=f"{name} Image", use_column_width=True)

    if st.button("Post to X (Twitter)"):
        try:
            media_ids = []
            for name, img in resized_images:
                img_io = BytesIO()
                img.save(img_io, format="PNG")
                img_io.seek(0)
                media = api.media_upload(filename=f"{name}.png", file=img_io)
                media_ids.append(media.media_id)
            
            api.update_status(status="Here are my resized images!", media_ids=media_ids)
            st.success("Images posted successfully to your X (Twitter) account!")
        except Exception as e:
            st.error(f"Failed to post images: {e}")
