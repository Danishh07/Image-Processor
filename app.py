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
import hashlib
import random
import string

# Configure page
st.set_page_config(page_title="Image Processor", page_icon="🖼️", layout="wide")

# Force HTTPS for OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'

# Twitter API credentials
try:
    CLIENT_ID = st.secrets["TWITTER_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["TWITTER_CLIENT_SECRET"]
except Exception:
    CLIENT_ID = "eW1BcGF0dEJTeHAwQnM3dFlGUEU6MTpjaQ"
    CLIENT_SECRET = "o5m97vDzMiAjqCqByvChBYvKNM3h4wBl5lanfdnIdyhZBhc6Lm"

REDIRECT_URI = "https://image-proceapp.streamlit.app"

# Generate a random code verifier
def generate_code_verifier(length=128):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Create a code challenge from the verifier
def create_code_challenge(code_verifier):
    code_verifier_bytes = code_verifier.encode('utf-8')
    code_challenge = hashlib.sha256(code_verifier_bytes).digest()
    return base64.urlsafe_b64encode(code_challenge).decode('utf-8').rstrip('=')

if 'code_verifier' not in st.session_state:
    st.session_state.code_verifier = generate_code_verifier()

code_challenge = create_code_challenge(st.session_state.code_verifier)

def exchange_code_for_token(code):
    token_url = "https://api.twitter.com/2/oauth2/token"
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode('utf-8')).decode('utf-8')

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": st.session_state.code_verifier
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    return None

def init_oauth_handler():
    return tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
    )

# Main UI
st.title("🖼️ Image Processor")

if 'oauth_state' not in st.session_state:
    st.session_state.oauth_state = str(uuid.uuid4())

params = st.experimental_get_query_params()
if "code" in params:
    code = params["code"][0]
    access_token_data = exchange_code_for_token(code)
    if access_token_data:
        st.session_state.oauth_token = access_token_data["access_token"]
        st.experimental_set_query_params()
        st.rerun()

if 'oauth_token' not in st.session_state:
    if st.button("Authenticate with Twitter"):
        oauth2_user_handler = init_oauth_handler()
        auth_url = oauth2_user_handler.get_authorization_url(code_challenge=code_challenge)
        st.markdown(f"[Click here to authenticate with Twitter]({auth_url})")
else:
    st.success("Authenticated with Twitter")

# Predefined image sizes
IMAGE_SIZES = [(300, 250), (728, 90), (160, 600), (300, 600)]

def resize_image(image, size):
    target_width, target_height = size
    new_image = Image.new('RGB', (target_width, target_height), 'white')

    width_ratio = target_width / image.width
    height_ratio = target_height / image.height
    scale_factor = min(width_ratio, height_ratio)

    new_width = int(image.width * scale_factor)
    new_height = int(image.height * scale_factor)
    
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    x = (target_width - new_width) // 2
    y = (target_height - new_height) // 2
    
    new_image.paste(resized, (x, y))
    return new_image

def post_to_twitter(images):
    if 'oauth_token' not in st.session_state:
        return False

    client = tweepy.Client(st.session_state.oauth_token, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    auth = tweepy.OAuth2AppHandler(CLIENT_ID, CLIENT_SECRET)
    api = tweepy.API(auth)
    
    media_ids = []
    for img in images:
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        media = api.media_upload(filename='image.png', file=io.BytesIO(img_byte_arr))
        media_ids.append(media.media_id)
    
    response = client.create_tweet(text='Check out these resized images! #ImageProcessor', media_ids=media_ids)
    return response.data.get('id') if response else False

st.write("Upload an image to automatically resize and post to Twitter!")

uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    original_image = Image.open(uploaded_file)
    st.subheader("Original Image")
    st.image(original_image, use_column_width=True)
    
    processed_images = []
    st.subheader("Processed Images")
    
    cols = st.columns(2)
    
    for idx, size in enumerate(IMAGE_SIZES):
        processed_image = resize_image(original_image, size)
        processed_images.append(processed_image)
        
        with cols[idx % 2]:
            st.write(f"Size: {size[0]}x{size[1]}")
            st.image(processed_image)
    
    if st.button("Post to Twitter"):
        if 'oauth_token' in st.session_state:
            if post_to_twitter(processed_images):
                st.success("Successfully posted to Twitter!")
            else:
                st.error("Failed to post to Twitter.")
        else:
            st.error("Please authenticate with Twitter first")