# app/workers/__init__.py
"""Workers module for background processing."""

import asyncio
import sys
import logging
import uuid
from datetime import datetime
from typing import Optional

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.campaign import Campaign

logger = logging.getLogger(__name__)


def ensure_windows_event_loop():
    """Ensure ProactorEventLoop is set for Windows subprocess support."""
    if sys.platform == "win32":
        # Force ProactorEventLoop for subprocess support
        loop = asyncio.get_event_loop()
        if not isinstance(loop, asyncio.ProactorEventLoop):
            logger.info("Setting ProactorEventLoop for Windows subprocess support")
            # Close the existing loop if it's running
            try:
                if loop.is_running():
                    logger.warning("Cannot change event loop while running")
                else:
                    loop.close()
            except:
                pass

            # Set ProactorEventLoop policy
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            # Create new loop
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            logger.info("ProactorEventLoop set successfully")


async def process_campaign_async(campaign_id: str, user_id: Optional[str] = None):
    """Process campaign asynchronously."""
    # Ensure proper event loop for Windows
    ensure_windows_event_loop()

    # Import from processors folder
    from .processors.campaign_processor import CampaignProcessor

    try:
        processor = CampaignProcessor(campaign_id, user_id=user_id)
        await processor.run()
        logger.info(f"Campaign {campaign_id[:8]} completed successfully")
    except Exception as e:
        logger.error(f"Campaign {campaign_id[:8]} failed: {e}")
        raise


def process_campaign(
    campaign_id: str, user_id: Optional[str] = None, headless: Optional[bool] = None
):
    """
    Process campaign synchronously.

    Args:
        campaign_id: UUID of the campaign to process
        user_id: Optional UUID of the user (if not provided, will be fetched from campaign)
        headless: Optional browser headless mode setting
    """
    # CRITICAL: Set Windows event loop policy BEFORE any async operations
    if sys.platform == "win32":
        # This must be done in the thread that will run the event loop
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.info("Set WindowsProactorEventLoopPolicy for subprocess support")

    settings = get_settings()

    # Check environment variables for browser settings
    import os

    # Override headless based on environment variable
    if os.getenv("DEV_AUTOMATION_HEADFUL", "false").lower() == "true":
        headless = False
    elif headless is None:
        headless = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

    # Validate campaign_id format
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError as e:
        raise ValueError(f"Invalid campaign_id format: {e}")

    # If user_id not provided, fetch from campaign
    if not user_id:
        db = SessionLocal()
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            if campaign:
                user_id = str(campaign.user_id)
                logger.info(
                    f"Retrieved user_id {user_id[:8]} for campaign {campaign_id[:8]}"
                )
            else:
                logger.warning(f"Campaign {campaign_id[:8]} not found in database")
        except Exception as e:
            logger.error(f"Error fetching campaign user_id: {e}")
        finally:
            db.close()

    logger.info(
        f"Starting campaign processing: {campaign_id[:8]} for user {user_id[:8] if user_id else 'unknown'} (headless={headless})"
    )

    # Create new event loop with ProactorEventLoop on Windows
    if sys.platform == "win32":
        # Create a new ProactorEventLoop
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        logger.info("Created new ProactorEventLoop for campaign processing")
    else:
        # Use standard event loop for non-Windows systems
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

    try:
        # Run the campaign
        loop.run_until_complete(process_campaign_async(campaign_id, user_id))
        logger.info(f"Campaign {campaign_id[:8]} completed")
    except Exception as e:
        logger.error(f"Campaign {campaign_id[:8]} failed: {e}")
        raise
    finally:
        try:
            # Clean up the loop
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            # Wait for all tasks to complete
            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )

            # Close the loop
            loop.close()
            logger.info("Event loop closed successfully")
        except Exception as e:
            logger.warning(f"Error closing event loop: {e}")


# Also export the sync version for direct use
def process_campaign_sync(campaign_id: str, user_id: Optional[str] = None):
    """Synchronous wrapper for campaign processing (direct call)."""
    from .processors.campaign_processor import process_campaign_sync as sync_processor

    sync_processor(campaign_id, user_id)
