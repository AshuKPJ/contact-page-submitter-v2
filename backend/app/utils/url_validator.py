# app/utils/url_validator.py
"""URL validation and normalization utilities."""

from urllib.parse import urlparse
from typing import Optional


class URLValidator:
    """Handle URL validation and normalization."""

    @staticmethod
    def validate_and_normalize(url: Optional[str]) -> str:
        """
        Validate and normalize a URL.

        Args:
            url: Raw URL string

        Returns:
            Normalized URL with protocol

        Raises:
            ValueError: If URL is invalid
        """
        if not url or not url.strip():
            raise ValueError("URL is required")

        clean_url = url.strip()

        # Add protocol if missing
        if not clean_url.startswith(("http://", "https://")):
            clean_url = f"https://{clean_url}"

        try:
            parsed = urlparse(clean_url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError(f"Invalid URL format: {url}")
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

        return clean_url

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        try:
            URLValidator.validate_and_normalize(url)
            return True
        except ValueError:
            return False
