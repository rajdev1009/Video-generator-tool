import streamlit as st
import os
import time
from io import BytesIO
from PIL import Image
from huggingface_hub import InferenceClient

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Video Final", page_icon="🎬", layout="centered")

# --- SETUP CLIENT ---
HF_TOKEN = os.environ.get("HF_TOKEN")

# ✅ NEW MODEL ID (Ali-Vilab is the new name for Damo)
MODEL_VIDEO = "ali-vilab/text-to-video-ms-1.7b"
MODEL_IMAGE = "stabilityai/stable-diffusion-xl-base-1.0"

client = InferenceClient(token=HF_TOKEN)

def generate_content(model_id, prompt, is_image=False):
    for attempt in range(3):
        try:
            # ✅ CORRECT SYNTAX (Keyword arguments only)
            if is_image:
                # Text-to-Image request
                image = client.text_to_image(prompt, model=model_id)
                return image
            else:
                # Text-to-Video request
                response = client.post(
                    json={"inputs": prompt}, 
                    model=model_id
                )
                return response
            
        except Exception as e:
            error_msg = str(e)
            
            # Cold Start (503)
            if "503" in error_msg or "loading" in error_msg.lower():
                st.toast(f"❄️ Model warming up... ({attempt+1}/3)")
                time.sleep(20)
                continue
            
            # 410 Gone / 404 Not Found
            if "410" in error_msg or "404" in error_msg:
                st.error(f"❌ Error: Model '{model_id}' temporary down hai.")
                return None
                
            st.warning(f"⚠️ Retry {attempt+1}...")
            time.sleep(5)
            
    st.error("❌ Server busy. Try again later.")
    return None

def main():
    st.title("🎬 AI Video Generator (Updated)")
    
    if not HF_TOKEN:
        st.error("🚨 HF_TOKEN missing!")
        return

    tab1, tab2 = st.tabs(["🎥 Text-to-Video", "🖼️ Text-to-Image"])

    # --- TAB 1: VIDEO (Updated Model) ---
    with tab1:
        st.subheader("Generate Video")
        prompt_video = st.text_area("Video Prompt (English):", height=100, placeholder="An astronaut riding a horse in space")
        
        if st.button("Generate Video 🚀", key="vid_btn"):
            if not prompt_video:
                st.warning("Prompt to likho!")
            else:
                with st.spinner("🎥 Video render ho rahi hai (Ali-Vilab Model)..."):
                    video_bytes = generate_content(MODEL_VIDEO, prompt_video, is_image=False)
                    if video_bytes:
                        st.success("✅ Video Success!")
                        st.video(video_bytes)

    # --- TAB 2: IMAGE (Backup) ---
    with tab2:
        st.subheader("Generate Image (Fast)")
        prompt_img = st.text_area("Image Prompt:", height=100, placeholder="Cyberpunk city")
        
        if st.button("Generate Image 📸", key="img_btn"):
            with st.spinner("🎨 Painting..."):
                image = generate_content(MODEL_IMAGE, prompt_img, is_image=True)
                if image:
                    st.success("✅ Image Created!")
                    st.image(image, use_column_width=True)

if __name__ == "__main__":
    main()
    
