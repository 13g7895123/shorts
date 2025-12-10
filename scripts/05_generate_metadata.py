#!/usr/bin/env python3
"""Script to generate metadata for videos."""

import sys
import argparse
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.publishing.metadata_builder import MetadataBuilder
from src.storage.database import get_session
from src.storage.repositories.video_repo import VideoRepository
from src.utils.logger import get_publishing_logger

logger = get_publishing_logger(__name__)


def main():
    """Main function to generate metadata."""
    parser = argparse.ArgumentParser(
        description="Generate metadata for videos"
    )
    
    parser.add_argument(
        '--video-id',
        type=int,
        help='Database video ID'
    )
    parser.add_argument(
        '--category',
        type=str,
        default='general',
        help='Video category'
    )
    parser.add_argument(
        '--style',
        type=str,
        default='engaging',
        choices=['engaging', 'descriptive', 'clickbait', 'professional'],
        help='Title style'
    )
    parser.add_argument(
        '--platform',
        type=str,
        default='youtube',
        choices=['youtube', 'tiktok', 'instagram'],
        help='Target platform'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (JSON)'
    )
    
    args = parser.parse_args()
    
    if not args.video_id:
        parser.error("--video-id is required")
    
    try:
        builder = MetadataBuilder()
        
        logger.info("=" * 60)
        logger.info(f"Generating Metadata for Video ID: {args.video_id}")
        logger.info("=" * 60)
        
        # Get video from database
        with get_session() as session:
            video = VideoRepository.get_by_id(session, args.video_id)
            
            if not video:
                logger.error(f"Video not found: {args.video_id}")
                return 1
            
            logger.info(f"Title: {video.title}")
            logger.info(f"Category: {args.category}")
            logger.info(f"Style: {args.style}")
            logger.info(f"Platform: {args.platform}")
            
            # Generate metadata
            if video.analysis_data:
                logger.info("\nUsing AI analysis data...")
                metadata = builder.build_from_analysis(
                    video.analysis_data,
                    category=args.category,
                    style=args.style,
                    platform=args.platform
                )
            else:
                logger.info("\nUsing basic video info...")
                content_desc = f"Title: {video.title}\nChannel: {video.channel or 'Unknown'}"
                metadata = builder.build_complete_metadata(
                    content_desc,
                    category=args.category,
                    style=args.style,
                    platform=args.platform
                )
        
        # Display results
        logger.info("\n" + "=" * 60)
        logger.info("Generated Metadata:")
        logger.info("=" * 60)
        logger.info(f"\nTitle ({len(metadata['title'])} chars):")
        logger.info(f"  {metadata['title']}")
        logger.info(f"\nDescription ({len(metadata['description'])} chars):")
        logger.info(f"  {metadata['description'][:200]}...")
        logger.info(f"\nTags ({len(metadata['tags'])} tags):")
        logger.info(f"  {', '.join(metadata['tags'][:10])}")
        if len(metadata['tags']) > 10:
            logger.info(f"  ... and {len(metadata['tags']) - 10} more")
        logger.info("=" * 60)
        
        # Save to file if specified
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n✓ Metadata saved to: {output_path}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Metadata generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
