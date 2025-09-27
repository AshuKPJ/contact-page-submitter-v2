# test_campaign_flow.py
"""Test the complete campaign processing flow."""

import asyncio
import sys
import uuid
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test database connection and basic queries."""
    print("=== Testing Database Connection ===")

    try:
        from app.core.database import SessionLocal
        from app.models.campaign import Campaign
        from app.models.user import User

        db = SessionLocal()

        # Test connection
        result = db.execute("SELECT 1").scalar()
        print(f"✓ Database connection: {result}")

        # Test campaigns table
        campaigns = db.query(Campaign).count()
        print(f"✓ Campaigns in database: {campaigns}")

        # Test users table
        users = db.query(User).count()
        print(f"✓ Users in database: {users}")

        db.close()
        return True

    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def create_test_campaign():
    """Create a test campaign with test data."""
    print("\n=== Creating Test Campaign ===")

    try:
        from app.core.database import SessionLocal
        from app.models.campaign import Campaign, CampaignStatus
        from app.models.submission import Submission, SubmissionStatus
        from app.models.user import User

        db = SessionLocal()

        # Create or get test user
        test_user_id = uuid.uuid4()
        test_user = User(
            id=test_user_id,
            email="test@example.com",
            username="testuser",
            hashed_password="dummy",
            is_active=True,
            is_verified=True,
        )

        # Check if user exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            test_user_id = existing_user.id
            print(f"✓ Using existing test user: {test_user_id}")
        else:
            db.add(test_user)
            db.commit()
            print(f"✓ Created test user: {test_user_id}")

        # Create test campaign
        test_campaign = Campaign(
            id=uuid.uuid4(),
            user_id=test_user_id,
            name="Test Campaign",
            description="Automated test campaign",
            status=CampaignStatus.PENDING,
            total_urls=2,
            created_at=datetime.utcnow(),
        )

        db.add(test_campaign)
        db.flush()  # Get the ID

        # Create test submissions
        test_urls = [
            "https://example.com",
            "https://httpbin.org/forms/post",  # Has an actual form
        ]

        for url in test_urls:
            submission = Submission(
                id=uuid.uuid4(),
                campaign_id=test_campaign.id,
                url=url,
                status=SubmissionStatus.PENDING,
                created_at=datetime.utcnow(),
            )
            db.add(submission)

        db.commit()

        print(f"✓ Created test campaign: {test_campaign.id}")
        print(f"✓ Created {len(test_urls)} test submissions")

        db.close()
        return str(test_campaign.id), str(test_user_id)

    except Exception as e:
        print(f"✗ Error creating test campaign: {e}")
        import traceback

        traceback.print_exc()
        return None, None


async def test_campaign_processor():
    """Test the campaign processor directly."""
    print("\n=== Testing Campaign Processor ===")

    # Create test campaign
    campaign_id, user_id = create_test_campaign()
    if not campaign_id:
        print("✗ Failed to create test campaign")
        return False

    try:
        from app.workers.processors.campaign_processor import CampaignProcessor

        # Create processor
        processor = CampaignProcessor(campaign_id, user_id)
        print("✓ CampaignProcessor created")

        # Test getting campaign
        campaign = await processor._get_campaign()
        if campaign:
            print(f"✓ Retrieved campaign: {campaign.name}")
        else:
            print("✗ Failed to retrieve campaign")
            return False

        # Test getting user data
        user_data = await processor._get_user_profile_data(uuid.UUID(user_id))
        print(f"✓ Retrieved user data: {len(user_data)} fields")

        # Test getting submissions
        submissions = await processor._get_pending_submissions()
        print(f"✓ Retrieved {len(submissions)} pending submissions")

        # Test automation start/stop
        await processor.automation.start()
        print("✓ Automation started")

        await processor.automation.stop()
        print("✓ Automation stopped")

        return True

    except Exception as e:
        print(f"✗ Campaign processor error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_full_campaign_run():
    """Test running a complete campaign."""
    print("\n=== Testing Full Campaign Run ===")

    # Create test campaign
    campaign_id, user_id = create_test_campaign()
    if not campaign_id:
        return False

    try:
        from app.workers.processors.campaign_processor import CampaignProcessor

        # Create processor with limited scope
        processor = CampaignProcessor(campaign_id, user_id)

        # Run just one submission as a test
        print("Running single submission test...")

        await processor.automation.start()

        # Get user data
        user_data = await processor._get_user_profile_data(uuid.UUID(user_id))

        # Test processing one URL
        result = await processor.automation.process_website(
            "https://httpbin.org/forms/post", user_data
        )

        print(f"✓ Processing result: {result}")

        await processor.automation.stop()

        return True

    except Exception as e:
        print(f"✗ Full campaign test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_subprocess_runner():
    """Test the subprocess runner that's used in production."""
    print("\n=== Testing Subprocess Runner ===")

    try:
        from app.workers.processors.subprocess_runner import run_campaign_direct

        # Create test campaign
        campaign_id, user_id = create_test_campaign()
        if not campaign_id:
            return False

        print(f"Testing subprocess with campaign: {campaign_id[:8]}")

        # This will run in a separate thread
        import threading
        import time

        def run_test():
            try:
                run_campaign_direct(campaign_id, user_id)
            except Exception as e:
                print(f"Subprocess error: {e}")

        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()

        # Wait a bit to see if it starts
        time.sleep(5)

        if thread.is_alive():
            print("✓ Subprocess runner started successfully")
            # Let it run for a bit more
            time.sleep(10)
            return True
        else:
            print("✗ Subprocess runner finished quickly (likely failed)")
            return False

    except Exception as e:
        print(f"✗ Subprocess runner test error: {e}")
        return False


if __name__ == "__main__":
    print("=== Campaign Processing Diagnostics ===")

    # Set event loop policy for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Test 1: Database connection
    db_success = test_database_connection()

    if not db_success:
        print("\n✗ Database connection failed. Fix your DATABASE_URL in .env")
        sys.exit(1)

    # Create event loop for async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Test 2: Campaign processor components
        processor_success = loop.run_until_complete(test_campaign_processor())

        # Test 3: Full campaign run (single submission)
        if processor_success:
            campaign_success = loop.run_until_complete(test_full_campaign_run())
        else:
            campaign_success = False

    finally:
        loop.close()

    # Test 4: Subprocess runner (production method)
    subprocess_success = test_subprocess_runner()

    print("\n=== Summary ===")
    print(f"Database: {'✓' if db_success else '✗'}")
    print(f"Campaign Processor: {'✓' if processor_success else '✗'}")
    print(f"Full Campaign Test: {'✓' if campaign_success else '✗'}")
    print(f"Subprocess Runner: {'✓' if subprocess_success else '✗'}")

    if all([db_success, processor_success, campaign_success]):
        print("\n🎉 All tests passed! Your campaign processing should work.")
        print("If the frontend still shows 'PROCESSING' without opening browser,")
        print("the issue is likely in the API endpoint or frontend communication.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
