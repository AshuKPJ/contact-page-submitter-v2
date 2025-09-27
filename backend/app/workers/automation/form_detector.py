# app/workers/automation/form_detector.py
"""Advanced form detection with iframe awareness and intelligent scoring."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from playwright.async_api import Page, Frame, ElementHandle

from app.workers.utils.logger import WorkerLogger

logger = logging.getLogger(__name__)


class FormAnalysisResult:
    """Comprehensive form analysis result."""

    def __init__(
        self,
        form: ElementHandle,
        score: int,
        field_counts: Dict[str, int],
        metadata: Dict[str, Any],
        frame_context: Optional[str] = None,
    ):
        self.form = form
        self.score = score
        self.field_counts = field_counts
        self.metadata = metadata
        self.frame_context = frame_context  # Track which frame this form is from
        self.is_contact_form = score >= 4

        # Enhanced metadata
        self.metadata["frame_context"] = frame_context


class FormDetector:
    """Intelligent form detection and analysis."""

    def __init__(
        self, user_id: Optional[str] = None, campaign_id: Optional[str] = None
    ):
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        # Enhanced positive indicators
        self.positive_indicators = [
            "contact",
            "message",
            "inquiry",
            "question",
            "comment",
            "get in touch",
            "reach out",
            "send",
            "email us",
            "talk to us",
            "write to us",
            "drop us a line",
            "questions that you may have",
            "assist you",
            "help you",
            "support",
            "feedback",
            "ask us",
            "connect",
            "consultation",
            "quote",
            "request",
            "interested",
        ]

        # Enhanced negative indicators
        self.negative_indicators = [
            "newsletter",
            "subscribe",
            "subscription",
            "login",
            "signin",
            "signup",
            "register",
            "search",
            "filter",
            "cart",
            "checkout",
            "payment",
            "donate",
            "mailing list",
            "stay updated",
            "stay informed",
            "join our newsletter",
            "get updates",
            "follow us",
            "download",
            "reset password",
            "forgot password",
            "create account",
        ]

        # Field patterns for better detection
        self.field_patterns = {
            "email": {
                "types": ["email"],
                "names": ["email", "e-mail", "mail", "emailaddress", "email_address"],
                "placeholders": [
                    "email",
                    "your email",
                    "enter email",
                    "e-mail address",
                ],
            },
            "name": {
                "types": ["text"],
                "names": [
                    "name",
                    "fullname",
                    "full_name",
                    "firstname",
                    "lastname",
                    "fname",
                    "lname",
                ],
                "placeholders": [
                    "name",
                    "your name",
                    "full name",
                    "first name",
                    "last name",
                ],
            },
            "message": {
                "names": [
                    "message",
                    "comment",
                    "inquiry",
                    "question",
                    "details",
                    "description",
                    "text",
                    "body",
                ],
                "placeholders": [
                    "message",
                    "your message",
                    "comments",
                    "how can we help",
                    "tell us more",
                ],
            },
            "phone": {
                "types": ["tel", "phone"],
                "names": [
                    "phone",
                    "telephone",
                    "mobile",
                    "cell",
                    "phonenumber",
                    "phone_number",
                ],
                "placeholders": ["phone", "telephone", "mobile", "contact number"],
            },
            "subject": {
                "types": ["text"],
                "names": ["subject", "topic", "reason", "regarding", "title"],
                "placeholders": ["subject", "topic", "what is this about"],
            },
        }

    async def detect_contact_forms(
        self, frame_or_page: Union[Page, Frame]
    ) -> List[FormAnalysisResult]:
        """
        Detect and analyze all forms in a page or frame.

        Args:
            frame_or_page: Either a Page or Frame object to search for forms

        Returns:
            List of FormAnalysisResult objects for contact forms
        """
        frame_context = "iframe" if hasattr(frame_or_page, "parent_frame") else "main"

        try:
            # Wait for forms to be present
            try:
                await frame_or_page.wait_for_selector(
                    "form", timeout=5000, state="attached"
                )
            except:
                self.logger.info(f"No forms found in {frame_context}")
                return []

            forms = await frame_or_page.query_selector_all("form")

            if not forms:
                self.logger.info(f"No forms found in {frame_context}")
                return []

            self.logger.info(f"Analyzing {len(forms)} forms in {frame_context}")

            contact_forms = []

            for i, form in enumerate(forms):
                try:
                    # Check if form is visible
                    is_visible = await form.is_visible()
                    if not is_visible:
                        self.logger.info(
                            f"Form {i+1} in {frame_context} is not visible, skipping"
                        )
                        continue

                    analysis = await self._analyze_form(form, i + 1, frame_context)

                    if analysis.is_contact_form:
                        self.logger.info(
                            f"Form {i+1} in {frame_context}: ACCEPTED as contact form (score: {analysis.score})"
                        )
                        contact_forms.append(analysis)
                    else:
                        self.logger.info(
                            f"Form {i+1} in {frame_context}: REJECTED (score: {analysis.score})"
                        )

                except Exception as e:
                    self.logger.warning(
                        f"Error analyzing form {i+1} in {frame_context}: {e}"
                    )
                    continue

            self.logger.info(
                f"Found {len(contact_forms)} contact forms in {frame_context}"
            )
            return contact_forms

        except Exception as e:
            self.logger.error(f"Error detecting forms in {frame_context}: {e}")
            return []

    async def _analyze_form(
        self, form: ElementHandle, form_index: int, frame_context: str = "main"
    ) -> FormAnalysisResult:
        """Analyze a single form with enhanced detection."""

        self.logger.info(f"Analyzing form {form_index} in {frame_context}")

        # Get form HTML and attributes
        form_html = await form.inner_html()
        form_text = form_html.lower()

        # Get form attributes
        form_attrs = await self._get_form_attributes(form)

        # Get surrounding context
        parent_context = await self._get_parent_context(form)
        full_context = (
            f"{form_text} {parent_context} {' '.join(form_attrs.values())}".lower()
        )

        # Count and analyze fields
        field_analysis = await self._analyze_form_fields(form)
        field_counts = field_analysis["counts"]
        field_details = field_analysis["details"]

        total_fields = sum(field_counts.values())

        # Calculate comprehensive score
        score = await self._calculate_comprehensive_score(
            form, field_counts, field_details, full_context, form_attrs
        )

        # Build metadata
        metadata = {
            "form_index": form_index,
            "frame_context": frame_context,
            "form_id": form_attrs.get("id", ""),
            "form_class": form_attrs.get("class", ""),
            "form_action": form_attrs.get("action", ""),
            "form_method": form_attrs.get("method", "post"),
            "total_fields": total_fields,
            "field_types": field_counts,
            "field_details": field_details,
            "has_required_fields": field_analysis.get("has_required_fields", False),
            "positive_indicators_found": [
                ind for ind in self.positive_indicators if ind in full_context
            ],
            "score_breakdown": await self._get_score_breakdown(
                field_counts, field_details, full_context
            ),
        }

        return FormAnalysisResult(
            form=form,
            score=score,
            field_counts=field_counts,
            metadata=metadata,
            frame_context=frame_context,
        )

    async def _get_form_attributes(self, form: ElementHandle) -> Dict[str, str]:
        """Get all form attributes."""
        attrs = {}
        for attr in ["id", "class", "action", "method", "name", "data-form-type"]:
            value = await form.get_attribute(attr)
            if value:
                attrs[attr] = value
        return attrs

    async def _get_parent_context(self, form: ElementHandle) -> str:
        """Get surrounding context of the form."""
        try:
            # Try to get parent element's text
            parent_text = await form.evaluate(
                """
                (form) => {
                    const parent = form.parentElement;
                    if (parent) {
                        // Get text from surrounding elements
                        const texts = [];
                        const prevSibling = form.previousElementSibling;
                        const nextSibling = form.nextElementSibling;
                        
                        if (prevSibling) texts.push(prevSibling.textContent);
                        if (parent.tagName !== 'BODY') texts.push(parent.textContent);
                        if (nextSibling) texts.push(nextSibling.textContent);
                        
                        return texts.join(' ').substring(0, 500);
                    }
                    return '';
                }
            """
            )
            return parent_text or ""
        except:
            return ""

    async def _analyze_form_fields(self, form: ElementHandle) -> Dict[str, Any]:
        """Comprehensive field analysis."""

        # Count basic field types
        field_counts = {
            "email": 0,
            "text": 0,
            "textarea": 0,
            "tel": 0,
            "submit": 0,
            "select": 0,
            "checkbox": 0,
            "radio": 0,
            "hidden": 0,
        }

        field_details = {
            "email_fields": [],
            "name_fields": [],
            "message_fields": [],
            "phone_fields": [],
            "subject_fields": [],
        }

        has_required_fields = False

        # Analyze input fields
        inputs = await form.query_selector_all("input")
        for input_elem in inputs:
            try:
                input_type = (await input_elem.get_attribute("type") or "text").lower()
                input_name = (await input_elem.get_attribute("name") or "").lower()
                input_id = (await input_elem.get_attribute("id") or "").lower()
                input_placeholder = (
                    await input_elem.get_attribute("placeholder") or ""
                ).lower()
                is_required = await input_elem.get_attribute("required") is not None

                if is_required:
                    has_required_fields = True

                # Categorize field
                if input_type == "email" or self._matches_pattern(
                    input_name,
                    input_id,
                    input_placeholder,
                    self.field_patterns["email"],
                ):
                    field_counts["email"] += 1
                    field_details["email_fields"].append(
                        {"name": input_name, "id": input_id, "required": is_required}
                    )
                elif input_type == "tel" or self._matches_pattern(
                    input_name,
                    input_id,
                    input_placeholder,
                    self.field_patterns["phone"],
                ):
                    field_counts["tel"] += 1
                    field_details["phone_fields"].append(
                        {"name": input_name, "id": input_id, "required": is_required}
                    )
                elif self._matches_pattern(
                    input_name, input_id, input_placeholder, self.field_patterns["name"]
                ):
                    field_counts["text"] += 1
                    field_details["name_fields"].append(
                        {"name": input_name, "id": input_id, "required": is_required}
                    )
                elif self._matches_pattern(
                    input_name,
                    input_id,
                    input_placeholder,
                    self.field_patterns["subject"],
                ):
                    field_counts["text"] += 1
                    field_details["subject_fields"].append(
                        {"name": input_name, "id": input_id, "required": is_required}
                    )
                elif input_type in ["text", "url", "number"]:
                    field_counts["text"] += 1
                elif input_type == "submit":
                    field_counts["submit"] += 1
                elif input_type == "checkbox":
                    field_counts["checkbox"] += 1
                elif input_type == "radio":
                    field_counts["radio"] += 1
                elif input_type == "hidden":
                    field_counts["hidden"] += 1

            except Exception as e:
                self.logger.warning(f"Error analyzing input field: {e}")

        # Analyze textarea fields
        textareas = await form.query_selector_all("textarea")
        for textarea in textareas:
            try:
                textarea_name = (await textarea.get_attribute("name") or "").lower()
                textarea_id = (await textarea.get_attribute("id") or "").lower()
                textarea_placeholder = (
                    await textarea.get_attribute("placeholder") or ""
                ).lower()
                is_required = await textarea.get_attribute("required") is not None

                if is_required:
                    has_required_fields = True

                field_counts["textarea"] += 1
                field_details["message_fields"].append(
                    {"name": textarea_name, "id": textarea_id, "required": is_required}
                )

            except Exception as e:
                self.logger.warning(f"Error analyzing textarea: {e}")

        # Analyze select fields
        selects = await form.query_selector_all("select")
        field_counts["select"] = len(selects)

        # Analyze buttons (as potential submit elements)
        buttons = await form.query_selector_all("button")
        for button in buttons:
            try:
                button_type = await button.get_attribute("type")
                if not button_type or button_type == "submit":
                    field_counts["submit"] += 1
            except:
                pass

        return {
            "counts": field_counts,
            "details": field_details,
            "has_required_fields": has_required_fields,
        }

    def _matches_pattern(
        self, name: str, id: str, placeholder: str, pattern: Dict
    ) -> bool:
        """Check if field matches a pattern."""
        # Check name patterns
        if "names" in pattern:
            for pattern_name in pattern["names"]:
                if pattern_name in name or pattern_name in id:
                    return True

        # Check placeholder patterns
        if "placeholders" in pattern:
            for pattern_placeholder in pattern["placeholders"]:
                if pattern_placeholder in placeholder:
                    return True

        return False

    async def _calculate_comprehensive_score(
        self,
        form: ElementHandle,
        field_counts: Dict[str, int],
        field_details: Dict[str, Any],
        context: str,
        form_attrs: Dict[str, str],
    ) -> int:
        """Calculate comprehensive form score."""
        score = 0

        # Essential fields scoring (higher weight)
        if field_counts["email"] > 0 or len(field_details["email_fields"]) > 0:
            score += 4  # Email is crucial

        if field_counts["textarea"] > 0 or len(field_details["message_fields"]) > 0:
            score += 4  # Message field is crucial

        # Supporting fields
        if len(field_details["name_fields"]) > 0:
            score += 2

        if len(field_details["phone_fields"]) > 0:
            score += 1

        if len(field_details["subject_fields"]) > 0:
            score += 1

        # Submit button
        if field_counts["submit"] > 0:
            score += 1

        # Context scoring
        positive_count = sum(1 for ind in self.positive_indicators if ind in context)
        if positive_count > 0:
            score += min(3, positive_count)  # Cap at 3 points

        # Negative indicators (penalties)
        negative_count = sum(1 for ind in self.negative_indicators if ind in context)
        if negative_count > 0:
            score -= min(5, negative_count * 2)  # Stronger penalty

        # Form action/method bonus
        action = form_attrs.get("action", "").lower()
        if any(word in action for word in ["contact", "send", "submit", "mail"]):
            score += 2

        # Minimum field requirement
        total_fields = sum(field_counts.values()) - field_counts["hidden"]
        if total_fields < 2:
            score = 0  # Too few fields
        elif total_fields > 15:
            score -= 2  # Probably not a simple contact form

        return max(0, score)  # Don't go negative

    async def _get_score_breakdown(
        self, field_counts: Dict[str, int], field_details: Dict[str, Any], context: str
    ) -> Dict[str, int]:
        """Get detailed score breakdown for debugging."""
        breakdown = {
            "email_score": 4 if field_counts["email"] > 0 else 0,
            "message_score": 4 if field_counts["textarea"] > 0 else 0,
            "name_score": 2 if len(field_details.get("name_fields", [])) > 0 else 0,
            "context_score": min(
                3, sum(1 for ind in self.positive_indicators if ind in context)
            ),
            "negative_penalty": -min(
                5, sum(1 for ind in self.negative_indicators if ind in context) * 2
            ),
        }
        breakdown["total"] = sum(breakdown.values())
        return breakdown
