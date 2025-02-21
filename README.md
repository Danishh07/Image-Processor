# Image Processor with Twitter Integration

This Streamlit application allows users to upload images, automatically resize them to specific dimensions, and post them to Twitter.

## Features

- Upload images (supports PNG, JPG, JPEG)
- Automatic resizing to four specific dimensions:
  - 300x250
  - 728x90
  - 160x600
  - 300x600
- Twitter integration for automatic posting
- Clean and intuitive user interface

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Twitter API credentials:
   - Create a Twitter Developer account at https://developer.twitter.com/
   - Create a new app and get your API credentials
   - Copy the credentials to `.env` file:
     - TWITTER_API_KEY
     - TWITTER_API_SECRET
     - TWITTER_ACCESS_TOKEN
     - TWITTER_ACCESS_SECRET

3. Run the application:
```bash
streamlit run app.py
```

## Deployment

This application can be easily deployed on Streamlit Cloud:

1. Push your code to a GitHub repository
2. Visit https://share.streamlit.io/
3. Connect your GitHub repository
4. Add your Twitter API credentials as secrets in the Streamlit Cloud dashboard

## Usage

1. Open the application in your web browser
2. Click "Choose an image file" to upload your image
3. View the automatically resized versions
4. Click "Post to Twitter" to share the images

## Technologies Used

- Python 3.8+
- Streamlit
- Pillow (PIL)
- Tweepy
- Python-dotenv
