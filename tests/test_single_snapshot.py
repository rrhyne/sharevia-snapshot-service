"""
Test for processing a single snapshot by ID
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import snapshot_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def test_process_single_snapshot():
    """
    Test processing a specific snapshot for a bookmark.
    
    This test retrieves snapshot sd_mhr5zu23tticxmgd5 for bookmark 
    6a828701-f79a-499d-8feb-e0d6e15bef28 and processes it.
    """
    bookmark_id = "6a828701-f79a-499d-8feb-e0d6e15bef28"
    snapshot_id = "sd_mhr5zu23tticxmgd5"
    
    # We need the URL to determine the service type (x vs linkedin)
    # For this test, we'll assume it's an X post
    url = "https://x.com/test"  # Replace with actual URL if known
    
    logger.info("=" * 60)
    logger.info("Testing process_snapshot_for_bookmark")
    logger.info(f"Bookmark ID: {bookmark_id}")
    logger.info(f"Snapshot ID: {snapshot_id}")
    logger.info(f"URL: {url}")
    logger.info("=" * 60)
    
    try:
        success = snapshot_service.process_snapshot_for_bookmark(
            bookmark_id=bookmark_id,
            snapshot_id=snapshot_id,
            url=url
        )
        
        if success:
            logger.info("✅ Test PASSED - Snapshot processed successfully")
        else:
            logger.error("❌ Test FAILED - Snapshot processing returned False")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Test FAILED with exception: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    result = test_process_single_snapshot()
    sys.exit(0 if result else 1)
