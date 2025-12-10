#!/usr/bin/env python3
"""CLI tool to manually add video URLs."""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.discovery.manual_input import ManualInput
from src.utils.logger import get_discovery_logger
from src.utils.exceptions import URLValidationError, VideoDiscoveryError

logger = get_discovery_logger(__name__)


def main():
    """Main function for adding URLs."""
    parser = argparse.ArgumentParser(
        description="Add YouTube video URLs to the database"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--url',
        type=str,
        help='Single URL to add'
    )
    group.add_argument(
        '--file',
        type=str,
        help='Path to CSV or JSON file with URLs'
    )
    group.add_argument(
        '--urls',
        type=str,
        nargs='+',
        help='Multiple URLs to add'
    )
    
    parser.add_argument(
        '--title',
        type=str,
        help='Video title (only for single URL)'
    )
    parser.add_argument(
        '--channel',
        type=str,
        help='Channel name (only for single URL)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.url:
            # Add single URL
            logger.info(f"Adding URL: {args.url}")
            success = ManualInput.add_single_url(
                args.url,
                title=args.title,
                channel=args.channel
            )
            
            if success:
                logger.info("✓ URL added successfully")
                return 0
            else:
                logger.warning("URL already exists in database")
                return 0
        
        elif args.urls:
            # Add multiple URLs
            logger.info(f"Adding {len(args.urls)} URLs")
            results = ManualInput.add_urls_from_list(args.urls)
            
            logger.info(f"✓ Added: {results['added']}")
            logger.info(f"⊘ Skipped: {results['skipped']}")
            logger.info(f"✗ Failed: {results['failed']}")
            
            return 0 if results['failed'] == 0 else 1
        
        elif args.file:
            # Import from file
            logger.info(f"Importing from file: {args.file}")
            results = ManualInput.import_from_file(args.file)
            
            logger.info(f"✓ Added: {results['added']}")
            logger.info(f"⊘ Skipped: {results['skipped']}")
            logger.info(f"✗ Failed: {results['failed']}")
            
            return 0 if results['failed'] == 0 else 1
    
    except URLValidationError as e:
        logger.error(f"Invalid URL: {e}")
        return 1
    except VideoDiscoveryError as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
