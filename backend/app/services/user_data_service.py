# app/services/user_data_service.py
"""Complete user data service with intelligent form filling capabilities."""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.user import User
from app.models.user_profile import UserProfile
from app.workers.utils.logger import WorkerLogger


class UserDataService:
    """Service to manage user data for intelligent form filling."""

    def __init__(self, db: Session, user_id: str, campaign_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.campaign_id = campaign_id
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        self.user = None
        self.user_profile = None
        self._load_user_data()

        # Intelligent defaults for unknown fields
        self.field_defaults = {
            # Yes/No fields - privacy conscious
            "newsletter": "no",
            "marketing": "no",
            "updates": "no",
            "subscribe": "no",
            "promotional": "no",
            "third_party": "no",
            # Required agreements
            "terms": "yes",
            "privacy": "yes",
            "consent": "yes",
            "agree": "yes",
            # Selection defaults
            "how_did_you_hear": "Other",
            "source": "Website",
            "referral": "Online Search",
            "budget": "To be discussed",
            "timeline": "1-3 months",
            "project_type": "General Inquiry",
            "company_size": "10-50",
            "urgency": "Normal",
            "priority": "Medium",
            # Contact preferences
            "preferred_contact_method": "Email",
            "best_time_to_call": "Business hours",
            # Generic text responses
            "additional_info": "No additional information at this time.",
            "comments": "Looking forward to discussing further.",
            "requirements": "We are evaluating solutions for our business needs.",
        }

    def _load_user_data(self):
        """Load user and profile data from database."""
        try:
            # Load user
            self.user = self.db.query(User).filter(User.id == self.user_id).first()

            if not self.user:
                self.logger.error(f"User {self.user_id} not found")
                return

            # Load or create profile
            self.user_profile = (
                self.db.query(UserProfile)
                .filter(UserProfile.user_id == self.user_id)
                .first()
            )

            if not self.user_profile:
                # Create profile with user's basic info
                self.user_profile = UserProfile(
                    user_id=self.user_id,
                    email=self.user.email,
                    first_name=self.user.first_name,
                    last_name=self.user.last_name,
                    form_preferences={},
                )
                self.db.add(self.user_profile)
                self.db.commit()
                self.logger.info(f"Created profile for user {self.user.email}")

            self.logger.info(f"Loaded data for: {self.user.email}")

        except Exception as e:
            self.logger.error(f"Error loading user data: {e}")
            self.db.rollback()

    def get_form_data(self, website_domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive form data for filling.

        Returns user's actual data + learned preferences + intelligent defaults.
        """
        if not self.user or not self.user_profile:
            return self._get_emergency_defaults()

        form_data = {}

        # 1. Core contact information
        form_data.update(self._get_contact_fields())

        # 2. Professional information
        form_data.update(self._get_professional_fields())

        # 3. Location information
        form_data.update(self._get_location_fields())

        # 4. Business/inquiry information
        form_data.update(self._get_business_fields())

        # 5. Message content
        form_data.update(self._get_message_fields())

        # 6. Apply learned preferences
        if self.user_profile.form_preferences:
            # Website-specific preferences
            if website_domain and website_domain in self.user_profile.form_preferences:
                form_data.update(self.user_profile.form_preferences[website_domain])

            # Global preferences
            if "global" in self.user_profile.form_preferences:
                for key, value in self.user_profile.form_preferences["global"].items():
                    if key not in form_data or not form_data[key]:
                        form_data[key] = value

        # 7. Add intelligent defaults for any missing common fields
        form_data.update(self._get_intelligent_defaults(form_data))

        # Remove empty values
        form_data = {k: v for k, v in form_data.items() if v}

        self.logger.info(
            f"Generated {len(form_data)} form fields for {website_domain or 'unknown'}"
        )
        return form_data

    def _get_contact_fields(self) -> Dict[str, str]:
        """Get contact field variations."""
        email = self.user_profile.email or self.user.email
        first_name = self.user_profile.first_name or self.user.first_name or ""
        last_name = self.user_profile.last_name or self.user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        phone = self.user_profile.phone_number or ""

        return {
            # Email variations
            "email": email,
            "email_address": email,
            "contact_email": email,
            "your_email": email,
            "e-mail": email,
            # Name variations
            "first_name": first_name,
            "firstname": first_name,
            "fname": first_name,
            "given_name": first_name,
            "last_name": last_name,
            "lastname": last_name,
            "lname": last_name,
            "surname": last_name,
            "family_name": last_name,
            "full_name": full_name,
            "fullname": full_name,
            "name": full_name,
            "your_name": full_name,
            "contact_name": full_name,
            # Phone variations
            "phone": phone,
            "phone_number": phone,
            "telephone": phone,
            "mobile": phone,
            "cell": phone,
            "contact_phone": phone,
        }

    def _get_professional_fields(self) -> Dict[str, str]:
        """Get professional field variations."""
        return {
            "company": self.user_profile.company_name or "",
            "company_name": self.user_profile.company_name or "",
            "organization": self.user_profile.company_name or "",
            "business": self.user_profile.company_name or "",
            "employer": self.user_profile.company_name or "",
            "job_title": self.user_profile.job_title or "",
            "title": self.user_profile.job_title or "",
            "position": self.user_profile.job_title or "",
            "role": self.user_profile.job_title or "",
            "designation": self.user_profile.job_title or "",
            "website": self.user_profile.website_url or "",
            "website_url": self.user_profile.website_url or "",
            "company_website": self.user_profile.website_url or "",
            "web_address": self.user_profile.website_url or "",
            "linkedin": self.user_profile.linkedin_url or "",
            "linkedin_url": self.user_profile.linkedin_url or "",
            "linkedin_profile": self.user_profile.linkedin_url or "",
            "industry": self.user_profile.industry or "Other",
            "sector": self.user_profile.industry or "Other",
            "vertical": self.user_profile.industry or "Other",
        }

    def _get_location_fields(self) -> Dict[str, str]:
        """Get location field variations."""
        return {
            "city": self.user_profile.city or "",
            "town": self.user_profile.city or "",
            "state": self.user_profile.state or "",
            "province": self.user_profile.state or "",
            "region": self.user_profile.region or self.user_profile.state or "",
            "zip": self.user_profile.zip_code or "",
            "zip_code": self.user_profile.zip_code or "",
            "zipcode": self.user_profile.zip_code or "",
            "postal_code": self.user_profile.zip_code or "",
            "postcode": self.user_profile.zip_code or "",
            "country": self.user_profile.country or "",
            "nation": self.user_profile.country or "",
            "timezone": self.user_profile.timezone or "UTC",
            "time_zone": self.user_profile.timezone or "UTC",
        }

    def _get_business_fields(self) -> Dict[str, str]:
        """Get business-related fields."""
        return {
            "budget": self.user_profile.budget_range or "To be discussed",
            "budget_range": self.user_profile.budget_range or "Flexible",
            "investment": self.user_profile.budget_range or "Open to discussion",
            "product_interest": self.user_profile.product_interest or "General inquiry",
            "service_interest": self.user_profile.product_interest
            or "Multiple services",
            "interest": self.user_profile.product_interest or "Your solutions",
            "referral_source": self.user_profile.referral_source or "Website",
            "how_did_you_hear": self.user_profile.referral_source or "Online search",
            "source": self.user_profile.referral_source or "Internet",
            "found_us": self.user_profile.referral_source or "Web search",
            "preferred_contact": self.user_profile.preferred_contact or "Email",
            "contact_method": self.user_profile.preferred_contact or "Email",
            "preferred_contact_method": self.user_profile.preferred_contact or "Email",
            "best_time": self.user_profile.best_time_to_contact or "Business hours",
            "best_time_to_call": self.user_profile.best_time_to_contact or "9AM-5PM",
            "availability": self.user_profile.best_time_to_contact or "Weekdays",
        }

    def _get_message_fields(self) -> Dict[str, str]:
        """Get message field content."""
        subject = self._generate_subject()
        message = self._generate_message()

        return {
            "subject": subject,
            "topic": subject,
            "regarding": subject,
            "message": message,
            "comments": message,
            "inquiry": message,
            "question": message,
            "details": message,
            "description": message,
            "additional_information": message,
            "project_description": message,
            "requirements": message,
        }

    def _generate_subject(self) -> str:
        """Generate appropriate subject line."""
        if self.user_profile.subject:
            return self.user_profile.subject

        if self.user_profile.product_interest:
            return f"Inquiry about {self.user_profile.product_interest}"

        if self.user_profile.company_name:
            return f"Business Inquiry from {self.user_profile.company_name}"

        return "Business Inquiry - Request for Information"

    def _generate_message(self) -> str:
        """Generate personalized message."""
        if self.user_profile.message:
            return self.user_profile.message

        parts = []

        # Greeting and introduction
        name = f"{self.user_profile.first_name or ''} {self.user_profile.last_name or ''}".strip()
        if name:
            parts.append(f"Hello,\n\nMy name is {name}")
            if self.user_profile.job_title and self.user_profile.company_name:
                parts.append(
                    f", {self.user_profile.job_title} at {self.user_profile.company_name}."
                )
            elif self.user_profile.company_name:
                parts.append(f" from {self.user_profile.company_name}.")
            else:
                parts.append(".")
        else:
            parts.append("Hello,")

        # Interest statement
        parts.append("\n\n")
        if self.user_profile.product_interest:
            parts.append(
                f"I am interested in learning more about {self.user_profile.product_interest}."
            )
        else:
            parts.append(
                "I am interested in learning more about your products and services."
            )

        # Industry context
        if self.user_profile.industry and self.user_profile.industry != "Other":
            parts.append(
                f" We operate in the {self.user_profile.industry} industry and are looking for solutions that can help our organization."
            )

        # Call to action
        parts.append(
            "\n\nI would appreciate the opportunity to discuss how your solutions can meet our needs."
        )

        # Contact preference
        if self.user_profile.preferred_contact:
            parts.append(
                f" Please feel free to contact me via {self.user_profile.preferred_contact}"
            )
            if self.user_profile.best_time_to_contact:
                parts.append(f" during {self.user_profile.best_time_to_contact}.")
            else:
                parts.append(".")

        # Closing
        parts.append("\n\nThank you for your time and consideration.\n\nBest regards")
        if name:
            parts.append(f",\n{name}")

        return "".join(parts)

    def _get_intelligent_defaults(
        self, existing_data: Dict[str, str]
    ) -> Dict[str, str]:
        """Add intelligent defaults for common fields not in user data."""
        defaults = {}

        for field, value in self.field_defaults.items():
            if field not in existing_data:
                defaults[field] = value

        return defaults

    def _get_emergency_defaults(self) -> Dict[str, str]:
        """Emergency defaults when no user data available."""
        return {
            "email": "contact@example.com",
            "name": "Interested Party",
            "message": "I am interested in learning more about your services.",
            "subject": "General Inquiry",
        }

    def save_preference(
        self, field_name: str, value: Any, website_domain: Optional[str] = None
    ):
        """Save a learned preference for future use."""
        try:
            if not self.user_profile:
                return

            if not self.user_profile.form_preferences:
                self.user_profile.form_preferences = {}

            # Save to appropriate scope
            if website_domain:
                if website_domain not in self.user_profile.form_preferences:
                    self.user_profile.form_preferences[website_domain] = {}
                self.user_profile.form_preferences[website_domain][field_name] = value
                self.logger.info(
                    f"Saved preference for {website_domain}: {field_name}={value}"
                )
            else:
                if "global" not in self.user_profile.form_preferences:
                    self.user_profile.form_preferences["global"] = {}
                self.user_profile.form_preferences["global"][field_name] = value
                self.logger.info(f"Saved global preference: {field_name}={value}")

            # Mark as modified and commit
            flag_modified(self.user_profile, "form_preferences")
            self.db.commit()

        except Exception as e:
            self.logger.error(f"Error saving preference: {e}")
            self.db.rollback()
