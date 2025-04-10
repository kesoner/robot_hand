#!/bin/bash

echo "=== 樹莓派手部追蹤接收程式安裝腳本 ==="
echo "正在更新系統套件..."
sudo apt-get update

# 檢查 Python 版本
echo "檢查 Python 版本..."
if command -v python3 &>/dev/null; then
    python3 --version
else
    echo "未找到 Python3，正在安裝..."
    sudo apt-get install -y python3 python3-pip
fi

# 檢查並創建虛擬環境
echo "檢查虛擬環境..."
if ! command -v virtualenv &>/dev/null; then
    echo "安裝 virtualenv..."
    python3 -m pip install virtualenv
fi

# 創建並啟動虛擬環境
if [ ! -d "venv" ]; then
    echo "創建虛擬環境..."
    python3 -m virtualenv venv
fi

echo "啟動虛擬環境..."
source venv/bin/activate

# 安裝必要套件
echo "安裝必要套件..."
pip install -r requirements.txt

echo "=== 安裝完成 ==="
echo "使用說明："
echo "1. 啟動虛擬環境："
echo "   source venv/bin/activate"
echo "2. 修改 receiver.py 中的 MQTT broker IP 地址"
echo "3. 運行程式："
echo "   python receiver.py"
echo "4. 結束程式：Ctrl+C"
echo "5. 退出虛擬環境："
echo "   deactivate" 