# app/workers/automation/form_filler.py
"""Enhanced form filler with intelligent field mapping, popup handling, and learning."""

import asyncio
from typing import Dict, Any, List, Optional
from playwright.async_api import ElementHandle, Page, Frame
from app.workers.utils.logger import WorkerLogger
from app.workers.automation.form_detector import FormAnalysisResult
from app.workers.automation.adaptive_field_mapper import AdaptiveFieldMapper


class FormFillResult:
    """Result of form filling operation with enhanced tracking."""

    def __init__(self, success: bool, fields_filled: int, errors: List[str] = None):
        self.success = success
        self.fields_filled = fields_filled
        self.errors = errors or []
        self.field_mappings = {}  # Track what was filled
        self.confidence_scores = {}  # Track confidence for each field
        self.popup_interactions = []  # Track popup interactions during filling
        self.retry_attempts = 0  # Track retry attempts
        self.total_fields_found = 0  # Total fields available
        self.skipped_fields = []  # Fields that were skipped


class FormFiller:
    """Intelligent form filler with popup handling and adaptive learning."""

    def __init__(
        self, user_id: Optional[str] = None, campaign_id: Optional[str] = None
    ):
        self.user_id = user_id
        self.campaign_id = campaign_id
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        # Track filling attempts for retry logic
        self.attempted_values = {}
        self.global_fill_stats = {
            "total_forms_attempted": 0,
            "successful_fills": 0,
            "total_fields_filled": 0,
        }

    async def fill_form(
        self, page: Page, form_analysis: FormAnalysisResult, user_data: Dict[str, Any]
    ) -> FormFillResult:
        """
        Fill form using intelligent mapping and user data with popup handling.

        Args:
            page: The page containing the form
            form_analysis: Analysis result from form detector
            user_data: User's profile data from database

        Returns:
            FormFillResult with comprehensive details of what was filled
        """
        self.global_fill_stats["total_forms_attempted"] += 1

        try:
            # Initialize adaptive field mapper with user data
            mapper = AdaptiveFieldMapper(self.user_id, self.campaign_id)

            # Get form context
            frame_context = form_analysis.metadata.get("frame_context", "main")
            self.logger.info(
                f"Starting intelligent form filling in {frame_context} frame"
            )

            # Verify form is still present and accessible
            if not await self._is_form_accessible(form_analysis.form):
                return FormFillResult(
                    success=False,
                    fields_filled=0,
                    errors=["Form no longer accessible on page"],
                )

            # Pre-fill preparation: handle any interfering popups
            await self._prepare_form_for_filling(page, form_analysis.form)

            # Get all fillable fields with enhanced analysis
            fields = await self._analyze_form_fields_comprehensive(form_analysis.form)
            self.logger.info(f"Found {len(fields)} fillable fields")

            if not fields:
                return FormFillResult(
                    success=False,
                    fields_filled=0,
                    errors=["No fillable fields found in form"],
                )

            # Initialize result tracking
            result = FormFillResult(success=False, fields_filled=0)
            result.total_fields_found = len(fields)

            # Fill fields with comprehensive error handling
            filled_count = 0
            errors = []
            field_mappings = {}
            confidence_scores = {}
            skipped_fields = []

            for field_index, field in enumerate(fields):
                try:
                    field_name = self._get_field_identifier(field)
                    field_type = field.get("type", "text")
                    field_element = field.get("element")

                    if not field_element:
                        skipped_fields.append(f"{field_name}: No element handle")
                        continue

                    # Skip if already filled (unless it's critical fields)
                    current_value = await self._get_field_value(field_element)
                    if current_value and not self._is_critical_field(
                        field_name, field_type
                    ):
                        self.logger.info(
                            f"Field '{field_name}' already has value: {current_value[:50]}"
                        )
                        skipped_fields.append(f"{field_name}: Already filled")
                        continue

                    # Get value from adaptive mapper
                    field_attributes = {
                        "type": field_type,
                        "options": field.get("options", []),
                        "placeholder": field.get("placeholder", ""),
                        "required": field.get("required", False),
                        "label": field.get("label", ""),
                        "class": field.get("class", ""),
                        "name": field.get("name", ""),
                        "id": field.get("id", ""),
                    }

                    # Get value with learning from previous attempts
                    previous_attempts = self.attempted_values.get(field_name, [])
                    value, confidence = mapper.suggest_value_with_context(
                        field_name, field_type, field_attributes, user_data
                    )

                    # Apply retry logic for failed previous attempts
                    if previous_attempts and value in previous_attempts:
                        value = self._get_alternative_value(
                            field_name, field_type, field_attributes, previous_attempts
                        )
                        confidence = max(
                            0.2, confidence * 0.5
                        )  # Reduce confidence for retries

                    # Handle required fields specially
                    if not value and field.get("required"):
                        value = self._get_fallback_value(
                            field_name, field_type, field_attributes
                        )
                        confidence = 0.3

                    if value is not None:
                        # Attempt to fill with retry and popup handling
                        fill_success, fill_error = await self._fill_field_with_retry(
                            page,
                            field_element,
                            value,
                            field_name,
                            field_type,
                            max_retries=2,
                        )

                        if fill_success:
                            filled_count += 1
                            field_mappings[field_name] = value
                            confidence_scores[field_name] = confidence
                            self.logger.info(
                                f"✓ Filled '{field_name}' with confidence {confidence:.2f}"
                            )

                            # Track successful value for learning
                            if field_name not in self.attempted_values:
                                self.attempted_values[field_name] = []
                        else:
                            # Track failed attempt for learning
                            if field_name not in self.attempted_values:
                                self.attempted_values[field_name] = []
                            self.attempted_values[field_name].append(value)

                            error_msg = f"Failed to fill {field_name}: {fill_error}"
                            errors.append(error_msg)
                            self.logger.warning(error_msg)
                    else:
                        skipped_fields.append(f"{field_name}: No suitable value")

                    # Small delay between fields to appear human-like
                    await asyncio.sleep(0.1)

                except Exception as e:
                    error_msg = (
                        f"Error filling field {field.get('name', 'unknown')}: {str(e)}"
                    )
                    errors.append(error_msg)
                    self.logger.warning(error_msg)

            # Verify minimum required fields are filled
            has_minimum = await self._verify_minimum_fields(
                form_analysis.form, field_mappings
            )

            # Update global statistics
            if filled_count > 0:
                self.global_fill_stats["successful_fills"] += 1
                self.global_fill_stats["total_fields_filled"] += filled_count

            # Create comprehensive result
            result.success = filled_count > 0 and has_minimum
            result.fields_filled = filled_count
            result.errors = errors
            result.field_mappings = field_mappings
            result.confidence_scores = confidence_scores
            result.skipped_fields = skipped_fields

            # Learn from the attempt if successful
            if result.success and field_mappings:
                domain = self._extract_domain_from_page(page)
                mapper.learn_from_success(field_mappings, domain)

            # Calculate overall confidence
            if confidence_scores:
                avg_confidence = sum(confidence_scores.values()) / len(
                    confidence_scores
                )
                result.overall_confidence = avg_confidence
            else:
                result.overall_confidence = 0.0

            self.logger.info(
                f"Form filling complete: {filled_count}/{len(fields)} fields filled "
                f"(skipped: {len(skipped_fields)}, errors: {len(errors)}), "
                f"average confidence: {result.overall_confidence:.2f}"
            )

            return result

        except Exception as e:
            self.logger.error(f"Form filling failed with exception: {str(e)}")
            return FormFillResult(success=False, fields_filled=0, errors=[str(e)])

    async def _prepare_form_for_filling(self, page: Page, form: ElementHandle):
        """Prepare form for filling by handling any interfering elements."""
        try:
            # Check if form is obscured by popups or overlays
            is_obscured = await form.evaluate(
                """
                (form) => {
                    const rect = form.getBoundingClientRect();
                    const centerX = rect.x + rect.width / 2;
                    const centerY = rect.y + rect.height / 2;
                    const elementAtPoint = document.elementFromPoint(centerX, centerY);
                    
                    // Check if the form or its descendants are at the center point
                    return !form.contains(elementAtPoint) && elementAtPoint !== form;
                }
            """
            )

            if is_obscured:
                self.logger.info(
                    "Form appears to be obscured, attempting to clear overlays"
                )
                # Try to remove specific overlays that might be blocking the form
                await self._remove_form_overlays(page, form)

            # Scroll form into view if needed
            await form.scroll_into_view_if_needed()

            # Small delay for scroll animation
            await asyncio.sleep(0.5)

        except Exception as e:
            self.logger.warning(f"Error preparing form for filling: {e}")

    async def _remove_form_overlays(self, page: Page, form: ElementHandle):
        """Remove overlays that might be blocking the specific form."""
        try:
            await page.evaluate(
                """
                (form) => {
                    const formRect = form.getBoundingClientRect();
                    const overlays = [];
                    
                    // Find all elements with high z-index
                    document.querySelectorAll('*').forEach(el => {
                        const style = window.getComputedStyle(el);
                        const zIndex = parseInt(style.zIndex);
                        
                        if (zIndex > 1000) {
                            const rect = el.getBoundingClientRect();
                            
                            // Check if overlay intersects with form
                            const intersects = !(
                                rect.right < formRect.left || 
                                rect.left > formRect.right || 
                                rect.bottom < formRect.top || 
                                rect.top > formRect.bottom
                            );
                            
                            if (intersects) {
                                // Check if it's a blocking overlay (not content)
                                const text = el.textContent || '';
                                if (text.length < 100) { // Likely a blocking element
                                    overlays.push(el);
                                }
                            }
                        }
                    });
                    
                    // Remove blocking overlays
                    overlays.forEach(el => {
                        el.style.display = 'none';
                        el.remove();
                    });
                    
                    return overlays.length;
                }
            """,
                form,
            )

        except Exception as e:
            self.logger.debug(f"Error removing form overlays: {e}")

    def _get_field_identifier(self, field: Dict[str, Any]) -> str:
        """Get a meaningful identifier for a field."""
        return (
            field.get("name")
            or field.get("id")
            or f"field_{field.get('type', 'unknown')}"
        )

    def _is_critical_field(self, field_name: str, field_type: str) -> bool:
        """Check if field is critical and should be refilled even if it has a value."""
        critical_patterns = ["email", "message", "comment", "inquiry"]
        field_name_lower = field_name.lower()

        return field_type == "email" or any(
            pattern in field_name_lower for pattern in critical_patterns
        )

    async def _is_form_accessible(self, form: ElementHandle) -> bool:
        """Check if form is still accessible and not removed from DOM."""
        try:
            # Check if form is still attached to DOM
            is_attached = await form.evaluate("el => document.body.contains(el)")
            if not is_attached:
                self.logger.warning("Form is no longer attached to DOM")
                return False

            # Check if form is visible and not hidden
            is_visible = await form.is_visible()
            if not is_visible:
                self.logger.warning("Form is not visible")
                return False

            # Check if form is not disabled
            is_disabled = await form.is_disabled()
            if is_disabled:
                self.logger.warning("Form is disabled")
                return False

            return True

        except Exception as e:
            self.logger.debug(f"Form accessibility check failed: {e}")
            return False

    async def _analyze_form_fields_comprehensive(
        self, form: ElementHandle
    ) -> List[Dict[str, Any]]:
        """Analyze and extract all fillable fields from form with comprehensive data."""
        fields = []

        try:
            # Get input fields
            inputs = await form.query_selector_all("input")
            for input_elem in inputs:
                try:
                    input_type = await input_elem.get_attribute("type") or "text"

                    # Skip non-fillable types
                    if input_type in [
                        "submit",
                        "button",
                        "hidden",
                        "image",
                        "reset",
                        "file",
                    ]:
                        continue

                    # Skip if not visible
                    if not await input_elem.is_visible():
                        continue

                    # Skip if disabled
                    if await input_elem.is_disabled():
                        continue

                    field_info = await self._extract_field_info(
                        form, input_elem, input_type
                    )
                    if field_info:
                        fields.append(field_info)

                except Exception as e:
                    self.logger.warning(f"Error analyzing input field: {e}")

            # Get textarea fields
            textareas = await form.query_selector_all("textarea")
            for textarea in textareas:
                try:
                    if not await textarea.is_visible() or await textarea.is_disabled():
                        continue

                    field_info = await self._extract_field_info(
                        form, textarea, "textarea"
                    )
                    if field_info:
                        fields.append(field_info)

                except Exception as e:
                    self.logger.warning(f"Error analyzing textarea: {e}")

            # Get select fields
            selects = await form.query_selector_all("select")
            for select in selects:
                try:
                    if not await select.is_visible() or await select.is_disabled():
                        continue

                    # Get options
                    options = []
                    option_elements = await select.query_selector_all("option")
                    for option in option_elements:
                        option_value = await option.get_attribute("value")
                        option_text = await option.inner_text()

                        # Prefer value, fall back to text
                        final_value = option_value if option_value else option_text
                        if final_value and final_value.strip():
                            options.append(final_value.strip())

                    field_info = await self._extract_field_info(form, select, "select")
                    if field_info:
                        field_info["options"] = options
                        fields.append(field_info)

                except Exception as e:
                    self.logger.warning(f"Error analyzing select field: {e}")

            # Get radio button groups
            radios = await form.query_selector_all('input[type="radio"]')
            radio_groups = {}

            for radio in radios:
                try:
                    if not await radio.is_visible():
                        continue

                    name = await radio.get_attribute("name")
                    if name and name not in radio_groups:
                        # Get all options for this radio group
                        group_radios = await form.query_selector_all(
                            f'input[name="{name}"]'
                        )
                        options = []

                        for group_radio in group_radios:
                            value = await group_radio.get_attribute("value")
                            if value:
                                options.append(value)

                        if options:
                            field_info = await self._extract_field_info(
                                form, radio, "radio"
                            )
                            if field_info:
                                field_info["options"] = options
                                radio_groups[name] = field_info
                                fields.append(field_info)

                except Exception as e:
                    self.logger.warning(f"Error analyzing radio field: {e}")

        except Exception as e:
            self.logger.error(f"Error analyzing form fields: {e}")

        return fields

    async def _extract_field_info(
        self, form: ElementHandle, element: ElementHandle, field_type: str
    ) -> Optional[Dict[str, Any]]:
        """Extract comprehensive information about a field."""
        try:
            field_info = {
                "element": element,
                "type": field_type,
                "name": await element.get_attribute("name") or "",
                "id": await element.get_attribute("id") or "",
                "placeholder": await element.get_attribute("placeholder") or "",
                "required": await element.get_attribute("required") is not None,
                "class": await element.get_attribute("class") or "",
                "autocomplete": await element.get_attribute("autocomplete") or "",
                "data_attributes": await self._get_data_attributes(element),
            }

            # Get label information
            field_info["label"] = await self._get_field_label(form, element)

            # Get additional context
            field_info["context"] = await self._get_field_context(element)

            # Get current value
            field_info["current_value"] = await self._get_field_value(element)

            return field_info

        except Exception as e:
            self.logger.warning(f"Error extracting field info: {e}")
            return None

    async def _get_data_attributes(self, element: ElementHandle) -> Dict[str, str]:
        """Get all data-* attributes from an element."""
        try:
            return await element.evaluate(
                """
                (el) => {
                    const dataAttrs = {};
                    for (const attr of el.attributes) {
                        if (attr.name.startsWith('data-')) {
                            dataAttrs[attr.name] = attr.value;
                        }
                    }
                    return dataAttrs;
                }
            """
            )
        except:
            return {}

    async def _get_field_label(self, form: ElementHandle, field: ElementHandle) -> str:
        """Try to get label for a field using multiple strategies."""
        try:
            # Strategy 1: Label with for attribute
            field_id = await field.get_attribute("id")
            if field_id:
                label = await form.query_selector(f'label[for="{field_id}"]')
                if label:
                    label_text = await label.inner_text()
                    if label_text:
                        return label_text.strip()

            # Strategy 2: Parent label
            parent_label_text = await field.evaluate(
                """
                (el) => {
                    const label = el.closest('label');
                    return label ? label.textContent : '';
                }
            """
            )

            if parent_label_text:
                return parent_label_text.strip()

            # Strategy 3: Preceding label or text
            preceding_text = await field.evaluate(
                """
                (el) => {
                    let sibling = el.previousElementSibling;
                    while (sibling) {
                        if (sibling.tagName === 'LABEL' || sibling.textContent.trim()) {
                            return sibling.textContent || '';
                        }
                        sibling = sibling.previousElementSibling;
                    }
                    return '';
                }
            """
            )

            if preceding_text:
                return preceding_text.strip()

        except Exception as e:
            self.logger.debug(f"Error getting field label: {e}")

        return ""

    async def _get_field_context(self, element: ElementHandle) -> str:
        """Get contextual information around the field."""
        try:
            context = await element.evaluate(
                """
                (el) => {
                    const container = el.closest('div, fieldset, section');
                    if (container) {
                        // Get text content but limit to reasonable length
                        const text = container.textContent || '';
                        return text.substring(0, 200);
                    }
                    return '';
                }
            """
            )
            return context.strip() if context else ""
        except:
            return ""

    async def _get_field_value(self, element: ElementHandle) -> str:
        """Get current value of a field."""
        try:
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")

            if tag_name in ["input", "textarea"]:
                return await element.input_value() or ""
            elif tag_name == "select":
                return await element.evaluate("el => el.value") or ""

            return ""
        except:
            return ""

    async def _fill_field_with_retry(
        self,
        page: Page,
        element: ElementHandle,
        value: Any,
        field_name: str,
        field_type: str,
        max_retries: int = 2,
    ) -> tuple[bool, Optional[str]]:
        """Fill a field with retry logic and popup handling."""

        for attempt in range(max_retries):
            try:
                # Check for popups before filling
                if attempt > 0:
                    await self._handle_inline_popups(page)

                success = await self._fill_field_safely(
                    element, value, field_name, field_type
                )

                if success:
                    return True, None

                # If first attempt failed, wait and try alternative strategy
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)

            except Exception as e:
                if attempt == max_retries - 1:
                    return False, str(e)
                await asyncio.sleep(0.5)

        return False, "All retry attempts failed"

    async def _handle_inline_popups(self, page: Page):
        """Handle popups that might appear during form filling."""
        try:
            # Quick check for common popup patterns
            popup_selectors = [
                '.modal:not([style*="display: none"])',
                '.popup:not([style*="display: none"])',
                '[role="dialog"]:not([style*="display: none"])',
            ]

            for selector in popup_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        # Try to find and click close button
                        close_btn = await element.query_selector(
                            'button:has-text("×"), button:has-text("Close"), .close'
                        )
                        if close_btn and await close_btn.is_visible():
                            await close_btn.click()
                            await asyncio.sleep(0.5)
                            break

        except Exception as e:
            self.logger.debug(f"Error handling inline popups: {e}")

    async def _fill_field_safely(
        self, element: ElementHandle, value: Any, field_name: str, field_type: str
    ) -> bool:
        """Safely fill a field with multiple strategies and validation."""
        try:
            if field_type == "checkbox":
                # Handle checkbox
                is_checked = await element.is_checked()
                target_state = bool(value)

                if target_state != is_checked:
                    await element.click()
                    # Verify state changed
                    new_state = await element.is_checked()
                    return new_state == target_state
                return True

            elif field_type == "radio":
                # Handle radio button - find the specific option
                if value:
                    radio_name = await element.get_attribute("name")
                    if radio_name:
                        # Find radio with matching value
                        form = await element.evaluate("el => el.closest('form')")
                        if form:
                            target_radio = await form.query_selector(
                                f'input[name="{radio_name}"][value="{value}"]'
                            )
                            if target_radio and await target_radio.is_visible():
                                await target_radio.click()
                                return await target_radio.is_checked()
                return False

            elif field_type == "select":
                # Handle select dropdown
                try:
                    await element.select_option(value)
                    # Verify selection
                    selected_value = await element.evaluate("el => el.value")
                    return str(value) == str(selected_value)
                except:
                    # Try alternative selection method
                    await element.click()
                    await asyncio.sleep(0.2)
                    option = await element.query_selector(f'option[value="{value}"]')
                    if not option:
                        option = await element.query_selector(
                            f'option:has-text("{value}")'
                        )
                    if option:
                        await option.click()
                        return True
                    return False

            else:
                # Handle text input with enhanced strategy
                # Strategy 1: Focus, clear, and type
                await element.focus()
                await asyncio.sleep(0.1)

                # Clear existing value
                await element.evaluate("el => el.value = ''")
                await element.fill("")  # Ensure it's cleared

                # Type new value with human-like delay
                if str(value):
                    await element.type(str(value), delay=30)

                # Trigger events to ensure frameworks detect the change
                await element.dispatch_event("input")
                await element.dispatch_event("change")
                await element.dispatch_event("blur")

                # Verify value was set
                await asyncio.sleep(0.1)
                new_value = await self._get_field_value(element)

                # Allow partial matches for complex values
                if str(value) in new_value or new_value in str(value):
                    return True

                # Strategy 2: Direct fill as fallback
                await element.fill(str(value))
                await element.dispatch_event("change")

                # Final verification
                final_value = await self._get_field_value(element)
                return bool(final_value and final_value.strip())

        except Exception as e:
            self.logger.warning(f"Error filling field {field_name}: {e}")

            # Last resort: JavaScript assignment
            try:
                await element.evaluate(
                    f"el => {{ el.value = '{value}'; el.dispatchEvent(new Event('change')); }}"
                )
                return True
            except:
                pass

        return False

    def _get_alternative_value(
        self,
        field_name: str,
        field_type: str,
        field_attributes: Dict[str, Any],
        previous_attempts: List[str],
    ) -> Any:
        """Get alternative value when previous attempts failed."""

        if field_type == "select" and field_attributes.get("options"):
            # Try different option for select fields
            options = field_attributes["options"]
            for option in options:
                if option not in previous_attempts:
                    return option
            return options[0] if options else ""

        elif field_type in ["text", "textarea"]:
            # Try variations for text fields
            if "message" in field_name.lower():
                alternatives = [
                    "I would like to learn more about your services.",
                    "Please contact me regarding your offerings.",
                    "I'm interested in discussing potential collaboration.",
                ]
            elif "subject" in field_name.lower():
                alternatives = [
                    "Inquiry",
                    "Business Question",
                    "Information Request",
                ]
            else:
                alternatives = ["Information requested", "Please contact me"]

            for alt in alternatives:
                if alt not in previous_attempts:
                    return alt

        return self._get_fallback_value(field_name, field_type, field_attributes)

    def _get_fallback_value(
        self, field_name: str, field_type: str, field_attributes: Dict[str, Any]
    ) -> Any:
        """Get fallback value for required fields with enhanced logic."""
        field_name_lower = field_name.lower()
        placeholder = field_attributes.get("placeholder", "").lower()
        label = field_attributes.get("label", "").lower()

        combined_context = f"{field_name_lower} {placeholder} {label}"

        # Email fields
        if field_type == "email" or any(
            word in combined_context for word in ["email", "e-mail", "@"]
        ):
            return "contact@example.com"

        # Phone fields
        if field_type == "tel" or any(
            word in combined_context for word in ["phone", "tel", "mobile", "number"]
        ):
            return "555-0100"

        # Name fields
        if any(word in combined_context for word in ["name", "first", "last", "full"]):
            if "first" in combined_context:
                return "John"
            elif "last" in combined_context:
                return "Doe"
            else:
                return "John Doe"

        # Company/organization
        if any(
            word in combined_context for word in ["company", "organization", "business"]
        ):
            return "Business Inc."

        # Message/comment fields
        if any(
            word in combined_context
            for word in ["message", "comment", "inquiry", "question", "details"]
        ):
            return "I am interested in learning more about your services."

        # Subject fields
        if any(
            word in combined_context for word in ["subject", "topic", "title", "reason"]
        ):
            return "Business Inquiry"

        # Website/URL fields
        if any(word in combined_context for word in ["website", "url", "site"]):
            return "https://example.com"

        # Select fields - try to find a safe default
        if field_type == "select":
            options = field_attributes.get("options", [])
            if options:
                # Look for safe options
                safe_options = ["other", "not specified", "general", "n/a"]
                for safe in safe_options:
                    for option in options:
                        if safe in option.lower():
                            return option
                return options[0]  # First option as last resort

        # Checkbox fields
        if field_type == "checkbox":
            # Default to unchecked unless it's terms/agreement
            if any(
                word in combined_context
                for word in ["agree", "terms", "accept", "consent"]
            ):
                return True
            return False

        # Default text value
        return "Not specified"

    async def _verify_minimum_fields(
        self, form: ElementHandle, field_mappings: Dict[str, Any]
    ) -> bool:
        """Verify minimum required fields are filled with enhanced checking."""
        try:
            # Check for email field
            has_email = False
            email_fields = await form.query_selector_all(
                'input[type="email"], input[name*="email" i], input[id*="email" i]'
            )

            for field in email_fields:
                if await field.is_visible():
                    value = await self._get_field_value(field)
                    if value and "@" in value and "." in value:
                        has_email = True
                        break

            # Check for message field
            has_message = False
            message_fields = await form.query_selector_all(
                'textarea, input[name*="message" i], input[name*="comment" i]'
            )

            for field in message_fields:
                if await field.is_visible():
                    value = await self._get_field_value(field)
                    if value and len(value.strip()) > 5:
                        has_message = True
                        break

            # Check for name field
            has_name = False
            name_fields = await form.query_selector_all(
                'input[name*="name" i], input[id*="name" i]'
            )

            for field in name_fields:
                if await field.is_visible():
                    value = await self._get_field_value(field)
                    if value and len(value.strip()) > 1:
                        has_name = True
                        break

            # Minimum requirements: at least email OR (message AND name)
            minimum_met = has_email or (has_message and has_name)

            self.logger.info(
                f"Minimum field verification: email={has_email}, message={has_message}, "
                f"name={has_name}, minimum_met={minimum_met}"
            )

            return minimum_met

        except Exception as e:
            self.logger.warning(f"Error verifying minimum fields: {e}")
            return len(field_mappings) > 0  # Fallback to any fields filled

    def _extract_domain_from_page(self, page: Page) -> str:
        """Extract domain from page URL for learning purposes."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(page.url)
            return parsed.netloc or "unknown"
        except:
            return "unknown"

    async def get_fillable_fields(self, form: ElementHandle) -> List[Dict[str, Any]]:
        """Public method to get fillable fields information."""
        return await self._analyze_form_fields_comprehensive(form)

    def get_fill_statistics(self) -> Dict[str, Any]:
        """Get comprehensive filling statistics."""
        stats = self.global_fill_stats.copy()

        if stats["total_forms_attempted"] > 0:
            stats["success_rate"] = (
                f"{(stats['successful_fills'] / stats['total_forms_attempted'] * 100):.1f}%"
            )
            stats["avg_fields_per_form"] = (
                f"{(stats['total_fields_filled'] / stats['successful_fills']):.1f}"
                if stats["successful_fills"] > 0
                else "0"
            )
        else:
            stats["success_rate"] = "0%"
            stats["avg_fields_per_form"] = "0"

        return stats
