# app/services/form_service.py
"""Form detection and interaction service."""

import logging
from typing import Dict, List, Optional, Any

from playwright.async_api import Page, ElementHandle

logger = logging.getLogger(__name__)


class FormService:
    """Handle form detection and interaction."""

    CONTACT_INDICATORS = [
        "contact",
        "message",
        "inquiry",
        "get in touch",
        "reach out",
        "send",
        "submit",
        "email us",
    ]

    FIELD_PATTERNS = {
        "email": ['input[type="email"]', 'input[name*="email" i]'],
        "name": ['input[name*="name" i]', 'input[placeholder*="name" i]'],
        "phone": ['input[type="tel"]', 'input[name*="phone" i]'],
        "message": ["textarea", 'textarea[name*="message" i]'],
        "subject": ['input[name*="subject" i]'],
        "company": ['input[name*="company" i]'],
    }

    async def detect_form(self, page: Page) -> Optional[Dict[str, Any]]:
        """Detect suitable form on page."""
        try:
            forms = await page.query_selector_all("form")

            for form in forms:
                if await self._is_contact_form(form):
                    inputs = await form.query_selector_all("input, textarea, select")

                    if inputs:
                        return {
                            "form": form,
                            "inputs": inputs,
                            "is_contact": True,
                        }

            # Return first form if no contact form found
            if forms:
                inputs = await forms[0].query_selector_all("input, textarea, select")
                return {
                    "form": forms[0],
                    "inputs": inputs,
                    "is_contact": False,
                }

        except Exception as e:
            logger.error(f"Error detecting form: {e}")

        return None

    async def fill_form(
        self, page: Page, form_info: Dict[str, Any], user_data: Dict[str, Any]
    ) -> bool:
        """Fill form with user data."""
        try:
            filled_count = 0

            for field_type, selectors in self.FIELD_PATTERNS.items():
                value = self._get_field_value(field_type, user_data)

                if not value:
                    continue

                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element and await element.is_visible():
                            await element.fill(value)
                            filled_count += 1
                            break
                    except Exception:
                        pass

            logger.info(f"Filled {filled_count} form fields")
            return filled_count > 0

        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False

    async def _is_contact_form(self, form: ElementHandle) -> bool:
        """Check if form is likely a contact form."""
        try:
            form_html = await form.inner_html()
            form_text = form_html.lower()

            return any(indicator in form_text for indicator in self.CONTACT_INDICATORS)
        except Exception:
            return False

    def _get_field_value(self, field_type: str, user_data: Dict[str, Any]) -> str:
        """Get value for field type."""
        mapping = {
            "email": user_data.get("email", ""),
            "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}",
            "phone": user_data.get("phone_number", ""),
            "message": user_data.get("message", ""),
            "subject": user_data.get("subject", ""),
            "company": user_data.get("company_name", ""),
        }

        return mapping.get(field_type, "").strip()
