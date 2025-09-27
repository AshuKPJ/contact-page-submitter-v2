# app/workers/automation/field_mapper.py
"""Intelligent field mapper that adapts to different website patterns."""

import re
from typing import Dict, Any, List, Optional, Tuple
from app.workers.utils.logger import WorkerLogger


class IntelligentFieldMapper:
    """Maps form fields to appropriate values using pattern recognition."""

    def __init__(
        self,
        user_data: Dict[str, Any],
        user_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ):
        self.user_data = user_data
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        # Build field mappings from user data
        self.mappings = self._build_mappings()

        # Pattern definitions for intelligent mapping
        self.patterns = {
            "newsletter": {
                "keywords": ["newsletter", "updates", "news", "subscribe", "mailing"],
                "default": False,
                "type": "checkbox",
            },
            "marketing": {
                "keywords": ["marketing", "promotional", "offers", "deals"],
                "default": False,
                "type": "checkbox",
            },
            "terms": {
                "keywords": ["terms", "conditions", "agree", "accept", "policy"],
                "default": True,
                "type": "checkbox",
            },
            "how_heard": {
                "keywords": [
                    "how",
                    "hear",
                    "find",
                    "found",
                    "discover",
                    "referral",
                    "source",
                ],
                "safe_options": ["Other", "Internet", "Web Search", "Online"],
                "type": "select",
            },
            "budget": {
                "keywords": ["budget", "investment", "cost", "price", "spend"],
                "safe_options": ["To be discussed", "Flexible", "Open", "Not sure"],
                "type": "select",
            },
            "timeline": {
                "keywords": ["timeline", "timeframe", "when", "start", "urgency"],
                "safe_options": [
                    "1-3 months",
                    "Flexible",
                    "Not urgent",
                    "Planning phase",
                ],
                "type": "select",
            },
            "company_size": {
                "keywords": ["size", "employees", "staff", "team", "people"],
                "safe_options": ["10-50", "Small", "Medium", "Growing"],
                "type": "select",
            },
        }

    def _build_mappings(self) -> Dict[str, Any]:
        """Build comprehensive field mappings from user data."""
        mappings = {}

        # Direct mappings from user data
        for key, value in self.user_data.items():
            if value:
                # Store with lowercase key for case-insensitive matching
                mappings[key.lower()] = value

                # Add variations without underscores
                mappings[key.lower().replace("_", "")] = value
                mappings[key.lower().replace("_", " ")] = value

        return mappings

    def map_field(
        self,
        field_name: str,
        field_type: str = "text",
        field_attributes: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, float]:
        """
        Map a field to appropriate value with confidence score.

        Returns: (value, confidence_score)
        """
        field_name_lower = field_name.lower()
        field_attributes = field_attributes or {}

        # Check for direct mapping
        direct_value = self._check_direct_mapping(field_name_lower)
        if direct_value is not None:
            return direct_value, 0.95  # High confidence for direct match

        # Check for pattern-based mapping
        pattern_value, confidence = self._check_pattern_mapping(
            field_name_lower, field_type, field_attributes
        )
        if pattern_value is not None:
            return pattern_value, confidence

        # Handle based on field type
        if field_type == "select" or field_type == "radio":
            return self._map_select_field(field_name_lower, field_attributes)
        elif field_type == "checkbox":
            return self._map_checkbox_field(field_name_lower)
        elif field_type in ["text", "textarea"]:
            return self._map_text_field(field_name_lower, field_attributes)
        else:
            return "", 0.1  # Low confidence for unknown fields

    def _check_direct_mapping(self, field_name: str) -> Optional[Any]:
        """Check if we have a direct mapping for this field."""
        # Exact match
        if field_name in self.mappings:
            return self.mappings[field_name]

        # Try without special characters
        clean_name = re.sub(r"[^a-z0-9]", "", field_name)
        if clean_name in self.mappings:
            return self.mappings[clean_name]

        # Try partial matches for common fields
        for key, value in self.mappings.items():
            if key in field_name or field_name in key:
                return value

        return None

    def _check_pattern_mapping(
        self, field_name: str, field_type: str, attributes: Dict[str, Any]
    ) -> Tuple[Optional[Any], float]:
        """Check pattern-based mapping."""
        for pattern_name, pattern_config in self.patterns.items():
            # Check if field matches pattern keywords
            if any(keyword in field_name for keyword in pattern_config["keywords"]):
                # Type must match
                if pattern_config.get("type") and pattern_config["type"] != field_type:
                    continue

                # For select fields, find safe option
                if (
                    field_type in ["select", "radio"]
                    and "safe_options" in pattern_config
                ):
                    options = attributes.get("options", [])
                    if options:
                        # Try to find a safe option
                        for safe_option in pattern_config["safe_options"]:
                            for option in options:
                                if safe_option.lower() in option.lower():
                                    return option, 0.75

                        # Return first safe option as fallback
                        return pattern_config["safe_options"][0], 0.5

                # For checkboxes, return default
                if field_type == "checkbox":
                    return pattern_config.get("default", False), 0.8

                # For text fields, check if we have a value
                if pattern_name in self.user_data:
                    return self.user_data[pattern_name], 0.85

        return None, 0

    def _map_select_field(
        self, field_name: str, attributes: Dict[str, Any]
    ) -> Tuple[str, float]:
        """Map select/radio fields to best option."""
        options = attributes.get("options", [])

        if not options:
            return "", 0.1

        # Look for safe/neutral options
        safe_keywords = ["other", "none", "not listed", "general", "n/a"]
        for option in options:
            option_lower = option.lower()
            for keyword in safe_keywords:
                if keyword in option_lower:
                    self.logger.info(
                        f"Selected safe option '{option}' for {field_name}"
                    )
                    return option, 0.6

        # Check if it's a required field with placeholder
        placeholder = attributes.get("placeholder", "").lower()
        if "select" in placeholder or "choose" in placeholder:
            # Return first non-empty option
            for option in options:
                if option and not option.startswith("--"):
                    return option, 0.4

        # Return first option as last resort
        return options[0] if options else "", 0.3

    def _map_checkbox_field(self, field_name: str) -> Tuple[bool, float]:
        """Map checkbox fields."""
        # Privacy-conscious defaults
        if any(
            word in field_name
            for word in ["newsletter", "marketing", "promotional", "third"]
        ):
            return False, 0.9

        # Required agreements
        if any(
            word in field_name
            for word in ["terms", "agree", "accept", "consent", "privacy"]
        ):
            return True, 0.9

        # Default to unchecked for unknown
        return False, 0.5

    def _map_text_field(
        self, field_name: str, attributes: Dict[str, Any]
    ) -> Tuple[str, float]:
        """Map text fields to appropriate values."""
        # Check placeholder for hints
        placeholder = attributes.get("placeholder", "").lower()

        # Message-type fields
        if any(
            word in field_name
            for word in ["message", "comment", "description", "details"]
        ):
            if "message" in self.user_data:
                return self.user_data["message"], 0.9
            return "I am interested in learning more about your services.", 0.7

        # Subject fields
        if "subject" in field_name or "topic" in field_name:
            if "subject" in self.user_data:
                return self.user_data["subject"], 0.9
            return "Business Inquiry", 0.7

        # Additional info fields
        if any(word in field_name for word in ["additional", "other", "notes"]):
            return "No additional information at this time.", 0.6

        # Check if placeholder gives hints
        if placeholder:
            # Email hint
            if "@" in placeholder or "email" in placeholder:
                return self.user_data.get("email", ""), 0.8

            # Phone hint
            if "phone" in placeholder or "number" in placeholder:
                return self.user_data.get("phone", ""), 0.8

            # Name hint
            if "name" in placeholder:
                return self.user_data.get("name", ""), 0.8

        return "", 0.2

    def get_field_value_with_learning(
        self,
        field_name: str,
        field_element: Dict[str, Any],
        previous_attempts: Optional[List[str]] = None,
    ) -> Tuple[Any, float]:
        """
        Get field value with learning from previous attempts.

        Args:
            field_name: Field name/ID
            field_element: Field element info (type, options, placeholder, etc.)
            previous_attempts: List of previously failed values for this field

        Returns:
            (value, confidence_score)
        """
        # Extract field info
        field_type = field_element.get("type", "text")
        field_options = field_element.get("options", [])
        field_attributes = {
            "options": field_options,
            "placeholder": field_element.get("placeholder", ""),
            "required": field_element.get("required", False),
            "label": field_element.get("label", ""),
        }

        # Get mapped value
        value, confidence = self.map_field(field_name, field_type, field_attributes)

        # If we have previous failed attempts, try alternatives
        if previous_attempts and value in previous_attempts:
            self.logger.info(f"Value '{value}' failed before, trying alternative")

            # For select fields, try next option
            if field_type in ["select", "radio"] and field_options:
                for option in field_options:
                    if option not in previous_attempts:
                        return option, 0.4

            # For text fields, try variation
            if field_type in ["text", "textarea"]:
                if "message" in field_name.lower():
                    return (
                        "Looking forward to discussing our requirements with you.",
                        0.5,
                    )
                elif "subject" in field_name.lower():
                    return "Request for Information", 0.5

            confidence *= 0.5  # Reduce confidence for retry

        return value, confidence

    def learn_from_success(self, field_mappings: Dict[str, Any]):
        """
        Learn from successful field mappings.

        Updates internal mappings based on what worked.
        """
        for field_name, value in field_mappings.items():
            if value and field_name.lower() not in self.mappings:
                self.mappings[field_name.lower()] = value
                self.logger.info(f"Learned new mapping: {field_name} -> {value}")
