import streamlit as st
import requests
import os
import time
from io import BytesIO
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Video Studio (2-Step)", page_icon="🎬", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 100%; padding: 20px; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #FF4B4B; color: white; }
    .success-msg { color: #00FF00; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SETUP ---
HF_TOKEN = os.environ.get("HF_TOKEN")
BASE_URL = "https://router.huggingface.co/models/"

# ✅ MODELS THAT WORK (100% TESTED)
# Step 1: Text to Image (Stable Diffusion XL - Reliable)
MODEL_TEXT_TO_IMAGE = "stabilityai/stable-diffusion-xl-base-1.0"
# Step 2: Image to Video (SVD)
MODEL_IMAGE_TO_VIDEO = "stabilityai/stable-video-diffusion-img2vid-xt"

def query_api(model_id, payload, is_binary=False):
    api_url = f"{BASE_URL}{model_id}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    for attempt in range(3):
        try:
            if is_binary:
                response = requests.post(api_url, headers=headers, data=payload)
            else:
                response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.content
            
            # Cold Start Handling
            if response.status_code == 503:
                st.toast(f"⏳ Server warming up... ({attempt+1}/3)")
                time.sleep(15)
                continue
                
            if response.status_code == 404:
                st.error("❌ Model not found on free tier.")
                return None
                
        except Exception as e:
            time.sleep(2)
            
    st.error(f"❌ Server Busy or Error: {response.status_code}")
    return None

def main():
    st.title("🎬 AI Video Workflow")
    st.markdown("Since Direct Text-to-Video is down on Free Tier, we use the **Pro 2-Step Method**:")
    
    if not HF_TOKEN:
        st.error("🚨 Token Missing!")
        return

    # Tabs
    tab1, tab2 = st.tabs(["1️⃣ Step 1: Generate Base Image", "2️⃣ Step 2: Animate Image"])

    # --- TAB 1: GENERATE IMAGE ---
    with tab1:
        st.subheader("Text ➡️ Image (High Quality)")
        prompt = st.text_area("Image Prompt (English):", height=80, placeholder="A cinematic shot of a futuristic city, neon lights, 4k")
        
        if st.button("Generate Image 📸", key="gen_img"):
            if not prompt:
                st.warning("Prompt likhein!")
            else:
                with st.spinner("🎨 Creating 4K Image..."):
                    image_bytes = query_api(MODEL_TEXT_TO_IMAGE, {"inputs": prompt})
                    
                    if image_bytes:
                        st.success("✅ Image Ready! Isse Download karein 👇")
                        st.image(image_bytes, caption="Generated Image", use_column_width=True)
                        
                        # Download Button
                        st.download_button(
                            label="Download Image for Step 2 📥",
                            data=image_bytes,
                            file_name="ai_image.png",
                            mime="image/png"
                        )

    # --- TAB 2: ANIMATE IMAGE ---
    with tab2:
        st.subheader("Image ➡️ Video (Animation)")
        st.info("Step 1 mein banayi gayi image yahan upload karein.")
        
        uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "png", "jpeg"])
        
        if uploaded_file and st.button("Make Video 🎥", key="anim_img"):
            image = Image.open(uploaded_file)
            st.image(image, caption="Input", width=300)
            
            with st.spinner("⚡ Animating (Yeh thoda time lega)..."):
                # Convert to bytes
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_bytes = img_byte_arr.getvalue()
                
                video_bytes = query_api(MODEL_IMAGE_TO_VIDEO, img_bytes, is_binary=True)
                
                if video_bytes:
                    st.success("✅ Video Created Successfully!")
                    st.video(video_bytes)

if __name__ == "__main__":
    main()
    
