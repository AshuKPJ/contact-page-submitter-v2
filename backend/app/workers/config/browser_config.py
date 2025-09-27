# app/workers/config/browser_config.py
"""Browser configuration for automation."""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BrowserConfig:
    """Configuration for browser automation."""

    headless: bool = True
    slow_mo: int = 0
    page_timeout: int = 30000
    navigation_timeout: int = 30000
    browser_type: str = "chromium"
    user_agent: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    ignore_https_errors: bool = True

    @classmethod
    def from_environment(cls) -> "BrowserConfig":
        """Create configuration from environment variables."""
        return cls(
            headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            slow_mo=int(os.getenv("BROWSER_SLOW_MO", "0")),
            page_timeout=int(os.getenv("BROWSER_PAGE_TIMEOUT", "30000")),
            navigation_timeout=int(os.getenv("BROWSER_NAV_TIMEOUT", "30000")),
            browser_type=os.getenv("BROWSER_TYPE", "chromium"),
            user_agent=os.getenv("BROWSER_USER_AGENT"),
            viewport_width=int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1920")),
            viewport_height=int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "1080")),
            ignore_https_errors=os.getenv("BROWSER_IGNORE_HTTPS", "true").lower()
            == "true",
        )

    def to_playwright_args(self) -> Dict[str, Any]:
        """Convert to Playwright browser args."""
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ]

        if self.headless:
            args.append("--headless")

        return {
            "headless": self.headless,
            "slow_mo": self.slow_mo,
            "args": args,
        }

    def to_context_args(self) -> Dict[str, Any]:
        """Convert to Playwright context args."""
        context_args = {
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
            "ignore_https_errors": self.ignore_https_errors,
            "java_script_enabled": True,
        }

        if self.user_agent:
            context_args["user_agent"] = self.user_agent
        else:
            context_args["user_agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

        return context_args
