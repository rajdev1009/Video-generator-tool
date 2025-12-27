import streamlit as st
import requests
import os
import time
from io import BytesIO
from PIL import Image

# --- PAGE CONFIGURATION (Mobile Friendly) ---
st.set_page_config(
    page_title="AI Video Generator Pro",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS FOR MOBILE OPTIMIZATION ---
st.markdown("""
    <style>
    .stApp { max-width: 100%; padding: 20px; }
    .stVideo { width: 100% !important; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 20px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- API CONFIGURATION ---
HF_TOKEN = os.environ.get("HF_TOKEN")

# ✅ UPDATED URLs (Fixed Error 410)
API_URL_TEXT = "https://router.huggingface.co/models/damo-vilab/text-to-video-ms-1.7b"
API_URL_IMAGE = "https://router.huggingface.co/models/stabilityai/stable-video-diffusion-img2vid-xt"

# --- CORE FUNCTION: GENERATE VIDEO WITH RETRY LOGIC ---
def query_huggingface_api(api_url, payload, is_binary=False):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if is_binary:
                response = requests.post(api_url, headers=headers, data=payload)
            else:
                response = requests.post(api_url, headers=headers, json=payload)
            
            # Success
            if response.status_code == 200:
                return response.content
            
            # Model Loading (Cold Start)
            elif response.status_code == 503:
                error_data = response.json()
                wait_time = error_data.get("estimated_time", 20)
                st.warning(f"⚠️ Model load ho raha hai. {int(wait_time)} seconds wait kar rahe hain... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue 
            
            # Handle Redirects or 410 Errors specifically
            elif response.status_code == 410:
                 st.error("🚨 API Endpoint changed. Please contact developer to update URLs.")
                 return None

            else:
                st.error(f"Server Error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            st.warning(f"🌐 Network glitch, retrying... (Attempt {attempt+1}/{max_retries})")
            time.sleep(2)
            
    st.error("❌ Server bahut busy hai. Please 2 minute baad try karein.")
    return None

# --- MAIN APP UI ---
def main():
    st.title("🎬 Ultimate AI Video Studio")
    
    if not HF_TOKEN:
        st.error("🚨 Configuration Error: HF_TOKEN missing in Koyeb settings.")
        return

    tab1, tab2 = st.tabs(["📝 Text-to-Video", "🖼️ Image-to-Video"])

    # --- TAB 1: TEXT TO VIDEO ---
    with tab1:
        st.header("Text se Video Banayein")
        # Note: English prompt is better for this model
        prompt = st.text_area("Video description (English mein likhein):", height=100, placeholder="An elephant walking in a forest...", key="text_prompt")

        if st.button("Generate from Text 🚀", key="btn_text"):
            if not prompt:
                st.warning("Please prompt likhein!")
            else:
                with st.spinner("🎥 Video generate ho rahi hai..."):
                    video_bytes = query_huggingface_api(API_URL_TEXT, {"inputs": prompt})
                    if video_bytes:
                        st.success("✅ Video Ready!")
                        st.video(video_bytes)

    # --- TAB 2: IMAGE TO VIDEO ---
    with tab2:
        st.header("Photo ko Zinda Karein")
        st.info("ℹ️ Tip: Clear photo use karein.")
        
        uploaded_file = st.file_uploader("Image upload karein (JPG/PNG)", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            if st.button("Animate This Image ✨", key="btn_image"):
                with st.spinner("⚡ Photo process ho rahi hai..."):
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format=image.format)
                    img_bytes = img_byte_arr.getvalue()
                    
                    video_bytes = query_huggingface_api(API_URL_IMAGE, img_bytes, is_binary=True)
                    
                    if video_bytes:
                        st.success("✅ Image Animated Successfully!")
                        st.video(video_bytes)

if __name__ == "__main__":
    main()
    
