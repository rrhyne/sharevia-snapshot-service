"""
Unit tests for process_result function using sample Brightdata data
"""

import json
import logging
import sys
import unittest
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import snapshot_service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class TestProcessResult(unittest.TestCase):
    """Test process_result with sample Brightdata data"""

    def setUp(self):
        """Load sample data files"""
        samples_dir = Path(__file__).parent / "brightdata-samples"
        
        with open(samples_dir / "sample-x-post.json", "r") as f:
            self.x_sample = json.load(f)
        
        with open(samples_dir / "sample-linkedin-post.json", "r") as f:
            self.linkedin_sample = json.load(f)

    def test_process_x_post(self):
        """Test processing an X (Twitter) post"""
        logger.info("Testing X post processing")
        
        result = snapshot_service.process_result(self.x_sample, "x")
        
        # Verify the result has expected keys
        self.assertIn("content", result)
        self.assertIn("preview_image_url", result)
        self.assertIn("preview_video_url", result)
        self.assertIn("social_profile_name", result)
        
        # Verify content extraction
        self.assertIsNotNone(result["content"])
        self.assertGreater(len(result["content"]), 0)
        self.assertEqual(
            result["content"],
            "New brand identity system for Helix-DB. Backed by YC and Nvidia."
        )
        
        # Verify image extraction (first photo from photos array)
        self.assertIsNotNone(result["preview_image_url"])
        self.assertEqual(
            result["preview_image_url"],
            "https://pbs.twimg.com/media/G4wFTaAXQAE17kL.png"
        )
        
        # Verify social profile name
        self.assertIsNotNone(result["social_profile_name"])
        self.assertEqual(result["social_profile_name"], "kyleanthony")
        
        logger.info(f"✅ X post test passed - Content: {result['content'][:50]}...")

    def test_process_linkedin_post(self):
        """Test processing a LinkedIn post"""
        logger.info("Testing LinkedIn post processing")
        
        result = snapshot_service.process_result(self.linkedin_sample, "linkedin")
        
        # Verify the result has expected keys
        self.assertIn("content", result)
        self.assertIn("preview_image_url", result)
        self.assertIn("social_profile_name", result)
        
        # Verify content extraction (should use post_text)
        self.assertIsNotNone(result["content"])
        self.assertGreater(len(result["content"]), 0)
        self.assertIn("SOC 2 Type II compliant", result["content"])
        
        # Verify image extraction (first image from images array)
        self.assertIsNotNone(result["preview_image_url"])
        self.assertTrue(result["preview_image_url"].startswith("https://media.licdn.com"))
        
        # Verify social profile name (user_id)
        self.assertIsNotNone(result["social_profile_name"])
        self.assertEqual(result["social_profile_name"], "malo-marrec")
        
        logger.info(f"✅ LinkedIn post test passed - Content: {result['content'][:50]}...")

    def test_process_unknown_service(self):
        """Test processing with unknown service name"""
        logger.info("Testing unknown service handling")
        
        result = snapshot_service.process_result(self.x_sample, "unknown")
        
        # Should return empty result
        self.assertEqual(result["content"], "")
        self.assertIsNone(result["preview_image_url"])
        self.assertIsNone(result["preview_video_url"])
        self.assertIsNone(result["social_profile_name"])
        
        logger.info("✅ Unknown service test passed")

    def test_process_x_post_no_video(self):
        """Test that X post without video has None for preview_video_url"""
        logger.info("Testing X post without video")
        
        result = snapshot_service.process_result(self.x_sample, "x")
        
        # Sample X post doesn't have videos
        self.assertIsNone(result["preview_video_url"])
        
        logger.info("✅ X post no video test passed")

    def test_process_linkedin_post_has_image(self):
        """Test that LinkedIn post correctly extracts first image"""
        logger.info("Testing LinkedIn post image extraction")
        
        result = snapshot_service.process_result(self.linkedin_sample, "linkedin")
        
        # LinkedIn sample has images array
        self.assertIsNotNone(result["preview_image_url"])
        expected_url = self.linkedin_sample["images"][0]
        self.assertEqual(result["preview_image_url"], expected_url)
        
        logger.info("✅ LinkedIn image extraction test passed")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
