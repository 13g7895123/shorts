#!/bin/bash

# YouTube Shorts 管理系統 - 開發環境啟動腳本

echo "🚀 YouTube Shorts 管理系統啟動中..."
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤：未找到 Python 3"
    exit 1
fi

# 檢查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 錯誤：未找到 Node.js"
    exit 1
fi

# 檢查虛擬環境
if [ ! -d ".venv" ]; then
    echo "📦 創建 Python 虛擬環境..."
    python3 -m venv .venv
fi

# 啟動後端
echo "🔧 啟動後端 API 伺服器..."
source .venv/bin/activate
python src/ui/api_server.py &
BACKEND_PID=$!

# 等待後端啟動
sleep 3

# 啟動前端
echo "🎨 啟動前端開發伺服器..."
cd web
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 系統啟動完成！"
echo ""
echo "📊 前端界面: http://localhost:3000"
echo "🔌 後端 API:  http://localhost:8000"
echo "📖 API 文檔:  http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服務"

# 等待用戶中斷
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

wait
