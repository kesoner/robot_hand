import paho.mqtt.client as mqtt
import json
import time

# MQTT設定
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "flex_glove/data"

# 當連接到MQTT broker時的回調函數
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code: " + str(rc))
    # 訂閱主題
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to topic: {MQTT_TOPIC}")

# 當收到訊息時的回調函數
def on_message(client, userdata, msg):
    try:
        # 解析JSON數據
        data = json.loads(msg.payload.decode())
        
        # 清空終端機並顯示數據
        print("\033[H\033[J")  # 清空螢幕
        print("接收到的手套數據:")
        print("-" * 40)
        print(f"拇指: {data['thumb']:3d}%  {'#' * (data['thumb']//2)}")
        print(f"食指: {data['index']:3d}%  {'#' * (data['index']//2)}")
        print(f"中指: {data['middle']:3d}%  {'#' * (data['middle']//2)}")
        print(f"無名: {data['ring']:3d}%  {'#' * (data['ring']//2)}")
        print(f"小指: {data['pinky']:3d}%  {'#' * (data['pinky']//2)}")
        print("-" * 40)
        
    except json.JSONDecodeError:
        print("Error: Invalid JSON data")
    except KeyError as e:
        print(f"Error: Missing key in data: {e}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    # 創建MQTT客戶端
    client = mqtt.Client()
    
    # 設置回調函數
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # 連接到MQTT broker
        print(f"Connecting to MQTT broker at {MQTT_BROKER}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # 開始接收訊息
        print("Starting message loop...")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        client.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 