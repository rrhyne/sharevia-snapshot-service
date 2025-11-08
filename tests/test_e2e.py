"""
End-to-End Integration Test

Tests the snapshot service against the actual Sharevia backend server.
This test:
1. Creates a bookmark via the backend API
2. Triggers a Brightdata scrape that returns a 202 (async)
3. Runs the snapshot service to process the snapshot
4. Verifies the bookmark was updated with the scraped content

Requirements:
- Backend server must be running
- Valid BRIGHTDATA_TOKEN in .env
- Valid Supabase credentials in .env
"""

import json
import logging
import os
import sys
import time
import unittest

import requests
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import snapshot_service

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
TEST_USER_ID = os.getenv("TEST_USER_ID", "74522d20-51df-4477-ba11-6a67570125f2")


class TestSnapshotServiceE2E(unittest.TestCase):
    """End-to-end tests against real backend and services"""

    @classmethod
    def setUpClass(cls):
        """Check if backend is running"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code != 200:
                raise Exception("Backend health check failed")
            logger.info(f"✅ Backend is running at {BACKEND_URL}")
        except requests.exceptions.RequestException as e:
            raise unittest.SkipTest(
                f"Backend server is not running at {BACKEND_URL}. "
                f"Please start the backend first. Error: {e}"
            )

    def setUp(self):
        """Set up test fixtures"""
        self.test_urls = [
            "https://x.com/CodePen/status/1986906291655110881",  # Video post
            "https://x.com/rushilshah_x/status/1986895101214511118",  # Image post
        ]
        self.created_bookmarks = []

    def tearDown(self):
        """Clean up created bookmarks"""
        # Note: You may want to add a delete endpoint to the backend for cleanup
        for bookmark in self.created_bookmarks:
            logger.info(f"Test bookmark created: {bookmark.get('id')} - manual cleanup may be needed")

    def test_e2e_bookmark_creation_and_snapshot_processing(self):
        """
        Full end-to-end test:
        1. Create a bookmark via backend
        2. Backend triggers Brightdata scrape (may return 202)
        3. Run snapshot service to process async results
        4. Verify bookmark is updated with content
        """
        test_url = self.test_urls[0]
        
        logger.info(f"=" * 70)
        logger.info(f"Starting E2E test for URL: {test_url}")
        logger.info(f"=" * 70)

        # Step 1: Create bookmark via backend
        logger.info("Step 1: Creating bookmark via backend API...")
        
        create_payload = {
            "user_id": TEST_USER_ID,
            "url": test_url,
            "title": "E2E Test Bookmark",
        }

        try:
            response = requests.post(
                f"{BACKEND_URL}/bookmarks",
                json=create_payload,
                timeout=120,  # Brightdata sync timeout is 70s
            )
            
            logger.info(f"Backend response status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                logger.error(f"Backend response: {response.text}")
                self.fail(f"Failed to create bookmark: {response.status_code}")

            bookmark_data = response.json()
            logger.info(f"Bookmark created: {json.dumps(bookmark_data, indent=2)}")
            
            bookmark_id = bookmark_data.get("id")
            self.assertIsNotNone(bookmark_id, "Bookmark ID should not be None")
            self.created_bookmarks.append(bookmark_data)

            # Check if we got a snapshot_id (indicates 202 async scrape)
            snapshot_id = bookmark_data.get("snapshot_id")
            
            if snapshot_id:
                logger.info(f"✅ Async scrape initiated - snapshot_id: {snapshot_id}")
                
                # Step 2: Run snapshot service to process
                logger.info("Step 2: Running snapshot service to process results...")
                
                # Give Brightdata a moment to start processing
                time.sleep(5)
                
                # Run snapshot service for a few iterations
                # This will poll and process the snapshot when ready
                logger.info("Polling for snapshot results (max 5 minutes)...")
                snapshot_service.poll_snapshots(
                    poll_interval=10,  # Check every 10 seconds
                    max_iterations=30,  # Max 5 minutes (30 * 10s)
                )
                
                # Step 3: Verify bookmark was updated
                logger.info("Step 3: Verifying bookmark was updated...")
                
                # Retrieve bookmark to check if it was updated
                get_response = requests.get(
                    f"{BACKEND_URL}/bookmarks?user_id={TEST_USER_ID}",
                    timeout=10,
                )
                
                if get_response.status_code == 200:
                    bookmarks = get_response.json()
                    updated_bookmark = next(
                        (b for b in bookmarks if b.get("id") == bookmark_id), None
                    )
                    
                    if updated_bookmark:
                        logger.info(f"Updated bookmark: {json.dumps(updated_bookmark, indent=2)}")
                        
                        # Verify it has content from snapshot
                        description = updated_bookmark.get("description")
                        preview_image = updated_bookmark.get("preview_image_url")
                        preview_video = updated_bookmark.get("preview_video_url")
                        
                        logger.info(f"Description length: {len(description) if description else 0}")
                        logger.info(f"Has preview image: {bool(preview_image)}")
                        logger.info(f"Has preview video: {bool(preview_video)}")
                        
                        # At least one of these should be populated
                        has_content = bool(description or preview_image or preview_video)
                        self.assertTrue(
                            has_content,
                            "Bookmark should have been updated with content from snapshot"
                        )
                        
                        if has_content:
                            logger.info("✅ E2E test PASSED - bookmark was updated from snapshot!")
                    else:
                        self.fail("Could not find updated bookmark")
                else:
                    self.fail(f"Failed to retrieve bookmarks: {get_response.status_code}")
                    
            else:
                # Got immediate results (200 response)
                logger.info("✅ Sync scrape succeeded - got immediate results")
                logger.info("Verifying bookmark has content...")
                
                description = bookmark_data.get("description")
                preview_image = bookmark_data.get("preview_image_url")
                preview_video = bookmark_data.get("preview_video_url")
                
                logger.info(f"Description length: {len(description) if description else 0}")
                logger.info(f"Has preview image: {bool(preview_image)}")
                logger.info(f"Has preview video: {bool(preview_video)}")
                
                # Should have content from immediate scrape
                has_content = bool(description or preview_image or preview_video)
                self.assertTrue(
                    has_content,
                    "Bookmark should have content from sync scrape"
                )
                
                if has_content:
                    logger.info("✅ E2E test PASSED - bookmark has sync content!")

        except requests.exceptions.Timeout:
            self.fail("Request to backend timed out")
        except Exception as e:
            logger.error(f"E2E test error: {e}", exc_info=True)
            raise

    def test_backend_healthcheck(self):
        """Simple test to verify backend is accessible"""
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        self.assertEqual(response.status_code, 200)
        logger.info(f"✅ Backend health check passed")


if __name__ == "__main__":
    print("=" * 70)
    print("Running End-to-End Tests for Snapshot Service")
    print("=" * 70)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print("=" * 70)
    print()
    print("Prerequisites:")
    print("  1. Backend server must be running")
    print("  2. Valid .env file with Brightdata and Supabase credentials")
    print("  3. Network access to Brightdata and Supabase APIs")
    print()
    print("=" * 70)
    
    unittest.main(verbosity=2)
