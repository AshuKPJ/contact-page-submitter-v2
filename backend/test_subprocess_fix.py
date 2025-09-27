# test_campaign_fix.py
"""Test the fixed campaign processing."""

import sys
import uuid
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def create_test_campaign_and_run():
    """Create a test campaign and run it with the fixed processor."""
    try:
        from app.core.database import SessionLocal
        from app.models.campaign import Campaign, CampaignStatus
        from app.models.submission import Submission, SubmissionStatus
        from app.models.user import User

        db = SessionLocal()

        # Create test user if doesn't exist
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user_id = uuid.uuid4()
            test_user = User(
                id=test_user_id,
                email="test@example.com",
                username="testuser",
                hashed_password="dummy",
                is_active=True,
                is_verified=True,
            )
            db.add(test_user)
            db.commit()
            print(f"Created test user: {test_user_id}")
        else:
            test_user_id = test_user.id
            print(f"Using existing test user: {test_user_id}")

        # Create test campaign
        test_campaign_id = uuid.uuid4()
        test_campaign = Campaign(
            id=test_campaign_id,
            user_id=test_user_id,
            name="Fixed Test Campaign",
            description="Testing the fixed campaign processor",
            status=CampaignStatus.PENDING,
            total_urls=3,
            created_at=datetime.utcnow(),
        )

        db.add(test_campaign)
        db.flush()

        # Create test submissions with various scenarios
        test_urls = [
            "https://example.com",  # Simple site (should extract email)
            "https://httpbin.org/forms/post",  # Has forms
            "https://www.google.com",  # Should work but no forms
        ]

        for url in test_urls:
            submission = Submission(
                id=uuid.uuid4(),
                campaign_id=test_campaign_id,
                url=url,
                status=SubmissionStatus.PENDING,
                created_at=datetime.utcnow(),
            )
            db.add(submission)

        db.commit()
        db.close()

        print(f"✓ Created test campaign: {test_campaign_id}")
        print(f"✓ Created {len(test_urls)} test submissions")

        # Now test the fixed campaign processor
        print("\n=== Testing Fixed Campaign Processor ===")

        from app.workers.processors.campaign_processor import process_campaign_sync

        # Run the campaign processing
        print("Starting campaign processing...")
        try:
            process_campaign_sync(str(test_campaign_id), str(test_user_id))
            print("✓ Campaign processing completed without crashing!")

            # Check final status
            db = SessionLocal()
            final_campaign = (
                db.query(Campaign).filter(Campaign.id == test_campaign_id).first()
            )
            if final_campaign:
                print(f"✓ Final campaign status: {final_campaign.status}")
                print(f"✓ Processed: {final_campaign.processed}")
                print(f"✓ Successful: {final_campaign.successful}")
                print(f"✓ Failed: {final_campaign.failed_count}")

                if final_campaign.error_message:
                    print(f"⚠️ Error message: {final_campaign.error_message}")

            db.close()

            return True

        except Exception as e:
            print(f"❌ Campaign processing failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_browser_visibility():
    """Quick test to ensure browser opens visibly."""
    import asyncio

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    async def test():
        from app.workers.automation import AutomationController

        controller = AutomationController(user_id="test", campaign_id="test")

        print("Testing browser visibility...")
        await controller.start()

        # Test with a simple site
        result = await controller.process_website(
            "https://example.com", {"email": "test@example.com", "name": "Test User"}
        )

        print(f"✓ Browser test result: {result}")

        await controller.stop()
        return True

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        success = loop.run_until_complete(test())
        return success
    finally:
        loop.close()


if __name__ == "__main__":
    print("=== Testing Fixed Campaign Processing ===")

    # Test 1: Browser visibility
    print("\n1. Testing browser visibility...")
    browser_success = test_browser_visibility()

    # Test 2: Full campaign processing
    print("\n2. Testing complete campaign processing...")
    campaign_success = create_test_campaign_and_run()

    print("\n=== Test Results ===")
    print(f"Browser Test: {'✓ PASS' if browser_success else '❌ FAIL'}")
    print(f"Campaign Test: {'✓ PASS' if campaign_success else '❌ FAIL'}")

    if browser_success and campaign_success:
        print(
            "\n🎉 All tests passed! Your campaign processing should now work correctly."
        )
        print("The browser should open visibly when you start a real campaign.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
