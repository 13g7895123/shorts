#!/usr/bin/env python3
"""Script to analyze videos using Gemini AI."""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.scene_analyzer import SceneAnalyzer
from src.analysis.prompt_generator import PromptGenerator
from src.storage.database import get_session
from src.storage.repositories.video_repo import VideoRepository
from src.storage.models import VideoStatus
from src.utils.logger import get_analysis_logger

logger = get_analysis_logger(__name__)


def main():
    """Main function to analyze videos."""
    parser = argparse.ArgumentParser(
        description="Analyze YouTube Shorts videos with AI"
    )
    
    parser.add_argument(
        '--video-id',
        type=int,
        help='Database video ID to analyze'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Analyze all pending videos in batch'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of videos to analyze in batch mode (default: 10)'
    )
    parser.add_argument(
        '--style',
        type=str,
        default='realistic',
        choices=['realistic', 'animated', 'artistic', 'cinematic'],
        help='Video generation style (default: realistic)'
    )
    parser.add_argument(
        '--generate-prompts',
        action='store_true',
        help='Also generate video generation prompts'
    )
    parser.add_argument(
        '--save-files',
        action='store_true',
        default=True,
        help='Save analysis and prompts to files (default: True)'
    )
    
    args = parser.parse_args()
    
    # Check that either video-id or batch is specified
    if not args.video_id and not args.batch:
        parser.error("Either --video-id or --batch must be specified")
    
    try:
        analyzer = SceneAnalyzer()
        
        if args.batch:
            # Batch analysis mode
            logger.info("=" * 60)
            logger.info(f"Starting Batch Video Analysis (limit: {args.limit})")
            logger.info("=" * 60)
            
            stats = analyzer.batch_analyze(
                limit=args.limit,
                save_to_files=args.save_files
            )
            
            logger.info("=" * 60)
            logger.info(f"Batch Analysis Complete:")
            logger.info(f"  ✓ Analyzed: {stats['analyzed']}")
            logger.info(f"  ✗ Failed: {stats['failed']}")
            logger.info("=" * 60)
            
            # Generate prompts if requested
            if args.generate_prompts and stats['analyzed'] > 0:
                logger.info("\nGenerating prompts for analyzed videos...")
                generate_prompts_for_analyzed(args.style, args.save_files)
            
            return 0 if stats['failed'] == 0 else 1
        
        else:
            # Single video analysis mode
            logger.info("=" * 60)
            logger.info(f"Analyzing Video ID: {args.video_id}")
            logger.info("=" * 60)
            
            # Get video info
            with get_session() as session:
                video = VideoRepository.get_by_id(session, args.video_id)
                if not video:
                    logger.error(f"Video ID {args.video_id} not found in database")
                    return 1
                
                logger.info(f"Title: {video.title}")
                logger.info(f"URL: {video.url}")
            
            # Perform analysis
            analysis_result = analyzer.analyze_video_by_id(args.video_id)
            
            # Save to file if requested
            if args.save_files:
                file_path = analyzer.save_analysis_to_file(analysis_result)
                logger.info(f"Analysis saved to: {file_path}")
            
            logger.info("=" * 60)
            logger.info(f"✓ Analysis Complete:")
            logger.info(f"  Scenes: {len(analysis_result.get('scenes', []))}")
            logger.info(f"  Style: {analysis_result.get('overall_style', 'N/A')}")
            logger.info(f"  Mood: {analysis_result.get('overall_mood', 'N/A')}")
            logger.info("=" * 60)
            
            # Generate prompts if requested
            if args.generate_prompts:
                logger.info("\nGenerating video generation prompts...")
                generate_prompts_for_video(
                    analysis_result,
                    args.style,
                    args.save_files
                )
            
            return 0
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


def generate_prompts_for_video(
    analysis_result: dict,
    style: str,
    save_to_file: bool
):
    """Generate prompts for a single analyzed video."""
    try:
        generator = PromptGenerator()
        
        generation_plan = generator.create_full_generation_plan(
            analysis_result,
            style=style
        )
        
        logger.info(f"✓ Generated {len(generation_plan['scene_prompts'])} scene prompts")
        logger.info(f"  Title: {generation_plan['metadata']['title'][:60]}...")
        logger.info(f"  Tags: {len(generation_plan['metadata']['tags'])} tags")
        
        if save_to_file:
            file_path = generator.save_generation_plan(generation_plan)
            logger.info(f"  Saved to: {file_path}")
    
    except Exception as e:
        logger.error(f"Failed to generate prompts: {e}")


def generate_prompts_for_analyzed(style: str, save_to_file: bool):
    """Generate prompts for all recently analyzed videos."""
    try:
        generator = PromptGenerator()
        
        with get_session() as session:
            # Get recently analyzed videos
            analyzed_videos = VideoRepository.get_by_status(
                session,
                VideoStatus.ANALYZED,
                limit=10
            )
            
            logger.info(f"Found {len(analyzed_videos)} analyzed videos")
            
            for video in analyzed_videos:
                if not video.analysis_data:
                    continue
                
                try:
                    logger.info(f"Generating prompts for: {video.title}")
                    
                    generation_plan = generator.create_full_generation_plan(
                        video.analysis_data,
                        style=style
                    )
                    
                    if save_to_file:
                        generator.save_generation_plan(generation_plan)
                    
                    logger.info(f"  ✓ Generated {len(generation_plan['scene_prompts'])} prompts")
                
                except Exception as e:
                    logger.error(f"  ✗ Failed: {e}")
    
    except Exception as e:
        logger.error(f"Batch prompt generation failed: {e}")


if __name__ == "__main__":
    sys.exit(main())
