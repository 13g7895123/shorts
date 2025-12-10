#!/usr/bin/env python3
"""Script to classify videos by category."""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.publishing.classifier import VideoClassifier
from src.utils.logger import get_publishing_logger

logger = get_publishing_logger(__name__)


def main():
    """Main function to classify videos."""
    parser = argparse.ArgumentParser(
        description="Classify videos by category"
    )
    
    parser.add_argument(
        '--video-id',
        type=int,
        help='Database video ID to classify'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Classify all videos in batch'
    )
    parser.add_argument(
        '--show-categories',
        action='store_true',
        help='Show all categories and their video counts'
    )
    
    args = parser.parse_args()
    
    try:
        classifier = VideoClassifier()
        
        if args.show_categories:
            # Show category statistics
            ready_videos = classifier.get_all_ready_videos()
            
            logger.info("=" * 60)
            logger.info("Video Categories")
            logger.info("=" * 60)
            
            if not ready_videos:
                logger.info("No categorized videos found")
            else:
                total = sum(len(videos) for videos in ready_videos.values())
                logger.info(f"Total ready videos: {total}\n")
                
                for category, videos in sorted(ready_videos.items()):
                    logger.info(f"{category.upper()}: {len(videos)} videos")
                    for video_path in videos[:3]:  # Show first 3
                        logger.info(f"  - {video_path.name}")
                    if len(videos) > 3:
                        logger.info(f"  ... and {len(videos) - 3} more")
            
            logger.info("=" * 60)
            return 0
        
        if args.batch:
            # Batch classification
            logger.info("=" * 60)
            logger.info("Starting Batch Video Classification")
            logger.info("=" * 60)
            
            result = classifier.batch_classify_videos()
            
            logger.info("=" * 60)
            logger.info("Classification Complete:")
            logger.info(f"  ✓ Classified: {result['stats']['classified']}")
            logger.info(f"  ✗ Failed: {result['stats']['failed']}")
            logger.info("\nCategories:")
            for category, count in sorted(result['categories'].items()):
                logger.info(f"  {category}: {count}")
            logger.info("=" * 60)
            
            return 0 if result['stats']['failed'] == 0 else 1
        
        elif args.video_id:
            # Single video classification
            logger.info("=" * 60)
            logger.info(f"Classifying Video ID: {args.video_id}")
            logger.info("=" * 60)
            
            category = classifier.classify_video_by_id(args.video_id)
            
            logger.info("=" * 60)
            logger.info(f"✓ Classification Result: {category.upper()}")
            logger.info("=" * 60)
            
            return 0
        
        else:
            parser.print_help()
            return 1
    
    except Exception as e:
        logger.error(f"Classification failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
