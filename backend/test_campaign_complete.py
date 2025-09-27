# simple_campaign_test.py
"""Simple campaign test using existing data."""

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


def get_or_create_test_data():
    """Get existing test user or use any existing user."""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.models.user_profile import UserProfile

        db = SessionLocal()

        # Try to find existing test user
        user = db.query(User).filter(User.email == "test@example.com").first()

        if not user:
            # Get any existing user
            user = db.query(User).first()
            if not user:
                print(
                    "❌ No users found in database. Please create a user through the frontend first."
                )
                return None, None

        print(f"✓ Using user: {user.email} (ID: {user.id})")

        # Check if user has profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if profile:
            print(f"✓ User has profile with data")
        else:
            print("⚠️ User has no profile - will use fallback data")

        db.close()
        return str(user.id), user.email

    except Exception as e:
        print(f"❌ Database error: {e}")
        return None, None


def create_simple_test_campaign(user_id: str):
    """Create a simple test campaign."""
    try:
        from app.core.database import SessionLocal
        from app.models.campaign import Campaign, CampaignStatus
        from app.models.submission import Submission, SubmissionStatus

        db = SessionLocal()

        # Create test campaign with unique name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_campaign_id = uuid.uuid4()

        campaign = Campaign(
            id=test_campaign_id,
            user_id=uuid.UUID(user_id),
            name=f"Test Campaign {timestamp}",
            description="Simple test campaign",
            status=CampaignStatus.DRAFT,  # Use DRAFT instead of PENDING
            total_urls=2,
            created_at=datetime.utcnow(),
        )

        db.add(campaign)
        db.flush()

        # Create simple test submissions
        test_urls = [
            "https://httpbin.org/forms/post",  # Has forms
            "https://example.com",  # Simple site
        ]

        for url in test_urls:
            submission = Submission(
                id=uuid.uuid4(),
                campaign_id=test_campaign_id,
                url=url,
                status=SubmissionStatus.PENDING.value,  # Use .value for string
                created_at=datetime.utcnow(),
            )
            db.add(submission)

        db.commit()
        db.close()

        print(f"✓ Created test campaign: {test_campaign_id}")
        print(f"✓ Created {len(test_urls)} test submissions")

        return str(test_campaign_id)

    except Exception as e:
        print(f"❌ Failed to create test campaign: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_browser_automation():
    """Quick browser test to verify it opens visibly."""
    try:
        import asyncio

        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        async def test():
            from app.workers.automation import AutomationController

            controller = AutomationController(user_id="test", campaign_id="test")

            print("🔥 Starting browser test - browser should open now...")
            await controller.start()

            # Test with a form site
            result = await controller.process_website(
                "https://httpbin.org/forms/post",
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "message": "This is a test message for form automation.",
                },
            )

            print(f"Browser test result: {result.get('success', False)}")
            print(f"Method used: {result.get('method', 'none')}")

            await controller.stop()
            return result.get("success", False)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(test())
        finally:
            loop.close()

    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False


def run_campaign_test(campaign_id: str, user_id: str):
    """Run the campaign processing test."""
    try:
        print(f"\n🚀 Starting campaign processing...")
        print(f"Campaign ID: {campaign_id[:8]}...")
        print(f"User ID: {user_id[:8]}...")
        print(f"🔥 BROWSER SHOULD OPEN VISIBLY NOW!")

        # Import and run the fixed campaign processor
        from app.workers.processors.campaign_processor import process_campaign_sync

        # Run the campaign
        process_campaign_sync(campaign_id, user_id)

        print("✅ Campaign processing completed!")

        # Check results
        from app.core.database import SessionLocal
        from app.models.campaign import Campaign
        from app.models.submission import Submission

        db = SessionLocal()

        campaign = (
            db.query(Campaign).filter(Campaign.id == uuid.UUID(campaign_id)).first()
        )
        submissions = (
            db.query(Submission)
            .filter(Submission.campaign_id == uuid.UUID(campaign_id))
            .all()
        )

        print(f"\n=== RESULTS ===")
        print(f"Campaign Status: {campaign.status}")
        print(f"Processed: {campaign.processed}/{campaign.total_urls}")
        print(f"Successful: {campaign.successful}")
        print(f"Failed: {campaign.failed_count}")

        if campaign.error_message:
            print(f"Error: {campaign.error_message}")

        for i, sub in enumerate(submissions, 1):
            status = "✅" if sub.success else "❌"
            print(f"  {status} {sub.url} -> {sub.status}")
            if sub.contact_method:
                print(f"      Method: {sub.contact_method}")
            if sub.email_extracted:
                print(f"      Email: {sub.email_extracted}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Campaign test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("=== Simple Campaign Processing Test ===")
    print("This test will:")
    print("1. Use existing database data")
    print("2. Create a simple test campaign")
    print("3. Run browser automation visibly")
    print("4. Show detailed results")
    print()

    # Step 1: Get test data
    print("1. Getting test user data...")
    user_id, user_email = get_or_create_test_data()
    if not user_id:
        return False

    # Step 2: Test browser first
    print("\n2. Testing browser automation...")
    browser_works = test_browser_automation()
    if not browser_works:
        print("❌ Browser test failed - fix browser issues first")
        return False
    print("✅ Browser test passed!")

    # Step 3: Create test campaign
    print("\n3. Creating test campaign...")
    campaign_id = create_simple_test_campaign(user_id)
    if not campaign_id:
        return False

    # Step 4: Run campaign test
    print("\n4. Running campaign processing test...")
    input("Press Enter to continue (browser will open for automation)...")

    campaign_works = run_campaign_test(campaign_id, user_id)

    print(f"\n=== FINAL RESULTS ===")
    print(f"Browser Test: {'✅ PASS' if browser_works else '❌ FAIL'}")
    print(f"Campaign Test: {'✅ PASS' if campaign_works else '❌ FAIL'}")

    if browser_works and campaign_works:
        print("\n🎉 SUCCESS! Your campaign processing is working!")
        print("You can now:")
        print("1. Upload a CSV file through the frontend")
        print("2. Create a campaign")
        print("3. Click 'Start Campaign'")
        print("4. Watch the browser automation work!")
    else:
        print("\n❌ Some tests failed. Check the errors above.")

    return browser_works and campaign_works


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
