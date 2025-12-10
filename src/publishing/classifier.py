"""Video classifier for categorizing videos before publishing."""

import json
from typing import Dict, List, Optional
from pathlib import Path
import shutil

from ..utils.logger import get_publishing_logger
from ..utils.exceptions import PublishingError
from ..storage.database import get_session
from ..storage.repositories.video_repo import VideoRepository

logger = get_publishing_logger(__name__)


class VideoClassifier:
    """Classify and organize videos based on content analysis."""
    
    def __init__(self):
        """Initialize video classifier."""
        self.base_ready_dir = Path("data/videos/ready")
        self.base_ready_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Video classifier initialized")
    
    def classify_by_analysis(self, analysis_data: Dict) -> str:
        """Classify video based on AI analysis data.
        
        Args:
            analysis_data: Video analysis dictionary
            
        Returns:
            Category name
        """
        # Extract key information from analysis
        overall_style = analysis_data.get('overall_style', '').lower()
        overall_mood = analysis_data.get('overall_mood', '').lower()
        scenes = analysis_data.get('scenes', [])
        
        # Simple keyword-based classification
        keywords = {
            'gaming': ['game', 'gaming', 'player', 'gameplay', 'character'],
            'tech': ['technology', 'gadget', 'phone', 'computer', 'software', 'tech'],
            'entertainment': ['funny', 'comedy', 'laugh', 'entertaining', 'fun'],
            'education': ['learn', 'tutorial', 'how to', 'guide', 'lesson', 'educational'],
            'lifestyle': ['daily', 'vlog', 'routine', 'lifestyle', 'life'],
            'animals': ['animal', 'pet', 'dog', 'cat', 'wildlife', 'cute'],
            'sports': ['sport', 'exercise', 'fitness', 'workout', 'athlete'],
            'music': ['music', 'song', 'dance', 'performance', 'concert'],
            'food': ['food', 'cooking', 'recipe', 'meal', 'restaurant'],
            'travel': ['travel', 'trip', 'destination', 'vacation', 'adventure']
        }
        
        # Collect text to analyze
        text_to_analyze = f"{overall_style} {overall_mood}"
        for scene in scenes[:3]:  # First 3 scenes
            text_to_analyze += f" {scene.get('visual_description', '')}"
            text_to_analyze += f" {scene.get('action', '')}"
        
        text_to_analyze = text_to_analyze.lower()
        
        # Score each category
        scores = {}
        for category, category_keywords in keywords.items():
            score = sum(1 for keyword in category_keywords if keyword in text_to_analyze)
            if score > 0:
                scores[category] = score
        
        # Return category with highest score, or 'general' if no match
        if scores:
            category = max(scores.items(), key=lambda x: x[1])[0]
            logger.info(f"Classified as '{category}' with score {scores[category]}")
            return category
        
        logger.info("No specific category matched, using 'general'")
        return 'general'
    
    def classify_by_metadata(self, title: str, description: str = "") -> str:
        """Classify video based on metadata (title and description).
        
        Args:
            title: Video title
            description: Video description
            
        Returns:
            Category name
        """
        text = f"{title} {description}".lower()
        
        # Simple keyword matching
        if any(word in text for word in ['game', 'gaming', 'player']):
            return 'gaming'
        elif any(word in text for word in ['tech', 'technology', 'gadget']):
            return 'tech'
        elif any(word in text for word in ['funny', 'comedy', 'laugh']):
            return 'entertainment'
        elif any(word in text for word in ['learn', 'tutorial', 'how to']):
            return 'education'
        elif any(word in text for word in ['vlog', 'daily', 'routine']):
            return 'lifestyle'
        elif any(word in text for word in ['animal', 'pet', 'dog', 'cat']):
            return 'animals'
        elif any(word in text for word in ['sport', 'fitness', 'workout']):
            return 'sports'
        elif any(word in text for word in ['music', 'song', 'dance']):
            return 'music'
        elif any(word in text for word in ['food', 'cooking', 'recipe']):
            return 'food'
        elif any(word in text for word in ['travel', 'trip', 'vacation']):
            return 'travel'
        
        return 'general'
    
    def classify_video_by_id(self, video_url_id: int) -> str:
        """Classify a video from database by ID.
        
        Args:
            video_url_id: Video URL ID from database
            
        Returns:
            Category name
            
        Raises:
            PublishingError: If video not found
        """
        with get_session() as session:
            video = VideoRepository.get_by_id(session, video_url_id)
            
            if not video:
                raise PublishingError(f"Video not found: {video_url_id}")
            
            # Try to classify from analysis data first
            if video.analysis_data:
                category = self.classify_by_analysis(video.analysis_data)
            else:
                # Fall back to metadata classification
                category = self.classify_by_metadata(
                    video.title or '',
                    ''
                )
            
            logger.info(f"Video {video_url_id} classified as: {category}")
            return category
    
    def organize_video_file(
        self,
        video_file_path: Path,
        category: str,
        video_id: str
    ) -> Path:
        """Move video file to appropriate category directory.
        
        Args:
            video_file_path: Current video file path
            category: Category name
            video_id: Video ID for naming
            
        Returns:
            New file path
            
        Raises:
            PublishingError: If file operations fail
        """
        if not video_file_path.exists():
            raise PublishingError(f"Video file not found: {video_file_path}")
        
        # Create category directory
        category_dir = self.base_ready_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate new filename
        suffix = video_file_path.suffix
        new_filename = f"{video_id}_ready{suffix}"
        new_path = category_dir / new_filename
        
        # Move file
        try:
            shutil.move(str(video_file_path), str(new_path))
            logger.info(f"Moved video to: {new_path}")
            return new_path
        
        except Exception as e:
            raise PublishingError(f"Failed to move video file: {e}")
    
    def get_category_videos(self, category: str) -> List[Path]:
        """Get all video files in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of video file paths
        """
        category_dir = self.base_ready_dir / category
        
        if not category_dir.exists():
            return []
        
        # Find all video files
        video_extensions = ['.mp4', '.webm', '.mov', '.avi']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(category_dir.glob(f"*{ext}"))
        
        return sorted(video_files)
    
    def get_all_ready_videos(self) -> Dict[str, List[Path]]:
        """Get all ready videos organized by category.
        
        Returns:
            Dictionary mapping category to list of video paths
        """
        ready_videos = {}
        
        # Iterate through category directories
        for category_dir in self.base_ready_dir.iterdir():
            if category_dir.is_dir():
                category = category_dir.name
                videos = self.get_category_videos(category)
                if videos:
                    ready_videos[category] = videos
        
        return ready_videos
    
    def batch_classify_videos(
        self,
        video_ids: Optional[List[int]] = None
    ) -> Dict[str, int]:
        """Classify multiple videos in batch.
        
        Args:
            video_ids: Optional list of video IDs to classify.
                      If None, classifies all videos.
            
        Returns:
            Dictionary with classification statistics
        """
        stats = {'classified': 0, 'failed': 0}
        categories_count = {}
        
        with get_session() as session:
            if video_ids:
                videos = [VideoRepository.get_by_id(session, vid) for vid in video_ids]
                videos = [v for v in videos if v is not None]
            else:
                from ..storage.models import VideoStatus
                # Get analyzed or processed videos
                videos = VideoRepository.get_by_status(session, VideoStatus.ANALYZED)
                videos += VideoRepository.get_by_status(session, VideoStatus.PROCESSED)
            
            logger.info(f"Classifying {len(videos)} videos")
            
            for video in videos:
                try:
                    category = self.classify_video_by_id(video.id)
                    
                    # Update category count
                    categories_count[category] = categories_count.get(category, 0) + 1
                    stats['classified'] += 1
                    
                    logger.info(f"✓ Video {video.id} ({video.title[:30]}...) -> {category}")
                
                except Exception as e:
                    stats['failed'] += 1
                    logger.error(f"✗ Failed to classify video {video.id}: {e}")
        
        logger.info(f"Classification complete: {stats['classified']} classified, {stats['failed']} failed")
        logger.info(f"Categories: {categories_count}")
        
        return {
            'stats': stats,
            'categories': categories_count
        }


def classify_video(video_url_id: int) -> str:
    """Convenience function to classify a video.
    
    Args:
        video_url_id: Video URL ID
        
    Returns:
        Category name
    """
    classifier = VideoClassifier()
    return classifier.classify_video_by_id(video_url_id)
