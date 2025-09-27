# app/services/browser_automation_service.py
"""Browser automation service layer."""

import asyncio
import logging
import time
from typing import Dict, Optional, Any
from datetime import datetime

from app.workers.browser_automation import BrowserAutomation

logger = logging.getLogger(__name__)


class BrowserAutomationService:
    """Service layer for browser automation."""

    def __init__(self, headless: bool = None):
        self.browser_automation = BrowserAutomation(headless)
        self.initialized = False
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "start_time": None,
        }

    async def initialize(self):
        """Initialize browser."""
        try:
            await self.browser_automation.start()
            self.initialized = True
            self.stats["start_time"] = datetime.utcnow()
            logger.info("Browser automation service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.initialized:
                await self.browser_automation.stop()
                self.initialized = False
                self._log_statistics()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def process_website(self, url: str, user_data: Dict) -> Dict[str, Any]:
        """Process a website."""
        if not self.initialized:
            return {
                "success": False,
                "error": "Service not initialized",
            }

        start_time = time.time()

        try:
            result = await self.browser_automation.process(url, user_data)

            # Update stats
            self.stats["total_processed"] += 1
            if result.get("success"):
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1

            result["processing_time"] = time.time() - start_time

            return result

        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
            }

    def _log_statistics(self):
        """Log processing statistics."""
        if self.stats["total_processed"] > 0:
            success_rate = (
                self.stats["successful"] / self.stats["total_processed"] * 100
            )
            logger.info(
                f"Session stats: Total={self.stats['total_processed']}, "
                f"Success rate={success_rate:.1f}%"
            )
