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
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- API CONFIGURATION ---
# Token Environment se uthayenge
HF_TOKEN = os.environ.get("HF_TOKEN")

# Models definition
API_URL_TEXT = "https://api-inference.huggingface.co/models/damo-vilab/text-to-video-ms-1.7b"
API_URL_IMAGE = "https://api-inference.huggingface.co/models/stabilityai/stable-video-diffusion-img2vid-xt"

# --- CORE FUNCTION: GENERATE VIDEO WITH RETRY LOGIC ---
def query_huggingface_api(api_url, payload, is_binary=False):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Retry Loop: 3 baar try karega
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if is_binary:
                # Image-to-Video ke liye raw binary data bhejte hain
                response = requests.post(api_url, headers=headers, data=payload)
            else:
                # Text-to-Video ke liye JSON bhejte hain
                response = requests.post(api_url, headers=headers, json=payload)
            
            # Agar success (200 OK) hai
            if response.status_code == 200:
                return response.content
            
            # Agar model load ho raha hai (503 Service Unavailable)
            elif response.status_code == 503:
                error_data = response.json()
                wait_time = error_data.get("estimated_time", 20)
                st.warning(f"⚠️ Model load ho raha hai (Cold Start). {int(wait_time)} seconds wait kar rahe hain... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue 
            
            # Agar API rate limit ya error de
            else:
                st.error(f"Server Error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            st.warning(f"🌐 Network glitch, retrying... (Attempt {attempt+1}/{max_retries})")
            time.sleep(2)
            
    st.error("❌ Server bahut busy hai ya Model load nahi ho pa raha. Please 2 minute baad try karein.")
    return None

# --- MAIN APP UI ---
def main():
    st.title("🎬 Ultimate AI Video Studio")
    
    # Check Token
    if not HF_TOKEN:
        st.error("🚨 Configuration Error: HF_TOKEN missing in Koyeb settings.")
        return

    # Tabs create karein
    tab1, tab2 = st.tabs(["📝 Text-to-Video", "🖼️ Image-to-Video"])

    # --- TAB 1: TEXT TO VIDEO ---
    with tab1:
        st.header("Text se Video Banayein")
        prompt = st.text_area("Video ka description likhein (English mein):", height=100, placeholder="An astronaut riding a horse in space...", key="text_prompt")

        if st.button("Generate from Text 🚀", key="btn_text"):
            if not prompt:
                st.warning("Please prompt likhein!")
            else:
                with st.spinner("🎥 Soch raha hoon aur video bana raha hoon..."):
                    video_bytes = query_huggingface_api(API_URL_TEXT, {"inputs": prompt})
                    if video_bytes:
                        st.success("✅ Video Ready!")
                        st.video(video_bytes)

    # --- TAB 2: IMAGE TO VIDEO ---
    with tab2:
        st.header("Photo ko Zinda Karein")
        st.info("ℹ️ Tip: Clear photo use karein. Yeh process heavy hai toh 1-2 minute lag sakte hain.")
        
        uploaded_file = st.file_uploader("Apni image upload karein (JPG/PNG)", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            # Image display karein
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            if st.button("Animate This Image ✨", key="btn_image"):
                with st.spinner("⚡ Photo mein jaan daal rahe hain (Sabar rakhein, ye heavy model hai)..."):
                    
                    # Image ko bytes mein convert karna zaroori hai API ke liye
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format=image.format)
                    img_bytes = img_byte_arr.getvalue()
                    
                    # API Call (Binary Mode = True)
                    video_bytes = query_huggingface_api(API_URL_IMAGE, img_bytes, is_binary=True)
                    
                    if video_bytes:
                        st.success("✅ Image Animated Successfully!")
                        st.video(video_bytes)

if __name__ == "__main__":
    main()
  
