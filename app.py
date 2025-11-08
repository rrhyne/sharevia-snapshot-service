#!/usr/bin/env python3
"""
Sharevia Snapshot Service - Main Entry Point

Polls Brightdata for snapshot results and updates bookmarks in Supabase.
"""

import logging
import os
import sys

import brightdata_client
import snapshot_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def validate_environment():
    """Validate required environment variables are set"""
    required_vars = [
        "BRIGHTDATA_TOKEN",
        "SUPABASE_PROJECT_REF",
        "SUPABASE_SERVICE_ROLE_KEY",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        logger.error("Please set these in your .env file or environment")
        return False

    return True


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Sharevia Snapshot Service Starting")
    logger.info("=" * 60)

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Get poll interval from environment or use default
    poll_interval = int(os.getenv("SNAPSHOT_POLL_INTERVAL", "60"))

    logger.info(f"Configuration:")
    logger.info(f"  - Poll interval: {poll_interval} seconds")
    logger.info(f"  - Brightdata API: {brightdata_client.BASE_URL}")
    logger.info(f"  - Supabase Project: {os.getenv('SUPABASE_PROJECT_REF')}")

    try:
        # Start the polling service
        snapshot_service.poll_snapshots(poll_interval=poll_interval)
    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal, shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
