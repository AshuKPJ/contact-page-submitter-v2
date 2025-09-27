# app/workers/automation/browser_automation.py
"""Enhanced browser automation with iframe support and robust error handling."""

import asyncio
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Page, Frame, ElementHandle
from app.workers.utils.logger import WorkerLogger
from app.workers.automation.form_detector import FormDetector
from app.workers.automation.form_filler import FormFiller
from app.workers.automation.form_submitter import FormSubmitter
from app.workers.automation.success_detector import SuccessDetector
from app.workers.automation.email_extractor import EmailExtractor
from app.workers.automation.captcha_handler import CaptchaHandler
from app.workers.automation.page_navigator import PageNavigator


class BrowserAutomation:
    """Browser automation controller with comprehensive form processing."""

    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 0,
        user_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self.user_id = user_id
        self.campaign_id = campaign_id
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        self.playwright = None
        self.browser = None
        self.context = None

        # Initialize components
        self.navigator = PageNavigator(user_id, campaign_id)
        self.detector = FormDetector(user_id, campaign_id)
        self.filler = FormFiller(user_id, campaign_id)
        self.submitter = FormSubmitter(user_id, campaign_id)
        self.success_detector = SuccessDetector(user_id, campaign_id)
        self.email_extractor = EmailExtractor(user_id, campaign_id)
        self.captcha_handler = CaptchaHandler(user_id, campaign_id)

    async def start(self):
        """Start browser with optimized settings."""
        self.playwright = await async_playwright().start()

        # Launch with optimized settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
            java_script_enabled=True,
        )

        # Add stealth scripts to avoid detection
        await self.context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = { runtime: {} };
        """
        )

        self.logger.info("Browser started with enhanced settings")

    async def stop(self):
        """Stop browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.logger.info("Browser stopped")

    async def process(self, url: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method with comprehensive form handling.

        Process flow:
        1. Navigate to URL
        2. Check main page forms and iframes
        3. Try contact page if needed
        4. Fallback to email extraction
        """
        page = None
        result = {
            "success": False,
            "method": None,
            "error": None,
            "details": {},
            "debug_info": {},
        }

        try:
            # Create new page with timeout settings
            page = await self.context.new_page()
            page.set_default_timeout(30000)

            # Navigate to URL
            nav_result = await self.navigator.navigate_to_url(page, url)
            if not nav_result.success:
                result["error"] = f"Navigation failed: {nav_result.error}"
                result["debug_info"]["navigation_error"] = nav_result.error
                return result

            # Wait for content to load
            await self.navigator.wait_for_dynamic_content(page)

            # Process current page (including iframes)
            self.logger.info(f"Processing main page: {page.url}")
            result = await self._process_page_comprehensively(page, user_data, result)

            if result["success"]:
                self.logger.info(f"Successfully processed via {result['method']}")
                return result

            # Try to find and navigate to contact page
            self.logger.info("Main page processing failed, looking for contact page")
            contact_url = await self.navigator.find_contact_page(page)

            if contact_url and contact_url != page.url:
                self.logger.info(f"Found contact page: {contact_url}")
                nav_result = await self.navigator.navigate_to_url(page, contact_url)

                if nav_result.success:
                    await self.navigator.wait_for_dynamic_content(page)
                    result = await self._process_page_comprehensively(
                        page, user_data, result
                    )

                    if result["success"]:
                        self.logger.info(
                            f"Successfully processed contact page via {result['method']}"
                        )
                        return result

            # Final fallback: Email extraction
            self.logger.info("Form processing failed, attempting email extraction")
            emails = await self.email_extractor.extract_emails(page)

            if emails:
                result.update(
                    {
                        "success": True,
                        "method": "email_extraction",
                        "details": {
                            "emails": emails,
                            "primary_email": emails[0] if emails else None,
                        },
                    }
                )
                self.logger.info(f"Email extraction successful: {emails[0]}")
                return result

            # No contact method found
            result["error"] = "No contact method found (no forms, no emails)"
            self.logger.warning(result["error"])
            return result

        except Exception as e:
            self.logger.error(f"Process error for {url}: {str(e)}")
            result["error"] = str(e)
            return result

        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

    async def _process_page_comprehensively(
        self, page: Page, user_data: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process all frames on the page (main + iframes)."""

        # Get all frames
        all_frames = self._get_all_frames(page)
        self.logger.info(f"Found {len(all_frames)} frames to process")

        # Process each frame
        for i, frame in enumerate(all_frames):
            frame_url = frame.url if hasattr(frame, "url") else "main"
            self.logger.info(f"Processing frame {i+1}/{len(all_frames)}: {frame_url}")

            try:
                # Detect forms in this frame
                forms = await self.detector.detect_contact_forms(frame)

                if not forms:
                    self.logger.info(f"No contact forms in frame: {frame_url}")
                    continue

                self.logger.info(
                    f"Found {len(forms)} contact form(s) in frame: {frame_url}"
                )

                # Try each form
                for j, form_analysis in enumerate(forms):
                    self.logger.info(
                        f"Processing form {j+1}/{len(forms)} (score: {form_analysis.score})"
                    )

                    # Fill the form
                    fill_result = await self.filler.fill_form(
                        page, form_analysis, user_data
                    )

                    if not fill_result.success:
                        self.logger.warning(
                            f"Failed to fill form: {fill_result.errors}"
                        )
                        continue

                    self.logger.info(
                        f"Successfully filled {fill_result.fields_filled} fields"
                    )

                    # Handle CAPTCHA if present
                    if self.captcha_handler.has_credentials:
                        captcha_result = (
                            await self.captcha_handler.handle_captcha_if_present(page)
                        )
                        if captcha_result.captcha_type:
                            self.logger.info(
                                f"CAPTCHA detected: {captcha_result.captcha_type}"
                            )
                            if captcha_result.solved:
                                self.logger.info("CAPTCHA solved successfully")
                            else:
                                self.logger.warning("Failed to solve CAPTCHA")

                    # Submit the form
                    submit_result = await self.submitter.submit_form(
                        page, form_analysis.form
                    )

                    if not submit_result.success:
                        self.logger.warning(
                            f"Failed to submit form: {submit_result.error}"
                        )
                        continue

                    self.logger.info(f"Form submitted via {submit_result.method}")

                    # Wait for submission to complete
                    await asyncio.sleep(3)

                    # Check for success indicators
                    success_indicator = await self.success_detector.detect_success(page)

                    # Build successful result
                    result.update(
                        {
                            "success": True,
                            "method": "form_submission",
                            "details": {
                                "frame": frame_url,
                                "form_index": j + 1,
                                "form_score": form_analysis.score,
                                "fields_filled": fill_result.fields_filled,
                                "submission_method": submit_result.method,
                                "success_indicator": success_indicator,
                                "form_metadata": form_analysis.metadata,
                            },
                        }
                    )

                    return result

            except Exception as e:
                self.logger.warning(f"Error processing frame {frame_url}: {str(e)}")
                continue

        return result

    def _get_all_frames(self, page: Page) -> List[Any]:
        """Get all frames including main page and iframes."""
        frames = [page]  # Start with main page

        try:
            # Add all iframes
            page_frames = page.frames
            for frame in page_frames:
                if frame != page.main_frame:  # Skip main frame as we already have page
                    frames.append(frame)

            self.logger.info(
                f"Collected {len(frames)} frames (1 main + {len(frames)-1} iframes)"
            )

        except Exception as e:
            self.logger.warning(f"Error collecting frames: {e}")

        return frames

    async def debug_website(self, url: str) -> Dict[str, Any]:
        """Provide comprehensive debugging information for a website."""
        page = None
        debug_info = {
            "url": url,
            "navigation": {},
            "frames": [],
            "forms": {},
            "emails": {},
            "captcha": {},
            "contact_links": [],
        }

        try:
            page = await self.context.new_page()
            page.set_default_timeout(30000)

            # Navigation
            nav_result = await self.navigator.navigate_to_url(page, url)
            debug_info["navigation"] = {
                "success": nav_result.success,
                "final_url": nav_result.final_url,
                "error": nav_result.error,
            }

            if not nav_result.success:
                return debug_info

            await self.navigator.wait_for_dynamic_content(page)

            # Frame analysis
            all_frames = self._get_all_frames(page)
            for i, frame in enumerate(all_frames):
                frame_info = {
                    "index": i,
                    "url": frame.url if hasattr(frame, "url") else "main",
                    "forms": [],
                }

                try:
                    forms = await self.detector.detect_contact_forms(frame)
                    for form in forms:
                        frame_info["forms"].append(
                            {
                                "score": form.score,
                                "is_contact": form.is_contact_form,
                                "fields": form.field_counts,
                                "metadata": form.metadata,
                            }
                        )
                except Exception as e:
                    frame_info["error"] = str(e)

                debug_info["frames"].append(frame_info)

            # Email extraction
            emails = await self.email_extractor.extract_emails(page)
            debug_info["emails"] = {"found": emails, "count": len(emails)}

            # Contact page detection
            contact_url = await self.navigator.find_contact_page(page)
            debug_info["contact_links"] = [contact_url] if contact_url else []

            # CAPTCHA info
            if self.captcha_handler.has_credentials:
                captcha_result = await self.captcha_handler.handle_captcha_if_present(
                    page
                )
                debug_info["captcha"] = {
                    "detected": captcha_result.captcha_type is not None,
                    "type": captcha_result.captcha_type,
                    "solved": captcha_result.solved,
                }

        except Exception as e:
            debug_info["error"] = str(e)

        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

        return debug_info
