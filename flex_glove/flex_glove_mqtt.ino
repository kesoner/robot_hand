#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi 設定
const char* ssid = "Kesonorn";
const char* password = "KS132842";

// MQTT Broker 設定
const char* mqtt_broker = "broker.emqx.io";  // 使用公共 MQTT broker
const int mqtt_port = 1883;
const char* mqtt_topic = "flex_glove/data";

// 建立 WiFi 和 MQTT 客戶端
WiFiClient espClient;
PubSubClient client(espClient);

// 定義 flex sensor 接腳
const int THUMB_PIN = 36;   // 拇指 (VP)
const int INDEX_PIN = 39;   // 食指 (VN)
const int MIDDLE_PIN = 34;  // 中指
const int RING_PIN = 35;    // 無名指
const int PINKY_PIN = 32;   // 小指

// 校準值
struct CalibrationValues {
    int straight;  // 手指伸直時的值
    int bent;      // 手指彎曲時的值
};

CalibrationValues calibration[5] = {
    {0, 1000},  // 拇指
    {0, 1000},  // 食指
    {0, 1000},  // 中指
    {0, 1000},  // 無名指
    {0, 1000}   // 小指
};

// 用於平滑化讀數的變數
const int numReadings = 10;
int readings[5][numReadings];
int readIndex[5] = {0, 0, 0, 0, 0};
int total[5] = {0, 0, 0, 0, 0};
float average[5] = {0, 0, 0, 0, 0};

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
        doc["thumb"] = (int)average[0];
        doc["index"] = (int)average[1];
        doc["middle"] = (int)average[2];
        doc["ring"] = (int)average[3];
        doc["pinky"] = (int)average[4];
        
        String output;
        serializeJson(doc, output);
        
        // 發送到 MQTT
        client.publish(mqtt_topic, output.c_str());
        
        // 顯示發送的數據
        Serial.print("發送數據: ");
        Serial.println(output);
        
        lastSendTime = currentTime;
    }
}

void updateSensorReadings() {
    // 讀取每個感測器
    int sensorPins[] = {THUMB_PIN, INDEX_PIN, MIDDLE_PIN, RING_PIN, PINKY_PIN};
    
    for (int i = 0; i < 5; i++) {
        // 從感測器讀取數值
        int reading = analogRead(sensorPins[i]);
        
        // 更新平滑化數組
        total[i] = total[i] - readings[i][readIndex[i]];
        readings[i][readIndex[i]] = reading;
        total[i] = total[i] + reading;
        readIndex[i] = (readIndex[i] + 1) % numReadings;
        
        // 計算平均值
        average[i] = total[i] / numReadings;
        
        // 將數值映射到 0-100 範圍
        average[i] = map(average[i], calibration[i].straight, calibration[i].bent, 0, 100);
        average[i] = constrain(average[i], 0, 100);
    }
}

void calibrateSensors() {
    Serial.println("開始校準...");
    delay(1000);
    
    Serial.println("請將手指伸直，等待 3 秒...");
    delay(3000);
    
    // 讀取伸直時的值
    int sensorPins[] = {THUMB_PIN, INDEX_PIN, MIDDLE_PIN, RING_PIN, PINKY_PIN};
    for (int i = 0; i < 5; i++) {
        calibration[i].straight = analogRead(sensorPins[i]);
    }
    
    Serial.println("請將手指彎曲，等待 3 秒...");
    delay(3000);
    
    // 讀取彎曲時的值
    for (int i = 0; i < 5; i++) {
        calibration[i].bent = analogRead(sensorPins[i]);
    }
    
    Serial.println("校準完成!");
    printCalibrationValues();
}

void printCalibrationValues() {
    Serial.println("校準值:");
    String fingerNames[] = {"拇指", "食指", "中指", "無名指", "小指"};
    for (int i = 0; i < 5; i++) {
        Serial.print(fingerNames[i]);
        Serial.print(" - 伸直: ");
        Serial.print(calibration[i].straight);
        Serial.print(", 彎曲: ");
        Serial.println(calibration[i].bent);
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