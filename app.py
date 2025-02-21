import streamlit as st
from PIL import Image
import io
import os
import tweepy

# Load environment variables
# load_dotenv()

# Configure page
st.set_page_config(page_title="Image Processor", page_icon="🖼️", layout="wide")

# Twitter API credentials from Streamlit secrets
TWITTER_API_KEY = st.secrets["TWITTER_API_KEY"]
TWITTER_API_SECRET = st.secrets["TWITTER_API_SECRET"]
TWITTER_ACCESS_TOKEN = st.secrets["TWITTER_ACCESS_TOKEN"]
TWITTER_ACCESS_SECRET = st.secrets["TWITTER_ACCESS_SECRET"]

# Predefined image sizes
IMAGE_SIZES = [
    (300, 250),
    (728, 90),
    (160, 600),
    (300, 600)
]

def resize_image(image, size):
    """Resize image while maintaining aspect ratio and adding white background"""
    target_width, target_height = size
    # Create new white background image
    new_image = Image.new('RGB', (target_width, target_height), 'white')
    
    # Calculate scaling factor
    width_ratio = target_width / image.width
    height_ratio = target_height / image.height
    scale_factor = min(width_ratio, height_ratio)
    
    # Calculate new size
    new_width = int(image.width * scale_factor)
    new_height = int(image.height * scale_factor)
    
    # Resize image
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Calculate position to paste (center)
    x = (target_width - new_width) // 2
    y = (target_height - new_height) // 2
    
    # Paste resized image onto white background
    new_image.paste(resized, (x, y))
    return new_image

def post_to_twitter(images):
    """Post images to Twitter"""
    try:
        # Authenticate with Twitter
        auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        api = tweepy.API(auth)
        
        # Upload images
        media_ids = []
        for img in images:
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Upload to Twitter
            media = api.media_upload(filename='image.png', file=io.BytesIO(img_byte_arr))
            media_ids.append(media.media_id)
        
        # Post tweet with all images
        api.update_status(
            status='Check out these automatically resized images! #ImageProcessor',
            media_ids=media_ids
        )
        return True
    except Exception as e:
        st.error(f"Error posting to Twitter: {str(e)}")
        return False

# Main UI
st.title("🖼️ Image Processor")
st.write("Upload an image to automatically resize it and post to Twitter!")

# File uploader
uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    # Display original image
    original_image = Image.open(uploaded_file)
    st.subheader("Original Image")
    st.image(original_image, use_column_width=True)
    
    # Process image
    processed_images = []
    st.subheader("Processed Images")
    
    # Create columns for processed images
    cols = st.columns(2)
    
    for idx, size in enumerate(IMAGE_SIZES):
        processed_image = resize_image(original_image, size)
        processed_images.append(processed_image)
        
        # Display in appropriate column
        with cols[idx % 2]:
            st.write(f"Size: {size[0]}x{size[1]}")
            st.image(processed_image)
    
    # Post to Twitter button
    if st.button("Post to Twitter"):
        with st.spinner("Posting to Twitter..."):
            if post_to_twitter(processed_images):
                st.success("Successfully posted to Twitter!")
            else:
                st.error("Failed to post to Twitter. Please check your credentials.")
