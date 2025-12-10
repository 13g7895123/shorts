# YouTube Shorts 自動化系統 - 快速入門

本指南將幫助您快速開始使用 YouTube Shorts 自動化生產系統。

---

## 📋 前置需求

- Python 3.12+
- `uv` (Python 套件管理器)
- YouTube Data API Key
- Gemini AI API Key (用於影片分析)
- Sora API Key (待實作，用於影片生成)

---

## 🚀 快速開始

### 1. 設置環境變數

複製 `.env.example` 並重命名為 `.env`：

```bash
cp .env.example .env
```

編輯 `.env` 文件，填入您的 API Keys：

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
SORA_API_KEY=your_sora_api_key_here
```

### 2. 安裝依賴

```bash
uv pip install -r requirements.txt
```

### 3. 初始化數據庫

```bash
uv run alembic upgrade head
```

---

## 📖 基本使用

### 發現爆款 Shorts

自動掃描 YouTube 尋找病毒式傳播的 Shorts：

```bash
uv run python scripts/01_discover_viral.py
```

這會：
- 掃描多個類別的熱門影片
- 篩選出 Shorts (≤60秒)
- 計算病毒傳播速度 (VPH)
- 自動存入數據庫

### 手動添加影片 URL

**添加單一 URL：**

```bash
uv run python scripts/02_add_urls.py \
  --url "https://youtube.com/shorts/xyz123" \
  --title "Amazing Short" \
  --channel "Cool Channel"
```

**批量導入：**

```bash
# 從 CSV 文件
uv run python scripts/02_add_urls.py --file videos.csv

# 從 JSON 文件
uv run python scripts/02_add_urls.py --file videos.json
```

**CSV 格式範例：**
```csv
url,title,channel,views,likes,duration
https://youtube.com/shorts/abc123,Title 1,Channel A,1000000,50000,45
https://youtube.com/shorts/def456,Title 2,Channel B,2000000,75000,55
```

### 分析影片

**分析單一影片：**

```bash
uv run python scripts/03_analyze_video.py \
  --video-id 1 \
  --generate-prompts \
  --style realistic
```

**批量分析：**

```bash
uv run python scripts/03_analyze_video.py \
  --batch \
  --limit 10 \
  --generate-prompts
```

分析將會：
- 使用 Gemini AI 分析影片場景
- 生成詳細的場景描述
- 創建 Sora 影片生成提示詞
- 生成標題、描述和標籤
- 保存結果到 `data/analysis/`

---

## 📊 查看數據庫狀態

使用 Python 直接查詢：

```python
from src.storage.database import get_session
from src.storage.repositories.video_repo import VideoRepository
from src.storage.repositories.analytics_repo import AnalyticsRepository

with get_session() as session:
    # 獲取所有影片
    videos = VideoRepository.get_all(session, limit=10)
    
    # 獲取待處理的影片
    pending = VideoRepository.get_pending_urls(session)
    
    # 獲取統計數據
    stats = AnalyticsRepository.get_statistics(session)
    print(stats)
```

---

## 🎨 風格選項

分析和生成時可選擇的風格：

- `realistic` - 寫實風格（默認）
- `animated` - 動畫風格
- `artistic` - 藝術風格
- `cinematic` - 電影風格

---

## 📁 輸出文件

### 分析結果
存放在 `data/analysis/`：

- `analysis_{video_id}_{timestamp}.json` - 場景分析
- `generation_plan_{video_id}_{timestamp}.json` - 生成計劃

### 日誌文件
存放在 `logs/`：

- `discovery/` - 爆款發現日誌
- `analysis/` - 分析相關日誌
- `errors/` - 錯誤日誌

---

## 🔍 常見任務

### 查看待處理的影片

```python
from src.storage.database import get_session
from src.storage.repositories.video_repo import VideoRepository
from src.storage.models import VideoStatus

with get_session() as session:
    pending = VideoRepository.get_by_status(session, VideoStatus.PENDING)
    print(f"待處理影片數量: {len(pending)}")
    
    for video in pending:
        print(f"- {video.title} ({video.url})")
```

### 更新影片狀態

```python
from src.storage.database import get_session
from src.storage.repositories.video_repo import VideoRepository
from src.storage.models import VideoStatus

with get_session() as session:
    VideoRepository.update_status(session, video_id=1, status=VideoStatus.ANALYZING)
```

### 獲取統計數據

```python
from src.storage.database import get_session
from src.storage.repositories.analytics_repo import AnalyticsRepository

with get_session() as session:
    stats = AnalyticsRepository.get_statistics(session, days=7)
    print(f"過去7天統計:")
    print(f"- 發現影片: {stats['video_status_counts']['pending']}")
    print(f"- 已分析: {stats['video_status_counts']['analyzed']}")
```

---

## ⚠️ 注意事項

### API 配額限制

1. **YouTube Data API**: 
   - 每日配額有限（通常10,000單位）
   - 避免頻繁調用
   
2. **Gemini AI API**:
   - 免費版有請求限制
   - 建議添加適當的延遲

3. **Sora API**:
   - 目前尚未公開發布
   - 需要等待官方 API

### 數據存儲

- 默認使用 SQLite
- 生產環境建議使用 PostgreSQL
- 修改 `.env` 中的 `DATABASE_URL` 即可切換

### 錯誤處理

所有腳本都包含錯誤處理和重試機制：
- 網絡錯誤會自動重試
- 速率限制會等待後重試
- 失敗的任務會記錄到數據庫

---

## 🐛 故障排除

### 問題：數據庫連接錯誤

```bash
# 重新運行遷移
uv run alembic upgrade head
```

### 問題：API Key 無效

確認 `.env` 文件中的 API Keys 正確設置。

### 問題：導入錯誤

```bash
# 重新安裝依賴
uv pip install -r requirements.txt
```

### 查看日誌

所有操作都會記錄到 `logs/` 目錄：

```bash
# 查看今天的日誌
cat logs/discovery/2025-12-10.log
cat logs/analysis/2025-12-10.log
cat logs/errors/2025-12-10.log
```

---

## 📚 進階配置

### 修改工作流程設置

編輯 `config/workflow.yaml`：

```yaml
discovery:
  check_interval: 24  # 監測間隔（小時）
  viral_criteria:
    min_views: 1000000  # 最低觀看數
    min_days_old: 1     # 最少發布天數
    max_days_old: 7     # 最多發布天數
```

### 自定義 Gemini 提示詞

編輯 `config/gemini.yaml` 中的 `prompts` 部分。

---

## 🎯 下一步

1. 收集足夠的爆款影片樣本
2. 分析影片場景和風格
3. 等待 Sora API 發布後實作生成功能
4. 設置自動化排程

---

## 📞 獲取幫助

- 查看 `IMPLEMENTATION_TASKS.md` 了解詳細功能
- 查看 `PROGRESS_SUMMARY.md` 了解當前進度
- 查看各模組的代碼註釋

---

**祝您使用愉快！** 🚀
