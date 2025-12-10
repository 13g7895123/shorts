#!/usr/bin/env python3
"""Script to schedule video uploads."""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.publishing.scheduler import UploadScheduler
from src.utils.logger import get_publishing_logger

logger = get_publishing_logger(__name__)


def main():
    """Main function to schedule uploads."""
    parser = argparse.ArgumentParser(
        description="Schedule video uploads"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add video to upload queue')
    add_parser.add_argument('--video', type=str, required=True, help='Path to video file')
    add_parser.add_argument('--metadata', type=str, required=True, help='Path to metadata JSON file')
    add_parser.add_argument('--platform', type=str, default='youtube', help='Target platform')
    add_parser.add_argument('--schedule', type=str, help='Schedule time (YYYY-MM-DD HH:MM)')
    add_parser.add_argument('--priority', type=int, default=5, help='Upload priority (1-10)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List upload queue')
    list_parser.add_argument('--platform', type=str, help='Filter by platform')
    list_parser.add_argument('--status', type=str, help='Filter by status')
    
    # Stats command
    subparsers.add_parser('stats', help='Show queue statistics')
    
    # Ready command
    ready_parser = subparsers.add_parser('ready', help='Show uploads ready to process')
    ready_parser.add_argument('--platform', type=str, help='Filter by platform')
    ready_parser.add_argument('--limit', type=int, default=10, help='Maximum results')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up completed entries')
    cleanup_parser.add_argument('--days', type=int, default=7, help='Keep entries from last N days')
    
    # Check limit command
    limit_parser = subparsers.add_parser('check-limit', help='Check daily upload limit')
    limit_parser.add_argument('--platform', type=str, default='youtube', help='Platform to check')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        scheduler = UploadScheduler()
        
        if args.command == 'add':
            # Add to queue
            import json
            
            video_path = Path(args.video)
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return 1
            
            metadata_path = Path(args.metadata)
            if not metadata_path.exists():
                logger.error(f"Metadata file not found: {metadata_path}")
                return 1
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            scheduled_time = None
            if args.schedule:
                scheduled_time = datetime.strptime(args.schedule, '%Y-%m-%d %H:%M')
            
            entry_id = scheduler.add_to_queue(
                video_file_path=video_path,
                metadata=metadata,
                platform=args.platform,
                scheduled_time=scheduled_time,
                priority=args.priority
            )
            
            logger.info(f"✓ Added to queue: {entry_id}")
            if scheduled_time:
                logger.info(f"  Scheduled for: {scheduled_time}")
            logger.info(f"  Priority: {args.priority}")
        
        elif args.command == 'list':
            # List queue
            queue = scheduler._load_queue()
            
            # Apply filters
            if args.platform:
                queue = [e for e in queue if e['platform'] == args.platform]
            if args.status:
                queue = [e for e in queue if e['status'] == args.status]
            
            logger.info("=" * 80)
            logger.info(f"Upload Queue ({len(queue)} entries)")
            logger.info("=" * 80)
            
            if not queue:
                logger.info("Queue is empty")
            else:
                for entry in queue:
                    logger.info(f"\nID: {entry['id']}")
                    logger.info(f"  Status: {entry['status']}")
                    logger.info(f"  Platform: {entry['platform']}")
                    logger.info(f"  Video: {Path(entry['video_file_path']).name}")
                    logger.info(f"  Title: {entry['metadata'].get('title', 'N/A')[:60]}...")
                    if entry.get('scheduled_time'):
                        logger.info(f"  Scheduled: {entry['scheduled_time']}")
                    logger.info(f"  Priority: {entry['priority']}")
                    logger.info(f"  Added: {entry['added_at']}")
            
            logger.info("=" * 80)
        
        elif args.command == 'stats':
            # Show statistics
            stats = scheduler.get_queue_statistics()
            
            logger.info("=" * 60)
            logger.info("Upload Queue Statistics")
            logger.info("=" * 60)
            logger.info(f"\nTotal entries: {stats['total']}")
            logger.info(f"  Queued: {stats.get('queued', 0)}")
            logger.info(f"  Uploading: {stats.get('uploading', 0)}")
            logger.info(f"  Completed: {stats.get('completed', 0)}")
            logger.info(f"  Failed: {stats.get('failed', 0)}")
            
            if stats['by_platform']:
                logger.info("\nBy Platform:")
                for platform, counts in stats['by_platform'].items():
                    logger.info(f"\n  {platform.upper()}:")
                    logger.info(f"    Queued: {counts.get('queued', 0)}")
                    logger.info(f"    Uploading: {counts.get('uploading', 0)}")
                    logger.info(f"    Completed: {counts.get('completed', 0)}")
                    logger.info(f"    Failed: {counts.get('failed', 0)}")
            
            logger.info("=" * 60)
        
        elif args.command == 'ready':
            # Show ready uploads
            ready = scheduler.get_ready_uploads(
                limit=args.limit,
                platform=args.platform
            )
            
            logger.info("=" * 80)
            logger.info(f"Ready Uploads ({len(ready)} entries)")
            logger.info("=" * 80)
            
            if not ready:
                logger.info("No uploads ready")
            else:
                for i, entry in enumerate(ready, 1):
                    logger.info(f"\n{i}. {entry['id']}")
                    logger.info(f"   Platform: {entry['platform']}")
                    logger.info(f"   Video: {Path(entry['video_file_path']).name}")
                    logger.info(f"   Title: {entry['metadata'].get('title', 'N/A')[:60]}...")
                    logger.info(f"   Priority: {entry['priority']}")
            
            logger.info("=" * 80)
        
        elif args.command == 'cleanup':
            # Cleanup completed
            logger.info(f"Cleaning up completed entries older than {args.days} days...")
            scheduler.cleanup_completed(days=args.days)
            logger.info("✓ Cleanup complete")
        
        elif args.command == 'check-limit':
            # Check daily limit
            limit_info = scheduler.check_daily_limit(platform=args.platform)
            
            logger.info("=" * 60)
            logger.info(f"Daily Upload Limit - {args.platform.upper()}")
            logger.info("=" * 60)
            logger.info(f"Limit: {limit_info['limit']}")
            logger.info(f"Used: {limit_info['used']}")
            logger.info(f"Remaining: {limit_info['remaining']}")
            
            if limit_info['limit_reached']:
                logger.warning("⚠ Daily limit reached!")
            else:
                logger.info(f"✓ {limit_info['remaining']} uploads available today")
            
            logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
