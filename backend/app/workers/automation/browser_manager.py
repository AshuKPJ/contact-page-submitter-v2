# app/workers/automation/browser_manager.py
"""Browser manager for handling browser lifecycle and page creation."""

import logging
from typing import Optional
from playwright.async_api import Page

from app.workers.automation.browser_automation import BrowserAutomation
from app.workers.config.browser_config import BrowserConfig
from app.workers.utils.logger import WorkerLogger

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages browser instances and page creation."""

    def __init__(
        self,
        config: Optional[BrowserConfig] = None,
        user_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ):
        """Initialize browser manager."""
        self.config = config or BrowserConfig.from_environment()
        self.user_id = user_id
        self.campaign_id = campaign_id
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        # Initialize browser automation with config
        self.browser = BrowserAutomation(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
            user_id=user_id,
            campaign_id=campaign_id,
        )

        self._is_started = False

    async def start(self):
        """Start the browser."""
        if not self._is_started:
            self.logger.info("Starting browser manager")
            await self.browser.start()
            self._is_started = True
            self.logger.info("Browser manager started successfully")

    async def stop(self):
        """Stop the browser."""
        if self._is_started:
            self.logger.info("Stopping browser manager")
            await self.browser.stop()
            self._is_started = False
            self.logger.info("Browser manager stopped successfully")

    async def create_new_page(self) -> Page:
        """Create a new browser page."""
        if not self._is_started:
            await self.start()

        if not self.browser.context:
            raise RuntimeError("Browser context not initialized")

        page = await self.browser.context.new_page()

        # Set default timeout from config
        page.set_default_timeout(self.config.page_timeout)

        self.logger.info("Created new browser page")
        return page

    @property
    def is_ready(self) -> bool:
        """Check if browser is ready."""
        return self._is_started and self.browser.context is not None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
