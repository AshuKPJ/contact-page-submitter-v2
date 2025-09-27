# app/utils/status_converter.py
"""Status converter utility for handling submission and campaign status conversions."""

from typing import Union, Optional
from app.models.submission import SubmissionStatus
from app.models.campaign import CampaignStatus


class StatusConverter:
    """Utility class for converting between string and enum status values."""

    # Submission status mappings
    SUBMISSION_STATUS_MAP = {
        "pending": SubmissionStatus.PENDING,
        "processing": SubmissionStatus.PROCESSING,
        "completed": SubmissionStatus.COMPLETED,  # This is used for successful submissions
        "failed": SubmissionStatus.FAILED,
        "retry": SubmissionStatus.RETRY,
        # Handle legacy "success" values by mapping to completed
        "success": SubmissionStatus.COMPLETED,  # Map legacy success to completed
    }

    # Reverse mapping for submission statuses
    SUBMISSION_STATUS_REVERSE = {
        SubmissionStatus.PENDING: "pending",
        SubmissionStatus.PROCESSING: "processing",
        SubmissionStatus.COMPLETED: "completed",
        SubmissionStatus.FAILED: "failed",
        SubmissionStatus.RETRY: "retry",
    }

    # Campaign status mappings (if you have a CampaignStatus enum)
    # Adjust these based on your actual CampaignStatus enum values
    CAMPAIGN_STATUS_MAP = {
        "pending": "pending",
        "processing": "processing",
        "completed": "completed",
        "failed": "failed",
        "active": "active",
        "paused": "paused",
        "cancelled": "cancelled",
    }

    @classmethod
    def to_submission_enum(cls, status_str: str) -> Optional[SubmissionStatus]:
        """
        Convert string status to SubmissionStatus enum.

        Args:
            status_str: String representation of status

        Returns:
            SubmissionStatus enum value or None if invalid
        """
        if not status_str:
            return None

        status_str = status_str.lower().strip()
        return cls.SUBMISSION_STATUS_MAP.get(status_str)

    @classmethod
    def from_submission_enum(cls, status_enum: SubmissionStatus) -> str:
        """
        Convert SubmissionStatus enum to string.

        Args:
            status_enum: SubmissionStatus enum value

        Returns:
            String representation of status
        """
        if not status_enum:
            return "pending"

        return cls.SUBMISSION_STATUS_REVERSE.get(status_enum, "pending")

    @classmethod
    def validate_submission_status(cls, status: Union[str, SubmissionStatus]) -> str:
        """
        Validate and normalize submission status.

        Args:
            status: Status as string or enum

        Returns:
            Normalized status string

        Raises:
            ValueError: If status is invalid
        """
        if isinstance(status, SubmissionStatus):
            return cls.from_submission_enum(status)

        if isinstance(status, str):
            status_lower = status.lower().strip()
            # Check if it's a valid status
            if status_lower in cls.SUBMISSION_STATUS_MAP:
                # Return the normalized form (not "success")
                enum_val = cls.SUBMISSION_STATUS_MAP[status_lower]
                return cls.from_submission_enum(enum_val)
            else:
                raise ValueError(
                    f"Invalid submission status: {status}. "
                    f"Must be one of: {', '.join(cls.SUBMISSION_STATUS_REVERSE.values())}"
                )

        raise TypeError(
            f"Status must be string or SubmissionStatus enum, got {type(status)}"
        )

    @classmethod
    def validate_campaign_status(cls, status: str) -> str:
        """
        Validate and normalize campaign status.

        Args:
            status: Status string

        Returns:
            Normalized status string

        Raises:
            ValueError: If status is invalid
        """
        if not status:
            return "pending"

        status_lower = status.lower().strip()
        if status_lower in cls.CAMPAIGN_STATUS_MAP:
            return cls.CAMPAIGN_STATUS_MAP[status_lower]
        else:
            raise ValueError(
                f"Invalid campaign status: {status}. "
                f"Must be one of: {', '.join(cls.CAMPAIGN_STATUS_MAP.keys())}"
            )

    @classmethod
    def is_terminal_status(cls, status: str, is_campaign: bool = False) -> bool:
        """
        Check if a status is terminal (completed or failed).

        Args:
            status: Status string
            is_campaign: Whether this is for a campaign or submission

        Returns:
            True if status is terminal
        """
        terminal_statuses = ["completed", "failed", "cancelled"]
        return status.lower() in terminal_statuses

    @classmethod
    def is_active_status(cls, status: str) -> bool:
        """
        Check if a status indicates active processing.

        Args:
            status: Status string

        Returns:
            True if status is active
        """
        active_statuses = ["processing", "active", "retry"]
        return status.lower() in active_statuses

    @classmethod
    def normalize_status(cls, status: str) -> str:
        """
        Normalize any status string to its canonical form.
        Handles legacy "success" values by converting to "completed".

        Args:
            status: Status string

        Returns:
            Normalized status string
        """
        if not status:
            return "pending"

        status_lower = status.lower().strip()

        # Map legacy "success" to "completed"
        if status_lower == "success":
            return "completed"

        # Return the lowercase version if it's valid
        valid_statuses = [
            "pending",
            "processing",
            "completed",
            "failed",
            "retry",
            "active",
            "paused",
            "cancelled",
        ]
        if status_lower in valid_statuses:
            return status_lower

        # Default to pending for unknown statuses
        return "pending"
