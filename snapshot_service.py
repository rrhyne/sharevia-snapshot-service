"""
Snapshot Service Core Logic

Handles the main polling loop and processing of snapshot results.
"""

import json
import logging
import time

import brightdata_client
import supabase_client

# Set up logger
logger = logging.getLogger(__name__)


def process_result(result_data, service_name):
    """
    Process a single result from Brightdata using extraction functions.

    Args:
        result_data (dict): The scraped data from Brightdata
        service_name (str): 'x' or 'linkedin'

    Returns:
        dict: Processed result with content, preview_image_url, preview_video_url, etc.
    """
    if service_name == "x":
        processed = brightdata_client.extract_x_content(result_data)
    elif service_name == "linkedin":
        processed = brightdata_client.extract_linkedin_content(result_data)
    else:
        logger.warning(f"Unknown service name: {service_name}")
        return {
            "content": "",
            "preview_image_url": None,
            "preview_video_url": None,
            "social_profile_name": None,
        }

    # Log the processed result
    if service_name == "x":
        logger.info(
            f"Processed X result: content={len(processed.get('content', ''))} chars, "
            f"image={bool(processed.get('preview_image_url'))}, "
            f"video={bool(processed.get('preview_video_url'))}"
        )
    else:
        logger.info(
            f"Processed LinkedIn result: content={len(processed.get('content', ''))} chars, "
            f"image={bool(processed.get('preview_image_url'))}"
        )

    return processed


def process_snapshot_for_bookmark(bookmark_id, snapshot_id, url):
    """
    Process a snapshot for a specific bookmark.

    Args:
        bookmark_id (str): The bookmark ID
        snapshot_id (str): The snapshot ID to download and process
        url (str): The URL that was scraped

    Returns:
        bool: True if successfully processed, False otherwise
    """
    logger.info(
        f"process_snapshot_for_bookmark {snapshot_id} for bookmark {bookmark_id}"
    )

    # Download snapshot results
    response = brightdata_client.download_snapshot_results(snapshot_id)

    if response:
        if response.status_code == 202:
            logger.info(f"Snapshot {snapshot_id} still processing...")
            return None
        elif response.status_code == 200:
            # Prepare updates dict with only non-None values

            results = response.json()
            updates = {}

            # Clear the snapshot_id since it's done
            updates["snapshot_id"] = None

            logger.info(f"✅ Downloaded { {json.dumps(results, indent=2)} }")
            if brightdata_client.check_download_for_errors(results):
                # TODO: this could be simplified
                for item in results:
                    if "error" in item:
                        logging.error(f"Error found: {item['error']}")
                        logging.error(f"Error code: {item.get('error_code', 'N/A')}")
                        updates["scrape_error"] = item["error"]
            else:
                # Process the first result (should only be one for the URL)
                result_data = results[0] if isinstance(results, list) else results

                # Determine service name from URL
                service_name = "linkedin" if "linkedin.com" in url else "x"
                processed = process_result(result_data, service_name)

                logger.info(f"Extracted content for {url}")
                logger.debug(f"  Content: {processed.get('content', '')[:100]}...")

                if processed.get("content"):
                    updates["description"] = processed["content"]
                if processed.get("preview_image_url"):
                    updates["preview_image_url"] = processed["preview_image_url"]
                if processed.get("preview_video_url"):
                    updates["preview_video_url"] = processed["preview_video_url"]
                if processed.get("social_profile_name"):
                    updates["social_profile_name"] = processed["social_profile_name"]

            # Update the bookmark
            result = supabase_client.update_bookmark(bookmark_id, updates)

    if result:
        logger.info(f"✅ Updated bookmark {bookmark_id} with snapshot data")
        return True
    else:
        logger.error(f"❌ Failed to update bookmark {bookmark_id}")
        return False


def poll_snapshots_once():
    """
    Run one polling cycle - check bookmarks for pending snapshots and process them.
    Does not sleep - that's handled by the caller.
    """
    # Get bookmarks that have snapshot_ids (pending async scrapes)
    bookmarks = supabase_client.get_bookmarks_with_snapshots()

    if not bookmarks:
        logger.info("No pending snapshots found")
        return

    logger.info(f"🔍 Found {len(bookmarks)} bookmark(s) with pending snapshot(s)")

    # Process each bookmark's snapshot
    for bookmark in bookmarks:
        bookmark_id = bookmark.get("id")
        snapshot_id = bookmark.get("snapshot_id")
        url = bookmark.get("url")

        if not snapshot_id:
            logger.warning(f"Bookmark {bookmark_id} has no snapshot_id, skipping")
            continue

        try:
            process_snapshot_for_bookmark(bookmark_id, snapshot_id, url)

        except Exception as e:
            logger.error(f"Error processing bookmark {bookmark_id}: {e}", exc_info=True)
            continue


def poll_snapshots(poll_interval=60, max_iterations=None):
    """
    Main polling loop - checks bookmarks for pending snapshots and processes them.

    Args:
        poll_interval (int): Seconds between polls (default: 60)
        max_iterations (int): Max number of iterations (None = infinite)
    """
    logger.info("Starting Brightdata snapshot polling service")
    logger.info(f"Poll interval: {poll_interval} seconds")
    logger.info("Checking bookmarks table for pending snapshot_ids...")

    iteration = 0

    while True:
        iteration += 1

        if max_iterations and iteration > max_iterations:
            logger.info(f"Reached max iterations ({max_iterations}), stopping")
            break

        try:
            poll_snapshots_once()
            time.sleep(poll_interval)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in polling loop: {e}", exc_info=True)
            time.sleep(poll_interval)
