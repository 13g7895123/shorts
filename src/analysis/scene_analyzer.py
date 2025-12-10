"""Scene analysis module for YouTube videos."""

import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from .gemini_client import GeminiClient
from ..utils.logger import get_analysis_logger
from ..utils.exceptions import SceneAnalysisError, AnalysisError
from ..storage.database import get_session
from ..storage.repositories.video_repo import VideoRepository
from ..storage.models import VideoStatus

logger = get_analysis_logger(__name__)


class SceneAnalyzer:
    """Analyze video scenes using Gemini AI."""
    
    def __init__(self):
        """Initialize scene analyzer with Gemini client."""
        try:
            self.client = GeminiClient()
            logger.info("Scene analyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize scene analyzer: {e}")
            raise SceneAnalysisError(f"Failed to initialize scene analyzer: {e}")
    
    def analyze_video_scenes(
        self,
        video_url: str,
        video_title: Optional[str] = None,
        video_duration: Optional[int] = None
    ) -> Dict:
        """Analyze video and break down into scenes.
        
        Args:
            video_url: YouTube video URL
            video_title: Optional video title for context
            video_duration: Optional video duration in seconds
            
        Returns:
            Dictionary containing scene analysis data
            
        Raises:
            SceneAnalysisError: If analysis fails
        """
        logger.info(f"Analyzing scenes for video: {video_url}")
        
        # Construct analysis prompt
        prompt = self._build_scene_analysis_prompt(
            video_url,
            video_title,
            video_duration
        )
        
        try:
            # Get analysis from Gemini
            result = self.client.generate_json(prompt)
            
            # Validate result structure
            self._validate_scene_analysis(result)
            
            logger.info(f"Scene analysis complete: {len(result.get('scenes', []))} scenes identified")
            return result
        
        except Exception as e:
            logger.error(f"Scene analysis failed: {e}")
            raise SceneAnalysisError(f"Failed to analyze video scenes: {e}")
    
    def _build_scene_analysis_prompt(
        self,
        video_url: str,
        video_title: Optional[str],
        video_duration: Optional[int]
    ) -> str:
        """Build prompt for scene analysis.
        
        Args:
            video_url: YouTube video URL
            video_title: Optional video title
            video_duration: Optional duration in seconds
            
        Returns:
            Formatted prompt string
        """
        context_parts = [f"Video URL: {video_url}"]
        
        if video_title:
            context_parts.append(f"Title: {video_title}")
        
        if video_duration:
            context_parts.append(f"Duration: {video_duration} seconds")
        
        context = "\n".join(context_parts)
        
        prompt = f"""
Analyze this YouTube Short video and break it down into distinct scenes for recreation.

{context}

Based on typical YouTube Shorts patterns and the provided information, identify and describe the key scenes in this video.

For each scene, provide:
1. Scene number (starting from 1)
2. Start time (seconds)
3. End time (seconds)
4. Duration (seconds)
5. Visual description (detailed, for video generation)
6. Action description (what's happening)
7. Camera angle/movement
8. Lighting and mood
9. Key elements (objects, people, environment)
10. Transition type to next scene (cut, fade, etc.)

Return the analysis in the following JSON format:
{{
    "video_url": "{video_url}",
    "total_duration": <duration in seconds>,
    "scene_count": <number of scenes>,
    "overall_style": "<style description>",
    "overall_mood": "<mood description>",
    "color_palette": ["<color1>", "<color2>", ...],
    "scenes": [
        {{
            "scene_number": 1,
            "start_time": 0.0,
            "end_time": 2.5,
            "duration": 2.5,
            "visual_description": "<detailed visual description>",
            "action": "<what's happening>",
            "camera": "<camera angle and movement>",
            "lighting": "<lighting description>",
            "mood": "<scene mood>",
            "key_elements": ["<element1>", "<element2>", ...],
            "transition": "<transition type>"
        }},
        ...
    ],
    "audio_notes": "<audio/music description>",
    "key_moments": ["<moment1>", "<moment2>", ...]
}}

Provide a comprehensive analysis that would allow someone to recreate a similar video.
"""
        return prompt
    
    def _validate_scene_analysis(self, result: Dict) -> None:
        """Validate scene analysis result structure.
        
        Args:
            result: Analysis result dictionary
            
        Raises:
            SceneAnalysisError: If validation fails
        """
        required_fields = ['scenes', 'scene_count']
        for field in required_fields:
            if field not in result:
                raise SceneAnalysisError(f"Missing required field in analysis: {field}")
        
        scenes = result.get('scenes', [])
        if not scenes:
            raise SceneAnalysisError("No scenes found in analysis")
        
        # Validate each scene
        required_scene_fields = ['scene_number', 'visual_description']
        for scene in scenes:
            for field in required_scene_fields:
                if field not in scene:
                    raise SceneAnalysisError(f"Missing required field in scene: {field}")
    
    def analyze_video_by_id(self, video_url_id: int) -> Dict:
        """Analyze video scenes by database ID.
        
        Args:
            video_url_id: Video URL ID from database
            
        Returns:
            Dictionary containing scene analysis data
            
        Raises:
            SceneAnalysisError: If analysis fails
        """
        with get_session() as session:
            # Get video from database
            video_url = VideoRepository.get_by_id(session, video_url_id)
            
            if not video_url:
                raise SceneAnalysisError(f"Video URL not found: {video_url_id}")
            
            # Update status to analyzing
            VideoRepository.update_status(session, video_url_id, VideoStatus.ANALYZING)
            
            try:
                # Perform analysis
                analysis_result = self.analyze_video_scenes(
                    video_url.url,
                    video_url.title,
                    video_url.duration
                )
                
                # Add metadata
                analysis_result['analyzed_at'] = datetime.utcnow().isoformat()
                analysis_result['video_id'] = video_url.video_id
                
                # Save analysis data to database
                VideoRepository.update_analysis_data(session, video_url_id, analysis_result)
                
                # Update status to analyzed
                VideoRepository.update_status(session, video_url_id, VideoStatus.ANALYZED)
                
                logger.info(f"Analysis saved for video {video_url_id}")
                return analysis_result
            
            except Exception as e:
                # Update status to failed
                VideoRepository.update_status(
                    session,
                    video_url_id,
                    VideoStatus.FAILED,
                    error_message=str(e)
                )
                raise
    
    def save_analysis_to_file(
        self,
        analysis_result: Dict,
        output_dir: str = "data/analysis"
    ) -> Path:
        """Save analysis result to a JSON file.
        
        Args:
            analysis_result: Analysis result dictionary
            output_dir: Output directory path
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        video_id = analysis_result.get('video_id', 'unknown')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"analysis_{video_id}_{timestamp}.json"
        
        file_path = output_path / filename
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis saved to file: {file_path}")
        return file_path
    
    def batch_analyze(
        self,
        limit: Optional[int] = None,
        save_to_files: bool = True
    ) -> Dict[str, int]:
        """Analyze multiple pending videos in batch.
        
        Args:
            limit: Maximum number of videos to analyze
            save_to_files: Whether to save analyses to files
            
        Returns:
            Dictionary with analysis statistics
        """
        logger.info("Starting batch video analysis")
        
        stats = {'analyzed': 0, 'failed': 0, 'skipped': 0}
        
        with get_session() as session:
            # Get pending videos
            pending_videos = VideoRepository.get_by_status(
                session,
                VideoStatus.PENDING,
                limit=limit
            )
            
            logger.info(f"Found {len(pending_videos)} pending videos to analyze")
            
            for video in pending_videos:
                try:
                    logger.info(f"Analyzing video {video.id}: {video.title}")
                    
                    # Analyze video
                    analysis_result = self.analyze_video_by_id(video.id)
                    
                    # Save to file if requested
                    if save_to_files:
                        self.save_analysis_to_file(analysis_result)
                    
                    stats['analyzed'] += 1
                    logger.info(f"✓ Video {video.id} analyzed successfully")
                
                except Exception as e:
                    stats['failed'] += 1
                    logger.error(f"✗ Failed to analyze video {video.id}: {e}")
        
        logger.info(f"Batch analysis complete: {stats['analyzed']} analyzed, {stats['failed']} failed")
        return stats


def analyze_video_scenes(video_url: str, video_title: Optional[str] = None) -> Dict:
    """Convenience function to analyze video scenes.
    
    Args:
        video_url: YouTube video URL
        video_title: Optional video title
        
    Returns:
        Scene analysis dictionary
    """
    analyzer = SceneAnalyzer()
    return analyzer.analyze_video_scenes(video_url, video_title)
