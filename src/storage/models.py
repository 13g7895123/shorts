"""Database models for the YouTube Shorts automation system."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Boolean, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .database import Base


class VideoStatus(enum.Enum):
    """Status of a video URL in the pipeline."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    GENERATING = "generating"
    GENERATED = "generated"
    PROCESSING = "processing"
    PROCESSED = "processed"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStatus(enum.Enum):
    """Status of a processing task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Platform(enum.Enum):
    """Supported publishing platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"


class VideoURL(Base):
    """Model for storing discovered video URLs."""
    
    __tablename__ = "video_urls"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    video_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    channel: Mapped[Optional[str]] = mapped_column(String(200))
    views: Mapped[Optional[int]] = mapped_column(Integer)
    likes: Mapped[Optional[int]] = mapped_column(Integer)
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    status: Mapped[VideoStatus] = mapped_column(
        SQLEnum(VideoStatus),
        default=VideoStatus.PENDING,
        nullable=False,
        index=True
    )
    
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    analysis_data: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    def __repr__(self):
        return f"<VideoURL(id={self.id}, video_id='{self.video_id}', status='{self.status.value}')>"


class Task(Base):
    """Model for tracking processing tasks."""
    
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_url_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    result: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    def __repr__(self):
        return f"<Task(id={self.id}, type='{self.task_type}', status='{self.status.value}')>"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class GeneratedVideo(Base):
    """Model for storing generated video information."""
    
    __tablename__ = "generated_videos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_url_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    task_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    duration: Mapped[Optional[float]] = mapped_column(Float)
    resolution: Mapped[Optional[str]] = mapped_column(String(20))
    fps: Mapped[Optional[int]] = mapped_column(Integer)
    
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_file_path: Mapped[Optional[str]] = mapped_column(String(1000))
    
    category: Mapped[Optional[str]] = mapped_column(String(50))
    video_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<GeneratedVideo(id={self.id}, file='{self.file_path}')>"


class PublishRecord(Base):
    """Model for tracking video publications to platforms."""
    
    __tablename__ = "publish_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    generated_video_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    platform: Mapped[Platform] = mapped_column(
        SQLEnum(Platform),
        nullable=False,
        index=True
    )
    
    platform_video_id: Mapped[Optional[str]] = mapped_column(String(100))
    platform_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[list]] = mapped_column(JSON)
    
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    views: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    likes: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    comments: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<PublishRecord(id={self.id}, platform='{self.platform.value}', published={self.is_published})>"
