# app/workers/automation/form_submitter.py
"""Enhanced form submission with multiple strategies and iframe support."""

import asyncio
from typing import Optional, List, Union
from playwright.async_api import Page, Frame, ElementHandle
from app.workers.utils.logger import WorkerLogger


class SubmissionResult:
    """Result of form submission attempt."""
    
    def __init__(self, success: bool, method: str, error: Optional[str] = None,
                 response_url: Optional[str] = None):
        self.success = success
        self.method = method
        self.error = error
        self.response_url = response_url
        self.submission_time = None


class FormSubmitter:
    """Intelligent form submission with multiple strategies."""
    
    def __init__(
        self, user_id: Optional[str] = None, campaign_id: Optional[str] = None
    ):
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)
        
        # Submit button patterns
        self.submit_patterns = [
            # Type-based selectors
            'button[type="submit"]',
            'input[type="submit"]',
            
            # Text-based selectors for buttons
            'button:has-text("Submit")',
            'button:has-text("Send")',
            'button:has-text("Contact")',
            'button:has-text("Get in Touch")',
            'button:has-text("Send Message")',
            'button:has-text("Submit Form")',
            'button:has-text("Send Inquiry")',
            'button:has-text("Contact Us")',
            'button:has-text("Request")',
            'button:has-text("Apply")',
            
            # Attribute-based selectors
            'button[name*="submit" i]',
            'button[id*="submit" i]',
            'button[class*="submit" i]',
            'input[value*="Send" i]',
            'input[value*="Submit" i]',
            
            # Generic button (as last resort)
            'button:not([type="button"]):not([type="reset"])',
            '*[role="button"][class*="submit" i]',
        ]

    async def submit_form(self, page: Page, form: ElementHandle) -> SubmissionResult:
        """
        Submit form using multiple strategies.
        
        Tries various submission methods in order of preference.
        """
        self.logger.info("Starting form submission")
        
        # Store initial URL for comparison
        initial_url = page.url
        
        # Strategy 1: Find and click submit button
        submit_result = await self._submit_via_button(page, form)
        if submit_result.success:
            return submit_result
        
        # Strategy 2: JavaScript form submission
        js_result = await self._submit_via_javascript(page, form)
        if js_result.success:
            return js_result
        
        # Strategy 3: Enter key submission
        enter_result = await self._submit_via_enter_key(page, form)
        if enter_result.success:
            return enter_result
        
        # Strategy 4: Find submit button outside form
        external_result = await self._submit_via_external_button(page, form)
        if external_result.success:
            return external_result
        
        # All strategies failed
        self.logger.warning("All submission strategies failed")
        return SubmissionResult(
            success=False,
            method="none",
            error="No submission method worked"
        )

    async def _submit_via_button(self, page: Page, form: ElementHandle) -> SubmissionResult:
        """Submit by clicking submit button within form."""
        self.logger.info("Attempting submission via button click")
        
        for selector in self.submit_patterns:
            try:
                # First try within the form
                button = await form.query_selector(selector)
                
                if button and await button.is_visible():
                    # Check if button is enabled
                    is_disabled = await button.is_disabled()
                    if is_disabled:
                        self.logger.info(f"Button {selector} is disabled")
                        continue
                    
                    # Get button text for logging
                    button_text = await self._get_button_text(button)
                    self.logger.info(f"Clicking submit button: '{button_text}'")
                    
                    # Click and wait for navigation
                    await self._click_and_wait(page, button)
                    
                    # Check if submission occurred
                    if await self._verify_submission(page):
                        self.logger.info(f"✓ Form submitted via button: {selector}")
                        return SubmissionResult(
                            success=True,
                            method=f"button_click:{selector}",
                            response_url=page.url
                        )
                        
            except Exception as e:
                self.logger.warning(f"Error with button selector {selector}: {e}")
                continue
        
        return SubmissionResult(success=False, method="button_click", 
                               error="No submit button found")

    async def _submit_via_javascript(self, page: Page, form: ElementHandle) -> SubmissionResult:
        """Submit form using JavaScript."""
        self.logger.info("Attempting submission via JavaScript")
        
        try:
            # Try form.submit() method
            await form.evaluate("form => form.submit()")
            await self._wait_for_submission(page)
            
            if await self._verify_submission(page):
                self.logger.info("✓ Form submitted via JavaScript")
                return SubmissionResult(
                    success=True,
                    method="javascript_submit",
                    response_url=page.url
                )
                
            # Try form.requestSubmit() (newer API)
            await form.evaluate("form => form.requestSubmit && form.requestSubmit()")
            await self._wait_for_submission(page)
            
            if await self._verify_submission(page):
                self.logger.info("✓ Form submitted via requestSubmit")
                return SubmissionResult(
                    success=True,
                    method="javascript_requestSubmit",
                    response_url=page.url
                )
                
        except Exception as e:
            self.logger.warning(f"JavaScript submission error: {e}")
        
        return SubmissionResult(success=False, method="javascript", 
                               error="JavaScript submission failed")

    async def _submit_via_enter_key(self, page: Page, form: ElementHandle) -> SubmissionResult:
        """Submit form by pressing Enter key in last input."""
        self.logger.info("Attempting submission via Enter key")
        
        try:
            # Get all fillable inputs
            inputs = await form.query_selector_all(
                'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea'
            )
            
            if inputs:
                # Focus on last visible input
                for input_elem in reversed(inputs):
                    if await input_elem.is_visible():
                        await input_elem.focus()
                        await asyncio.sleep(0.3)
                        
                        # Press Enter
                        await input_elem.press("Enter")
                        await self._wait_for_submission(page)
                        
                        if await self._verify_submission(page):
                            self.logger.info("✓ Form submitted via Enter key")
                            return SubmissionResult(
                                success=True,
                                method="enter_key",
                                response_url=page.url
                            )
                        break
                        
        except Exception as e:
            self.logger.warning(f"Enter key submission error: {e}")
        
        return SubmissionResult(success=False, method="enter_key", 
                               error="Enter key submission failed")

    async def _submit_via_external_button(self, page: Page, form: ElementHandle) -> SubmissionResult:
        """Find and click submit button outside the form element."""
        self.logger.info("Attempting submission via external button")
        
        try:
            # Get form ID to find associated buttons
            form_id = await form.get_attribute("id")
            
            if form_id:
                # Look for buttons with form attribute
                external_button = await page.query_selector(f'button[form="{form_id}"]')
                
                if external_button and await external_button.is_visible():
                    await self._click_and_wait(page, external_button)
                    
                    if await self._verify_submission(page):
                        self.logger.info("✓ Form submitted via external button")
                        return SubmissionResult(
                            success=True,
                            method="external_button",
                            response_url=page.url
                        )
            
            # Look for submit buttons near the form
            for selector in self.submit_patterns[:5]:  # Try first 5 patterns
                buttons = await page.query_selector_all(selector)
                
                for button in buttons:
                    if await button.is_visible():
                        # Check if button is near the form
                        is_near = await page.evaluate("""
                            (form, button) => {
                                const formRect = form.getBoundingClientRect();
                                const buttonRect = button.getBoundingClientRect();
                                const distance = Math.abs(formRect.bottom - buttonRect.top);
                                return distance < 200;  // Within 200px
                            }
                        """, form, button)
                        
                        if is_near:
                            await self._click_and_wait(page, button)
                            
                            if await self._verify_submission(page):
                                self.logger.info("✓ Form submitted via nearby button")
                                return SubmissionResult(
                                    success=True,
                                    method="nearby_button",
                                    response_url=page.url
                                )
                                
        except Exception as e:
            self.logger.warning(f"External button submission error: {e}")
        
        return SubmissionResult(success=False, method="external_button", 
                               error="No external button found")

    async def _click_and_wait(self, page: Page, button: ElementHandle):
        """Click button and wait for response."""
        try:
            # Set up promises for navigation/response
            navigation_promise = page.wait_for_navigation(
                timeout=10000,
                wait_until="domcontentloaded"
            )
            
            # Click the button
            await button.click()
            
            # Wait for navigation or timeout
            try:
                await navigation_promise
            except:
                # Navigation might not occur for AJAX forms
                await asyncio.sleep(2)
                
        except Exception as e:
            self.logger.warning(f"Click and wait error: {e}")

    async def _wait_for_submission(self, page: Page):
        """Wait for form submission to complete."""
        try:
            # Wait for potential navigation
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            # Timeout is okay, might be AJAX
            pass
        
        # Additional wait for AJAX responses
        await asyncio.sleep(2)

    async def _verify_submission(self, page: Page) -> bool:
        """Verify if form was actually submitted."""
        try:
            # Check for URL change
            current_url = page.url
            if "thank" in current_url.lower() or "success" in current_url.lower():
                return True
            
            # Check for success messages on page
            success_indicators = [
                "thank you",
                "thanks",
                "message sent",
                "successfully submitted",
                "we'll get back",
                "received your",
                "submission successful"
            ]
            
            page_text = await page.inner_text("body")
            page_text_lower = page_text.lower()
            
            for indicator in success_indicators:
                if indicator in page_text_lower:
                    return True
            
            # Check for form removal/hiding
            forms_count = len(await page.query_selector_all("form:visible"))
            if forms_count == 0:
                # Form might have been hidden after submission
                return True
            
            # Check for success elements
            success_elements = await page.query_selector_all(
                '.success, .alert-success, [class*="success"], [class*="thank"]'
            )
            
            for element in success_elements:
                if await element.is_visible():
                    return True
                    
        except Exception as e:
            self.logger.warning(f"Error verifying submission: {e}")
        
        return False

    async def _get_button_text(self, button: ElementHandle) -> str:
        """Get button text or value."""
        try:
            # Try inner text first
            text = await button.inner_text()
            if text:
                return text.strip()
            
            # Try value attribute
            value = await button.get_attribute("value")
            if value:
                return value.strip()
            
            # Try aria-label
            aria_label = await button.get_attribute("aria-label")
            if aria_label:
                return aria_label.strip()
                
            return "Unknown"
            
        except:
            return "Unknown"

    async def submit_with_validation(
        self, page: Page, form: ElementHandle, max_retries: int = 2
    ) -> SubmissionResult:
        """
        Submit form with validation and retry logic.
        
        Handles validation errors and retries submission.
        """
        for attempt in range(max_retries):
            self.logger.info(f"Submission attempt {attempt + 1}/{max_retries}")
            
            # Check for validation errors before submission
            validation_errors = await self._check_validation_errors(form)
            if validation_errors:
                self.logger.warning(f"Validation errors found: {validation_errors}")
                # Could attempt to fix validation errors here
            
            # Attempt submission
            result = await self.submit_form(page, form)
            
            if result.success:
                return result
            
            # Check if we should retry
            if attempt < max_retries - 1:
                self.logger.info("Retrying submission after delay...")
                await asyncio.sleep(2)
        
        return SubmissionResult(
            success=False,
            method="validation_failed",
            error=f"Failed after {max_retries} attempts"
        )

    async def _check_validation_errors(self, form: ElementHandle) -> List[str]:
        """Check for HTML5 validation errors."""
        errors = []
        
        try:
            # Check for :invalid pseudo-class
            invalid_fields = await form.query_selector_all(":invalid")
            
            for field in invalid_fields:
                field_name = await field.get_attribute("name") or "unknown"
                validation_msg = await field.evaluate("el => el.validationMessage")
                if validation_msg:
                    errors.append(f"{field_name}: {validation_msg}")
                    
        except Exception as e:
            self.logger.warning(f"Error checking validation: {e}")
        
        return errors