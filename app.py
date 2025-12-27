import streamlit as st
import os
import time
from io import BytesIO
from PIL import Image
from huggingface_hub import InferenceClient

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Video Pro", page_icon="🎬", layout="centered")

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

# Models IDs
MODEL_TEXT = "damo-vilab/text-to-video-ms-1.7b"
MODEL_IMAGE = "stabilityai/stable-video-diffusion-img2vid-xt"

# Initialize Client (Yeh automatic connection sambhalega)
client = InferenceClient(token=HF_TOKEN)

def generate_video(model_id, inputs, is_binary=False):
    # Retry Logic (3 times)
    for attempt in range(3):
        try:
            if is_binary:
                # Image-to-Video
                response = client.post(model_id, data=inputs)
            else:
                # Text-to-Video
                response = client.post(model_id, json={"inputs": inputs})
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            
            # Agar Model Load ho raha hai (503)
            if "503" in error_msg or "loading" in error_msg.lower():
                st.warning(f"⚠️ Model load ho raha hai (Cold Start)... {20}s wait. (Try {attempt+1}/3)")
                time.sleep(20)
                continue
            
            # Agar koi aur error hai
            elif "404" in error_msg:
                st.error("❌ Error 404: Model temporarily down or moved by Hugging Face.")
                return None
            else:
                # Chhota error dikhayenge, technical detail chhupa denge
                st.warning(f"🔄 Server busy, retrying... ({attempt+1}/3)")
                time.sleep(5)
    
    st.error("❌ Server abhi response nahi de raha. Please 5 minute baad try karein.")
    return None

def main():
    st.title("🎬 AI Video Generator (Official API)")
    
    if not HF_TOKEN:
        st.error("🚨 HF_TOKEN environment variable missing hai!")
        return

    tab1, tab2 = st.tabs(["📝 Text-to-Video", "🖼️ Image-to-Video"])

    # --- TAB 1: TEXT ---
    with tab1:
        prompt = st.text_area("English Prompt:", height=100, placeholder="A dog running in the snow...")
        if st.button("Generate Video 🚀", key="text_btn"):
            if not prompt:
                st.warning("Prompt likhein!")
            else:
                with st.spinner("🎥 Video ban rahi hai..."):
                    video_data = generate_video(MODEL_TEXT, prompt)
                    if video_data:
                        st.success("✅ Success!")
                        st.video(video_data)

    # --- TAB 2: IMAGE ---
    with tab2:
        file = st.file_uploader("Image Upload (JPG/PNG)", type=["jpg", "png"])
        if file and st.button("Animate Image ✨", key="img_btn"):
            image = Image.open(file)
            st.image(image, caption="Input", use_column_width=True)
            
            with st.spinner("⚡ Processing heavy model..."):
                # Convert Image to Bytes
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_bytes = img_byte_arr.getvalue()
                
                video_data = generate_video(MODEL_IMAGE, img_bytes, is_binary=True)
                if video_data:
                    st.success("✅ Animated!")
                    st.video(video_data)

if __name__ == "__main__":
    main()
    
