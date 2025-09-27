# app/workers/campaign_processor.py - Enhanced Campaign Processor with Real Browser Automation
"""
Campaign processor that handles form submissions using Playwright
"""
import sys
import os
import time
import logging
import json
import traceback
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from playwright.async_api import (
        async_playwright,
        Page,
        Browser,
        BrowserContext,
        TimeoutError as PlaywrightTimeout,
    )
    from app.workers.config.browser_config import BrowserConfig
except ImportError as e:
    logger.error(f"Required modules not installed: {e}")
    logger.error("Install with: pip install sqlalchemy playwright")
    logger.error("Then run: playwright install chromium")
    sys.exit(1)


class FormSubmitter:
    """Handles actual form submission using Playwright"""

    def __init__(self, browser_config: BrowserConfig):
        self.config = browser_config
        self.browser = None
        self.context = None
        self.playwright = None

    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()

            # Launch browser based on config
            if self.config.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(
                    **self.config.to_playwright_args()
                )
            elif self.config.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(
                    **self.config.to_playwright_args()
                )
            else:
                self.browser = await self.playwright.chromium.launch(
                    **self.config.to_playwright_args()
                )

            # Create context with config
            self.context = await self.browser.new_context(
                **self.config.to_context_args()
            )

            logger.info(f"Browser initialized: {self.config.browser_type}")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def find_contact_form(self, page: Page) -> Optional[Dict[str, Any]]:
        """Find contact form on the page"""
        try:
            # Common form selectors
            form_selectors = [
                'form[id*="contact"]',
                'form[class*="contact"]',
                'form[id*="message"]',
                'form[class*="message"]',
                'form[action*="contact"]',
                'form[action*="submit"]',
                "#contact-form",
                ".contact-form",
                'form[method="post"]',
                "form",  # Last resort - any form
            ]

            for selector in form_selectors:
                form = await page.query_selector(selector)
                if form:
                    # Check if it has input fields
                    inputs = await form.query_selector_all(
                        'input[type="text"], input[type="email"], textarea'
                    )
                    if len(inputs) > 0:
                        logger.info(f"Found form with selector: {selector}")
                        return {
                            "selector": selector,
                            "element": form,
                            "input_count": len(inputs),
                        }

            return None

        except Exception as e:
            logger.error(f"Error finding form: {e}")
            return None

    async def fill_form(
        self, page: Page, form_info: Dict[str, Any], message: str
    ) -> bool:
        """Fill out the contact form"""
        try:
            form = form_info["element"]

            # Common field mappings
            field_mappings = {
                "name": ["name", "full_name", "your_name", "fullname", "contact_name"],
                "email": [
                    "email",
                    "e-mail",
                    "emailaddress",
                    "email_address",
                    "your_email",
                ],
                "subject": ["subject", "title", "topic", "regarding"],
                "message": [
                    "message",
                    "comment",
                    "comments",
                    "inquiry",
                    "details",
                    "body",
                    "content",
                ],
                "phone": ["phone", "telephone", "mobile", "number", "contact_number"],
            }

            filled_fields = 0

            # Fill name field
            for field_name in field_mappings["name"]:
                name_field = await form.query_selector(
                    f'input[name*="{field_name}" i], input[id*="{field_name}" i]'
                )
                if name_field:
                    await name_field.fill("John Smith")
                    filled_fields += 1
                    break

            # Fill email field
            for field_name in field_mappings["email"]:
                email_field = await form.query_selector(
                    f'input[name*="{field_name}" i], input[id*="{field_name}" i], input[type="email"]'
                )
                if email_field:
                    await email_field.fill("contact@example.com")
                    filled_fields += 1
                    break

            # Fill subject field if exists
            for field_name in field_mappings["subject"]:
                subject_field = await form.query_selector(
                    f'input[name*="{field_name}" i], input[id*="{field_name}" i]'
                )
                if subject_field:
                    await subject_field.fill("Business Inquiry")
                    filled_fields += 1
                    break

            # Fill message field
            for field_name in field_mappings["message"]:
                message_field = await form.query_selector(
                    f'textarea[name*="{field_name}" i], textarea[id*="{field_name}" i], textarea'
                )
                if message_field:
                    await message_field.fill(message)
                    filled_fields += 1
                    break

            logger.info(f"Filled {filled_fields} form fields")
            return filled_fields >= 2  # At least email and message

        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False

    async def handle_captcha(self, page: Page) -> bool:
        """Check for and handle CAPTCHA (placeholder for integration)"""
        try:
            # Check for common CAPTCHA indicators
            captcha_indicators = [
                '[class*="recaptcha"]',
                '[id*="recaptcha"]',
                '[class*="captcha"]',
                '[id*="captcha"]',
                'iframe[src*="recaptcha"]',
                'iframe[src*="hcaptcha"]',
            ]

            for selector in captcha_indicators:
                captcha = await page.query_selector(selector)
                if captcha:
                    logger.warning("CAPTCHA detected on page")
                    # Here you would integrate with a CAPTCHA solving service
                    # For now, we'll return False
                    return False

            return True  # No CAPTCHA found

        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {e}")
            return True  # Continue anyway

    async def submit_form(self, page: Page, form_info: Dict[str, Any]) -> bool:
        """Submit the form"""
        try:
            form = form_info["element"]

            # Look for submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button[class*="submit"]',
                'button[id*="submit"]',
                'button[name*="submit"]',
                "button",  # Last resort
            ]

            submit_button = None
            for selector in submit_selectors:
                submit_button = await form.query_selector(selector)
                if submit_button:
                    break

            if not submit_button:
                # Try page-wide search
                for selector in submit_selectors:
                    submit_button = await page.query_selector(selector)
                    if submit_button:
                        break

            if submit_button:
                # Click submit button
                await submit_button.click()

                # Wait for navigation or response
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except PlaywrightTimeout:
                    pass  # Page might not navigate

                # Check for success indicators
                success_indicators = [
                    "thank you",
                    "success",
                    "received",
                    "submitted",
                    "we will get back",
                ]

                page_content = await page.content()
                page_text = page_content.lower()

                for indicator in success_indicators:
                    if indicator in page_text:
                        logger.info(f"Success indicator found: {indicator}")
                        return True

                # Check if form is no longer visible (might indicate success)
                form_still_visible = await page.query_selector(form_info["selector"])
                if not form_still_visible:
                    logger.info("Form no longer visible after submission")
                    return True

                return True  # Assume success if no error

            logger.warning("No submit button found")
            return False

        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False

    async def process_url(self, url: str, message: str) -> Dict[str, Any]:
        """Process a single URL - find form, fill it, and submit"""
        result = {
            "success": False,
            "error": None,
            "form_found": False,
            "form_filled": False,
            "form_submitted": False,
            "has_captcha": False,
        }

        page = None
        try:
            # Create new page for this submission
            page = await self.context.new_page()

            # Navigate to URL with timeout
            try:
                await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=self.config.navigation_timeout,
                )
            except PlaywrightTimeout:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.config.navigation_timeout,
                )

            logger.info(f"Navigated to {url}")

            # Find contact form
            form_info = await self.find_contact_form(page)
            if not form_info:
                # Try to find contact page link
                contact_link = await page.query_selector(
                    'a[href*="contact"], a:has-text("Contact")'
                )
                if contact_link:
                    await contact_link.click()
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    form_info = await self.find_contact_form(page)

            if not form_info:
                result["error"] = "No contact form found"
                return result

            result["form_found"] = True

            # Check for CAPTCHA
            has_captcha = not await self.handle_captcha(page)
            result["has_captcha"] = has_captcha

            if (
                has_captcha and not self.config.ignore_https_errors
            ):  # Using as proxy for "strict mode"
                result["error"] = "CAPTCHA detected"
                return result

            # Fill form
            form_filled = await self.fill_form(page, form_info, message)
            if not form_filled:
                result["error"] = "Failed to fill form fields"
                return result

            result["form_filled"] = True

            # Submit form
            form_submitted = await self.submit_form(page, form_info)
            result["form_submitted"] = form_submitted
            result["success"] = form_submitted

            if not form_submitted:
                result["error"] = "Form submission failed"

            # Take screenshot for debugging (optional)
            if os.getenv("SAVE_SCREENSHOTS", "false").lower() == "true":
                await page.screenshot(path=f'screenshots/{url.replace("/", "_")}.png')

            return result

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            result["error"] = str(e)
            return result

        finally:
            if page:
                await page.close()


class CampaignProcessor:
    """Process campaign submissions with real browser automation"""

    def __init__(self, campaign_id: str, user_id: str, db_url: Optional[str] = None):
        self.campaign_id = campaign_id
        self.user_id = user_id
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///./app.db")

        # Setup database
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Browser config
        self.browser_config = BrowserConfig.from_environment()
        self.form_submitter = FormSubmitter(self.browser_config)

        # Processing state
        self.is_running = True
        self.processed_count = 0
        self.success_count = 0
        self.failed_count = 0

        logger.info(f"Initialized processor for campaign {campaign_id}")

    def get_db(self):
        """Get database session"""
        return self.SessionLocal()

    async def process_submission(
        self, submission: Dict[str, Any], message: str
    ) -> Dict[str, Any]:
        """Process a single submission using browser automation"""
        url = submission.get("url")
        logger.info(f"Processing submission {submission['id']} for URL: {url}")

        # Process with browser
        result = await self.form_submitter.process_url(url, message)

        return result

    def update_submission_status(
        self, db, submission_id: str, success: bool, result: Dict[str, Any]
    ):
        """Update submission status in database"""
        try:
            status = "success" if success else "failed"

            # Build error message from result
            error_message = None
            if not success:
                if result.get("has_captcha"):
                    error_message = "CAPTCHA detected"
                elif not result.get("form_found"):
                    error_message = "No contact form found"
                elif not result.get("form_filled"):
                    error_message = "Could not fill form fields"
                elif not result.get("form_submitted"):
                    error_message = "Form submission failed"
                else:
                    error_message = result.get("error", "Unknown error")

            update_query = text(
                """
                UPDATE submissions 
                SET status = :status,
                    error_message = :error_message,
                    form_found = :form_found,
                    has_captcha = :has_captcha,
                    processed_at = :processed_at,
                    updated_at = :updated_at
                WHERE id = :id
            """
            )

            db.execute(
                update_query,
                {
                    "id": submission_id,
                    "status": status,
                    "error_message": error_message,
                    "form_found": result.get("form_found", False),
                    "has_captcha": result.get("has_captcha", False),
                    "processed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )

        except Exception as e:
            logger.error(f"Failed to update submission {submission_id}: {e}")

    def update_campaign_progress(self, db):
        """Update campaign progress"""
        try:
            update_query = text(
                """
                UPDATE campaigns 
                SET processed = :processed,
                    successful = :successful,
                    failed = :failed,
                    updated_at = :updated_at
                WHERE id = :campaign_id
            """
            )

            db.execute(
                update_query,
                {
                    "campaign_id": self.campaign_id,
                    "processed": self.processed_count,
                    "successful": self.success_count,
                    "failed": self.failed_count,
                    "updated_at": datetime.utcnow(),
                },
            )

            db.commit()

        except Exception as e:
            logger.error(f"Failed to update campaign progress: {e}")
            db.rollback()

    def get_campaign_message(self, db) -> str:
        """Get campaign message template"""
        try:
            query = text("SELECT message FROM campaigns WHERE id = :campaign_id")
            result = db.execute(query, {"campaign_id": self.campaign_id}).first()

            if result and result[0]:
                return result[0]

            return "Hello, I'm interested in learning more about your services."

        except Exception as e:
            logger.error(f"Failed to get campaign message: {e}")
            return "Hello, I'm interested in your services."

    def get_pending_submissions(self, db, batch_size: int = 10) -> List[Dict[str, Any]]:
        """Get batch of pending submissions"""
        try:
            query = text(
                """
                SELECT id, url, campaign_id, user_id
                FROM submissions 
                WHERE campaign_id = :campaign_id 
                AND status = 'pending'
                ORDER BY created_at
                LIMIT :limit
            """
            )

            result = db.execute(
                query, {"campaign_id": self.campaign_id, "limit": batch_size}
            ).fetchall()

            submissions = []
            for row in result:
                submissions.append(
                    {
                        "id": str(row[0]),
                        "url": row[1],
                        "campaign_id": str(row[2]),
                        "user_id": str(row[3]) if row[3] else None,
                    }
                )

            return submissions

        except Exception as e:
            logger.error(f"Failed to get pending submissions: {e}")
            return []

    def check_campaign_status(self, db) -> str:
        """Check if campaign should continue"""
        try:
            query = text("SELECT status FROM campaigns WHERE id = :campaign_id")
            result = db.execute(query, {"campaign_id": self.campaign_id}).first()

            if result:
                return result[0]
            return "UNKNOWN"

        except Exception as e:
            logger.error(f"Failed to check campaign status: {e}")
            return "ERROR"

    def mark_campaign_complete(self, db):
        """Mark campaign as completed"""
        try:
            update_query = text(
                """
                UPDATE campaigns 
                SET status = 'COMPLETED',
                    completed_at = :completed_at,
                    updated_at = :updated_at
                WHERE id = :campaign_id
            """
            )

            now = datetime.utcnow()
            db.execute(
                update_query,
                {
                    "campaign_id": self.campaign_id,
                    "completed_at": now,
                    "updated_at": now,
                },
            )

            db.commit()
            logger.info(f"Campaign {self.campaign_id} marked as completed")

        except Exception as e:
            logger.error(f"Failed to mark campaign as complete: {e}")
            db.rollback()

    def mark_campaign_failed(self, db, error_message: str):
        """Mark campaign as failed"""
        try:
            update_query = text(
                """
                UPDATE campaigns 
                SET status = 'FAILED',
                    error_message = :error_message,
                    updated_at = :updated_at
                WHERE id = :campaign_id
            """
            )

            db.execute(
                update_query,
                {
                    "campaign_id": self.campaign_id,
                    "error_message": error_message[:500],
                    "updated_at": datetime.utcnow(),
                },
            )

            db.commit()
            logger.error(
                f"Campaign {self.campaign_id} marked as failed: {error_message}"
            )

        except Exception as e:
            logger.error(f"Failed to mark campaign as failed: {e}")
            db.rollback()

    async def run(self):
        """Main async processing loop"""
        logger.info(f"Starting campaign processor for {self.campaign_id}")
        db = self.get_db()

        try:
            # Initialize browser
            await self.form_submitter.initialize()

            # Get campaign message
            message = self.get_campaign_message(db)

            while self.is_running:
                # Check campaign status
                status = self.check_campaign_status(db)

                if status not in ["PROCESSING", "RUNNING"]:
                    logger.info(
                        f"Campaign {self.campaign_id} status is {status}, stopping"
                    )
                    break

                # Get pending submissions
                submissions = self.get_pending_submissions(db, batch_size=5)

                if not submissions:
                    logger.info(
                        f"No more pending submissions for campaign {self.campaign_id}"
                    )
                    self.mark_campaign_complete(db)
                    break

                logger.info(f"Processing batch of {len(submissions)} submissions")

                # Process each submission
                for submission in submissions:
                    try:
                        # Process with browser automation
                        result = await self.process_submission(submission, message)

                        # Update database
                        if result["success"]:
                            self.success_count += 1
                        else:
                            self.failed_count += 1

                        self.processed_count += 1
                        self.update_submission_status(
                            db, submission["id"], result["success"], result
                        )

                    except Exception as e:
                        logger.error(
                            f"Error processing submission {submission['id']}: {e}"
                        )
                        self.failed_count += 1
                        self.processed_count += 1
                        self.update_submission_status(
                            db, submission["id"], False, {"error": str(e)[:200]}
                        )

                # Commit batch and update progress
                db.commit()
                self.update_campaign_progress(db)

                logger.info(
                    f"Batch complete. Total: {self.processed_count}, Success: {self.success_count}, Failed: {self.failed_count}"
                )

                # Brief pause between batches
                await asyncio.sleep(2)

            logger.info(
                f"Campaign processor finished. Total: {self.processed_count}, Success: {self.success_count}, Failed: {self.failed_count}"
            )

        except Exception as e:
            error_msg = f"Campaign processor error: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.mark_campaign_failed(db, str(e))

        finally:
            # Cleanup
            await self.form_submitter.cleanup()
            db.close()

    def stop(self):
        """Stop the processor"""
        logger.info(f"Stopping campaign processor for {self.campaign_id}")
        self.is_running = False


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python campaign_processor.py <campaign_id> <user_id>")
        sys.exit(1)

    campaign_id = sys.argv[1]
    user_id = sys.argv[2]

    logger.info(f"Campaign processor started for campaign {campaign_id}")

    try:
        processor = CampaignProcessor(campaign_id, user_id)

        # Run async processor
        asyncio.run(processor.run())

    except Exception as e:
        logger.error(f"Fatal error: {e}\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
