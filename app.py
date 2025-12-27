import streamlit as st
import requests
import os
import time
from io import BytesIO
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Video Final", page_icon="🎬", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 100%; padding: 20px; }
    .stVideo { width: 100% !important; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- SETUP ---
HF_TOKEN = os.environ.get("HF_TOKEN")

# ✅ FORCE NEW ROUTER URL (Hard-Coded)
# Hum library use nahi karenge, khud URL banayenge
BASE_URL = "https://router.huggingface.co/models/"

MODEL_TEXT = "cerspense/zeroscope_v2_576w"
MODEL_IMAGE = "stabilityai/stable-video-diffusion-img2vid-xt"

def generate_video_manual(model_id, payload, is_binary=False):
    # URL khud construct kar rahe hain taaki koi galti na ho
    api_url = f"{BASE_URL}{model_id}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    for attempt in range(3):
        try:
            if is_binary:
                response = requests.post(api_url, headers=headers, data=payload)
            else:
                response = requests.post(api_url, headers=headers, json=payload)
            
            # --- SUCCESS CASE ---
            if response.status_code == 200:
                return response.content
            
            # --- HANDLING ERRORS ---
            error_msg = response.text
            
            # 1. Cold Start (Model Loading)
            if response.status_code == 503:
                wait_time = 20
                st.warning(f"⚠️ Server Jaag raha hai (Warming up)... {wait_time}s wait. (Try {attempt+1}/3)")
                time.sleep(wait_time)
                continue
            
            # 2. Old URL Error (Should not happen now, but safe side)
            if response.status_code == 410:
                 st.error("🚨 Critical: URL Issue. Lekin humne router use kiya hai, toh ye nahi aana chahiye.")
                 return None

            # 3. Other Errors
            st.warning(f"⚠️ Attempt {attempt+1} failed: {response.status_code}")
            time.sleep(3)

        except Exception as e:
            st.error(f"🚫 Network Error: {str(e)}")
            time.sleep(2)
            
    st.error("❌ Sab try kar liya, par server response nahi de raha.")
    return None

def main():
    st.title("🎬 AI Video Generator (Direct Router)")
    
    if not HF_TOKEN:
        st.error("🚨 Token Missing! Koyeb settings check karein.")
        return

    tab1, tab2 = st.tabs(["📝 Text-to-Video", "🖼️ Image-to-Video"])

    # --- TAB 1: TEXT ---
    with tab1:
        st.info("Best Prompt: 'A panda eating bamboo, 4k, high quality'")
        prompt = st.text_area("Prompt (English only):", height=100)
        
        if st.button("Generate Video ⚡", key="text_btn"):
            if not prompt:
                st.warning("Prompt likhein!")
            else:
                with st.spinner("🎥 Video ban rahi hai..."):
                    # Payload setup
                    payload = {"inputs": prompt + ", 576x320, 24fps, 4k, high quality"}
                    video_data = generate_video_manual(MODEL_TEXT, payload)
                    
                    if video_data:
                        st.success("✅ Video Ban Gayi!")
                        st.video(video_data)

    # --- TAB 2: IMAGE ---
    with tab2:
        st.warning("⚠️ Free tier par Image model bohot busy rehta hai.")
        file = st.file_uploader("Image Upload", type=["jpg", "png"])
        
        if file and st.button("Animate Image ✨", key="img_btn"):
            image = Image.open(file)
            st.image(image, caption="Input", use_column_width=True)
            
            with st.spinner("⚡ Processing..."):
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_bytes = img_byte_arr.getvalue()
                
                video_data = generate_video_manual(MODEL_IMAGE, img_bytes, is_binary=True)
                if video_data:
                    st.success("✅ Animated!")
                    st.video(video_data)

if __name__ == "__main__":
    main()
    
