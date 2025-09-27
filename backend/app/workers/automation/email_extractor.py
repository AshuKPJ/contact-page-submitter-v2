# app/workers/automation/email_extractor.py
import re
from typing import List
from playwright.async_api import Page
from app.workers.utils.logger import WorkerLogger


class EmailExtractor:
    def __init__(self, user_id=None, campaign_id=None):
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )

    async def extract_emails(self, page: Page) -> List[str]:
        """Extract emails from page using multiple strategies."""
        emails = set()

        # Strategy 1: mailto links
        try:
            mailto_links = await page.query_selector_all('a[href^="mailto:"]')
            for link in mailto_links:
                href = await link.get_attribute("href")
                if href:
                    email = href.replace("mailto:", "").split("?")[0]
                    if self._is_valid_email(email):
                        emails.add(email)
        except Exception as e:
            self.logger.warning(f"Mailto extraction error: {e}")

        # Strategy 2: text scanning
        try:
            body_text = await page.inner_text("body")
            found_emails = self.email_pattern.findall(body_text)
            for email in found_emails:
                if self._is_valid_email(email):
                    emails.add(email)
        except Exception as e:
            self.logger.warning(f"Text extraction error: {e}")

        # Filter and return
        filtered = [
            e
            for e in emails
            if not any(x in e.lower() for x in ["noreply", "example.com"])
        ]
        return list(filtered)[:5]

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        return bool(email and len(email) < 255 and self.email_pattern.match(email))
