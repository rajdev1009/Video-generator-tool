import streamlit as st
import os
import time
from io import BytesIO
from PIL import Image
from huggingface_hub import InferenceClient

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Video Zeroscope", page_icon="🎬", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 100%; padding: 20px; }
    .stVideo { width: 100% !important; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- SETUP CLIENT ---
HF_TOKEN = os.environ.get("HF_TOKEN")

# Models
MODEL_TEXT = "cerspense/zeroscope_v2_576w"
MODEL_IMAGE = "stabilityai/stable-video-diffusion-img2vid-xt"

client = InferenceClient(token=HF_TOKEN)

def generate_video(model_id, inputs, is_binary=False):
    # Retry Logic
    for attempt in range(3):
        try:
            # ✅ FIX: 'model=' likhna zaroori hai (Keyword Argument)
            if is_binary:
                response = client.post(data=inputs, model=model_id)
            else:
                response = client.post(json={"inputs": inputs}, model=model_id)
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            
            # Cold Start Handling
            if "503" in error_msg or "loading" in error_msg.lower():
                wait_time = 25
                st.warning(f"⚠️ Server Jaag raha hai (Warming up)... {wait_time}s wait. (Try {attempt+1}/3)")
                time.sleep(wait_time)
                continue
            
            # Error display
            st.error(f"🚫 Attempt {attempt+1} Failed. Reason: {error_msg}")
            time.sleep(5)
    
    return None

def main():
    st.title("🎬 AI Video Generator (Zeroscope)")
    
    if not HF_TOKEN:
        st.error("🚨 Token Missing! Koyeb settings check karein.")
        return

    tab1, tab2 = st.tabs(["📝 Text-to-Video", "🖼️ Image-to-Video"])

    # --- TAB 1: TEXT ---
    with tab1:
        st.info("Best Prompt: 'A panda eating bamboo, high quality, 4k'")
        prompt = st.text_area("Prompt (English only):", height=100)
        
        if st.button("Generate Video ⚡", key="text_btn"):
            if not prompt:
                st.warning("Prompt likhein!")
            else:
                with st.spinner("🎥 Video ban rahi hai (Zeroscope)..."):
                    # Prompt enhancement
                    full_prompt = prompt + ", 576x320, 24fps, 4k, high quality"
                    video_data = generate_video(MODEL_TEXT, full_prompt)
                    
                    if video_data:
                        st.success("✅ Video Ban Gayi!")
                        st.video(video_data)

    # --- TAB 2: IMAGE ---
    with tab2:
        st.warning("⚠️ Note: Image-to-Video free tier par heavy load ki wajah se fail ho sakta hai.")
        file = st.file_uploader("Image Upload", type=["jpg", "png"])
        
        if file and st.button("Animate Image ✨", key="img_btn"):
            image = Image.open(file)
            st.image(image, caption="Input", use_column_width=True)
            
            with st.spinner("⚡ Processing..."):
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_bytes = img_byte_arr.getvalue()
                
                video_data = generate_video(MODEL_IMAGE, img_bytes, is_binary=True)
                if video_data:
                    st.success("✅ Animated!")
                    st.video(video_data)

if __name__ == "__main__":
    main()
    
