"""URL validation and YouTube video ID extraction."""

import re
from typing import Optional
from urllib.parse import urlparse, parse_qs

from ..utils.logger import get_discovery_logger
from ..utils.exceptions import URLValidationError

logger = get_discovery_logger(__name__)


class URLValidator:
    """Validator for YouTube Shorts URLs."""
    
    # YouTube URL patterns
    SHORTS_PATTERNS = [
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
    ]
    
    WATCH_PATTERN = r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})'
    
    @classmethod
    def extract_video_id(cls, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL.
        
        Args:
            url: YouTube URL string
            
        Returns:
            Video ID if found, None otherwise
        """
        # Try Shorts patterns
        for pattern in cls.SHORTS_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Try watch pattern
        match = re.search(cls.WATCH_PATTERN, url)
        if match:
            return match.group(1)
        
        # Try parsing as query parameter
        try:
            parsed = urlparse(url)
            if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
                # Check for v parameter
                params = parse_qs(parsed.query)
                if 'v' in params:
                    video_id = params['v'][0]
                    if len(video_id) == 11:
                        return video_id
        except Exception:
            pass
        
        return None
    
    @classmethod
    def is_valid_youtube_url(cls, url: str) -> bool:
        """Check if URL is a valid YouTube URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if valid YouTube URL
        """
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and \
                   ('youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc)
        except Exception:
            return False
    
    @classmethod
    def is_shorts_url(cls, url: str) -> bool:
        """Check if URL is a YouTube Shorts URL.
        
        Args:
            url: URL string to check
            
        Returns:
            True if Shorts URL
        """
        return any(re.search(pattern, url) for pattern in cls.SHORTS_PATTERNS)
    
    @classmethod
    def validate_and_extract(cls, url: str) -> str:
        """Validate URL and extract video ID.
        
        Args:
            url: YouTube URL string
            
        Returns:
            Video ID
            
        Raises:
            URLValidationError: If URL is invalid or video ID cannot be extracted
        """
        # Check if valid YouTube URL
        if not cls.is_valid_youtube_url(url):
            raise URLValidationError(f"Invalid YouTube URL: {url}")
        
        # Extract video ID
        video_id = cls.extract_video_id(url)
        if not video_id:
            raise URLValidationError(f"Could not extract video ID from URL: {url}")
        
        logger.info(f"Validated URL and extracted video ID: {video_id}")
        return video_id
    
    @classmethod
    def normalize_url(cls, url: str, prefer_shorts: bool = True) -> str:
        """Normalize YouTube URL to standard format.
        
        Args:
            url: YouTube URL string
            prefer_shorts: If True, use Shorts format; otherwise use watch format
            
        Returns:
            Normalized URL
            
        Raises:
            URLValidationError: If URL is invalid
        """
        video_id = cls.validate_and_extract(url)
        
        if prefer_shorts:
            return f"https://www.youtube.com/shorts/{video_id}"
        else:
            return f"https://www.youtube.com/watch?v={video_id}"
    
    @classmethod
    def is_valid_video_id(cls, video_id: str) -> bool:
        """Check if string is a valid YouTube video ID.
        
        Args:
            video_id: Video ID string
            
        Returns:
            True if valid video ID format
        """
        return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))
