"""
Supabase API Client

Handles communication with Supabase for bookmark lookups and updates.
"""

import logging
import os

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)

# Supabase configuration (matches backend/supabase.py)
PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF")  # e.g. "kqcksqolkgzrqyxjqvul"
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# PostgREST API base URL
BASE_URL = f"https://{PROJECT_REF}.supabase.co/rest/v1" if PROJECT_REF else None

# Table name for storing bookmarks
BOOKMARKS_TABLE = "bookmarks"


def call_postgrest(
    table: str,
    method: str = "GET",
    params: dict = None,
    json_body: dict = None,
    resource_id: str = None,
):
    """
    Sends a request to the PostgREST API.

    Args:
        table: Table name (e.g. "bookmarks")
        method: HTTP method (GET, POST, PATCH, DELETE)
        params: Query parameters as a dict
        json_body: JSON payload for POST/PATCH requests
        resource_id: ID for specific resource operations

    Returns:
        requests.Response object
    """
    if not PROJECT_REF:
        raise ValueError("SUPABASE_PROJECT_REF environment variable not set")

    if not SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable not set")

    # Build URL
    url = f"{BASE_URL}/{table}"
    if resource_id:
        url += f"?id=eq.{resource_id}"

    # Standard PostgREST headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Prefer": "return=representation",  # Return the inserted/updated rows
    }

    logger.info(f"Calling PostgREST API: {method} {url}")

    response = requests.request(
        method=method,
        url=url,
        params=params,
        json=json_body,
        headers=headers,
        timeout=30,
    )

    # PostgREST returns different status codes than typical REST APIs
    if response.status_code not in [200, 201, 204]:
        logger.error(f"PostgREST error: {response.status_code} - {response.text}")
        response.raise_for_status()

    return response


def get_bookmark_by_url(url: str):
    """
    Retrieve a single bookmark by URL.

    Args:
        url: URL to find

    Returns:
        Bookmark record or None if not found
    """
    logger.info(f"Retrieving bookmark for URL: {url}")

    try:
        params = {"url": f"eq.{url}", "limit": 1}

        response = call_postgrest(table=BOOKMARKS_TABLE, method="GET", params=params)

        result = response.json()
        if result and len(result) > 0:
            logger.info(f"Found bookmark for URL: {url}")
            return result[0]
        else:
            logger.warning(f"No bookmark found for URL: {url}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve bookmark from Supabase: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving bookmark: {str(e)}", exc_info=True)
        return None


def get_bookmarks_with_snapshots():
    """
    Get all bookmarks that have a snapshot_id (pending async scrapes).

    Returns:
        list: List of bookmark records with snapshot_ids
    """
    logger.debug(f"Retrieving bookmarks with snapshot_ids...")

    try:
        # Query for bookmarks where snapshot_id is not null
        params = {
            "snapshot_id": "not.is.null",
            "select": "id,url,snapshot_id"
        }

        response = call_postgrest(table=BOOKMARKS_TABLE, method="GET", params=params)

        result = response.json()
        if result:
            logger.debug(f"Found {len(result)} bookmark(s) with snapshot_ids")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve bookmarks from Supabase: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error retrieving bookmarks: {str(e)}", exc_info=True)
        return []


def update_bookmark(bookmark_id: str, updates: dict):
    """
    Update an existing bookmark using PostgREST.

    Args:
        bookmark_id: UUID of the bookmark to update
        updates: Dictionary of fields to update

    Returns:
        Updated record or None if failed
    """
    logger.info(f"Updating bookmark {bookmark_id}")

    try:
        response = call_postgrest(
            table=BOOKMARKS_TABLE,
            method="PATCH",  # PostgREST uses PATCH for updates
            json_body=updates,
            resource_id=bookmark_id,
        )

        result = response.json()
        logger.info(f"Successfully updated bookmark: {result}")
        return result[0] if result else None  # PostgREST returns array

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update bookmark in Supabase: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error updating bookmark: {str(e)}", exc_info=True)
        return None
