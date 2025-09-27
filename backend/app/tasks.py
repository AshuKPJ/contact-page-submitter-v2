# backend/app/tasks.py
import asyncio
import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.campaign import Campaign, CampaignStatus
from app.models.website import Website
import time


async def process_campaign(campaign_id: str):
    """Process campaign websites - simple version for testing"""
    db = SessionLocal()

    try:
        print(f"[AUTOMATION] Starting campaign processing: {campaign_id}")

        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            print(f"[AUTOMATION] Campaign not found: {campaign_id}")
            return

        # Get websites for this campaign
        websites = db.query(Website).filter(Website.campaign_id == campaign_id).all()

        if not websites:
            print(f"[AUTOMATION] No websites found for campaign: {campaign_id}")
            # If no websites in DB, use the campaign's total_websites count for simulation
            num_websites = campaign.total_websites or 10
            websites = [{"domain": f"example{i}.com"} for i in range(num_websites)]

        print(f"[AUTOMATION] Processing {len(websites)} websites")

        # Update campaign status to ACTIVE
        campaign.status = CampaignStatus.ACTIVE
        campaign.started_at = datetime.utcnow()
        db.commit()

        # Process each website
        for index, website in enumerate(websites):
            # Simulate processing delay (2-5 seconds per site for testing)
            await asyncio.sleep(random.uniform(2, 5))

            # Simulate success/failure (90% success rate)
            success = random.random() < 0.9

            if success:
                campaign.successful = (campaign.successful or 0) + 1
                print(
                    f"[AUTOMATION] ✓ Processed {website.domain if hasattr(website, 'domain') else website['domain']} successfully"
                )
            else:
                campaign.failed = (campaign.failed or 0) + 1
                print(
                    f"[AUTOMATION] ✗ Failed to process {website.domain if hasattr(website, 'domain') else website['domain']}"
                )

            campaign.processed = (campaign.processed or 0) + 1

            # Update progress in database
            db.commit()

            print(
                f"[AUTOMATION] Progress: {campaign.processed}/{len(websites)} ({(campaign.processed/len(websites)*100):.1f}%)"
            )

        # Mark campaign as completed
        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.utcnow()
        db.commit()

        print(f"[AUTOMATION] Campaign {campaign_id} completed!")
        print(
            f"[AUTOMATION] Results: {campaign.successful} successful, {campaign.failed} failed"
        )

    except Exception as e:
        print(f"[AUTOMATION ERROR] {str(e)}")
        if campaign:
            campaign.status = CampaignStatus.FAILED
            db.commit()
    finally:
        db.close()


# For synchronous execution (if not using async)
def process_campaign_sync(campaign_id: str):
    """Synchronous wrapper for the async function"""
    asyncio.run(process_campaign(campaign_id))


# Simple delay function for testing without Celery
class MockTask:
    def delay(self, campaign_id):
        """Mock Celery-like interface"""
        # Run in background thread
        import threading

        thread = threading.Thread(target=process_campaign_sync, args=(campaign_id,))
        thread.daemon = True
        thread.start()
        print(f"[AUTOMATION] Started background processing for campaign {campaign_id}")


# Export as if it were a Celery task
process_campaign = MockTask()
