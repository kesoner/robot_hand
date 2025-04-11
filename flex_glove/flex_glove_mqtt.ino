#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi 設定
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Broker 設定
const char* mqtt_broker = "broker.emqx.io";
const int mqtt_port = 1883;
const char* mqtt_topic = "flex_glove/data";

// 建立 WiFi 和 MQTT 客戶端
WiFiClient espClient;
PubSubClient client(espClient);

// 定義 flex sensor 接腳
const int THUMB_PIN = 32;   // 拇指
const int INDEX_PIN = 33;   // 食指
const int MIDDLE_PIN = 34;  // 中指
const int RING_PIN = 35;    // 無名指
const int PINKY_PIN = 36;   // 小指

// 校準值結構
struct CalibrationValues {
    int straight;  // 手指伸直時的 ADC 值（約 1000-2000）
    int bent;      // 手指彎曲時的 ADC 值（約 2000-3000）
};

// 每個手指的校準值
CalibrationValues calibration[5] = {
    {0, 1000},  // 拇指的校準值範圍
    {0, 1000},  // 食指的校準值範圍
    {0, 1000},  // 中指的校準值範圍
    {0, 1000},  // 無名指的校準值範圍
    {0, 1000}   // 小指的校準值範圍
};

// 用於平滑化讀數的變數（減少數值跳動）
const int numReadings = 10;        // 平均值取樣數
int readings[5][numReadings];      // 儲存每個手指的最近 10 次讀數
int readIndex[5] = {0, 0, 0, 0, 0}; // 目前的讀數索引
int total[5] = {0, 0, 0, 0, 0};     // 讀數總和
float average[5] = {0, 0, 0, 0, 0}; // 平均值

// 時間控制
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 100;  // 每100ms發送一次數據

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n開始 Flex Sensor MQTT 測試");
    
    // 初始化平滑化陣列
    for (int finger = 0; finger < 5; finger++) {
        for (int i = 0; i < numReadings; i++) {
            readings[finger][i] = 0;
        }
    }
    
    // 連接 WiFi
    setupWiFi();
    
    // 設置 MQTT
    client.setServer(mqtt_broker, mqtt_port);
    
    // 開始校準程序
    calibrateSensors();
}

void loop() {
    // 確保 MQTT 連接
    if (!client.connected()) {
        reconnect();
    }
    client.loop();
    
    // 讀取並處理每個感測器的數據
    updateSensorReadings();
    
    // 每隔一段時間發送數據
    unsigned long currentTime = millis();
    if (currentTime - lastSendTime >= sendInterval) {
        // 準備 JSON 數據
        StaticJsonDocument<200> doc;
        
        // 儲存處理後的數值（0-100 範圍）
        doc["thumb"] = (int)average[0];   // 拇指彎曲度
        doc["index"] = (int)average[1];   // 食指彎曲度
        doc["middle"] = (int)average[2];  // 中指彎曲度
        doc["ring"] = (int)average[3];    // 無名指彎曲度
        doc["pinky"] = (int)average[4];   // 小指彎曲度
        
        String output;
        serializeJson(doc, output);
        
        // 發送到 MQTT
        client.publish(mqtt_topic, output.c_str());
        
        // 顯示發送的數據和原始 ADC 值
        Serial.print("發送數據: ");
        Serial.println(output);
        Serial.println("原始 ADC 值:");
        for (int i = 0; i < 5; i++) {
            Serial.print(readings[i][readIndex[i]]);
            Serial.print("\t");
        }
        Serial.println();
        
        lastSendTime = currentTime;
    }
}

void updateSensorReadings() {
    // 讀取每個感測器
    int sensorPins[] = {THUMB_PIN, INDEX_PIN, MIDDLE_PIN, RING_PIN, PINKY_PIN};
    
    for (int i = 0; i < 5; i++) {
        // 從感測器讀取 ADC 值（0-4095）
        int reading = analogRead(sensorPins[i]);
        
        // 更新平滑化數組
        total[i] = total[i] - readings[i][readIndex[i]];
        readings[i][readIndex[i]] = reading;
        total[i] = total[i] + reading;
        readIndex[i] = (readIndex[i] + 1) % numReadings;
        
        // 計算平均值
        average[i] = total[i] / numReadings;
        
        // 將 ADC 值映射到 0-100 範圍
        // 0 = 完全伸直
        // 100 = 完全彎曲
        average[i] = map(average[i], calibration[i].straight, calibration[i].bent, 0, 100);
        average[i] = constrain(average[i], 0, 100);  // 確保值在 0-100 範圍內
    }
}

void calibrateSensors() {
    Serial.println("開始校準...");
    Serial.println("此過程將設定每個手指的最大和最小值");
    delay(1000);
    
    Serial.println("請將手指完全伸直，等待 3 秒...");
    delay(3000);
    
    // 讀取伸直時的 ADC 值
    int sensorPins[] = {THUMB_PIN, INDEX_PIN, MIDDLE_PIN, RING_PIN, PINKY_PIN};
    for (int i = 0; i < 5; i++) {
        calibration[i].straight = analogRead(sensorPins[i]);
    }
    
    Serial.println("請將手指完全彎曲，等待 3 秒...");
    delay(3000);
    
    // 讀取彎曲時的 ADC 值
    for (int i = 0; i < 5; i++) {
        calibration[i].bent = analogRead(sensorPins[i]);
    }
    
    Serial.println("校準完成!");
    printCalibrationValues();
}

void printCalibrationValues() {
    Serial.println("校準值 (ADC 數值):");
    String fingerNames[] = {"拇指", "食指", "中指", "無名指", "小指"};
    for (int i = 0; i < 5; i++) {
        Serial.print(fingerNames[i]);
        Serial.print(" - 伸直: ");
        Serial.print(calibration[i].straight);
        Serial.print(" (ADC), 彎曲: ");
        Serial.print(calibration[i].bent);
        Serial.println(" (ADC)");
    }
}

void setupWiFi() {
    delay(10);
    Serial.println();
    Serial.print("連接到 WiFi: ");
    Serial.println(ssid);

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("");
    Serial.println("WiFi 已連接");
    Serial.println("IP 地址: ");
    Serial.println(WiFi.localIP());
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("嘗試 MQTT 連接...");
        String clientId = "ESP32FlexGlove-" + String(random(0xffff), HEX);
        
        if (client.connect(clientId.c_str())) {
            Serial.println("已連接");
        } else {
            Serial.print("連接失敗, rc=");
            Serial.print(client.state());
            Serial.println(" 5秒後重試");
            delay(5000);
        }
    }
} 
