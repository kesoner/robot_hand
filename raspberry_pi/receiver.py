import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# MQTT 設定
BROKER = "localhost"  # 改為發送端的 IP 地址
PORT = 1883
TOPIC = "hand_tracking"  # 與發送端相同的主題

class HandDataReceiver:
    def __init__(self):
        # 設置 MQTT 客戶端
        self.client = mqtt.Client("RaspberryPi_Receiver")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # 連接狀態
        self.connected = False
        
        # 最後接收的數據
        self.last_data = None
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ 已連接到 MQTT broker")
            self.client.subscribe(TOPIC)
            print(f"✅ 已訂閱主題: {TOPIC}")
            self.connected = True
        else:
            print(f"❌ 連接失敗 (錯誤碼: {rc})")
    
    def on_message(self, client, userdata, msg):
        try:
            # 解析接收到的數據
            data = json.loads(msg.payload.decode())
            
            # 格式化時間戳
            timestamp = datetime.fromtimestamp(data['timestamp'])
            time_str = timestamp.strftime("%H:%M:%S")
            
            print("\n" + "="*50)
            print(f"📩 接收時間: {time_str}")
            print("-"*50)
            
            # 顯示每個手指的角度數據
            for finger in data['fingers']:
                name = finger['name']
                pip = finger['pip_angle']
                dip = finger['dip_angle']
                total = finger['total_angle']
                
                # 計算彎曲程度（越接近180度越伸直）
                bend_percent = (180 - (360-total)) / 180 * 100
                bend_status = "伸直" if bend_percent > 80 else "彎曲" if bend_percent < 40 else "半彎曲"
                
                print(f"【{name}】")
                print(f"  ├─ PIP: {pip:.1f}°")
                print(f"  ├─ DIP: {dip:.1f}°")
                print(f"  ├─ 總角度: {total:.1f}°")
                print(f"  └─ 狀態: {bend_status} ({bend_percent:.1f}%)")
            
            print("="*50)
            
            # 保存最後接收的數據
            self.last_data = data
            
        except json.JSONDecodeError:
            print("❌ 無效的 JSON 格式")
        except Exception as e:
            print(f"❌ 處理錯誤: {str(e)}")
    
    def start(self):
        print(f"🔄 正在連接到 MQTT broker ({BROKER})...")
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n🛑 程式結束")
        except Exception as e:
            print(f"❌ 連接錯誤: {str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        if self.connected:
            self.client.disconnect()
            print("👋 已斷開連接")

def main():
    print("🤖 樹莓派手部追蹤數據接收器")
    print("="*50)
    print("📝 使用說明:")
    print("1. 確保發送端程式正在運行")
    print("2. 確認 MQTT broker 的 IP 位址正確")
    print("3. 按 Ctrl+C 可以結束程式")
    print("="*50)
    
    receiver = HandDataReceiver()
    receiver.start()

if __name__ == "__main__":
    main() 