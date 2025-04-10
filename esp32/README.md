# ESP32 手部追蹤機器手臂控制

這個專案使用 ESP32 接收手部追蹤數據並控制伺服馬達，實現機器手臂的動作模仿。

## 硬體需求

- ESP32 開發板
- 5個 SG90 伺服馬達（或類似規格）
- 麵包板和跳線
- USB 數據線
- 5V 電源供應器（建議使用外部電源供應伺服馬達）

## 接線圖

伺服馬達接線：
- 拇指 (Thumb) -> GPIO2
- 食指 (Index) -> GPIO4
- 中指 (Middle) -> GPIO5
- 無名指 (Ring) -> GPIO12
- 小指 (Pinky) -> GPIO13

注意：
- 所有伺服馬達的 VCC 建議接到外部 5V 電源
- 所有伺服馬達的 GND 需要和 ESP32 共地

## 軟體需求

### Arduino IDE 設置
1. 安裝 Arduino IDE
2. 添加 ESP32 開發板支援
   - 檔案 -> 偏好設定
   - 在"額外開發板管理器網址"中添加：
     `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - 工具 -> 開發板 -> 開發板管理器
   - 搜尋並安裝 "ESP32"

### 必要的程式庫
- WiFi.h (內建)
- PubSubClient (用於 MQTT)
- ArduinoJson (用於解析 JSON)
- ESP32Servo (用於控制伺服馬達)

安裝方法：
1. 工具 -> 管理程式庫
2. 搜尋並安裝：
   - "PubSubClient"
   - "ArduinoJson"
   - "ESP32Servo"

## 配置說明

在 `hand_receiver.ino` 中修改以下設定：

```cpp
// WiFi 設定
const char* ssid = "YOUR_WIFI_SSID";        // 改為你的 WiFi 名稱
const char* password = "YOUR_WIFI_PASSWORD"; // 改為你的 WiFi 密碼

// MQTT Broker 設定
const char* mqtt_broker = "YOUR_MQTT_BROKER_IP"; // 改為發送端電腦的 IP
```

## 使用方法

1. 按照接線圖連接硬體
2. 修改程式中的 WiFi 和 MQTT 設定
3. 編譯並上傳程式到 ESP32
4. 打開序列監視器（115200 baud）觀察連接狀態
5. 確認 MQTT 連接成功後，即可接收手部追蹤數據

## 程式說明

- 程式會自動連接 WiFi 和 MQTT broker
- 接收到手部追蹤數據後，會解析 JSON 格式
- 將每個手指的角度數據轉換為伺服馬達角度（0-180度）
- 控制對應的伺服馬達移動到指定位置

## 故障排除

1. 如果無法連接 WiFi：
   - 檢查 WiFi 名稱和密碼是否正確
   - 確認 ESP32 在 WiFi 範圍內

2. 如果無法連接 MQTT：
   - 確認 broker IP 地址正確
   - 檢查發送端程式是否正在運行
   - 確認 ESP32 和發送端在同一網路

3. 如果伺服馬達不動作：
   - 檢查接線是否正確
   - 確認電源供應是否足夠
   - 查看序列監視器的調試信息

4. 如果動作不準確：
   - 調整角度映射範圍
   - 檢查伺服馬達的機械限位
   - 可能需要進行角度校準

## 注意事項

1. 供電要求：
   - ESP32 建議使用 USB 供電
   - 伺服馬達建議使用獨立的 5V 電源供應器

2. 安全考慮：
   - 首次測試時，建議將伺服馬達機械結構拆離
   - 確保機械結構有適當的活動範圍
   - 注意伺服馬達的發熱情況

3. 優化建議：
   - 可以添加濾波來使動作更平滑
   - 可以設定死區來減少抖動
   - 可以添加緩動功能使動作更自然 