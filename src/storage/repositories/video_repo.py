"""Repository for VideoURL model operations."""

from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import VideoURL, VideoStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class VideoRepository:
    """Repository for managing video URL records."""
    
    @staticmethod
    def add_url(
        session: Session,
        url: str,
        video_id: str,
        title: Optional[str] = None,
        channel: Optional[str] = None,
        views: Optional[int] = None,
        likes: Optional[int] = None,
        duration: Optional[int] = None,
        published_at: Optional[datetime] = None
    ) -> VideoURL:
        """Add a new video URL to the database.
        
        Args:
            session: Database session
            url: YouTube video URL
            video_id: YouTube video ID
            title: Video title
            channel: Channel name
            views: View count
            likes: Like count
            duration: Video duration in seconds
            published_at: Publication date
            
        Returns:
            Created VideoURL instance
        """
        video_url = VideoURL(
            url=url,
            video_id=video_id,
            title=title,
            channel=channel,
            views=views,
            likes=likes,
            duration=duration,
            published_at=published_at,
            status=VideoStatus.PENDING
        )
        
        session.add(video_url)
        session.flush()
        
        logger.info(f"Added video URL: {video_id} - {title}")
        return video_url
    
    @staticmethod
    def get_by_id(session: Session, video_url_id: int) -> Optional[VideoURL]:
        """Get video URL by ID."""
        return session.get(VideoURL, video_url_id)
    
    @staticmethod
    def get_by_video_id(session: Session, video_id: str) -> Optional[VideoURL]:
        """Get video URL by YouTube video ID."""
        stmt = select(VideoURL).where(VideoURL.video_id == video_id)
        return session.execute(stmt).scalar_one_or_none()
    
    @staticmethod
    def get_by_url(session: Session, url: str) -> Optional[VideoURL]:
        """Get video URL by URL string."""
        stmt = select(VideoURL).where(VideoURL.url == url)
        return session.execute(stmt).scalar_one_or_none()
    
    @staticmethod
    def get_by_status(
        session: Session,
        status: VideoStatus,
        limit: Optional[int] = None
    ) -> List[VideoURL]:
        """Get video URLs by status.
        
        Args:
            session: Database session
            status: Video status to filter by
            limit: Maximum number of results
            
        Returns:
            List of VideoURL instances
        """
        stmt = select(VideoURL).where(VideoURL.status == status)
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    def get_pending_urls(session: Session, limit: Optional[int] = None) -> List[VideoURL]:
        """Get pending video URLs.
        
        Args:
            session: Database session
            limit: Maximum number of results
            
        Returns:
            List of pending VideoURL instances
        """
        return VideoRepository.get_by_status(session, VideoStatus.PENDING, limit)
    
    @staticmethod
    def update_status(
        session: Session,
        video_url_id: int,
        status: VideoStatus,
        error_message: Optional[str] = None
    ) -> Optional[VideoURL]:
        """Update video URL status.
        
        Args:
            session: Database session
            video_url_id: Video URL ID
            status: New status
            error_message: Optional error message if status is FAILED
            
        Returns:
            Updated VideoURL instance or None if not found
        """
        video_url = session.get(VideoURL, video_url_id)
        
        if video_url:
            video_url.status = status
            video_url.updated_at = datetime.utcnow()
            
            if error_message:
                video_url.error_message = error_message
            
            session.flush()
            logger.info(f"Updated video {video_url_id} status to {status.value}")
        
        return video_url
    
    @staticmethod
    def update_analysis_data(
        session: Session,
        video_url_id: int,
        analysis_data: dict
    ) -> Optional[VideoURL]:
        """Update video URL analysis data.
        
        Args:
            session: Database session
            video_url_id: Video URL ID
            analysis_data: Analysis data dictionary
            
        Returns:
            Updated VideoURL instance or None if not found
        """
        video_url = session.get(VideoURL, video_url_id)
        
        if video_url:
            video_url.analysis_data = analysis_data
            video_url.updated_at = datetime.utcnow()
            session.flush()
            logger.info(f"Updated analysis data for video {video_url_id}")
        
        return video_url
    
    @staticmethod
    def increment_retry_count(session: Session, video_url_id: int) -> Optional[VideoURL]:
        """Increment retry count for a video URL.
        
        Args:
            session: Database session
            video_url_id: Video URL ID
            
        Returns:
            Updated VideoURL instance or None if not found
        """
        video_url = session.get(VideoURL, video_url_id)
        
        if video_url:
            video_url.retry_count += 1
            video_url.updated_at = datetime.utcnow()
            session.flush()
            logger.info(f"Incremented retry count for video {video_url_id} to {video_url.retry_count}")
        
        return video_url
    
    @staticmethod
    def get_all(
        session: Session,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[VideoURL]:
        """Get all video URLs with optional pagination.
        
        Args:
            session: Database session
            limit: Maximum number of results
            offset: Number of records to skip
            
        Returns:
            List of VideoURL instances
        """
        stmt = select(VideoURL).order_by(VideoURL.discovered_at.desc())
        
        if offset:
            stmt = stmt.offset(offset)
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    def get_recent_viral(
        session: Session,
        days: int = 7,
        min_views: int = 1000000,
        limit: Optional[int] = None
    ) -> List[VideoURL]:
        """Get recently discovered viral videos.
        
        Args:
            session: Database session
            days: Number of days to look back
            min_views: Minimum view count
            limit: Maximum number of results
            
        Returns:
            List of VideoURL instances
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(VideoURL).where(
            VideoURL.discovered_at >= cutoff_date,
            VideoURL.views >= min_views
        ).order_by(VideoURL.views.desc())
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    def exists_by_video_id(session: Session, video_id: str) -> bool:
        """Check if a video URL exists by video ID.
        
        Args:
            session: Database session
            video_id: YouTube video ID
            
        Returns:
            True if exists, False otherwise
        """
        stmt = select(VideoURL).where(VideoURL.video_id == video_id)
        result = session.execute(stmt).first()
        return result is not None
    
    @staticmethod
    def delete(session: Session, video_url_id: int) -> bool:
        """Delete a video URL record.
        
        Args:
            session: Database session
            video_url_id: Video URL ID
            
        Returns:
            True if deleted, False if not found
        """
        video_url = session.get(VideoURL, video_url_id)
        
        if video_url:
            session.delete(video_url)
            session.flush()
            logger.info(f"Deleted video URL {video_url_id}")
            return True
        
        return False
