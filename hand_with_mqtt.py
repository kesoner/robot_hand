import cv2
import mediapipe as mp
import numpy as np
import threading
from PIL import ImageFont, ImageDraw, Image
import time
import json
import os
import logging
import base64
from Mqtt import mqtt_publisher, mqtt_subscriber

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 手機攝像頭設置
MOBILE_CAMERA_IP = "10.219.83.13"  # 手機 IP 地址
MOBILE_CAMERA_PORT = 8080  # IP Webcam 的預設端口
MOBILE_CAMERA_URL = f"http://{MOBILE_CAMERA_IP}:{MOBILE_CAMERA_PORT}/video"  # 使用 /video URL

# 設置攝像頭參數（根據測試結果）
CAMERA_WIDTH = 640  # 減小解析度以提高性能
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# 使用預設字體
font = ImageFont.load_default()

# 初始化 MediaPipe
try:
    # 設置 MediaPipe 參數
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    mp_draw = mp.solutions.drawing_utils
    
    # 等待 MediaPipe 初始化完成
    time.sleep(2)
    
    logger.info("MediaPipe 初始化完成")
except Exception as e:
    logger.error(f"初始化 MediaPipe 時發生錯誤: {str(e)}")
    raise

# 計算角度的函數
def calculate_angle(a, b, c):
    """計算三點之間的角度（2D）
    
    Args:
        a: 點 A 的座標 (x, y)
        b: 點 B 的座標 (x, y) - 中間點
        c: 點 C 的座標 (x, y)
    
    Returns:
        float: 角度（度數）
    """
    # 計算向量
    ba = np.array(b) - np.array(a)
    bc = np.array(c) - np.array(b)
    
    # 計算餘弦值
    cos_theta = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    
    # 計算角度並轉換為度數
    angle = np.arccos(np.clip(cos_theta, -1.0, 1.0))  # 避免數值誤差
    return np.degrees(angle)

def init_camera():
    """Initialize camera"""
    print(f"Connecting to mobile camera: {MOBILE_CAMERA_URL}")
    
    # Only use mobile camera
    cap = cv2.VideoCapture(MOBILE_CAMERA_URL)
    if not cap.isOpened():
        print(f"❌ Failed to connect to mobile camera ({MOBILE_CAMERA_URL})")
        return None
    
    print(f"✅ Successfully connected to mobile camera ({MOBILE_CAMERA_URL})")
    
    # Set camera parameters
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
    
    # Check if parameters are set successfully
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Parameters after setting - Width: {width}, Height: {height}, FPS: {fps}")

    return cap

# 主程序函數
def hand_camera():
    # 初始化攝像頭
    cap = init_camera()
    if cap is None:
        logger.error("無法初始化攝像頭")
        return
    
    # 初始化變數
    last_time = time.time()
    frame_count = 0
    fps = 0
    last_mqtt_time = time.time()
    mqtt_interval = 2.0  # 每兩秒傳送一次
    last_hand_time = time.time()
    hand_interval = 0.1  # 手部追蹤更新間隔
    
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                logger.error("無法讀取攝像頭畫面")
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
                            # 取得關節座標，並轉換為相對座標
                            mcp = [landmarks[indices[0]].x * frame.shape[1], landmarks[indices[0]].y * frame.shape[0]]
                            pip = [landmarks[indices[1]].x * frame.shape[1], landmarks[indices[1]].y * frame.shape[0]]
                            dip = [landmarks[indices[2]].x * frame.shape[1], landmarks[indices[2]].y * frame.shape[0]]
                            tip = [landmarks[indices[3]].x * frame.shape[1], landmarks[indices[3]].y * frame.shape[0]]
                            
                            # 計算角度
                            pip_angle = calculate_angle(mcp, pip, dip)
                            dip_angle = calculate_angle(pip, dip, tip)
                            
                            # 確保角度在合理範圍內
                            pip_angle = min(max(pip_angle, 0), 180)
                            dip_angle = min(max(dip_angle, 0), 180)
                            
                            # 計算總角度
                            total_angle = pip_angle + dip_angle
                            if total_angle > 180:
                                total_angle = 180
                            
                            angles[name] = (pip_angle, dip_angle, total_angle)
                        
                        # 繪製中文字
                        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        draw = ImageDraw.Draw(img_pil)
                        
                        # 顯示 FPS 和效能資訊
                        draw.text((2, 2), f"FPS: {fps}", font=font, fill=(255, 255, 0))
                        draw.text((2, 20), f"Res: {CAMERA_WIDTH}x{CAMERA_HEIGHT}", font=font, fill=(255, 255, 0))
                        
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
                            try:
                                data_str = json.dumps(all_fingers_data)
                                mqtt_publisher(data_str)
                                print(f"📨 發送手部數據 (時間: {time.strftime('%H:%M:%S', time.localtime(time.time()))})")
                            except Exception as e:
                                logger.error(f"發送 MQTT 數據時發生錯誤: {str(e)}")
                                logger.error(f"數據格式: {data_str}")
                            last_mqtt_time = current_time
                        
                        frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
                
                last_hand_time = current_time
            
            # 顯示視頻幀
            cv2.imshow("Hand Tracking", frame)
            
            # 檢查退出條件
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
        except Exception as e:
            logger.error(f"處理攝像頭畫面時發生錯誤: {str(e)}")
            break
    
    # 清理資源
    cap.release()
    cv2.destroyAllWindows()

def init_camera():
    """Initialize camera"""
    print(f"Connecting to mobile camera: {MOBILE_CAMERA_URL}")
    
    # Only use mobile camera
    cap = cv2.VideoCapture(MOBILE_CAMERA_URL)
    if not cap.isOpened():
        print(f"❌ Failed to connect to mobile camera ({MOBILE_CAMERA_URL})")
        return None
    
    print(f"✅ Successfully connected to mobile camera ({MOBILE_CAMERA_URL})")
    
    # Set camera parameters
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
    
    # Check if parameters are set successfully
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Parameters after setting - Width: {width}, Height: {height}, FPS: {fps}")

    return cap

# 主程序函數
def hand_camera():
    # 初始化攝像頭
    cap = init_camera()
    if cap is None:
        print("❌ 無法初始化攝像頭")
        return
    
# 不需要重複設置相機參數，因為已經在 init_camera() 中設置過了
    # 使用 init_camera() 中設置的解析度和幀率
    
    # 初始化變數
    last_time = time.time()
    frame_count = 0
    fps = 0
    last_mqtt_time = time.time()
    mqtt_interval = 2.0  # 每兩秒傳送一次
    last_hand_time = time.time()
    hand_interval = 0.3  # 增加手部追蹤更新間隔到0.3秒
    last_angles = {}  # 用於存儲上一幀的角度
    angle_smoothing = 0.3  # 角度平滑參數（0.0-1.0）
    
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
                    
                    # 使用數字編碼替代中文字符
                    fingers = {
                        0: [1, 2, 3, 4],    # 拇指
                        1: [5, 6, 7, 8],    # 食指
                        2: [9, 10, 11, 12], # 中指
                        3: [13, 14, 15, 16],# 無名指
                        4: [17, 18, 19, 20] # 小指
                    }
                    
                    angles = {}
                    y_offset = 30  # 調整文字起始位置
                    
                    for name, indices in fingers.items():
                        # 取得關節座標，只使用 x, y 座標
                        mcp = [landmarks[indices[0]].x, landmarks[indices[0]].y]
                        pip = [landmarks[indices[1]].x, landmarks[indices[1]].y]
                        dip = [landmarks[indices[2]].x, landmarks[indices[2]].y]
                        tip = [landmarks[indices[3]].x, landmarks[indices[3]].y]
                        
                        # 計算角度
                        pip_angle = calculate_angle(mcp, pip, dip)
                        dip_angle = calculate_angle(pip, dip, tip)
                        
                        # 計算總角度
                        total_angle = pip_angle + dip_angle
                        if total_angle > 180:
                            total_angle = 180
                        
                        # 如果有上一幀的角度，進行平滑處理
                        if name in last_angles:
                            last_pip, last_dip, last_total = last_angles[name]
                            pip_angle = pip_angle * angle_smoothing + last_pip * (1 - angle_smoothing)
                            dip_angle = dip_angle * angle_smoothing + last_dip * (1 - angle_smoothing)
                            total_angle = total_angle * angle_smoothing + last_total * (1 - angle_smoothing)
                        
                        angles[name] = (pip_angle, dip_angle, total_angle)
                        last_angles[name] = angles[name]
                    
                    # 繪製中文字
                    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(img_pil)
                    
                    # 顯示 FPS 和效能資訊
                    draw.text((2, 2), f"FPS: {fps}", font=font, fill=(255, 255, 0))
                    # 顯示解析度和幀率
                    draw.text((2, 20), f"Res: {frame.shape[1]}x{frame.shape[0]}", font=font, fill=(255, 255, 0))
                    draw.text((2, 40), f"FPS: {fps}", font=font, fill=(255, 255, 0))
                    
                    # 在顯示時將數字轉換回中文字符
                    finger_names = ["拇指", "食指", "中指", "無名指", "小指"]
                    for idx, (pip_angle, dip_angle, total_angle) in angles.items():
                        name = finger_names[idx]
                        text = f"{name} PIP:{int(pip_angle)}° DIP:{int(dip_angle)}° 總計:{int(total_angle)}°"
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
                            # 使用數字編碼替代中文字符
                            finger_data = {
                                "finger_id": idx,
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
