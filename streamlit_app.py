import streamlit as st
from PIL import Image
import numpy as np
import tensorflow as tf
import openai
import requests
from io import BytesIO
import json

ESP32_CAM_IP = "192.168.0.30"  # 你的攝影機 IP
CLASS_NAMES = ["小白", "小雞毛"]

@st.cache_resource
def load_model():
    return tf.keras.models.load_model("tm_model/keras_model.h5")
model = load_model()

try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.warning("未取得 OpenAI API 金鑰，請於 secrets.toml 設定 OPENAI_API_KEY")
    st.stop()

st.title("🎨 AI繪本故事自動生成 Demo (ESP32-CAM 即時連線)")

with st.container():
    st.header("👀 即時預覽與拍照")
    mjpeg_url = f"http://{ESP32_CAM_IP}:81/stream"
    st.markdown(
        f'<img src="{mjpeg_url}" width="320" />',
        unsafe_allow_html=True
    )
    st.caption(f"即時畫面來自：{ESP32_CAM_IP}")

    # 拍照後馬上辨識
    if st.button("拍照辨識"):
        with st.spinner("正在從 ESP32-CAM 拍照..."):
            try:
                r = requests.get(f"http://{ESP32_CAM_IP}/capture", timeout=5)
                img = Image.open(BytesIO(r.content))
                st.image(img, caption="拍照結果", use_column_width=True)
                # 分類
                img_resized = img.resize((224, 224))
                img_np = np.expand_dims(np.array(img_resized) / 255.0, axis=0)
                preds = model.predict(img_np)[0]
                idx = np.argmax(preds)
                label = CLASS_NAMES[idx]
                confidence = preds[idx]
                st.session_state['ai_label'] = label
                st.session_state['ai_conf'] = confidence
                st.session_state['last_img'] = img
                st.success(f"模型判斷主題：**{label}** (信心值：{confidence:.2f})")
            except Exception as e:
                st.error(f"取得照片失敗：{e}")
                st.stop()

# **只有辨識成功後才顯示下面選項**
if 'ai_label' in st.session_state and 'last_img' in st.session_state:
    st.header("🧠 AI 產生繪本故事")
    st.markdown(f"**辨識結果：{st.session_state['ai_label']} (信心值：{st.session_state['ai_conf']:.2f})**")

    story_morals = ["感恩", "孝順", "體貼他人", "勇敢", "誠實", "分享", "合作", "尊重", "包容"]
    selected_moral = st.selectbox("請選擇希望孩子學到的故事寓意", story_morals)

    if st.button("產生故事"):
        with st.spinner("AI 正在寫故事中..."):
            label = st.session_state['ai_label']
            img = st.session_state['last_img']

            prompt = (
                f"這是一張小朋友畫的畫作，主題是「{label}」。"
                f"請根據主題，以及「{selected_moral}」這個寓意，產生三個150字內、有起承轉合的童話故事，每個故事在轉折處插入一個適合啟發小朋友討論的問題（請獨立為一個欄位，不要夾在故事文字中）。"
                "請全部用繁體中文回答。"
                "請用以下json格式回覆：{\"stories\":[{\"title\":\"\",\"text\":\"\",\"question\":\"\"},...],\"summary_question\":\"\"}"
            )
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1024,
            )
            result_text = response["choices"][0]["message"]["content"]

            try:
                story_json = json.loads(result_text)
                st.markdown("---")
                st.markdown("### 🧸 AI 生成故事")
                for s in story_json.get("stories", []):
                    st.markdown(f"**{s['title']}**")
                    st.write(s['text'])
                    st.markdown(f"> 問題：{s['question']}")
                    st.markdown("---")
                st.markdown("#### 總結討論問題")
                st.info(story_json.get("summary_question", ""))
            except Exception as e:
                st.error("解析失敗，以下為原始回覆：")
                st.code(result_text, language="json")

st.info("確保 Streamlit 伺服器與 ESP32-CAM 在同一區網！")
