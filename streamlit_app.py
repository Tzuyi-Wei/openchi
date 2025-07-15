import streamlit as st
from PIL import Image
import numpy as np
import tensorflow as tf
import openai

# 🧠 你的模型標籤名稱（照你的訓練順序填）
CLASS_NAMES = ["狐狸與森林", "小熊與太陽", "小鳥與蘋果"]  # 改成你自己的！

# 1. 載入 Keras/TensorFlow 模型（只需做一次）
@st.cache_resource
def load_model():
    model = tf.keras.models.load_model("tm_model")  # tm_model/ 或 model.h5
    return model

model = load_model()

# 2. 設定 OpenAI API Key（填自己的）
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else "sk-..."  # 建議改成你的

st.title("🎨 AI 故事繪本生成 Demo")
st.write("上傳孩子畫作，自動分類主題，並由 GPT 生成三個故事和關鍵提問。")

uploaded_file = st.file_uploader("請上傳畫作圖片", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # 顯示上傳圖片
    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, caption="上傳的畫作", use_column_width=True)
    
    # 前處理：模型需 (224,224) 圖片
    img_resized = image.resize((224, 224))
    img_np = np.expand_dims(np.array(img_resized) / 255.0, axis=0)
    
    # AI 分類
    preds = model.predict(img_np)[0]
    idx = np.argmax(preds)
    label = CLASS_NAMES[idx]
    confidence = preds[idx]
    st.success(f"模型判斷主題：**{label}** (信心值：{confidence:.2f})")
    
    # GPT 生成三個故事＋一個提問
    prompt = (
        f"你是一個會為兒童畫作創作故事的繪本作家。這張畫的主題是「{label}」。"
        "請以這個主題為素材，生成三個簡短的童話故事開頭（每則 50 字以內），"
        "以及一個適合小朋友討論的提問。用 JSON 格式回傳：\n"
        '{"stories":[{"title":"","text":""},...],"question":""}'
    )
    if st.button("產生故事"):
        with st.spinner("AI 正在寫故事..."):
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            result = response["choices"][0]["message"]["content"]
            st.markdown("---")
            st.markdown("### GPT 生成故事：")
            st.markdown(result)
