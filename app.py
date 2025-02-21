import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import streamlit as st
from PIL import Image
import io
import tweepy
import os
import time
import uuid
import urllib.parse
import requests
import base64

# Configure page
st.set_page_config(page_title="Image Processor", page_icon="🖼️", layout="wide")

# Force HTTPS for OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'

# Debug information about the environment
st.write("Debug - Environment:")
st.write({
    "HTTPS": os.environ.get('HTTPS', 'Not set'),
    "SERVER_PROTOCOL": os.environ.get('SERVER_PROTOCOL', 'Not set'),
    "HTTP_X_FORWARDED_PROTO": os.environ.get('HTTP_X_FORWARDED_PROTO', 'Not set')
})

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

# Constants
REDIRECT_URI = "https://image-proceapp.streamlit.app"

def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    token_url = "https://api.twitter.com/2/oauth2/token"
    
    # Create the authorization header
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode('utf-8')).decode('utf-8')
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": "challenge"
    }
    
    st.write("Debug - Token request data:", data)
    
    response = requests.post(token_url, headers=headers, data=data)
    st.write("Debug - Token response status:", response.status_code)
    st.write("Debug - Token response:", response.text)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Token exchange failed: {response.text}")

def init_oauth_handler():
    """Initialize the OAuth handler"""
    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
    )
    return oauth2_user_handler

# Main UI
st.title("🖼️ Image Processor")

# Initialize session state
if 'oauth_state' not in st.session_state:
    st.session_state.oauth_state = str(uuid.uuid4())

# Check URL parameters
params = st.experimental_get_query_params()
st.write("Debug - Query Parameters:", params)
st.write("Debug - Current State:", st.session_state.oauth_state)

# Handle OAuth flow
if "code" in params:
    try:
        # Get the authorization code
        code = params["code"][0]
        st.write("Debug - Code:", code)
        
        # Exchange code for token
        try:
            access_token_data = exchange_code_for_token(code)
            st.write("Debug - Token data received:", access_token_data)
            
            # Store the token
            st.session_state.oauth_token = access_token_data["access_token"]
            st.success("Successfully authenticated with Twitter!")
            
            # Clear URL parameters
            st.experimental_set_query_params()
            st.rerun()
        except Exception as e:
            st.error(f"Error exchanging code for token: {str(e)}")
            st.write("Debug - Exchange error:", str(e))
            
    except Exception as e:
        st.error(f"Error in OAuth flow: {str(e)}")
        if "insecure_transport" in str(e).lower():
            st.error("This app requires HTTPS. Please make sure you're using the HTTPS URL.")

# Show authentication status and button
if 'oauth_token' not in st.session_state:
    st.warning("Please authenticate with Twitter first")
    
    # Create auth URL when button is clicked
    if st.button("Authenticate with Twitter"):
        try:
            oauth2_user_handler = init_oauth_handler()
            auth_url = oauth2_user_handler.get_authorization_url()
            st.write("Debug - Generated Auth URL:", auth_url)
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
