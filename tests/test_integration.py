"""
Integration Tests for Snapshot Service

Tests the snapshot service against real/mocked APIs to ensure
it can poll snapshots, process results, and update bookmarks.
"""

import json
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import brightdata_client
import snapshot_service
import supabase_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSnapshotServiceIntegration(unittest.TestCase):
    """Integration tests for snapshot service with mocked Brightdata API"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_snapshot_id = "sd_mhql37y7qe7v7zjt2"
        self.test_url = "https://x.com/test/status/123456789"
        self.test_bookmark_id = "bookmark_test_123"

    @patch("brightdata_client.requests.get")
    def test_get_snapshots(self, mock_get):
        """Test retrieving snapshots from Brightdata API"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": self.test_snapshot_id,
                "status": "ready",
                "created_at": "2024-11-08T10:00:00Z",
            }
        ]
        mock_get.return_value = mock_response

        # Call the function
        snapshots = brightdata_client.get_snapshots()

        # Verify
        self.assertIsNotNone(snapshots)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0]["id"], self.test_snapshot_id)
        self.assertEqual(snapshots[0]["status"], "ready")

    @patch("brightdata_client.requests.get")
    def test_download_snapshot_results(self, mock_get):
        """Test downloading snapshot results from Brightdata"""
        # Mock the API response with X/Twitter data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "url": self.test_url,
                "description": "Test tweet content",
                "photos": ["https://example.com/photo.jpg"],
                "videos": [],
                "user_posted": "@testuser",
                "domain": "x.com",
            }
        ]
        mock_get.return_value = mock_response

        # Call the function
        results = brightdata_client.download_snapshot_results(self.test_snapshot_id)

        # Verify
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], self.test_url)
        self.assertIn("description", results[0])

    def test_extract_x_content(self):
        """Test extracting content from X/Twitter response"""
        test_data = {
            "description": "This is a test tweet",
            "photos": ["https://example.com/image.jpg"],
            "videos": [],
            "user_posted": "@testuser",
        }

        result = brightdata_client.extract_x_content(test_data)

        self.assertEqual(result["content"], "This is a test tweet")
        self.assertEqual(result["preview_image_url"], "https://example.com/image.jpg")
        self.assertIsNone(result["preview_video_url"])
        self.assertEqual(result["social_profile_name"], "@testuser")

    def test_extract_x_content_with_video(self):
        """Test extracting content from X/Twitter with video"""
        test_data = {
            "description": "Video tweet",
            "photos": [],
            "videos": [{"video_url": "https://example.com/video.mp4"}],
            "user_posted": "@videouser",
        }

        result = brightdata_client.extract_x_content(test_data)

        self.assertEqual(result["content"], "Video tweet")
        self.assertIsNone(result["preview_image_url"])
        self.assertEqual(result["preview_video_url"], "https://example.com/video.mp4")

    def test_extract_linkedin_content(self):
        """Test extracting content from LinkedIn response"""
        test_data = {
            "post_text": "This is a LinkedIn post",
            "images": ["https://example.com/linkedin.jpg"],
            "user_id": "john-doe",
        }

        result = brightdata_client.extract_linkedin_content(test_data)

        self.assertEqual(result["content"], "This is a LinkedIn post")
        self.assertEqual(
            result["preview_image_url"], "https://example.com/linkedin.jpg"
        )
        self.assertEqual(result["social_profile_name"], "john-doe")

    @patch("supabase_client.call_postgrest")
    def test_get_bookmark_by_url(self, mock_postgrest):
        """Test retrieving bookmark by URL from Supabase"""
        # Mock Supabase response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": self.test_bookmark_id,
                "url": self.test_url,
                "title": "Test Bookmark",
                "user_id": "user123",
            }
        ]
        mock_postgrest.return_value = mock_response

        # Call the function
        bookmark = supabase_client.get_bookmark_by_url(self.test_url)

        # Verify
        self.assertIsNotNone(bookmark)
        self.assertEqual(bookmark["id"], self.test_bookmark_id)
        self.assertEqual(bookmark["url"], self.test_url)

    @patch("supabase_client.call_postgrest")
    def test_update_bookmark(self, mock_postgrest):
        """Test updating a bookmark in Supabase"""
        # Mock Supabase response
        updates = {
            "description": "Updated content",
            "preview_image_url": "https://example.com/image.jpg",
        }

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": self.test_bookmark_id,
                "description": "Updated content",
                "preview_image_url": "https://example.com/image.jpg",
            }
        ]
        mock_postgrest.return_value = mock_response

        # Call the function
        result = supabase_client.update_bookmark(self.test_bookmark_id, updates)

        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], self.test_bookmark_id)
        self.assertEqual(result["description"], "Updated content")

    def test_process_result_x(self):
        """Test processing a result for X/Twitter"""
        test_data = {
            "description": "Test tweet",
            "photos": ["https://example.com/photo.jpg"],
            "user_posted": "@testuser",
        }

        result = snapshot_service.process_result(test_data, "x")

        self.assertEqual(result["content"], "Test tweet")
        self.assertEqual(result["preview_image_url"], "https://example.com/photo.jpg")
        self.assertEqual(result["social_profile_name"], "@testuser")

    def test_process_result_linkedin(self):
        """Test processing a result for LinkedIn"""
        test_data = {
            "post_text": "LinkedIn post",
            "images": ["https://example.com/linkedin.jpg"],
            "user_id": "user-123",
        }

        result = snapshot_service.process_result(test_data, "linkedin")

        self.assertEqual(result["content"], "LinkedIn post")
        self.assertEqual(
            result["preview_image_url"], "https://example.com/linkedin.jpg"
        )
        self.assertEqual(result["social_profile_name"], "user-123")

    @patch("brightdata_client.download_snapshot_results")
    @patch("supabase_client.update_bookmark")
    def test_process_snapshot_for_bookmark(self, mock_update_bookmark, mock_download):
        """Test processing a snapshot for a specific bookmark"""
        # Mock download results
        mock_download.return_value = [
            {
                "url": self.test_url,
                "description": "Test tweet content",
                "photos": ["https://example.com/photo.jpg"],
                "user_posted": "@testuser",
            }
        ]

        # Mock bookmark update
        mock_update_bookmark.return_value = {
            "id": self.test_bookmark_id,
            "description": "Test tweet content",
        }

        # Process snapshot
        success = snapshot_service.process_snapshot_for_bookmark(
            self.test_bookmark_id, self.test_snapshot_id, self.test_url
        )

        # Verify success
        self.assertTrue(success)

        # Verify download was called
        mock_download.assert_called_once_with(self.test_snapshot_id)

        # Verify bookmark was updated
        mock_update_bookmark.assert_called_once()
        call_args = mock_update_bookmark.call_args
        self.assertEqual(call_args[0][0], self.test_bookmark_id)

        updates = call_args[0][1]
        self.assertEqual(updates["description"], "Test tweet content")
        self.assertEqual(updates["preview_image_url"], "https://example.com/photo.jpg")
        self.assertEqual(updates["social_profile_name"], "@testuser")
        self.assertIsNone(updates["snapshot_id"])  # Should clear snapshot_id

    @patch("brightdata_client.download_snapshot_results")
    @patch("brightdata_client.get_snapshot_status")
    @patch("supabase_client.update_bookmark")
    @patch("supabase_client.get_bookmarks_with_snapshots")
    def test_full_poll_cycle(
        self,
        mock_get_bookmarks,
        mock_update_bookmark,
        mock_get_status,
        mock_download,
    ):
        """Test a complete polling cycle with new bookmark-centric approach"""
        # Mock get_bookmarks_with_snapshots - return one bookmark with snapshot_id
        mock_get_bookmarks.return_value = [
            {
                "id": self.test_bookmark_id,
                "url": self.test_url,
                "snapshot_id": self.test_snapshot_id,
            }
        ]

        # Mock snapshot status check - ready
        mock_get_status.return_value = {
            "id": self.test_snapshot_id,
            "status": "ready",
        }

        # Mock download_snapshot_results
        mock_download.return_value = [
            {
                "url": self.test_url,
                "description": "Full cycle test",
                "photos": ["https://example.com/image.jpg"],
                "user_posted": "@testuser",
            }
        ]

        # Mock bookmark update
        mock_update_bookmark.return_value = {"id": self.test_bookmark_id}

        # Run one poll iteration
        snapshot_service.poll_snapshots(poll_interval=0.1, max_iterations=1)

        # Verify the full cycle
        mock_get_bookmarks.assert_called_once()
        mock_get_status.assert_called_once_with(self.test_snapshot_id)
        mock_download.assert_called_once_with(self.test_snapshot_id)
        mock_update_bookmark.assert_called_once()
        
        # Verify snapshot_id was cleared
        call_args = mock_update_bookmark.call_args
        updates = call_args[0][1]
        self.assertIsNone(updates["snapshot_id"])


if __name__ == "__main__":
    print("=" * 70)
    print("Running Integration Tests for Snapshot Service")
    print("=" * 70)
    unittest.main(verbosity=2)
