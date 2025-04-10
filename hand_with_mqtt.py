import cv2
import mediapipe as mp
import numpy as np
import threading
from PIL import ImageFont, ImageDraw, Image
import time
import json
import os

from Mqtt_test import mqtt_publisher, mqtt_subscriber

# 初始化 MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# 加載中文字型
try:
    font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "中文字體", "NotoSansTC-VariableFont_wght.ttf")
    font = ImageFont.truetype(font_path, 16)  # 進一步減小字型大小
except Exception as e:
    print(f"無法載入字體: {str(e)}")
    print("使用預設字體")
    font = ImageFont.load_default()

# 計算夾角
def calculate_angle(a, b, c):
    """ 計算 B 點為中心，向量 BA 和 BC 之間的夾角 """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    cos_theta = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cos_theta, -1.0, 1.0))  # 避免數值誤差
    return np.degrees(angle)

def hand_camera():
    # 取得攝影機畫面
    cap = cv2.VideoCapture(0)
    
    # 設置最低的解析度
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
    
    # 設置最低的幀率
    cap.set(cv2.CAP_PROP_FPS, 5)
    
    # 初始化變數
    last_time = time.time()
    frame_count = 0
    fps = 0
    last_mqtt_time = time.time()
    mqtt_interval = 2.0  # 修改為每兩秒傳送一次
    last_hand_time = time.time()
    hand_interval = 0.1  # 手部追蹤更新間隔
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 計算 FPS
        frame_count += 1
        current_time = time.time()
        if current_time - last_time >= 1.0:
            fps = frame_count
            frame_count = 0
            last_time = current_time
        
        # 只在特定時間間隔進行手部追蹤
        if current_time - last_hand_time >= hand_interval:
            # 轉換 BGR 到 RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(frame_rgb)
            
            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    landmarks = hand_landmarks.landmark
                    
                    fingers = {
                        "拇指": [1, 2, 3, 4],
                        "食指": [5, 6, 7, 8],
                        "中指": [9, 10, 11, 12],
                        "無名指": [13, 14, 15, 16],
                        "小指": [17, 18, 19, 20]
                    }
                    
                    angles = {}
                    y_offset = 30  # 調整文字起始位置
                    
                    for name, indices in fingers.items():
                        mcp = [landmarks[indices[0]].x, landmarks[indices[0]].y, landmarks[indices[0]].z]
                        pip = [landmarks[indices[1]].x, landmarks[indices[1]].y, landmarks[indices[1]].z]
                        dip = [landmarks[indices[2]].x, landmarks[indices[2]].y, landmarks[indices[2]].z]
                        tip = [landmarks[indices[3]].x, landmarks[indices[3]].y, landmarks[indices[3]].z]
                        
                        pip_angle = calculate_angle(mcp, pip, dip)
                        dip_angle = calculate_angle(pip, dip, tip)
                        total_angle = pip_angle + dip_angle
                        
                        angles[name] = (pip_angle, dip_angle, total_angle)
                    
                    # 繪製中文字
                    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(img_pil)
                    
                    # 顯示 FPS 和效能資訊
                    draw.text((2, 2), f"FPS: {fps}", font=font, fill=(255, 255, 0))
                    draw.text((2, 20), f"Res: 160x120", font=font, fill=(255, 255, 0))
                    
                    for name, (pip_angle, dip_angle, total_angle) in angles.items():
                        text = f"{name} PIP:{int(pip_angle)}° DIP:{int(dip_angle)}° 總計:{int(180-(360-total_angle))}°"
                        draw.text((2, y_offset), text, font=font, fill=(255, 255, 0))
                        y_offset += 20  # 減小行間距
                    
                    # 只在特定時間間隔發送 MQTT 消息
                    if current_time - last_mqtt_time >= mqtt_interval:
                        # 建立包含所有手指數據的字典
                        all_fingers_data = {
                            "timestamp": time.time(),
                            "fingers": []
                        }
                        
                        for name, (pip_angle, dip_angle, total_angle) in angles.items():
                            finger_data = {
                                "name": name,
                                "pip_angle": float(pip_angle),
                                "dip_angle": float(dip_angle),
                                "total_angle": float(total_angle)
                            }
                            all_fingers_data["fingers"].append(finger_data)
                        
                        # 將所有手指數據轉換為 JSON 並發送
                        data_str = json.dumps(all_fingers_data)
                        mqtt_publisher(data_str)
                        print(f"📨 發送手部數據 (時間: {time.strftime('%H:%M:%S', time.localtime(time.time()))})")
                        last_mqtt_time = current_time
                    
                    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            
            last_hand_time = current_time
        
        cv2.imshow("Hand Tracking", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        # 啟動 MQTT 訂閱者線程
        subscriber_thread = threading.Thread(target=mqtt_subscriber)
        subscriber_thread.daemon = True
        subscriber_thread.start()

        # 啟動主程序
        hand_camera()
    except KeyboardInterrupt:
        print("\n程式結束")
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
    finally:
        cv2.destroyAllWindows()
    
