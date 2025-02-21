import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import streamlit as st
from PIL import Image
import io
import tweepy
import os
import time
import uuid

# Configure page
st.set_page_config(page_title="Image Processor", page_icon="🖼️", layout="wide")

# Force HTTPS for OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'

# Twitter API credentials - try to get from secrets, otherwise use environment variables
try:
    # Try to get from nested secrets first
    CLIENT_ID = st.secrets.secrets.TWITTER_CLIENT_ID
    CLIENT_SECRET = st.secrets.secrets.TWITTER_CLIENT_SECRET
except Exception:
    try:
        # Try to get from top-level secrets
        CLIENT_ID = st.secrets["TWITTER_CLIENT_ID"]
        CLIENT_SECRET = st.secrets["TWITTER_CLIENT_SECRET"]
    except Exception:
        # Use hardcoded values as fallback
        CLIENT_ID = "eW1BcGF0dEJTeHAwQnM3dFlGUEU6MTpjaQ"
        CLIENT_SECRET = "o5m97vDzMiAjqCqByvChBYvKNM3h4wBl5lanfdnIdyhZBhc6Lm"

def init_oauth_handler():
    """Initialize the OAuth handler"""
    return tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="https://image-proceapp.streamlit.app/",
        scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
    )

# Main UI
st.title("🖼️ Image Processor")

# Check URL parameters
params = st.experimental_get_query_params()

# Handle OAuth flow
if "code" in params:
    try:
        # Get the authorization code
        code = params["code"][0]
        
        # Create a new handler and get the token
        oauth2_user_handler = init_oauth_handler()
        access_token = oauth2_user_handler.fetch_token(code)
        
        # Store the token
        st.session_state.oauth_token = access_token
        st.success("Successfully authenticated with Twitter!")
        
        # Clear URL parameters
        st.experimental_set_query_params()
    except Exception as e:
        st.error(f"Error authenticating: {str(e)}")
        if "insecure_transport" in str(e).lower():
            st.error("This app requires HTTPS. Please make sure you're using the HTTPS URL.")
        # Clear any existing token
        if 'oauth_token' in st.session_state:
            del st.session_state.oauth_token

# Show authentication status and button
if 'oauth_token' not in st.session_state:
    st.warning("Please authenticate with Twitter first")
    
    # Create auth URL when button is clicked
    if st.button("Authenticate with Twitter"):
        try:
            oauth2_user_handler = init_oauth_handler()
            auth_url = oauth2_user_handler.get_authorization_url()
            st.markdown(f"[Click here to authenticate with Twitter]({auth_url})")
        except Exception as e:
            st.error(f"Error generating authentication URL: {str(e)}")
else:
    st.success("Authenticated with Twitter")

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
        if 'oauth_token' not in st.session_state:
            st.error("Please authenticate with Twitter first")
            return False

        # Get the client
        client = tweepy.Client(
            st.session_state.oauth_token,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )

        # Initialize API v1.1 for media upload
        auth = tweepy.OAuth2AppHandler(CLIENT_ID, CLIENT_SECRET)
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
            # Post tweet with all images
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
        1. Authentication token may have expired
        2. Twitter account may not be approved for API access
        3. Rate limits may have been exceeded
        
        Please try authenticating again.
        """)
        return False

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
        if 'oauth_token' in st.session_state:
            with st.spinner("Posting to Twitter..."):
                if post_to_twitter(processed_images):
                    st.success("Successfully posted to Twitter!")
                else:
                    st.error("Failed to post to Twitter. Please check the error messages above.")
        else:
            st.error("Please authenticate with Twitter first")
