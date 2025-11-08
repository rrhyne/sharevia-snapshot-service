#!/usr/bin/env python3
"""
Sharevia Snapshot Service - Worker

Polls Brightdata for snapshot results and updates bookmarks in Supabase.
Runs as a worker process with a maximum runtime before exiting.
"""

import logging
import os
import sys
import time

import brightdata_client
import snapshot_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("snapshot-worker")


def setup_logging():
    """Configure logging for the worker"""
    log_format = '%(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


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


def main():
    """Main worker loop"""
    setup_logging()

    # Maximum runtime in seconds (5 minutes = 300 seconds)
    MAX_PROC_RUNTIME_IN_SECONDS = int(os.getenv("MAX_RUNTIME_SECONDS", "300"))
    
    logger.info("=" * 60)
    logger.info("Sharevia Snapshot Worker Starting")
    logger.info("=" * 60)
    logger.info("Max runtime: %d seconds", MAX_PROC_RUNTIME_IN_SECONDS)

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Get poll interval from environment or use default
    poll_interval = int(os.getenv("SNAPSHOT_POLL_INTERVAL", "30"))

    logger.info("Configuration:")
    logger.info("  - Poll interval: %d seconds", poll_interval)
    logger.info("  - Brightdata API: %s", brightdata_client.BASE_URL)
    logger.info("  - Supabase Project: %s", os.getenv('SUPABASE_PROJECT_REF'))

    proc_runtime_in_secs = 0

    while proc_runtime_in_secs < MAX_PROC_RUNTIME_IN_SECONDS:
        logger.info("Worker running for %d seconds", proc_runtime_in_secs)

        start = time.monotonic()

        try:
            logger.info("Polling for snapshots...")
            # Run one iteration of snapshot polling
            snapshot_service.poll_snapshots_once()
            logger.info("Polling cycle complete")
        except Exception as e:
            logger.error("Error during polling cycle: %s", e, exc_info=True)

        end = time.monotonic()
        elapsed = end - start

        proc_runtime_in_secs += elapsed

        # If we haven't exceeded max runtime, sleep until next poll
        if proc_runtime_in_secs < MAX_PROC_RUNTIME_IN_SECONDS:
            sleep_time = min(poll_interval, MAX_PROC_RUNTIME_IN_SECONDS - proc_runtime_in_secs)
            logger.info("Sleeping for %d seconds before next poll", sleep_time)
            time.sleep(sleep_time)
            proc_runtime_in_secs += sleep_time

    logger.info("Exceeded max runtime (%d seconds). Exiting gracefully", MAX_PROC_RUNTIME_IN_SECONDS)


if __name__ == "__main__":
    main()
