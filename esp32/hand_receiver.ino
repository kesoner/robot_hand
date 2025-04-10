#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Servo.h>

// WiFi 設定
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Broker 設定
const char* mqtt_broker = "YOUR_MQTT_BROKER_IP";
const int mqtt_port = 1883;
const char* mqtt_topic = "hand_tracking";

// 建立 WiFi 和 MQTT 客戶端
WiFiClient espClient;
PubSubClient client(espClient);

// 伺服馬達設定
Servo thumb;    // 拇指
Servo index;    // 食指
Servo middle;   // 中指
Servo ring;     // 無名指
Servo pinky;    // 小指

// 伺服馬達腳位
const int THUMB_PIN = 2;   // GPIO2
const int INDEX_PIN = 4;   // GPIO4
const int MIDDLE_PIN = 5;  // GPIO5
const int RING_PIN = 12;   // GPIO12
const int PINKY_PIN = 13;  // GPIO13

// JSON 文件大小
const int capacity = JSON_OBJECT_SIZE(50);

void setup() {
    // 初始化序列通訊
    Serial.begin(115200);
    
    // 設置伺服馬達
    thumb.attach(THUMB_PIN);
    index.attach(INDEX_PIN);
    middle.attach(MIDDLE_PIN);
    ring.attach(RING_PIN);
    pinky.attach(PINKY_PIN);
    
    // 初始化所有手指位置
    resetFingers();
    
    // 連接 WiFi
    setupWiFi();
    
    // 設置 MQTT
    client.setServer(mqtt_broker, mqtt_port);
    client.setCallback(callback);
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();
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

void callback(char* topic, byte* payload, unsigned int length) {
    // 建立 JSON 緩衝區
    StaticJsonDocument<capacity> doc;
    
    // 將接收到的數據轉換為字串
    char message[length + 1];
    memcpy(message, payload, length);
    message[length] = '\0';
    
    // 解析 JSON
    DeserializationError error = deserializeJson(doc, message);
    
    if (error) {
        Serial.print("JSON 解析失敗: ");
        Serial.println(error.c_str());
        return;
    }
    
    // 處理手指數據
    JsonArray fingers = doc["fingers"];
    for (JsonObject finger : fingers) {
        const char* name = finger["name"];
        float total_angle = finger["total_angle"];
        
        // 將角度轉換為伺服馬達角度（0-180）
        int servo_angle = map(int(180 - (360-total_angle)), 0, 180, 0, 180);
        
        // 控制對應的伺服馬達
        if (strcmp(name, "拇指") == 0) {
            thumb.write(servo_angle);
        } else if (strcmp(name, "食指") == 0) {
            index.write(servo_angle);
        } else if (strcmp(name, "中指") == 0) {
            middle.write(servo_angle);
        } else if (strcmp(name, "無名指") == 0) {
            ring.write(servo_angle);
        } else if (strcmp(name, "小指") == 0) {
            pinky.write(servo_angle);
        }
        
        // 輸出調試信息
        Serial.print(name);
        Serial.print(": ");
        Serial.println(servo_angle);
    }
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("嘗試 MQTT 連接...");
        String clientId = "ESP32Client-" + String(random(0xffff), HEX);
        
        if (client.connect(clientId.c_str())) {
            Serial.println("已連接");
            client.subscribe(mqtt_topic);
        } else {
            Serial.print("連接失敗, rc=");
            Serial.print(client.state());
            Serial.println(" 5秒後重試");
            delay(5000);
        }
    }
}

void resetFingers() {
    // 將所有手指設置到初始位置
    thumb.write(0);
    index.write(0);
    middle.write(0);
    ring.write(0);
    pinky.write(0);
    delay(1000);
} 