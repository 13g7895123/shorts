"""YouTube Shorts monitoring and discovery module."""

import datetime
import isodate
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils.config import config
from ..utils.logger import get_discovery_logger
from ..utils.exceptions import VideoDiscoveryError
from ..storage.database import get_session
from ..storage.repositories.video_repo import VideoRepository

logger = get_discovery_logger(__name__)


class YouTubeMonitor:
    """Monitor YouTube for viral Shorts videos."""
    
    def __init__(self):
        """Initialize YouTube API service."""
        api_key = config.youtube_api_key
        if not api_key:
            raise VideoDiscoveryError("YOUTUBE_API_KEY not found in environment variables")
        
        try:
            self.youtube = build("youtube", "v3", developerKey=api_key)
            logger.info("YouTube API service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API service: {e}")
            raise VideoDiscoveryError(f"Failed to initialize YouTube API: {e}")
    
    def get_most_popular_videos(
        self,
        region_code: str = 'US',
        max_results_per_category: int = 50
    ) -> List[Dict]:
        """Fetch most popular videos from specific categories.
        
        Args:
            region_code: YouTube region code
            max_results_per_category: Maximum results per category
            
        Returns:
            List of video dictionaries
        """
        # High-density Shorts categories
        target_categories = [
            ('15', 'Animals & Pets'),
            ('23', 'Comedy'),
            ('20', 'Gaming'),
            ('24', 'Entertainment'),
            ('17', 'Sports'),
            ('22', 'People & Blogs')
        ]
        
        all_videos = {}
        
        logger.info(f"Fetching videos from {len(target_categories)} categories (Region: {region_code})")
        
        for cat_id, cat_name in target_categories:
            try:
                request = self.youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    chart="mostPopular",
                    regionCode=region_code,
                    videoCategoryId=cat_id,
                    maxResults=max_results_per_category
                )
                response = request.execute()
                items = response.get('items', [])
                
                logger.info(f"Category {cat_name} ({cat_id}): {len(items)} videos fetched")
                
                for item in items:
                    all_videos[item['id']] = item
                    
            except HttpError as e:
                logger.error(f"Error fetching category {cat_name}: {e}")
        
        unique_videos = list(all_videos.values())
        logger.info(f"Total unique videos fetched: {len(unique_videos)}")
        return unique_videos
    
    @staticmethod
    def parse_duration(duration_iso: str) -> float:
        """Parse ISO 8601 duration to seconds.
        
        Args:
            duration_iso: ISO 8601 duration string
            
        Returns:
            Duration in seconds
        """
        try:
            dt = isodate.parse_duration(duration_iso)
            return dt.total_seconds()
        except Exception:
            return 0
    
    @staticmethod
    def is_short(video: Dict, max_duration: int = 60) -> bool:
        """Check if a video is a Short based on duration.
        
        Args:
            video: Video data dictionary
            max_duration: Maximum duration for Shorts in seconds
            
        Returns:
            True if video is a Short
        """
        duration_iso = video['contentDetails']['duration']
        seconds = YouTubeMonitor.parse_duration(duration_iso)
        return 0 < seconds <= max_duration
    
    def filter_videos(
        self,
        videos: List[Dict],
        max_age_hours: int = 48,
        min_vph: int = 0
    ) -> List[Dict]:
        """Filter videos to find viral Shorts.
        
        Args:
            videos: List of video dictionaries
            max_age_hours: Maximum age in hours since publication
            min_vph: Minimum views per hour threshold
            
        Returns:
            List of filtered video data dictionaries
        """
        filtered_videos = []
        stats = {
            'total': len(videos),
            'music_excluded': 0,
            'duration_excluded': 0,
            'old_excluded': 0,
            'low_vph_excluded': 0,
            'kept': 0
        }
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for video in videos:
            # Exclude Music category (10)
            category_id = video['snippet'].get('categoryId')
            if category_id == '10':
                stats['music_excluded'] += 1
                continue
            
            # Check if it's a Short
            if not self.is_short(video):
                stats['duration_excluded'] += 1
                continue
            
            # Check video age
            published_at_str = video['snippet']['publishedAt']
            published_at = isodate.parse_datetime(published_at_str)
            
            time_diff = now - published_at
            hours_since_published = time_diff.total_seconds() / 3600
            
            if hours_since_published >= max_age_hours or hours_since_published <= 0:
                stats['old_excluded'] += 1
                continue
            
            # Calculate views per hour
            view_count = int(video['statistics'].get('viewCount', 0))
            vph = view_count / hours_since_published if hours_since_published > 0 else 0
            
            if vph < min_vph:
                stats['low_vph_excluded'] += 1
                continue
            
            # Extract video data
            video_data = {
                'video_id': video['id'],
                'title': video['snippet']['title'],
                'channel': video['snippet']['channelTitle'],
                'views': view_count,
                'likes': int(video['statistics'].get('likeCount', 0)),
                'vph': int(vph),
                'published_at': published_at,
                'duration': int(self.parse_duration(video['contentDetails']['duration'])),
                'url': f"https://www.youtube.com/shorts/{video['id']}"
            }
            
            filtered_videos.append(video_data)
            stats['kept'] += 1
        
        # Log statistics
        logger.info("=== Filtering Statistics ===")
        logger.info(f"Total videos processed: {stats['total']}")
        logger.info(f"Excluded Music: {stats['music_excluded']}")
        logger.info(f"Excluded Duration: {stats['duration_excluded']}")
        logger.info(f"Excluded Old: {stats['old_excluded']}")
        logger.info(f"Excluded Low VPH: {stats['low_vph_excluded']}")
        logger.info(f"Candidates Remaining: {stats['kept']}")
        
        return filtered_videos
    
    def discover_and_save(
        self,
        region_code: str = 'US',
        max_age_hours: int = 48,
        min_vph: int = 10000
    ) -> int:
        """Discover viral Shorts and save to database.
        
        Args:
            region_code: YouTube region code
            max_age_hours: Maximum age in hours
            min_vph: Minimum views per hour
            
        Returns:
            Number of new videos added to database
        """
        logger.info(f"Starting viral Shorts discovery (Region: {region_code})")
        
        # Fetch videos
        raw_videos = self.get_most_popular_videos(region_code=region_code)
        
        # Filter videos
        viral_videos = self.filter_videos(
            raw_videos,
            max_age_hours=max_age_hours,
            min_vph=min_vph
        )
        
        # Sort by VPH
        viral_videos.sort(key=lambda x: x['vph'], reverse=True)
        
        # Save to database
        new_count = 0
        with get_session() as session:
            for video_data in viral_videos:
                # Check if already exists
                if not VideoRepository.exists_by_video_id(session, video_data['video_id']):
                    VideoRepository.add_url(
                        session,
                        url=video_data['url'],
                        video_id=video_data['video_id'],
                        title=video_data['title'],
                        channel=video_data['channel'],
                        views=video_data['views'],
                        likes=video_data['likes'],
                        duration=video_data['duration'],
                        published_at=video_data['published_at']
                    )
                    new_count += 1
                    logger.info(f"Added new viral Short: {video_data['title']}")
        
        logger.info(f"Discovery complete: {new_count} new videos added, {len(viral_videos) - new_count} duplicates skipped")
        return new_count


def discover_viral_shorts(
    region_code: str = 'US',
    max_age_hours: int = 48,
    min_vph: int = 10000
) -> int:
    """Convenience function to discover viral Shorts.
    
    Args:
        region_code: YouTube region code
        max_age_hours: Maximum age in hours
        min_vph: Minimum views per hour
        
    Returns:
        Number of new videos added
    """
    monitor = YouTubeMonitor()
    return monitor.discover_and_save(region_code, max_age_hours, min_vph)
