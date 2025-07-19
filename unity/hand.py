import cv2
import mediapipe as mp
import math
import socket

# ====== UDP 參數 ======
UDP_IP = ""
UDP_PORT = 65432
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ====== MediaPipe Hands 初始化 ======
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=2,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

def distance(lm1, lm2, w, h):
    x1, y1 = int(lm1.x * w), int(lm1.y * h)
    x2, y2 = int(lm2.x * w), int(lm2.y * h)
    return math.hypot(x2 - x1, y2 - y1)

def finger_status(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    pips = [2, 6, 10, 14, 18]
    status = []
    for tip, pip in zip(tips, pips):
        if tip == 4:
            status.append(hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x)
        else:
            status.append(hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y)
    return status

prev_gesture = ""

while True:
    ret, frame = cap.read()
    if not ret:
        break
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    h, w, _ = frame.shape

    gesture = "Detecting..."

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            fingers = finger_status(hand_landmarks)

            # 1. OK
            dist = distance(hand_landmarks.landmark[4], hand_landmarks.landmark[8], w, h)
            ok_cond = dist < 35
            mid_up = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
            ring_up = hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y
            pinky_up = hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y
            if ok_cond and mid_up and ring_up and pinky_up:
                gesture = "OK"
            # 2. YA
            elif fingers == [False, True, True, False, False]:
                gesture = "YA"
            # 3. 拇指右
            elif (fingers == [True, False, False, False, False] and
                  hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x and
                  hand_landmarks.landmark[8].y > hand_landmarks.landmark[6].y and
                  hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y and
                  hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y and
                  hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y):
                gesture = "THUMB_RIGHT"
            # 4. 張開
            elif fingers == [True, True, True, True, True]:
                gesture = "OPEN"

            cv2.putText(frame, gesture, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.7, (0, 255, 255), 3)

            # ============ 發送 UDP，只在偵測結果改變時發送 ============
            if gesture != prev_gesture and gesture != "Detecting...":
                sock.sendto(gesture.encode(), (UDP_IP, UDP_PORT))
                print(f"發送手勢：{gesture}")
                prev_gesture = gesture
            # ========================================================

    cv2.imshow('Hand Gesture', frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
