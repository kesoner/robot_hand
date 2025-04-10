import paho.mqtt.client as mqtt
import threading
import time
import json

# MQTT 設定
BROKER = "localhost"
PORT = 1883
TOPIC = "test/message"

class MQTTTest:
    def __init__(self):
        # 設置訂閱者
        self.subscriber = mqtt.Client("Subscriber")
        self.subscriber.on_connect = self.on_connect
        self.subscriber.on_message = self.on_message
        
        # 設置發布者
        self.publisher = mqtt.Client("Publisher")
        
        # 連接狀態
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ MQTT 連接成功")
            self.subscriber.subscribe(TOPIC)
            print(f"✅ 已訂閱主題: {TOPIC}")
            self.connected = True
        else:
            print(f"❌ 連接失敗 (錯誤碼: {rc})")
    
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            print(f"📩 收到: {data}")
        except:
            print(f"❌ 無效的訊息格式")
    
    def start(self):
        # 連接訂閱者
        print("🔄 正在連接到 MQTT...")
        self.subscriber.connect(BROKER, PORT)
        self.subscriber.loop_start()
        
        # 連接發布者
        self.publisher.connect(BROKER, PORT)
        
        # 等待連接成功
        time.sleep(1)
        
        # 開始發送測試訊息
        count = 1
        try:
            while True:
                if self.connected:
                    message = {
                        "id": count,
                        "time": time.strftime("%H:%M:%S"),
                        "data": f"測試訊息 {count}"
                    }
                    
                    # 發送訊息
                    self.publisher.publish(TOPIC, json.dumps(message, ensure_ascii=False))
                    print(f"📤 發送: {message}")
                    count += 1
                
                time.sleep(1)  # 每秒發送一次
                
        except KeyboardInterrupt:
            print("\n🛑 程式結束")
        finally:
            self.stop()
    
    def stop(self):
        self.subscriber.loop_stop()
        self.subscriber.disconnect()
        self.publisher.disconnect()

if __name__ == "__main__":
    mqtt_test = MQTTTest()
    mqtt_test.start()
