"""
Brightdata API Client

Handles communication with Brightdata API for snapshot management and result downloading.
"""

import json
import logging
import os

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)

BRIGHTDATA_TOKEN = os.getenv("BRIGHTDATA_TOKEN")
BASE_URL = "https://api.brightdata.com/datasets/v3"


def get_headers():
    """Get API headers for Brightdata requests"""
    return {
        "Authorization": f"Bearer {BRIGHTDATA_TOKEN}",
        "Content-Type": "application/json",
    }


def get_snapshots():
    """
    Get list of all snapshots from Brightdata.

    Returns:
        list: List of snapshot objects with id, status, created_at, etc.
    """
    url = f"{BASE_URL}/snapshots"

    try:
        response = requests.get(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        snapshots = response.json()
        # Only log if snapshots exist (reduces noise)
        if snapshots:
            logger.debug(f"Retrieved {len(snapshots)} snapshots")
        return snapshots
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get snapshots: {e}")
        return []


def check_download_for_errors(response_data):
    if isinstance(response_data, list) and len(response_data) > 0:
        for item in response_data:
            if "error" in item:
                logging.error(f"Error found: {item['error']}")
                logging.error(f"Error code: {item.get('error_code', 'N/A')}")
                return True
    return False


def download_snapshot_results(snapshot_id):
    """
    Download results from a ready snapshot.

    Args:
        snapshot_id (str): The snapshot ID to download

    Returns:
        list: List of scraped results, or None if failed
    """

    DOWNLOAD_API_URL = (
        f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
    )
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(DOWNLOAD_API_URL, headers=headers)
        return response

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading snapshot {snapshot_id}: {e}")
        return None


def extract_linkedin_content(content_data):
    """Extract content and preview image from LinkedIn Brightdata response"""
    if isinstance(content_data, dict):
        content = (
            content_data.get("post_text")
            or content_data.get("text")
            or content_data.get("title")
            or content_data.get("headline")
            or str(content_data)
        )

        images = content_data.get("images", [])
        preview_image_url = images[0] if images and len(images) > 0 else None
        social_profile_name = content_data.get("user_id")

        return {
            "content": content,
            "preview_image_url": preview_image_url,
            "social_profile_name": social_profile_name,
        }
    else:
        return {
            "content": str(content_data),
            "preview_image_url": None,
            "social_profile_name": None,
        }


def extract_x_content(content_data):
    """Extract content, preview image/video from X Brightdata response"""
    if isinstance(content_data, dict):
        content = (
            content_data.get("description")
            or content_data.get("text")
            or content_data.get("content")
            or str(content_data)
        )

        photos = content_data.get("photos", [])
        preview_image_url = photos[0] if photos and len(photos) > 0 else None

        # If no photos, check for videos
        preview_video_url = None
        if not preview_image_url:
            videos = content_data.get("videos", [])
            if videos and len(videos) > 0:
                # Extract video_url from the video object
                video_obj = videos[0]
                preview_video_url = (
                    video_obj.get("video_url")
                    if isinstance(video_obj, dict)
                    else video_obj
                )

        social_profile_name = content_data.get("user_posted")

        return {
            "content": content,
            "preview_image_url": preview_image_url,
            "preview_video_url": preview_video_url,
            "social_profile_name": social_profile_name,
        }
    else:
        return {
            "content": str(content_data),
            "preview_image_url": None,
            "preview_video_url": None,
            "social_profile_name": None,
        }
