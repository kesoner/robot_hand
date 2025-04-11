# Flex Sensor 手套控制器 (with MQTT)

這個專案實現了一個基於 ESP32 的智能手套，使用 flex sensors 來檢測手指的彎曲程度，並通過 MQTT 協議即時傳輸數據。

## 硬體需求

- ESP32 開發板
- 5個 Flex Sensors
- 5個 10kΩ 電阻（上拉電阻）
- 麵包板和連接線
- USB 數據線

## 接線圖

Flex Sensors 接線：
- 拇指 -> GPIO36 (VP)
- 食指 -> GPIO39 (VN)
- 中指 -> GPIO34
- 無名指 -> GPIO35
- 小指 -> GPIO32

每個 Flex Sensor 需要：
- 一端接 3.3V
- 一端接對應的 GPIO 和 10kΩ 上拉電阻
- 電阻另一端接地 (GND)

## 軟體需求

### ESP32 端
1. Arduino IDE
2. 必要的函式庫：
   - WiFi.h
   - PubSubClient.h
   - ArduinoJson.h

### 接收端（Python）
1. Python 3.x
2. 必要的套件：
   ```bash
   pip install paho-mqtt
   ```

## 設定和使用

### ESP32 程式設定
1. 打開 `flex_glove_mqtt.ino`
2. 修改 WiFi 設定：
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
3. 如果需要，修改 MQTT 設定：
   ```cpp
   const char* mqtt_broker = "broker.emqx.io";
   const int mqtt_port = 1883;
   const char* mqtt_topic = "flex_glove/data";
   ```
4. 上傳程式到 ESP32

### Python 接收程式
1. 運行接收程式：
   ```bash
   python mqtt_receiver.py
   ```
2. 程式會自動連接到 MQTT broker 並開始接收數據

## 數據格式

ESP32 發送的 JSON 數據格式：
```json
{
  "thumb": 45,    // 拇指彎曲度 (0-100)
  "index": 30,    // 食指彎曲度 (0-100)
  "middle": 20,   // 中指彎曲度 (0-100)
  "ring": 15,     // 無名指彎曲度 (0-100)
  "pinky": 10     // 小指彎曲度 (0-100)
}
```

## 校準說明

1. 上電後，程式會進入校準模式
2. 按照序列監視器的提示：
   - 當看到提示時將手指完全伸直
   - 等待 3 秒
   - 當看到提示時將手指完全彎曲
   - 等待 3 秒
3. 校準完成後，程式會開始正常運作

## 故障排除

1. ESP32 無法連接 WiFi
   - 確認 WiFi 設定是否正確
   - 確認 WiFi 訊號強度
   - 檢查序列監視器的錯誤訊息

2. 數據不準確
   - 重新進行校準
   - 檢查 flex sensors 的連接
   - 確認上拉電阻是否正確連接

3. Python 程式無法接收數據
   - 確認 ESP32 是否成功連接到 MQTT broker
   - 檢查網路連接
   - 確認訂閱的主題是否正確

## 注意事項

1. 使用 3.3V 供電，不要使用 5V
2. 確保所有接線牢固
3. 避免過度彎曲 flex sensors
4. 定期進行校準以保持準確度

## 授權

MIT License 