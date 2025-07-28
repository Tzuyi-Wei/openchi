import cv2
import requests
import firebase_admin
from firebase_admin import credentials, storage
import numpy as np

# Firebase 設定
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'openhci-64132.firebasestorage.app'
})
bucket = storage.bucket()

# 相機 IP
CAMERA_URL = 'http://192.168.0.239/capture'

def fetch_frame():
    try:
        response = requests.get(CAMERA_URL, timeout=5)
        if response.status_code == 200:
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame, response.content
        else:
            print("⚠️ 錯誤狀態碼:", response.status_code)
            return None, None
    except Exception as e:
        print("❌ 擷取影像失敗:", e)
        return None, None

def upload_latest(image_bytes):
    try:
        blob = bucket.blob("captures/latest.jpg")
        blob.upload_from_string(image_bytes, content_type='image/jpeg')
        blob.make_public()
        print("✅ 最新圖片已上傳並覆蓋")
        print("📎 連結：", blob.public_url)
    except Exception as e:
        print("❌ 上傳失敗:", e)

# 主迴圈
print("📡 正在連接 ESP32-CAM 即時影像，按 y 拍照上傳，q 離開")

while True:
    frame, raw_bytes = fetch_frame()
    if frame is not None:
        cv2.imshow("ESP32-CAM Live", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('y'):
            print("📸 拍照並上傳中...")
            upload_latest(raw_bytes)
        elif key == ord('q'):
            print("👋 離開程式")
            break

cv2.destroyAllWindows()
