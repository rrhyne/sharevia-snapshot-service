#!/usr/bin/env python3
"""
Sharevia Snapshot Service - Main Entry Point

Polls Brightdata for snapshot results and updates bookmarks in Supabase.
Runs a Flask web server on port 8081 for health checks while polling in background.
"""

import logging
import os
import sys
import threading

import brightdata_client
import snapshot_service
from dotenv import load_dotenv
from flask import Flask, jsonify

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Create Flask app for health checks
app = Flask(__name__)


@app.route("/")
def health_check():
    """Health check endpoint for Digital Ocean"""
    return jsonify({"status": "ok", "service": "snapshot-service"}), 200


@app.route("/health")
def health():
    """Alternative health check endpoint"""
    return jsonify({"status": "healthy", "service": "snapshot-service"}), 200


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


def run_polling_service():
    """Run the snapshot polling service in a background thread"""
    poll_interval = int(os.getenv("SNAPSHOT_POLL_INTERVAL", "30"))
    logger.info(f"Starting polling service with {poll_interval}s interval")

    try:
        snapshot_service.poll_snapshots(poll_interval=poll_interval)
    except Exception as e:
        logger.error(f"Polling service error: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Sharevia Snapshot Service Starting")
    logger.info("=" * 60)

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Get poll interval from environment or use default
    poll_interval = int(os.getenv("SNAPSHOT_POLL_INTERVAL", "30"))

    logger.info(f"Configuration:")
    logger.info(f"  - Poll interval: {poll_interval} seconds")
    logger.info(f"  - Brightdata API: {brightdata_client.BASE_URL}")
    logger.info(f"  - Supabase Project: {os.getenv('SUPABASE_PROJECT_REF')}")
    logger.info(f"  - Web server: 0.0.0.0:8081")

    # Start the polling service in a background thread
    polling_thread = threading.Thread(target=run_polling_service, daemon=True)
    polling_thread.start()
    logger.info("Polling service started in background thread")

    # Start Flask web server for health checks
    logger.info("Starting web server on port 8081...")
    app.run(host="0.0.0.0", port=8081, debug=False)
