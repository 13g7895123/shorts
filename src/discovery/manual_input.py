"""Manual video URL input and batch import functionality."""

import csv
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .url_validator import URLValidator
from ..utils.logger import get_discovery_logger
from ..utils.exceptions import URLValidationError, VideoDiscoveryError
from ..storage.database import get_session
from ..storage.repositories.video_repo import VideoRepository

logger = get_discovery_logger(__name__)


class ManualInput:
    """Handle manual video URL input and batch imports."""
    
    @staticmethod
    def add_single_url(
        url: str,
        title: Optional[str] = None,
        channel: Optional[str] = None,
        views: Optional[int] = None,
        likes: Optional[int] = None,
        duration: Optional[int] = None
    ) -> bool:
        """Add a single video URL to the database.
        
        Args:
            url: YouTube video URL
            title: Optional video title
            channel: Optional channel name
            views: Optional view count
            likes: Optional like count
            duration: Optional duration in seconds
            
        Returns:
            True if added successfully, False if already exists
            
        Raises:
            URLValidationError: If URL is invalid
        """
        # Validate and extract video ID
        video_id = URLValidator.validate_and_extract(url)
        
        # Normalize URL to Shorts format
        normalized_url = URLValidator.normalize_url(url, prefer_shorts=True)
        
        with get_session() as session:
            # Check if already exists
            if VideoRepository.exists_by_video_id(session, video_id):
                logger.warning(f"Video {video_id} already exists in database")
                return False
            
            # Add to database
            VideoRepository.add_url(
                session,
                url=normalized_url,
                video_id=video_id,
                title=title,
                channel=channel,
                views=views,
                likes=likes,
                duration=duration,
                published_at=datetime.utcnow()
            )
            
            logger.info(f"Successfully added video: {video_id} - {title or 'Unknown'}")
            return True
    
    @staticmethod
    def add_urls_from_list(urls: List[str]) -> Dict[str, int]:
        """Add multiple URLs from a list.
        
        Args:
            urls: List of YouTube URLs
            
        Returns:
            Dictionary with counts: {'added': int, 'skipped': int, 'failed': int}
        """
        results = {'added': 0, 'skipped': 0, 'failed': 0}
        
        for url in urls:
            try:
                if ManualInput.add_single_url(url.strip()):
                    results['added'] += 1
                else:
                    results['skipped'] += 1
            except Exception as e:
                logger.error(f"Failed to add URL {url}: {e}")
                results['failed'] += 1
        
        logger.info(f"Batch import complete: {results['added']} added, {results['skipped']} skipped, {results['failed']} failed")
        return results
    
    @staticmethod
    def import_from_csv(file_path: str) -> Dict[str, int]:
        """Import videos from a CSV file.
        
        Expected CSV format:
        url, title, channel, views, likes, duration
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dictionary with counts: {'added': int, 'skipped': int, 'failed': int}
            
        Raises:
            VideoDiscoveryError: If file cannot be read
        """
        path = Path(file_path)
        if not path.exists():
            raise VideoDiscoveryError(f"CSV file not found: {file_path}")
        
        results = {'added': 0, 'skipped': 0, 'failed': 0}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    url = row.get('url', '').strip()
                    if not url:
                        continue
                    
                    try:
                        # Parse optional fields
                        title = row.get('title') or None
                        channel = row.get('channel') or None
                        views = int(row['views']) if row.get('views') else None
                        likes = int(row['likes']) if row.get('likes') else None
                        duration = int(row['duration']) if row.get('duration') else None
                        
                        if ManualInput.add_single_url(url, title, channel, views, likes, duration):
                            results['added'] += 1
                        else:
                            results['skipped'] += 1
                    except Exception as e:
                        logger.error(f"Failed to process row with URL {url}: {e}")
                        results['failed'] += 1
        
        except Exception as e:
            raise VideoDiscoveryError(f"Failed to read CSV file: {e}")
        
        logger.info(f"CSV import complete: {results['added']} added, {results['skipped']} skipped, {results['failed']} failed")
        return results
    
    @staticmethod
    def import_from_json(file_path: str) -> Dict[str, int]:
        """Import videos from a JSON file.
        
        Expected JSON format:
        [
            {
                "url": "...",
                "title": "...",
                "channel": "...",
                "views": 123,
                "likes": 456,
                "duration": 60
            },
            ...
        ]
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dictionary with counts: {'added': int, 'skipped': int, 'failed': int}
            
        Raises:
            VideoDiscoveryError: If file cannot be read
        """
        path = Path(file_path)
        if not path.exists():
            raise VideoDiscoveryError(f"JSON file not found: {file_path}")
        
        results = {'added': 0, 'skipped': 0, 'failed': 0}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise VideoDiscoveryError("JSON file must contain an array of video objects")
            
            for item in data:
                url = item.get('url', '').strip()
                if not url:
                    continue
                
                try:
                    if ManualInput.add_single_url(
                        url,
                        title=item.get('title'),
                        channel=item.get('channel'),
                        views=item.get('views'),
                        likes=item.get('likes'),
                        duration=item.get('duration')
                    ):
                        results['added'] += 1
                    else:
                        results['skipped'] += 1
                except Exception as e:
                    logger.error(f"Failed to process item with URL {url}: {e}")
                    results['failed'] += 1
        
        except json.JSONDecodeError as e:
            raise VideoDiscoveryError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise VideoDiscoveryError(f"Failed to read JSON file: {e}")
        
        logger.info(f"JSON import complete: {results['added']} added, {results['skipped']} skipped, {results['failed']} failed")
        return results
    
    @staticmethod
    def import_from_file(file_path: str) -> Dict[str, int]:
        """Import videos from a file (auto-detect format).
        
        Args:
            file_path: Path to file (CSV or JSON)
            
        Returns:
            Dictionary with counts: {'added': int, 'skipped': int, 'failed': int}
            
        Raises:
            VideoDiscoveryError: If file format is unsupported
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            return ManualInput.import_from_csv(file_path)
        elif suffix == '.json':
            return ManualInput.import_from_json(file_path)
        else:
            raise VideoDiscoveryError(f"Unsupported file format: {suffix}. Use .csv or .json")
