"""Repository for analytics and statistics operations."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import VideoURL, Task, GeneratedVideo, PublishRecord, VideoStatus, TaskStatus, Platform
from ...utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsRepository:
    """Repository for analytics and statistics."""
    
    @staticmethod
    def record_generation(
        session: Session,
        video_url_id: int,
        file_path: str,
        file_size: Optional[int] = None,
        duration: Optional[float] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None,
        task_id: Optional[int] = None
    ) -> GeneratedVideo:
        """Record a generated video.
        
        Args:
            session: Database session
            video_url_id: Source video URL ID
            file_path: Path to generated video file
            file_size: File size in bytes
            duration: Video duration in seconds
            resolution: Video resolution (e.g., '1080x1920')
            fps: Frames per second
            task_id: Related task ID
            
        Returns:
            Created GeneratedVideo instance
        """
        generated_video = GeneratedVideo(
            video_url_id=video_url_id,
            task_id=task_id,
            file_path=file_path,
            file_size=file_size,
            duration=duration,
            resolution=resolution,
            fps=fps
        )
        
        session.add(generated_video)
        session.flush()
        
        logger.info(f"Recorded generated video: {file_path}")
        return generated_video
    
    @staticmethod
    def get_statistics(session: Session, days: Optional[int] = None) -> Dict:
        """Get overall statistics.
        
        Args:
            session: Database session
            days: Optional number of days to look back
            
        Returns:
            Dictionary containing statistics
        """
        # Base query filters
        filters = []
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            filters.append(VideoURL.discovered_at >= cutoff_date)
        
        # Count videos by status
        video_status_counts = {}
        for status in VideoStatus:
            stmt = select(func.count(VideoURL.id)).where(VideoURL.status == status)
            if filters:
                for f in filters:
                    stmt = stmt.where(f)
            count = session.execute(stmt).scalar()
            video_status_counts[status.value] = count
        
        # Count tasks by status
        task_status_counts = {}
        for status in TaskStatus:
            stmt = select(func.count(Task.id)).where(Task.status == status)
            count = session.execute(stmt).scalar()
            task_status_counts[status.value] = count
        
        # Count generated videos
        stmt = select(func.count(GeneratedVideo.id))
        total_generated = session.execute(stmt).scalar()
        
        stmt = select(func.count(GeneratedVideo.id)).where(GeneratedVideo.is_processed == True)
        total_processed = session.execute(stmt).scalar()
        
        # Count published videos
        stmt = select(func.count(PublishRecord.id)).where(PublishRecord.is_published == True)
        total_published = session.execute(stmt).scalar()
        
        # Platform breakdown
        platform_counts = {}
        for platform in Platform:
            stmt = select(func.count(PublishRecord.id)).where(
                PublishRecord.platform == platform,
                PublishRecord.is_published == True
            )
            count = session.execute(stmt).scalar()
            platform_counts[platform.value] = count
        
        return {
            "video_status_counts": video_status_counts,
            "task_status_counts": task_status_counts,
            "generated_videos": {
                "total": total_generated,
                "processed": total_processed
            },
            "published_videos": {
                "total": total_published,
                "by_platform": platform_counts
            },
            "period_days": days
        }
    
    @staticmethod
    def get_success_rate(session: Session, days: Optional[int] = 7) -> Dict:
        """Calculate success rates for the pipeline.
        
        Args:
            session: Database session
            days: Number of days to look back
            
        Returns:
            Dictionary containing success rates
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Video processing success rate
        stmt = select(func.count(VideoURL.id)).where(VideoURL.discovered_at >= cutoff_date)
        total_videos = session.execute(stmt).scalar()
        
        stmt = select(func.count(VideoURL.id)).where(
            VideoURL.discovered_at >= cutoff_date,
            VideoURL.status == VideoStatus.PUBLISHED
        )
        published_videos = session.execute(stmt).scalar()
        
        # Task success rate
        stmt = select(func.count(Task.id)).where(Task.created_at >= cutoff_date)
        total_tasks = session.execute(stmt).scalar()
        
        stmt = select(func.count(Task.id)).where(
            Task.created_at >= cutoff_date,
            Task.status == TaskStatus.COMPLETED
        )
        completed_tasks = session.execute(stmt).scalar()
        
        stmt = select(func.count(Task.id)).where(
            Task.created_at >= cutoff_date,
            Task.status == TaskStatus.FAILED
        )
        failed_tasks = session.execute(stmt).scalar()
        
        return {
            "video_success_rate": published_videos / total_videos if total_videos > 0 else 0,
            "task_success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "task_failure_rate": failed_tasks / total_tasks if total_tasks > 0 else 0,
            "total_videos": total_videos,
            "published_videos": published_videos,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "period_days": days
        }
    
    @staticmethod
    def get_performance_metrics(session: Session, task_type: Optional[str] = None) -> Dict:
        """Get performance metrics for tasks.
        
        Args:
            session: Database session
            task_type: Optional task type filter
            
        Returns:
            Dictionary containing performance metrics
        """
        stmt = select(Task).where(
            Task.status == TaskStatus.COMPLETED,
            Task.started_at.isnot(None),
            Task.completed_at.isnot(None)
        )
        
        if task_type:
            stmt = stmt.where(Task.task_type == task_type)
        
        tasks = session.execute(stmt).scalars().all()
        
        if not tasks:
            return {"task_type": task_type, "count": 0}
        
        durations = [task.duration for task in tasks if task.duration]
        
        if not durations:
            return {"task_type": task_type, "count": len(tasks)}
        
        return {
            "task_type": task_type,
            "count": len(tasks),
            "avg_duration_seconds": sum(durations) / len(durations),
            "min_duration_seconds": min(durations),
            "max_duration_seconds": max(durations)
        }
    
    @staticmethod
    def get_top_performing_videos(
        session: Session,
        limit: int = 10,
        days: Optional[int] = None
    ) -> List[Dict]:
        """Get top performing published videos.
        
        Args:
            session: Database session
            limit: Maximum number of results
            days: Optional number of days to look back
            
        Returns:
            List of dictionaries containing video performance data
        """
        stmt = select(PublishRecord).where(PublishRecord.is_published == True)
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            stmt = stmt.where(PublishRecord.published_at >= cutoff_date)
        
        stmt = stmt.order_by(PublishRecord.views.desc()).limit(limit)
        
        records = session.execute(stmt).scalars().all()
        
        result = []
        for record in records:
            result.append({
                "id": record.id,
                "platform": record.platform.value,
                "title": record.title,
                "views": record.views or 0,
                "likes": record.likes or 0,
                "comments": record.comments or 0,
                "published_at": record.published_at,
                "platform_url": record.platform_url
            })
        
        return result
