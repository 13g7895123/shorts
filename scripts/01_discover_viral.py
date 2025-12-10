#!/usr/bin/env python3
"""Script to discover viral YouTube Shorts."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.discovery.youtube_monitor import discover_viral_shorts
from src.utils.logger import get_discovery_logger

logger = get_discovery_logger(__name__)


def main():
    """Main function to discover viral Shorts."""
    logger.info("=" * 60)
    logger.info("Starting Viral Shorts Discovery")
    logger.info("=" * 60)
    
    try:
        # Discover and save viral Shorts
        new_count = discover_viral_shorts(
            region_code='US',
            max_age_hours=48,
            min_vph=10000  # Minimum 10k views per hour
        )
        
        logger.info("=" * 60)
        logger.info(f"Discovery Complete: {new_count} new videos added")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
