import streamlit as st
import requests
import os
import time
from io import BytesIO
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Video Studio (Classic)", page_icon="🎬", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 100%; padding: 20px; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #2e86de; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SETUP ---
HF_TOKEN = os.environ.get("HF_TOKEN")
BASE_URL = "https://api-inference.huggingface.co/models/"

# ✅ SOLUTION: USE LIGHTWEIGHT CLASSIC MODELS
# Step 1: Image (Old but Reliable)
MODEL_TEXT_TO_IMAGE = "runwayml/stable-diffusion-v1-5"
# Step 2: Video (Only SVD is left, we try best effort)
MODEL_IMAGE_TO_VIDEO = "stabilityai/stable-video-diffusion-img2vid-xt"

def query_api(model_id, payload, is_binary=False):
    # Direct URL approach
    api_url = f"{BASE_URL}{model_id}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    for attempt in range(3):
        try:
            if is_binary:
                response = requests.post(api_url, headers=headers, data=payload)
            else:
                response = requests.post(api_url, headers=headers, json=payload)
            
            # SUCCESS
            if response.status_code == 200:
                return response.content
            
            # DEBUGGING: Print exact error if failed
            error_details = response.text
            
            # Cold Start
            if response.status_code == 503:
                st.toast(f"⚠️ Model Loading... ({attempt+1}/3)")
                time.sleep(20)
                continue
            
            # Agar Free Tier Error hai
            if "Model not found" in error_details or response.status_code == 404:
                 st.error(f"❌ '{model_id}' Free Tier par available nahi hai.")
                 return None

            # Retry
            time.sleep(3)

        except Exception as e:
            st.error(f"Error: {str(e)}")
            time.sleep(2)
            
    st.error(f"❌ Failed. Server Code: {response.status_code}")
    return None

def main():
    st.title("🎬 AI Video Studio (Lite Version)")
    st.markdown("Using **Stable Diffusion v1.5** (Most reliable free model).")
    
    if not HF_TOKEN:
        st.error("🚨 Token Missing!")
        return

    tab1, tab2 = st.tabs(["1️⃣ Generate Image", "2️⃣ Animate Image"])

    # --- TAB 1: TEXT TO IMAGE (v1.5) ---
    with tab1:
        prompt = st.text_area("Image Prompt:", placeholder="A cyberpunk cat neon city")
        
        if st.button("Generate Image 📸", key="gen_btn"):
            if not prompt:
                st.warning("Prompt likhein!")
            else:
                with st.spinner("🎨 Creating Image (Classic v1.5)..."):
                    image_bytes = query_api(MODEL_TEXT_TO_IMAGE, {"inputs": prompt})
                    
                    if image_bytes:
                        st.success("✅ Image Ready!")
                        st.image(image_bytes, caption="Generated Image", use_column_width=True)
                        st.download_button("Download Image 📥", image_bytes, "image.png", "image/png")

    # --- TAB 2: IMAGE TO VIDEO ---
    with tab2:
        st.info("Upload the image you just created.")
        uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png"])
        
        if uploaded_file and st.button("Animate Video 🎥", key="vid_btn"):
            image = Image.open(uploaded_file)
            st.image(image, caption="Input", width=200)
            
            with st.spinner("⚡ Animating (May take 2-3 mins)..."):
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_bytes = img_byte_arr.getvalue()
                
                video_bytes = query_api(MODEL_IMAGE_TO_VIDEO, img_bytes, is_binary=True)
                
                if video_bytes:
                    st.success("✅ Video Created!")
                    st.video(video_bytes)

if __name__ == "__main__":
    main()
    
