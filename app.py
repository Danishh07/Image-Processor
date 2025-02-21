import streamlit as st
from PIL import Image
import io
import tweepy

# Configure page
st.set_page_config(page_title="Image Processor", page_icon="🖼️", layout="wide")

# Debug information about secrets
st.write("Available secrets:", list(st.secrets.keys()) if hasattr(st.secrets, "keys") else "No secrets available")

# Try to get Twitter API credentials from Streamlit secrets
try:
    TWITTER_API_KEY = st.secrets.secrets.TWITTER_API_KEY
    TWITTER_API_SECRET = st.secrets.secrets.TWITTER_API_SECRET
    TWITTER_ACCESS_TOKEN = st.secrets.secrets.TWITTER_ACCESS_TOKEN
    TWITTER_ACCESS_SECRET = st.secrets.secrets.TWITTER_ACCESS_SECRET
    twitter_configured = True
    st.success("Twitter credentials loaded successfully!")
except Exception as e:
    st.error("""
    Twitter API credentials not found in secrets. 
    Please make sure you've configured the following secrets in your Streamlit Cloud dashboard:
    
    [secrets]
    TWITTER_API_KEY = "your_api_key"
    TWITTER_API_SECRET = "your_api_secret"
    TWITTER_ACCESS_TOKEN = "your_access_token"
    TWITTER_ACCESS_SECRET = "your_access_secret"
    
    Error details: {}
    """.format(str(e)))
    twitter_configured = False

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
    if not twitter_configured:
        st.error("Twitter API is not configured. Please check the secrets configuration.")
        return False

    try:
        # Initialize Twitter API v2 client
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        
        # Initialize API v1.1 for media upload
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY,
            TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN,
            TWITTER_ACCESS_SECRET
        )
        api = tweepy.API(auth)
        
        # Upload images
        media_ids = []
        for img in images:
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            try:
                # Upload to Twitter
                media = api.media_upload(filename='image.png', file=io.BytesIO(img_byte_arr))
                media_ids.append(media.media_id)
            except Exception as e:
                st.error(f"Error uploading image: {str(e)}")
                return False
        
        try:
            # Post tweet with all images using v2 API
            response = client.create_tweet(
                text='Check out these automatically resized images! #ImageProcessor',
                media_ids=media_ids
            )
            st.write("Tweet posted successfully! Tweet ID:", response.data['id'])
            return True
        except Exception as e:
            st.error(f"Error creating tweet: {str(e)}")
            return False
            
    except Exception as e:
        st.error(f"""
        Error posting to Twitter: {str(e)}
        
        Common issues:
        1. API keys may be incorrect
        2. Twitter account may not be approved for API access
        3. Rate limits may have been exceeded
        
        Please verify your Twitter API credentials and permissions.
        """)
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
        if twitter_configured:
            with st.spinner("Posting to Twitter..."):
                if post_to_twitter(processed_images):
                    st.success("Successfully posted to Twitter!")
                else:
                    st.error("Failed to post to Twitter. Please check the error messages above.")
        else:
            st.error("Twitter API is not configured. Please check the secrets configuration.")
