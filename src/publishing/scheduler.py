"""Upload scheduler for managing video publishing schedules."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

from ..utils.logger import get_publishing_logger
from ..utils.exceptions import PublishingError
from ..utils.config import config
from ..storage.database import get_session
from ..storage.models import PublishRecord, Platform

logger = get_publishing_logger(__name__)


class UploadScheduler:
    """Manage video upload schedules and queues."""
    
    def __init__(self):
        """Initialize upload scheduler."""
        self.config = config.load_yaml("platforms")
        self.schedule_config = config.load_yaml("schedule")
        self.queue_file = config.project_root / "data" / "upload_queue.json"
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Upload scheduler initialized")
    
    def _load_queue(self) -> List[Dict]:
        """Load upload queue from file.
        
        Returns:
            List of queued upload tasks
        """
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_queue(self, queue: List[Dict]):
        """Save upload queue to file.
        
        Args:
            queue: List of queued upload tasks
        """
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2, default=str)
    
    def add_to_queue(
        self,
        video_file_path: Path,
        metadata: Dict,
        platform: str = "youtube",
        scheduled_time: Optional[datetime] = None,
        priority: int = 5
    ) -> str:
        """Add video to upload queue.
        
        Args:
            video_file_path: Path to video file
            metadata: Video metadata dictionary
            platform: Target platform
            scheduled_time: Optional scheduled upload time
            priority: Upload priority (1-10, higher = more urgent)
            
        Returns:
            Queue entry ID
        """
        queue = self._load_queue()
        
        # Generate entry ID
        entry_id = f"{platform}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        entry = {
            'id': entry_id,
            'video_file_path': str(video_file_path),
            'metadata': metadata,
            'platform': platform,
            'scheduled_time': scheduled_time.isoformat() if scheduled_time else None,
            'priority': priority,
            'status': 'queued',
            'added_at': datetime.utcnow().isoformat(),
            'attempts': 0,
            'last_error': None
        }
        
        queue.append(entry)
        self._save_queue(queue)
        
        logger.info(f"Added to queue: {entry_id} (priority: {priority})")
        return entry_id
    
    def get_next_upload_time(
        self,
        platform: str = "youtube",
        base_time: Optional[datetime] = None
    ) -> datetime:
        """Calculate next optimal upload time.
        
        Args:
            platform: Target platform
            base_time: Base time to calculate from (default: now)
            
        Returns:
            Next optimal upload time
        """
        if base_time is None:
            base_time = datetime.utcnow()
        
        # Get platform config
        platform_config = self.config.get('general', {}).get('scheduling', {})
        optimal_times = platform_config.get('optimal_times', [9, 12, 18, 21])
        
        # Find next optimal hour
        current_hour = base_time.hour
        next_hours = [h for h in optimal_times if h > current_hour]
        
        if next_hours:
            # Use next optimal time today
            next_hour = next_hours[0]
            next_time = base_time.replace(hour=next_hour, minute=0, second=0, microsecond=0)
        else:
            # Use first optimal time tomorrow
            next_hour = optimal_times[0]
            next_time = base_time + timedelta(days=1)
            next_time = next_time.replace(hour=next_hour, minute=0, second=0, microsecond=0)
        
        logger.info(f"Next optimal upload time: {next_time}")
        return next_time
    
    def check_daily_limit(
        self,
        platform: str = "youtube",
        date: Optional[datetime] = None
    ) -> Dict:
        """Check if daily upload limit has been reached.
        
        Args:
            platform: Target platform
            date: Date to check (default: today)
            
        Returns:
            Dictionary with limit info
        """
        if date is None:
            date = datetime.utcnow()
        
        # Get platform limits
        daily_limit = self.schedule_config.get('publishing', {}).get('schedule', {}).get('daily_limit', 3)
        
        # Count uploads today
        with get_session() as session:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            # Query published videos today
            from sqlalchemy import select, and_
            stmt = select(PublishRecord).where(
                and_(
                    PublishRecord.platform == Platform.YOUTUBE if platform == "youtube" else Platform.TIKTOK,
                    PublishRecord.published_at >= start_of_day,
                    PublishRecord.published_at < end_of_day,
                    PublishRecord.is_published == True
                )
            )
            
            result = session.execute(stmt)
            today_uploads = len(list(result.scalars()))
        
        remaining = max(0, daily_limit - today_uploads)
        
        logger.info(f"Daily limit check: {today_uploads}/{daily_limit} used, {remaining} remaining")
        
        return {
            'limit': daily_limit,
            'used': today_uploads,
            'remaining': remaining,
            'limit_reached': remaining == 0
        }
    
    def get_ready_uploads(
        self,
        limit: Optional[int] = None,
        platform: Optional[str] = None
    ) -> List[Dict]:
        """Get uploads ready to be processed.
        
        Args:
            limit: Maximum number of uploads to return
            platform: Filter by platform
            
        Returns:
            List of ready upload entries
        """
        queue = self._load_queue()
        now = datetime.utcnow()
        
        # Filter ready uploads
        ready = []
        for entry in queue:
            if entry['status'] != 'queued':
                continue
            
            if platform and entry['platform'] != platform:
                continue
            
            # Check if scheduled time has passed
            scheduled_time = entry.get('scheduled_time')
            if scheduled_time:
                scheduled_dt = datetime.fromisoformat(scheduled_time)
                if scheduled_dt > now:
                    continue
            
            ready.append(entry)
        
        # Sort by priority (higher first) and scheduled time
        ready.sort(key=lambda x: (-x['priority'], x.get('scheduled_time', '')))
        
        if limit:
            ready = ready[:limit]
        
        logger.info(f"Found {len(ready)} ready uploads")
        return ready
    
    def update_entry_status(
        self,
        entry_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update status of a queue entry.
        
        Args:
            entry_id: Queue entry ID
            status: New status (queued, uploading, completed, failed)
            error_message: Optional error message
        """
        queue = self._load_queue()
        
        for entry in queue:
            if entry['id'] == entry_id:
                entry['status'] = status
                
                if status == 'uploading':
                    entry['started_at'] = datetime.utcnow().isoformat()
                elif status in ['completed', 'failed']:
                    entry['completed_at'] = datetime.utcnow().isoformat()
                
                if error_message:
                    entry['last_error'] = error_message
                    entry['attempts'] = entry.get('attempts', 0) + 1
                
                logger.info(f"Updated entry {entry_id}: status={status}")
                break
        
        self._save_queue(queue)
    
    def remove_from_queue(self, entry_id: str):
        """Remove entry from queue.
        
        Args:
            entry_id: Queue entry ID
        """
        queue = self._load_queue()
        queue = [e for e in queue if e['id'] != entry_id]
        self._save_queue(queue)
        logger.info(f"Removed from queue: {entry_id}")
    
    def cleanup_completed(self, days: int = 7):
        """Remove completed entries older than specified days.
        
        Args:
            days: Number of days to keep completed entries
        """
        queue = self._load_queue()
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        original_count = len(queue)
        
        # Keep only recent or non-completed entries
        queue = [
            e for e in queue
            if e['status'] != 'completed' or
            datetime.fromisoformat(e.get('completed_at', datetime.utcnow().isoformat())) > cutoff
        ]
        
        removed = original_count - len(queue)
        
        if removed > 0:
            self._save_queue(queue)
            logger.info(f"Cleaned up {removed} completed entries")
    
    def get_queue_statistics(self) -> Dict:
        """Get statistics about the upload queue.
        
        Returns:
            Dictionary with queue statistics
        """
        queue = self._load_queue()
        
        stats = {
            'total': len(queue),
            'queued': 0,
            'uploading': 0,
            'completed': 0,
            'failed': 0,
            'by_platform': {}
        }
        
        for entry in queue:
            status = entry['status']
            stats[status] = stats.get(status, 0) + 1
            
            platform = entry['platform']
            if platform not in stats['by_platform']:
                stats['by_platform'][platform] = {'queued': 0, 'uploading': 0, 'completed': 0, 'failed': 0}
            stats['by_platform'][platform][status] = stats['by_platform'][platform].get(status, 0) + 1
        
        return stats
    
    def schedule_batch_uploads(
        self,
        video_files: List[Path],
        metadata_list: List[Dict],
        platform: str = "youtube",
        start_time: Optional[datetime] = None,
        interval_hours: int = 4
    ) -> List[str]:
        """Schedule multiple videos for upload with time intervals.
        
        Args:
            video_files: List of video file paths
            metadata_list: List of metadata dictionaries
            platform: Target platform
            start_time: Start time for first upload
            interval_hours: Hours between uploads
            
        Returns:
            List of queue entry IDs
        """
        if len(video_files) != len(metadata_list):
            raise PublishingError("Number of video files and metadata must match")
        
        if start_time is None:
            start_time = self.get_next_upload_time(platform)
        
        entry_ids = []
        current_time = start_time
        
        for i, (video_file, metadata) in enumerate(zip(video_files, metadata_list)):
            entry_id = self.add_to_queue(
                video_file_path=video_file,
                metadata=metadata,
                platform=platform,
                scheduled_time=current_time,
                priority=5
            )
            
            entry_ids.append(entry_id)
            current_time += timedelta(hours=interval_hours)
            
            logger.info(f"Scheduled upload {i+1}/{len(video_files)}: {video_file.name} at {current_time}")
        
        logger.info(f"Scheduled {len(entry_ids)} uploads")
        return entry_ids


def schedule_upload(
    video_file_path: Path,
    metadata: Dict,
    platform: str = "youtube",
    scheduled_time: Optional[datetime] = None
) -> str:
    """Convenience function to schedule an upload.
    
    Args:
        video_file_path: Path to video file
        metadata: Video metadata
        platform: Target platform
        scheduled_time: Optional scheduled time
        
    Returns:
        Queue entry ID
    """
    scheduler = UploadScheduler()
    return scheduler.add_to_queue(video_file_path, metadata, platform, scheduled_time)
