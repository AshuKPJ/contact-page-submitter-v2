# app/workers/automation/success_detector.py
"""Enhanced success detection with multiple verification strategies."""

from typing import Optional, Dict, Any, List
from playwright.async_api import Page
from app.workers.utils.logger import WorkerLogger


class SuccessDetector:
    """Comprehensive success detection for form submissions."""

    def __init__(self, user_id=None, campaign_id=None):
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        # Success text patterns
        self.success_patterns = [
            # Common success messages
            "thank you",
            "thanks",
            "success",
            "successfully",
            "submitted",
            "received",
            "sent",
            "complete",
            # Specific form success messages
            "message sent",
            "message has been sent",
            "form submitted",
            "submission successful",
            "we'll get back",
            "we will get back",
            "we'll be in touch",
            "we will be in touch",
            "we'll contact you",
            "we will contact you",
            # Receipt confirmations
            "your message has been received",
            "we have received your",
            "your inquiry has been",
            "your request has been",
            "your submission has been",
            "we got your message",
            "thanks for your submission",
            # Follow-up promises
            "we will respond",
            "we'll respond",
            "expect a response",
            "expect a reply",
            "someone will contact",
            "our team will reach out",
            "we'll reach out",
            "hear from us soon",
            # Appreciation messages
            "appreciate your interest",
            "thanks for reaching out",
            "thanks for contacting",
            "thank you for your interest",
            "thank you for contacting",
            "appreciate you reaching out",
            # Confirmation messages
            "confirmation email",
            "check your email",
            "confirmation has been sent",
            "you should receive",
            "email confirmation",
            "you will receive an email",
        ]

        # Success element selectors
        self.success_selectors = [
            # Class-based selectors
            ".success",
            ".alert-success",
            ".message-success",
            ".form-success",
            ".submission-success",
            '[class*="success"]',
            '[class*="thank"]',
            '[class*="confirmation"]',
            '[class*="complete"]',
            ".notification-success",
            ".toast-success",
            # ID-based selectors
            "#success",
            "#thank-you",
            "#thankyou",
            "#confirmation",
            "#form-success",
            '[id*="success"]',
            '[id*="thank"]',
            "#success-message",
            "#confirmation-message",
            # Role-based selectors
            '[role="alert"]',
            '[role="status"]',
            '[aria-live="polite"]',
            '[aria-live="assertive"]',
            # Data attribute selectors
            '[data-success="true"]',
            '[data-submitted="true"]',
            '[data-status="success"]',
            "[data-form-success]",
            # Common framework patterns
            ".alert.alert-success",  # Bootstrap
            ".uk-alert-success",  # UIKit
            ".message.success",  # Semantic UI
            ".notice--success",  # BEM notation
            ".Toastify__toast--success",  # React Toastify
            ".ant-message-success",  # Ant Design
            ".el-message--success",  # Element UI
        ]

        # URL patterns that indicate success
        self.success_url_patterns = [
            "thank",
            "thanks",
            "success",
            "confirmation",
            "submitted",
            "complete",
            "done",
            "received",
            "confirmed",
            "sent",
        ]

        # Modal/popup selectors
        self.modal_selectors = [
            ".modal",
            ".popup",
            ".dialog",
            "[role='dialog']",
            ".overlay",
            ".lightbox",
            ".toast",
            ".notification",
            "[data-modal]",
            "[aria-modal='true']",
        ]

    async def detect_success(self, page: Page) -> Optional[str]:
        """
        Detect if form submission was successful.

        Returns success indicator string if found, None otherwise.
        """
        try:
            # Strategy 1: Check URL for success indicators
            url_indicator = self._check_url_success(page.url)
            if url_indicator:
                self.logger.info(f"✓ Success detected in URL: {url_indicator}")
                return f"url:{url_indicator}"

            # Strategy 2: Check page content for success text
            text_indicator = await self._check_text_success(page)
            if text_indicator:
                self.logger.info(f"✓ Success detected in text: {text_indicator}")
                return f"text:{text_indicator}"

            # Strategy 3: Check for success elements
            element_indicator = await self._check_element_success(page)
            if element_indicator:
                self.logger.info(f"✓ Success detected in element: {element_indicator}")
                return f"element:{element_indicator}"

            # Strategy 4: Check for form state changes
            form_indicator = await self._check_form_state(page)
            if form_indicator:
                self.logger.info(f"✓ Success detected via form state: {form_indicator}")
                return f"form_state:{form_indicator}"

            # Strategy 5: Check for modal/popup success
            modal_indicator = await self._check_modal_success(page)
            if modal_indicator:
                self.logger.info(f"✓ Success detected in modal: {modal_indicator}")
                return f"modal:{modal_indicator}"

            # Strategy 6: Check for AJAX success indicators
            ajax_indicator = await self._check_ajax_success(page)
            if ajax_indicator:
                self.logger.info(f"✓ Success detected via AJAX: {ajax_indicator}")
                return f"ajax:{ajax_indicator}"

            self.logger.info("No success indicators detected")
            return None

        except Exception as e:
            self.logger.error(f"Success detection error: {e}")
            return None

    def _check_url_success(self, url: str) -> Optional[str]:
        """Check if URL contains success indicators."""
        url_lower = url.lower()

        for pattern in self.success_url_patterns:
            if pattern in url_lower:
                return pattern

        # Check for success in query parameters
        if "?" in url:
            query_part = url.split("?")[1]
            query_lower = query_part.lower()
            for pattern in ["success", "submitted", "sent", "thank"]:
                if pattern in query_lower:
                    return f"query_{pattern}"

        # Check for success in path
        if any(f"/{pattern}" in url_lower for pattern in self.success_url_patterns):
            return "path_success"

        return None

    async def _check_text_success(self, page: Page) -> Optional[str]:
        """Check page text for success messages."""
        try:
            # Get page text
            page_text = await page.inner_text("body")
            page_text_lower = page_text.lower()

            # Check each success pattern
            for pattern in self.success_patterns:
                if pattern in page_text_lower:
                    # Try to get more context
                    context = await self._get_text_context(page, pattern)
                    if context:
                        # Verify it's not negative context
                        if not self._is_negative_context(context):
                            return f"{pattern}"
                    else:
                        return pattern

        except Exception as e:
            self.logger.warning(f"Error checking text success: {e}")

        return None

    async def _check_element_success(self, page: Page) -> Optional[str]:
        """Check for success elements on the page."""
        for selector in self.success_selectors:
            try:
                elements = await page.query_selector_all(selector)

                for element in elements:
                    if await element.is_visible():
                        # Get element text
                        text = await element.inner_text()
                        if text:
                            text_lower = text.lower()
                            # Verify it contains success-related text
                            for pattern in [
                                "thank",
                                "success",
                                "received",
                                "sent",
                                "complete",
                            ]:
                                if pattern in text_lower:
                                    return f"{selector}:{pattern}"
                        else:
                            # Element exists and is visible, might be success icon
                            return f"{selector}:visible"

            except Exception as e:
                continue

        return None

    async def _check_form_state(self, page: Page) -> Optional[str]:
        """Check if form has been hidden or replaced."""
        try:
            # Check if forms are now hidden
            forms = await page.query_selector_all("form")
            visible_forms = []

            for form in forms:
                if await form.is_visible():
                    visible_forms.append(form)

            # If no visible forms, might indicate success
            if len(forms) > 0 and len(visible_forms) == 0:
                return "forms_hidden"

            # Check if form inputs are disabled
            inputs = await page.query_selector_all("input, textarea, select")
            disabled_count = 0

            for input_elem in inputs:
                if await input_elem.is_disabled():
                    disabled_count += 1

            if len(inputs) > 0 and disabled_count == len(inputs):
                return "all_inputs_disabled"

            # Check for form replacement
            success_containers = await page.query_selector_all(
                '[class*="form-container"], [id*="form-container"], .form-wrapper'
            )

            for container in success_containers:
                container_text = await container.inner_text()
                if container_text:
                    container_lower = container_text.lower()
                    if any(
                        pattern in container_lower
                        for pattern in ["thank", "success", "sent"]
                    ):
                        # Check if it has no form inside
                        inner_forms = await container.query_selector_all("form")
                        if len(inner_forms) == 0:
                            return "form_replaced_with_message"

        except Exception as e:
            self.logger.warning(f"Error checking form state: {e}")

        return None

    async def _check_modal_success(self, page: Page) -> Optional[str]:
        """Check for success messages in modals or popups."""
        try:
            for selector in self.modal_selectors:
                modals = await page.query_selector_all(selector)

                for modal in modals:
                    if await modal.is_visible():
                        modal_text = await modal.inner_text()
                        if modal_text:
                            modal_lower = modal_text.lower()

                            # Check for success patterns in modal
                            for pattern in [
                                "thank",
                                "success",
                                "received",
                                "sent",
                                "complete",
                            ]:
                                if pattern in modal_lower:
                                    return f"modal_{pattern}"

        except Exception as e:
            self.logger.warning(f"Error checking modal success: {e}")

        return None

    async def _check_ajax_success(self, page: Page) -> Optional[str]:
        """Check for AJAX-style success indicators."""
        try:
            # Check for dynamically added success elements
            dynamic_selectors = [
                '[style*="display: block"]',
                '[style*="visibility: visible"]',
                '[style*="opacity: 1"]',
            ]

            for selector in dynamic_selectors:
                elements = await page.query_selector_all(selector)

                for element in elements:
                    element_text = await element.inner_text()
                    if element_text:
                        text_lower = element_text.lower()

                        # Check for success indicators
                        for pattern in ["thank", "success", "sent", "received"]:
                            if pattern in text_lower:
                                # Verify it wasn't visible before
                                classes = await element.get_attribute("class") or ""
                                if any(
                                    cls in classes
                                    for cls in [
                                        "success",
                                        "alert",
                                        "message",
                                        "notification",
                                    ]
                                ):
                                    return f"ajax_{pattern}"

            # Check for JavaScript-based redirects
            current_url = page.url
            if "ajax" in current_url.lower() or "xhr" in current_url.lower():
                if any(
                    pattern in current_url.lower()
                    for pattern in self.success_url_patterns
                ):
                    return "ajax_redirect"

        except Exception as e:
            self.logger.warning(f"Error checking AJAX success: {e}")

        return None

    async def _get_text_context(self, page: Page, pattern: str) -> Optional[str]:
        """Get context around a text pattern."""
        try:
            # Try to find the element containing the pattern
            elements = await page.query_selector_all(f'*:has-text("{pattern}")')

            for element in elements[:5]:  # Check first 5 matches
                try:
                    text = await element.inner_text()
                    if text and len(text) < 500:  # Reasonable context length
                        return text
                except:
                    continue

        except:
            pass

        return None

    def _is_negative_context(self, context: str) -> bool:
        """Check if context indicates failure rather than success."""
        negative_patterns = [
            "did not",
            "didn't",
            "could not",
            "couldn't",
            "failed",
            "error",
            "problem",
            "issue",
            "try again",
            "please check",
            "invalid",
            "not sent",
            "not received",
            "unsuccessful",
        ]

        context_lower = context.lower()
        return any(pattern in context_lower for pattern in negative_patterns)

    async def wait_and_detect(self, page: Page, timeout: int = 10) -> Optional[str]:
        """
        Wait for success indicators with timeout.

        Useful for slow-loading success messages.
        """
        import asyncio

        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            result = await self.detect_success(page)
            if result:
                return result

            await asyncio.sleep(1)

        return None
