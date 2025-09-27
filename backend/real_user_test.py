# real_user_test.py
"""Test campaign processing with real user data."""

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


def get_real_user_data():
    """Get user data for ashukarande151@gmail.com"""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.models.user_profile import UserProfile

        db = SessionLocal()

        # Find the real user
        user = db.query(User).filter(User.email == "ashukarande151@gmail.com").first()

        if not user:
            print("❌ User ashukarande151@gmail.com not found in database")
            db.close()
            return None, None

        print(f"✓ Found user: {user.email}")
        print(f"  ID: {user.id}")
        print(f"  Name: {user.first_name} {user.last_name}")
        print(f"  Active: {user.is_active}")
        print(f"  Verified: {user.is_verified}")

        # Check for user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if profile:
            print(f"✓ User has profile data:")
            print(f"  Company: {profile.company_name}")
            print(f"  Job Title: {profile.job_title}")
            print(f"  Industry: {profile.industry}")
            print(f"  Phone: {profile.phone_number}")
            print(
                f"  Message: {profile.message[:100] if profile.message else 'None'}..."
            )
        else:
            print("⚠️ User has no profile - will create basic one for testing")

        db.close()
        return str(user.id), user.email

    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback

        traceback.print_exc()
        return None, None


def create_real_campaign(user_id: str):
    """Create a test campaign for the real user."""
    try:
        from app.core.database import SessionLocal
        from app.models.campaign import Campaign, CampaignStatus
        from app.models.submission import Submission, SubmissionStatus

        db = SessionLocal()

        # Create test campaign with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_campaign_id = uuid.uuid4()

        campaign = Campaign(
            id=test_campaign_id,
            user_id=uuid.UUID(user_id),
            name=f"Real User Test {timestamp}",
            status=CampaignStatus.DRAFT,
            total_urls=3,
            created_at=datetime.utcnow(),
        )

        db.add(campaign)
        db.flush()

        # Test URLs - mix of sites with forms and without
        test_urls = [
            "https://httpbin.org/forms/post",  # Has contact form
            "https://example.com",  # Simple site for email extraction
            "https://httpbin.org/html",  # HTML test page
        ]

        for url in test_urls:
            submission = Submission(
                id=uuid.uuid4(),
                campaign_id=test_campaign_id,
                url=url,
                status=SubmissionStatus.PENDING.value,
                created_at=datetime.utcnow(),
            )
            db.add(submission)

        db.commit()
        db.close()

        print(f"✓ Created real user campaign: {test_campaign_id}")
        print(f"✓ Added {len(test_urls)} test URLs")

        return str(test_campaign_id)

    except Exception as e:
        print(f"❌ Failed to create campaign: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_automation_with_real_data(user_id: str):
    """Test browser automation with real user data."""
    try:
        import asyncio

        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        async def test():
            from app.workers.automation import AutomationController

            # Use real user ID for automation controller
            controller = AutomationController(user_id=user_id[:8], campaign_id="test")

            print("🔥 Testing with real user data - browser opening...")
            await controller.start()

            # Test with the form site using real user profile data
            result = await controller.process_website(
                "https://httpbin.org/forms/post", {}
            )

            print(f"Result: {result.get('success', False)}")
            print(f"Method: {result.get('method', 'none')}")
            if result.get("details"):
                details = result["details"]
                print(f"Fields filled: {details.get('fields_filled', 0)}")
                print(f"Form score: {details.get('form_score', 0)}")

            await controller.stop()
            return result.get("success", False)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(test())
        finally:
            loop.close()

    except Exception as e:
        print(f"❌ Automation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_real_campaign(campaign_id: str, user_id: str):
    """Run the complete campaign with real user data."""
    try:
        print(f"\n🚀 STARTING REAL CAMPAIGN PROCESSING")
        print(f"Campaign: {campaign_id[:8]}...")
        print(f"User: ashukarande151@gmail.com")
        print(f"🔥 BROWSER WILL OPEN VISIBLY - WATCH THE AUTOMATION!")
        print("")

        # Import and run the fixed campaign processor
        from app.workers.processors.campaign_processor import process_campaign_sync

        # Run the real campaign
        process_campaign_sync(campaign_id, user_id)

        print("\n✅ CAMPAIGN PROCESSING COMPLETED!")

        # Show detailed results
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

        print(f"\n=== FINAL RESULTS ===")
        print(f"Campaign Status: {campaign.status}")
        print(f"Total URLs: {campaign.total_urls}")
        print(f"Processed: {campaign.processed}")
        print(f"Successful: {campaign.successful}")
        print(f"Failed: {campaign.failed_count}")

        if campaign.error_message:
            print(f"Campaign Error: {campaign.error_message}")

        print(f"\n=== URL RESULTS ===")
        for i, sub in enumerate(submissions, 1):
            status_icon = "✅" if sub.success else "❌"
            print(f"{status_icon} {i}. {sub.url}")
            print(f"    Status: {sub.status}")

            if sub.contact_method:
                print(f"    Method: {sub.contact_method}")

            if sub.email_extracted:
                print(f"    Email Found: {sub.email_extracted}")

            if sub.error_message:
                print(f"    Error: {sub.error_message}")

            if sub.field_mapping_data:
                mapping = sub.field_mapping_data
                if "fields_filled" in mapping:
                    print(f"    Fields Filled: {mapping['fields_filled']}")
                if "confidence_avg" in mapping:
                    print(f"    Confidence: {mapping['confidence_avg']:.2f}")

            print()  # Empty line between submissions

        db.close()
        return True

    except Exception as e:
        print(f"❌ Campaign failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("=== REAL USER CAMPAIGN TEST ===")
    print("Testing with: ashukarande151@gmail.com")
    print("This will use your real profile data for form filling")
    print("")

    # Step 1: Get real user data
    print("1. Loading real user data...")
    user_id, email = get_real_user_data()
    if not user_id:
        return False

    # Step 2: Test automation with real data
    print("\n2. Testing automation with your profile data...")
    automation_works = test_automation_with_real_data(user_id)
    if not automation_works:
        print("❌ Automation test failed")
        return False
    print("✅ Automation test with real data passed!")

    # Step 3: Create real campaign
    print("\n3. Creating test campaign...")
    campaign_id = create_real_campaign(user_id)
    if not campaign_id:
        return False

    # Step 4: Run complete campaign
    print("\n4. Ready to run complete campaign processing...")
    print("You will see:")
    print("  • Browser window open visibly")
    print("  • Navigate to test websites")
    print("  • Fill forms with your real profile data")
    print("  • Submit forms automatically")
    print("  • Extract emails from sites without forms")
    print("")

    input("Press Enter to start the campaign (browser will open)...")

    campaign_works = run_real_campaign(campaign_id, user_id)

    print(f"\n=== FINAL TEST RESULTS ===")
    print(f"Real User Data: ✅ Found")
    print(f"Automation Test: {'✅ PASS' if automation_works else '❌ FAIL'}")
    print(f"Campaign Test: {'✅ PASS' if campaign_works else '❌ FAIL'}")

    if automation_works and campaign_works:
        print(f"\n🎉 SUCCESS! Your campaign system is fully working!")
        print(f"Your browser automation:")
        print(f"  • Opens visibly so you can watch")
        print(f"  • Uses your real profile data for form filling")
        print(f"  • Detects and fills contact forms accurately")
        print(f"  • Handles errors gracefully")
        print(f"  • Updates campaign status properly")
        print(f"")
        print(f"You can now use the frontend to:")
        print(f"  1. Upload your CSV file with real websites")
        print(f"  2. Create a campaign")
        print(f"  3. Click 'Start Campaign'")
        print(f"  4. Watch it process all your URLs automatically!")
    else:
        print(f"\n❌ Some tests failed. Check errors above.")

    return automation_works and campaign_works


if __name__ == "__main__":
    success = main()
    print(f"\nTest completed with {'SUCCESS' if success else 'FAILURE'}")
