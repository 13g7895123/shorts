# YouTube Shorts 自動化管理系統

一個功能完整的 YouTube Shorts 自動化管理平台，整合爆款發現、AI 分析、影片生成和自動發布功能。

## ✨ 系統特色

### 🎯 核心功能
1. **爆款發現系統** - 自動監測熱門 Shorts、手動添加 URL、批量導入
2. **AI 智能分析** - Gemini AI 場景分析、情緒識別、優化建議
3. **影片管理** - 自動分類、元數據生成、多平台支援
4. **智能排程** - 最佳時間計算、佇列管理、自動上傳
5. **現代化 Web 界面** - Vue 3 前端、響應式設計、即時狀態更新

## 🚀 快速開始

### 一鍵啟動（推薦）
```bash
chmod +x start.sh && ./start.sh
```

### 訪問系統
- 🎨 前端界面: http://localhost:3000
- 🔌 後端 API: http://localhost:8000
- 📖 API 文檔: http://localhost:8000/docs

## 🛠️ 技術棧

**前端**: Vue 3 + Vite + Pinia + Vue Router + Axios  
**後端**: FastAPI + SQLAlchemy + Uvicorn  
**AI/API**: Google Gemini AI + YouTube Data API v3

## 📁 專案架構

```
youtube-short/
├── web/              # Vue 3 前端 (6個頁面)
├── src/ui/           # FastAPI 後端 API
├── src/discovery/    # 爆款發現模組
├── src/analysis/     # AI 分析模組
├── src/publishing/   # 發布管理模組
└── start.sh          # 啟動腳本
```

詳細文檔請查看 `web/README.md` 和 `PROGRESS_SUMMARY.md`
