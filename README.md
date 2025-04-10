# 手部追蹤與 MQTT 通訊系統

這是一個使用 MediaPipe 進行手部追蹤並結合 MQTT 通訊的系統，可以即時追蹤手部動作並將數據傳送到 MQTT 伺服器。

## 功能特點

- 即時手部追蹤
- 手指關節角度計算
- MQTT 即時數據傳輸
- 視覺化介面顯示

## 環境設置

### 方法一：使用 Conda 環境（推薦）

1. 安裝 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 [Anaconda](https://www.anaconda.com/download)
2. 在專案目錄下執行：
   ```bash
   conda env create -f environment.yml
   ```
3. 啟用環境：
   ```bash
   conda activate robot_hand
   ```

### 方法二：使用 pip 安裝

1. 確保已安裝 Python 3.9 或更新版本
2. 在專案目錄下執行：
   ```bash
   pip install -r requirements.txt
   ```

## 系統需求

- Python 3.9 或更新版本
- OpenCV (cv2) 4.8.1.78
- MediaPipe 0.10.8
- Paho MQTT Client 1.6.1
- NumPy 1.26.2
- PIL (Python Imaging Library) 10.1.0

## 使用說明

1. 確保已安裝所有必要的依賴套件
2. 確認 MQTT 伺服器已啟動並可連接
3. 執行主程式：
   ```bash
   python main.py
   ```
4. 程式會開啟攝影機並開始追蹤手部動作
5. 按 'q' 鍵可結束程式

## 數據格式

程式會將每根手指的數據以 JSON 格式發布到 MQTT 伺服器，格式如下：

```json
{
    "name": "手指名稱",
    "pip_angle": PIP角度,
    "dip_angle": DIP角度,
    "total_angle": 總計角度
}
```

## 手指追蹤說明

程式會追蹤以下五根手指：
- 拇指 (Thumb)
- 食指 (Index)
- 中指 (Middle)
- 無名指 (Ring)
- 小指 (Pinky)

每根手指會計算三個角度：
- PIP (近端指間關節) 角度
- DIP (遠端指間關節) 角度
- 總計角度

## 注意事項

- 確保攝影機可以正常運作
- 使用時請保持適當的照明
- 手部應保持在攝影機視野範圍內
- 建議在背景較為單純的環境中使用
- 建議使用 Conda 環境以避免套件衝突

## 授權

本專案採用 MIT 授權條款 