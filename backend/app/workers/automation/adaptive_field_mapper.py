# app/workers/automation/adaptive_field_mapper.py
"""Adaptive field mapper that learns from different website patterns."""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from app.workers.utils.logger import WorkerLogger


class AdaptiveFieldMapper:
    """
    Intelligent field mapper that learns and adapts to different website patterns.
    Uses ML-like pattern recognition to improve form filling accuracy over time.
    """

    def __init__(
        self, user_id: Optional[str] = None, campaign_id: Optional[str] = None
    ):
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        # Common field patterns and their variations
        self.field_patterns = {
            "selection_fields": {
                # How did you hear about us variations
                "referral_source": {
                    "patterns": [
                        r"how.*hear",
                        r"how.*find",
                        r"where.*hear",
                        r"referr",
                        r"source",
                        r"found.*us",
                        r"discover",
                    ],
                    "common_values": {
                        "google": [
                            "Google",
                            "Search Engine",
                            "Google Search",
                            "Web Search",
                        ],
                        "social": ["Social Media", "Facebook", "LinkedIn", "Twitter"],
                        "referral": [
                            "Referral",
                            "Friend",
                            "Colleague",
                            "Word of Mouth",
                        ],
                        "other": ["Other", "Others", "Not Listed", "None of the above"],
                    },
                    "default": "other",
                },
                # Industry/Sector
                "industry": {
                    "patterns": [
                        r"industry",
                        r"sector",
                        r"business.*type",
                        r"vertical",
                        r"field",
                        r"domain",
                    ],
                    "common_values": {
                        "technology": ["Technology", "IT", "Software", "Tech"],
                        "healthcare": ["Healthcare", "Medical", "Health"],
                        "finance": ["Finance", "Banking", "Financial Services"],
                        "retail": ["Retail", "E-commerce", "Commerce"],
                        "other": ["Other", "Others", "Not Listed"],
                    },
                    "default": "other",
                },
                # Company size
                "company_size": {
                    "patterns": [
                        r"company.*size",
                        r"employees",
                        r"team.*size",
                        r"organization.*size",
                        r"staff",
                        r"headcount",
                    ],
                    "common_values": {
                        "small": ["1-10", "Small", "< 10", "Startup"],
                        "medium": ["11-50", "51-200", "Medium", "Mid-size"],
                        "large": ["200+", "500+", "Large", "Enterprise"],
                        "solo": ["1", "Solo", "Individual", "Freelancer"],
                    },
                    "default": "11-50",
                },
                # Budget range
                "budget": {
                    "patterns": [
                        r"budget",
                        r"investment",
                        r"price.*range",
                        r"spend",
                        r"funding",
                    ],
                    "common_values": {
                        "low": ["< $10k", "Under 10000", "Small budget"],
                        "medium": ["$10k-50k", "10000-50000", "Moderate"],
                        "high": ["> $50k", "50000+", "Enterprise"],
                        "tbd": ["To be discussed", "Not sure", "Flexible"],
                    },
                    "default": "To be discussed",
                },
                # Timeline
                "timeline": {
                    "patterns": [
                        r"timeline",
                        r"when.*start",
                        r"timeframe",
                        r"urgency",
                        r"start.*date",
                        r"implementation",
                    ],
                    "common_values": {
                        "immediate": ["Immediately", "ASAP", "Urgent", "Now"],
                        "month": ["Within a month", "1 month", "30 days"],
                        "quarter": ["1-3 months", "This quarter", "Q1", "Q2"],
                        "later": ["6+ months", "Next year", "Planning phase"],
                    },
                    "default": "1-3 months",
                },
                # Project type
                "project_type": {
                    "patterns": [
                        r"project.*type",
                        r"service.*type",
                        r"inquiry.*type",
                        r"request.*type",
                        r"need",
                    ],
                    "common_values": {
                        "new": ["New Project", "New Development", "Greenfield"],
                        "existing": ["Existing Project", "Maintenance", "Support"],
                        "consultation": ["Consultation", "Advisory", "Consulting"],
                        "other": ["Other", "General Inquiry", "Multiple"],
                    },
                    "default": "other",
                },
            },
            "yes_no_fields": {
                # Newsletter/Marketing
                "newsletter": {
                    "patterns": [
                        r"newsletter",
                        r"updates",
                        r"marketing",
                        r"communications",
                        r"subscribe",
                        r"mailing.*list",
                        r"email.*list",
                    ],
                    "yes_values": ["Yes", "Subscribe", "Opt In", "1", "true"],
                    "no_values": ["No", "No Thanks", "Opt Out", "0", "false"],
                    "default": "no",  # Privacy-conscious default
                },
                # Terms and conditions
                "terms": {
                    "patterns": [
                        r"terms",
                        r"conditions",
                        r"agree",
                        r"accept",
                        r"privacy",
                        r"gdpr",
                        r"consent",
                    ],
                    "yes_values": ["Yes", "I Agree", "Accept", "1", "true"],
                    "no_values": ["No", "Decline", "0", "false"],
                    "default": "yes",  # Usually required
                },
                # Existing customer
                "existing_customer": {
                    "patterns": [
                        r"existing.*customer",
                        r"current.*client",
                        r"already.*customer",
                        r"new.*customer",
                    ],
                    "yes_values": ["Yes", "Existing", "Current", "1", "true"],
                    "no_values": ["No", "New", "Prospect", "0", "false"],
                    "default": "no",
                },
            },
            "text_fields": {
                # Additional information fields
                "additional_info": {
                    "patterns": [
                        r"additional",
                        r"other.*info",
                        r"anything.*else",
                        r"comments",
                        r"notes",
                        r"remarks",
                    ],
                    "default": "No additional information at this time.",
                },
                # Requirements
                "requirements": {
                    "patterns": [
                        r"requirements",
                        r"specifications",
                        r"needs",
                        r"goals",
                        r"objectives",
                    ],
                    "default": "We are looking for a comprehensive solution that meets our business needs.",
                },
            },
        }

        # Learning history (could be persisted to database)
        self.learning_history = {}

    def map_field(
        self,
        field_name: str,
        field_type: str,
        field_options: Optional[List[str]] = None,
        user_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Intelligently map a field to appropriate value.

        Args:
            field_name: Name/ID of the field
            field_type: Type of field (select, radio, checkbox, text, etc.)
            field_options: Available options for select/radio fields
            user_data: User's profile data

        Returns:
            Appropriate value for the field
        """
        field_name_lower = field_name.lower()

        # Check if we have user data for this exact field
        if user_data and field_name in user_data and user_data[field_name]:
            return user_data[field_name]

        # Check for learned patterns for this field
        if field_name in self.learning_history:
            return self.learning_history[field_name]

        # Determine field category and get appropriate value
        if field_type in ["select", "radio"]:
            return self._map_selection_field(field_name_lower, field_options, user_data)
        elif field_type == "checkbox":
            return self._map_checkbox_field(field_name_lower, user_data)
        elif field_type in ["text", "textarea"]:
            return self._map_text_field(field_name_lower, user_data)
        else:
            return self._get_default_value(field_type)

    def _map_selection_field(
        self,
        field_name: str,
        options: Optional[List[str]] = None,
        user_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Map selection fields (dropdown, radio) to best option."""

        # Check each selection pattern
        for field_key, field_config in self.field_patterns["selection_fields"].items():
            if self._matches_pattern(field_name, field_config["patterns"]):
                # Found matching pattern
                if options:
                    # Try to match with available options
                    for value_key, value_variations in field_config[
                        "common_values"
                    ].items():
                        for variation in value_variations:
                            for option in options:
                                if variation.lower() in option.lower():
                                    self.logger.info(
                                        f"Matched {field_name} to '{option}' via pattern '{field_key}'"
                                    )
                                    return option

                    # Look for "Other" option as fallback
                    for option in options:
                        if "other" in option.lower():
                            return option

                    # Return first option if no match
                    if options:
                        return options[0]

                # Return default for this field type
                return field_config["default"]

        # No pattern match - try to find "Other" or return first option
        if options:
            for option in options:
                if any(
                    word in option.lower() for word in ["other", "none", "not listed"]
                ):
                    return option
            return options[0] if options else ""

        return "Other"

    def _map_checkbox_field(
        self, field_name: str, user_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Map checkbox fields to appropriate boolean value."""

        # Check yes/no patterns
        for field_key, field_config in self.field_patterns["yes_no_fields"].items():
            if self._matches_pattern(field_name, field_config["patterns"]):
                # Special handling for newsletter - respect user privacy
                if field_key == "newsletter":
                    # Check if user has explicitly opted in
                    if user_data and user_data.get("marketing_consent"):
                        return True
                    return False  # Default to no for marketing

                # For terms/privacy, usually need to agree
                if field_key in ["terms", "privacy"]:
                    return True

                # Return configured default
                return field_config["default"] != "no"

        # Default based on field name hints
        if any(word in field_name for word in ["required", "agree", "accept", "terms"]):
            return True
        if any(
            word in field_name for word in ["newsletter", "marketing", "promotional"]
        ):
            return False

        return False

    def _map_text_field(
        self, field_name: str, user_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Map text fields to appropriate values."""

        # Check text field patterns
        for field_key, field_config in self.field_patterns["text_fields"].items():
            if self._matches_pattern(field_name, field_config["patterns"]):
                # Check if user has specific data for this type
                if user_data and field_key in user_data:
                    return user_data[field_key]
                return field_config["default"]

        # Generic text field defaults
        if "why" in field_name:
            return "We are looking for a solution that can help us achieve our business goals."
        if "describe" in field_name:
            return "We need a comprehensive solution for our requirements."
        if "additional" in field_name or "other" in field_name:
            return "No additional information at this time."

        return ""

    def _matches_pattern(self, field_name: str, patterns: List[str]) -> bool:
        """Check if field name matches any of the patterns."""
        for pattern in patterns:
            if re.search(pattern, field_name, re.IGNORECASE):
                return True
        return False

    def _get_default_value(self, field_type: str) -> Any:
        """Get default value based on field type."""
        defaults = {
            "text": "",
            "email": "",
            "tel": "",
            "number": "1",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "checkbox": False,
            "radio": "",
            "select": "",
            "textarea": "",
        }
        return defaults.get(field_type, "")

    def learn_from_success(self, field_mappings: Dict[str, Any], website_domain: str):
        """
        Learn from successful form submission.

        Args:
            field_mappings: The field mappings that were successful
            website_domain: The domain where submission succeeded
        """
        # Store successful patterns
        for field_name, value in field_mappings.items():
            key = f"{website_domain}:{field_name}"
            self.learning_history[key] = value

        self.logger.info(
            f"Learned {len(field_mappings)} field patterns from {website_domain}"
        )

    def get_field_confidence(self, field_name: str, suggested_value: Any) -> float:
        """
        Get confidence score for a field mapping.

        Returns:
            Confidence score between 0 and 1
        """
        # High confidence if we've seen this exact field before
        if field_name in self.learning_history:
            return 0.95

        # Medium-high confidence for pattern matches
        field_name_lower = field_name.lower()
        for patterns in self.field_patterns.values():
            for field_config in patterns.values():
                if "patterns" in field_config:
                    if self._matches_pattern(
                        field_name_lower, field_config["patterns"]
                    ):
                        return 0.75

        # Low confidence for unknown fields
        return 0.3

    def suggest_value_with_context(
        self,
        field_name: str,
        field_type: str,
        field_context: Dict[str, Any],
        user_data: Dict[str, Any],
    ) -> Tuple[Any, float]:
        """
        Suggest value with context awareness and confidence score.

        Args:
            field_name: Field name/ID
            field_type: Field type
            field_context: Additional context (labels, placeholders, etc.)
            user_data: User profile data

        Returns:
            Tuple of (suggested_value, confidence_score)
        """
        # Get base suggestion
        value = self.map_field(
            field_name, field_type, field_context.get("options"), user_data
        )

        # Get confidence
        confidence = self.get_field_confidence(field_name, value)

        # Adjust based on context
        if field_context.get("required") and not value:
            # Required field needs a value
            if field_type == "text":
                value = "Information to be provided"
                confidence = 0.5
            elif field_type == "select" and field_context.get("options"):
                value = field_context["options"][0]
                confidence = 0.6

        return value, confidence
