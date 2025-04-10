# 樹莓派安裝指南

這份指南將幫助你從零開始設置樹莓派並運行手部追蹤接收程式。

## 1. 樹莓派初始設置

### 1.1 準備工作
需要的設備：
- 樹莓派（建議使用 Raspberry Pi 4）
- Micro SD 卡（建議 16GB 以上）
- 電源供應器
- 鍵盤、滑鼠（初始設置時需要）
- 顯示器（初始設置時需要）
- 網路連接（Wi-Fi 或網路線）

### 1.2 安裝作業系統
1. 下載 Raspberry Pi Imager：
   - 前往 https://www.raspberrypi.com/software/
   - 下載並安裝 Raspberry Pi Imager

2. 安裝系統：
   - 將 Micro SD 卡插入電腦
   - 打開 Raspberry Pi Imager
   - 選擇 "Raspberry Pi OS (32-bit)"
   - 選擇你的 SD 卡
   - 點擊 "寫入"

### 1.3 初始化設置
1. 將 SD 卡插入樹莓派
2. 連接顯示器、鍵盤、滑鼠
3. 接上電源
4. 依照畫面指示完成：
   - 選擇語言和地區
   - 設置使用者名稱和密碼
   - 連接 Wi-Fi
   - 更新系統

## 2. 網路設置

### 2.1 查看 IP 地址
1. 打開終端機，輸入：
```bash
ip addr show
```
2. 記下 `wlan0`（Wi-Fi）或 `eth0`（網路線）的 IP 地址

### 2.2 啟用 SSH（遠端連接）
1. 打開終端機
2. 輸入以下命令：
```bash
sudo raspi-config
```
3. 選擇 "Interface Options" → "SSH" → "Yes"
4. 重新啟動樹莓派：
```bash
sudo reboot
```

## 3. 安裝程式

### 3.1 從電腦傳送檔案到樹莓派
在你的電腦上執行：
```bash
# 替換 {樹莓派IP} 為你的樹莓派 IP 地址
scp -r robot_hand/raspberry_pi pi@{樹莓派IP}:/home/pi/
```

### 3.2 連接到樹莓派
```bash
ssh pi@{樹莓派IP}
```

### 3.3 安裝程式
```bash
cd /home/pi/raspberry_pi
chmod +x setup.sh
./setup.sh
```

## 4. 設置 MQTT

### 4.1 確認網路連接
1. 確保樹莓派和發送端（你的電腦）在同一個網路下
2. 在樹莓派上 ping 發送端：
```bash
ping {發送端IP}
```

### 4.2 修改接收程式設定
1. 編輯 receiver.py：
```bash
nano receiver.py
```
2. 修改 BROKER 變數為發送端 IP：
```python
BROKER = "192.168.x.x"  # 改為你電腦的 IP 地址
```
3. 儲存並離開（Ctrl+X，然後按 Y）

## 5. 運行程式

### 5.1 啟動虛擬環境
```bash
cd /home/pi/raspberry_pi
source venv/bin/activate
```

### 5.2 運行接收程式
```bash
python receiver.py
```

### 5.3 檢查運作狀況
- 確認終端機顯示 "已連接到 MQTT broker"
- 觀察是否收到手部追蹤數據
- 檢查數據格式是否正確

### 5.4 結束程式
- 按 Ctrl+C 結束程式
- 輸入 `deactivate` 退出虛擬環境

## 6. 故障排除

### 6.1 連接問題
如果無法連接到 MQTT broker：
1. 檢查網路連接：
```bash
ping 192.168.x.x  # 發送端 IP
```
2. 確認發送端程式正在運行
3. 檢查防火牆設定：
```bash
sudo ufw status
```

### 6.2 程式問題
如果程式無法運行：
1. 確認虛擬環境已啟動
2. 重新安裝套件：
```bash
pip install -r requirements.txt
```
3. 檢查錯誤訊息

### 6.3 中文顯示問題
如果出現亂碼：
1. 設置環境變數：
```bash
export PYTHONIOENCODING=utf8
```
2. 在 ~/.bashrc 中加入此設定：
```bash
echo "export PYTHONIOENCODING=utf8" >> ~/.bashrc
source ~/.bashrc
```

## 7. 自動啟動設置（選擇性）

如果想要樹莓派開機時自動運行程式：

1. 創建服務檔案：
```bash
sudo nano /etc/systemd/system/hand-receiver.service
```

2. 加入以下內容：
```ini
[Unit]
Description=Hand Tracking Receiver
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/raspberry_pi
ExecStart=/home/pi/raspberry_pi/venv/bin/python receiver.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. 啟用服務：
```bash
sudo systemctl enable hand-receiver
sudo systemctl start hand-receiver
```

4. 檢查狀態：
```bash
sudo systemctl status hand-receiver
``` 