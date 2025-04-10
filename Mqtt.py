import paho.mqtt.client as mqtt
import threading
import time
import json

# 設定 MQTT 伺服器
broker_address = "localhost"
port = 1883
topic_hand = "hand_tracking"  # 修改主題名稱

# ========== MQTT 接收程式 ========== #
def on_message(client, userdata, message):
    try:
        payload = message.payload.decode()
        data = json.loads(payload)
        
        # 檢查是否包含 fingers 陣列
        if isinstance(data, dict) and "fingers" in data and isinstance(data["fingers"], list):
            print("\n" + "="*50)
            print(f"📩 收到手部數據 (時間: {time.strftime('%H:%M:%S', time.localtime(data['timestamp']))})")
            print("-"*50)
            for finger in data["fingers"]:
                if isinstance(finger, dict) and all(k in finger for k in ['name', 'pip_angle', 'dip_angle', 'total_angle']):
                    print(f"【{finger['name']}】")
                    print(f"  ├─ PIP 角度: {float(finger['pip_angle']):.1f}°")
                    print(f"  ├─ DIP 角度: {float(finger['dip_angle']):.1f}°")
                    print(f"  └─ 總計角度: {float(finger['total_angle']):.1f}°")
                else:
                    print(f"⚠️ 手指數據格式不正確: {finger}")
            print("="*50 + "\n")
        else:
            print(f"⚠️ 數據格式不正確: {data}")
    except json.JSONDecodeError:
        print(f"⚠️ JSON 格式錯誤: {message.payload}")
    except Exception as e:
        pass  # 忽略錯誤訊息

def mqtt_subscriber():
    client = mqtt.Client()
    client.on_message = on_message
    
    try:
        print("🔄 正在連接到 MQTT 伺服器...")
        client.connect(broker_address, port, 60)
        client.subscribe(topic_hand)
        print(f"✅ 已訂閱主題: {topic_hand}")
        print("✅ MQTT 訂閱服務已啟動")
        client.loop_forever()
    except Exception as e:
        print(f"❌ 連接錯誤: {e}")

# ========== MQTT 發送程式 ========== #
def mqtt_publisher(data):
    client = mqtt.Client()
    
    try:
        client.connect(broker_address, port, 60)
        client.loop_start()
        
        json_data = json.dumps(data)
        client.publish(topic_hand, json_data)
        print(f"📨 發送手部數據 (時間: {time.strftime('%H:%M:%S', time.localtime(time.time()))})")
    except Exception as e:
        print(f"❌ 發送錯誤: {e}")
    
    client.loop_stop()
    client.disconnect()

# ========== 啟動多執行緒 ========== #
if __name__ == "__main__":
    # 啟動訂閱者執行緒
    subscriber_thread = threading.Thread(target=mqtt_subscriber)
    subscriber_thread.daemon = True  # 設為守護執行緒
    subscriber_thread.start()
    
    print("✅ MQTT 服務已啟動")