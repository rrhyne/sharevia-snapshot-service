"""
Unit tests for process_result function using sample Brightdata data
"""

import argparse
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
        
        # Load all Instagram samples
        self.instagram_samples = []
        for instagram_file in sorted(samples_dir.glob("instagram_*.json")):
            with open(instagram_file, "r") as f:
                self.instagram_samples.append(json.load(f))

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

    def test_process_instagram_post(self):
        """Test processing Instagram posts"""
        logger.info(f"Testing Instagram post processing with {len(self.instagram_samples)} samples")
        
        for idx, instagram_sample in enumerate(self.instagram_samples):
            logger.info(f"Testing Instagram sample {idx + 1}")
            
            print("\n" + "="*80)
            print(f"Instagram Sample {idx + 1} - INPUT DATA:")
            print("="*80)
            print(json.dumps(instagram_sample, indent=2))
            
            result = snapshot_service.process_result(instagram_sample, "instagram")
            
            print("\n" + "="*80)
            print(f"Instagram Sample {idx + 1} - RESPONSE:")
            print("="*80)
            print(json.dumps(result, indent=2))
            print("="*80 + "\n")
            
            # Verify the result has expected keys
            self.assertIn("content", result)
            self.assertIn("preview_image_url", result)
            self.assertIn("social_profile_name", result)
            
            # Verify content extraction
            self.assertIsNotNone(result["content"])
            self.assertGreater(len(result["content"]), 0)
            
            # Verify social profile name
            self.assertIsNotNone(result["social_profile_name"])
            
            logger.info(f"✅ Instagram sample {idx + 1} test passed - Profile: {result['social_profile_name']}")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test process_result function")
    parser.add_argument(
        "--service",
        choices=["all", "x", "linkedin", "instagram"],
        default="all",
        help="Which service to test (default: all)"
    )
    args, remaining = parser.parse_known_args()
    
    # If specific service requested, filter tests
    if args.service != "all":
        suite = unittest.TestLoader().loadTestsFromTestCase(TestProcessResult)
        filtered_suite = unittest.TestSuite()
        
        for test in suite:
            test_name = test._testMethodName
            if args.service == "x" and "x" in test_name.lower():
                filtered_suite.addTest(test)
            elif args.service == "linkedin" and "linkedin" in test_name.lower():
                filtered_suite.addTest(test)
            elif args.service == "instagram" and "instagram" in test_name.lower():
                filtered_suite.addTest(test)
        
        # Run filtered tests
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(filtered_suite)
    else:
        # Run all tests with verbose output
        unittest.main(argv=[''], verbosity=2, exit=True)
