# app/workers/automation/__init__.py
"""Unified Automation Controller that integrates with your existing services."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.workers.automation.browser_automation import BrowserAutomation
from app.services.form_service import FormService
from app.services.captcha_service import CaptchaService
from app.services.csv_parser_service import CSVParserService
from app.workers.utils.logger import WorkerLogger

logger = logging.getLogger(__name__)


class AutomationController:
    """
    Unified automation controller that integrates with your existing services.

    This acts as a bridge between the campaign processor and your service layer.
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        headless: bool = True,
    ):
        self.user_id = user_id
        self.campaign_id = campaign_id
        self.headless = headless
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        # Initialize your existing browser automation
        self.browser_automation = BrowserAutomation(headless=headless)

        # Initialize services with database session if needed
        self.form_service = FormService()
        self.captcha_service = None  # Will be initialized with DB session

        # Track statistics
        self.stats = {
            "total_processed": 0,
            "successful_forms": 0,
            "successful_emails": 0,
            "failed_attempts": 0,
            "start_time": None,
        }

    async def start(self) -> None:
        """Start the automation system."""
        try:
            self.stats["start_time"] = datetime.utcnow()
            await self.browser_automation.start()

            # Initialize CAPTCHA service with database if available
            if self.user_id:
                try:
                    from app.core.database import SessionLocal

                    db = SessionLocal()
                    self.captcha_service = CaptchaService(
                        db=db, user_id=self.user_id, campaign_id=self.campaign_id
                    )
                except Exception as e:
                    self.logger.warning(f"Could not initialize CAPTCHA service: {e}")

            self.logger.info("Automation controller started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start automation system: {e}")
            raise

    async def stop(self) -> None:
        """Stop the automation system."""
        try:
            if self.browser_automation:
                await self.browser_automation.stop()
            self.logger.info("Automation controller stopped successfully")
        except Exception as e:
            self.logger.warning(f"Error during shutdown: {e}")

    async def process_website(
        self, url: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a website using your existing browser automation.

        This method adapts the output format to match what the campaign processor expects.
        """
        self.logger.info(f"Processing website: {url}")
        self.stats["total_processed"] += 1

        try:
            # Use your existing browser automation process method
            result = await self.browser_automation.process(url, user_data)

            # Adapt the result format to match campaign processor expectations
            adapted_result = self._adapt_result_format(result, url)

            # Update statistics
            if adapted_result["success"]:
                method = adapted_result.get("method")
                if method == "form_submission":
                    self.stats["successful_forms"] += 1
                elif method == "email_extraction":
                    self.stats["successful_emails"] += 1
            else:
                self.stats["failed_attempts"] += 1

            self.logger.info(
                f"Website processing complete: {adapted_result['success']}"
            )
            return adapted_result

        except Exception as e:
            self.logger.error(f"Error processing {url}: {e}")
            self.stats["failed_attempts"] += 1

            return {
                "success": False,
                "method": None,
                "error": str(e),
                "details": {},
                "debug_info": {"error_type": "processing_error"},
            }

    def _adapt_result_format(
        self, original_result: Dict[str, Any], url: str
    ) -> Dict[str, Any]:
        """
        Adapt your browser automation result format to match campaign processor expectations.
        """
        # Your browser automation returns:
        # {
        #   "success": bool,
        #   "method": "form" | "email" | "none",
        #   "error": Optional[str],
        #   "details": {...}
        # }

        success = original_result.get("success", False)
        original_method = original_result.get("method", "none")
        error = original_result.get("error")
        details = original_result.get("details", {})

        # Map your method names to campaign processor expectations
        method_mapping = {
            "form": "form_submission",
            "email": "email_extraction",
            "none": None,
        }

        adapted_method = method_mapping.get(original_method, original_method)

        # Build adapted result
        adapted_result = {
            "success": success,
            "method": adapted_method,
            "error": error,
            "details": {},
            "debug_info": {},
        }

        # Adapt details based on method
        if success and adapted_method == "form_submission":
            adapted_result["details"] = {
                "frame": "main",
                "submitted_via": details.get("submitted_via", "form_submit"),
                "success_hint": details.get("success_hint"),
                "fields_filled": self._count_filled_fields(details),
                "form_score": 10,  # Default score
            }
        elif success and adapted_method == "email_extraction":
            emails = details.get("emails_found", []) or [details.get("primary_email")]
            emails = [e for e in emails if e]  # Remove None values
            adapted_result["details"] = {
                "emails": emails,
                "primary_email": emails[0] if emails else None,
            }

        # Add debug info
        adapted_result["debug_info"] = {
            "original_method": original_method,
            "url": url,
            "processing_time": datetime.utcnow().isoformat(),
        }

        return adapted_result

    def _count_filled_fields(self, details: Dict[str, Any]) -> int:
        """Estimate number of fields filled based on details."""
        # This is a rough estimate since your browser automation
        # doesn't explicitly track field counts
        if details.get("submitted_via"):
            return 3  # Assume at least name, email, message
        return 1

    async def process_batch(
        self, urls: List[str], user_data: Dict[str, Any], delay_seconds: int = 3
    ) -> List[Dict[str, Any]]:
        """Process multiple URLs in sequence with delay."""
        results = []

        for i, url in enumerate(urls):
            self.logger.info(f"Processing {i+1}/{len(urls)}: {url}")

            result = await self.process_website(url, user_data)
            result["batch_index"] = i + 1
            result["batch_total"] = len(urls)
            results.append(result)

            # Rate limiting
            if i < len(urls) - 1:
                await asyncio.sleep(delay_seconds)

        return results

    async def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        total = self.stats["total_processed"]
        successful = self.stats["successful_forms"] + self.stats["successful_emails"]

        return {
            "total_processed": total,
            "successful": successful,
            "failed": self.stats["failed_attempts"],
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            "form_submissions": self.stats["successful_forms"],
            "email_extractions": self.stats["successful_emails"],
            "start_time": (
                self.stats["start_time"].isoformat()
                if self.stats["start_time"]
                else None
            ),
        }

    @property
    def is_ready(self) -> bool:
        """Check if automation system is ready."""
        return self.browser_automation is not None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
