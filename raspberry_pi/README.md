# 樹莓派手部追蹤接收程式

這個資料夾包含了用於樹莓派的程式，主要用於接收手部追蹤數據。

## 檔案說明

- `receiver.py`: 主要的接收程式，用於接收並顯示手部追蹤數據
- `requirements.txt`: 必要的 Python 套件清單
- `setup.sh`: 自動化安裝腳本

## 快速安裝

1. 將整個資料夾複製到樹莓派：
```bash
scp -r raspberry_pi pi@你的樹莓派IP:/home/pi/
```

2. SSH 連接到樹莓派：
```bash
ssh pi@你的樹莓派IP
```

3. 進入程式資料夾：
```bash
cd /home/pi/raspberry_pi
```

4. 給予安裝腳本執行權限：
```bash
chmod +x setup.sh
```

5. 執行安裝腳本：
```bash
./setup.sh
```

## 手動安裝步驟

如果自動安裝腳本無法正常運作，可以按照以下步驟手動安裝：

1. 更新系統套件：
```bash
sudo apt-get update
```

2. 安裝 Python 虛擬環境：
```bash
python3 -m pip install virtualenv
```

3. 創建並啟動虛擬環境：
```bash
python3 -m virtualenv venv
source venv/bin/activate
```

4. 安裝必要套件：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 啟動虛擬環境（如果尚未啟動）：
```bash
source venv/bin/activate
```

2. 修改 `receiver.py` 中的 MQTT broker 設定：
```python
BROKER = "192.168.x.x"  # 改為發送端（電腦）的 IP 地址
```

3. 運行程式：
```bash
python receiver.py
```

4. 結束程式：按 Ctrl+C

5. 退出虛擬環境：
```bash
deactivate
```

## 程式功能

- 自動連接到 MQTT broker
- 即時接收手部追蹤數據
- 顯示每個手指的角度資訊
- 計算並顯示手指的彎曲程度
- 支援中文顯示

## 數據格式

接收的數據格式為 JSON，包含：
- 時間戳
- 每個手指的：
  - PIP 角度
  - DIP 角度
  - 總角度
  - 彎曲狀態

## 故障排除

1. 如果無法連接到 MQTT broker：
   - 確認發送端（電腦）和樹莓派在同一個網路下
   - 檢查 IP 地址是否正確
   - 確認發送端的 MQTT broker 正在運行

2. 如果程式無法運行：
   - 確認虛擬環境已經啟動
   - 檢查所有必要套件是否已安裝
   - 查看錯誤訊息並根據提示進行處理

3. 如果顯示亂碼：
   - 確認終端機支援 UTF-8 編碼
   - 設置環境變數：`export PYTHONIOENCODING=utf8` 