"""
FastAPI 後端服務
提供前端所需的 REST API
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.storage.database import DatabaseManager
from src.storage.repositories.video_repo import VideoRepository
from src.discovery.youtube_monitor import YouTubeMonitor
from src.discovery.url_validator import URLValidator
from src.analysis.gemini_client import GeminiClient
from src.analysis.scene_analyzer import SceneAnalyzer
from src.publishing.classifier import VideoClassifier
from src.publishing.metadata_builder import MetadataBuilder
from src.publishing.scheduler import UploadScheduler
from src.utils.config import ConfigManager
from src.utils.logger import setup_logger

app = FastAPI(title="YouTube Shorts Manager API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化
logger = setup_logger(__name__)
config = ConfigManager()
db_manager = DatabaseManager(config)
video_repo = VideoRepository(db_manager)

# Pydantic 模型
class VideoFilter(BaseModel):
    status: Optional[str] = None
    category: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    limit: int = 20

class DiscoverParams(BaseModel):
    min_views: int = 100000
    limit: int = 10

class URLInput(BaseModel):
    url: str

class AnalyzeParams(BaseModel):
    batch_size: int = 5

class MetadataParams(BaseModel):
    category: str
    style: str = "engaging"
    platform: str = "youtube"

class ScheduleInput(BaseModel):
    video_id: int
    platform: str
    scheduled_time: str
    priority: str = "normal"

# API 路由
@app.get("/api/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/api/stats")
async def get_stats():
    """獲取統計數據"""
    videos = video_repo.get_all()
    return {
        "total_videos": len(videos),
        "analyzed": len([v for v in videos if v.status in ["analyzed", "classified"]]),
        "scheduled": len([v for v in videos if v.status == "scheduled"]),
        "published": len([v for v in videos if v.status == "published"]),
    }

@app.get("/api/videos")
async def get_videos(
    status: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """獲取影片列表"""
    videos = video_repo.get_all()
    
    # 篩選
    if status:
        videos = [v for v in videos if v.status == status]
    if category:
        videos = [v for v in videos if v.category == category]
    
    # 分頁
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "videos": [
            {
                "id": v.id,
                "url": v.url,
                "title": v.title or "",
                "thumbnail": v.thumbnail or "",
                "category": v.category or "",
                "status": v.status,
                "views": v.views or 0,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in videos[start:end]
        ],
        "total": len(videos),
        "page": page,
        "limit": limit,
    }

@app.get("/api/videos/{video_id}")
async def get_video(video_id: int):
    """獲取單個影片詳情"""
    video = video_repo.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {
        "id": video.id,
        "url": video.url,
        "title": video.title,
        "thumbnail": video.thumbnail,
        "category": video.category,
        "status": video.status,
        "views": video.views,
        "likes": video.likes,
        "duration": video.duration,
        "created_at": video.created_at.isoformat() if video.created_at else None,
    }

@app.post("/api/discover/viral")
async def discover_viral(params: DiscoverParams):
    """發現爆款影片"""
    try:
        monitor = YouTubeMonitor(config)
        videos = monitor.discover_viral_shorts(
            min_views=params.min_views,
            limit=params.limit
        )
        
        # 儲存到資料庫
        for video_data in videos:
            video_repo.create(
                url=video_data["url"],
                title=video_data.get("title"),
                thumbnail=video_data.get("thumbnail"),
                views=video_data.get("views"),
                likes=video_data.get("likes"),
            )
        
        return {"videos": videos, "count": len(videos)}
    except Exception as e:
        logger.error(f"Discover failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discover/url")
async def add_url(input: URLInput):
    """添加單個 URL"""
    try:
        validator = URLValidator()
        if not validator.is_valid_url(input.url):
            raise HTTPException(status_code=400, detail="Invalid URL")
        
        video_repo.create(url=input.url)
        return {"success": True, "url": input.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/video/{video_id}")
async def analyze_video(video_id: int):
    """分析單個影片"""
    try:
        video = video_repo.get_by_id(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # TODO: 實作分析邏輯
        video_repo.update_status(video_id, "analyzed")
        
        return {"success": True, "video_id": video_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/batch")
async def batch_analyze(params: AnalyzeParams):
    """批量分析"""
    try:
        videos = video_repo.get_by_status("pending")
        videos = videos[:params.batch_size]
        
        for video in videos:
            video_repo.update_status(video.id, "analyzed")
        
        return {"success": True, "analyzed": len(videos)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/schedule")
async def get_schedules():
    """獲取排程列表"""
    # TODO: 實作排程查詢
    return {"schedules": [], "total": 0}

@app.post("/api/schedule")
async def add_schedule(schedule: ScheduleInput):
    """新增排程"""
    # TODO: 實作新增排程
    return {"success": True}

@app.get("/api/schedule/stats")
async def get_schedule_stats():
    """獲取排程統計"""
    return {
        "total": 0,
        "pending": 0,
        "completed": 0,
    }

# 靜態文件服務（生產環境）
# app.mount("/", StaticFiles(directory="web/dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
