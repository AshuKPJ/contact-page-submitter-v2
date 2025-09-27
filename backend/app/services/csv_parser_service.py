# app/services/csv_parser_service.py
"""Enhanced CSV Parser Service with comprehensive data cleaning and validation"""

import csv
import io
import re
import logging
from typing import List, Tuple, Optional, Dict, Any, Set
from urllib.parse import urlparse, urlunparse
from collections import Counter

logger = logging.getLogger(__name__)


class CSVParserService:
    """Service for parsing, cleaning, and validating CSV files"""

    # Common invalid domain patterns
    INVALID_DOMAINS = {
        "example.com",
        "test.com",
        "localhost",
        "127.0.0.1",
        "dummy.com",
        "sample.com",
        "yoursite.com",
        "website.com",
    }

    # Valid TLD patterns
    VALID_TLD_PATTERN = re.compile(r"\.[a-zA-Z]{2,}$")

    @staticmethod
    async def parse_csv_file(content: bytes) -> Tuple[List[str], Dict[str, Any]]:
        """
        Parse CSV file with comprehensive cleaning and validation

        Args:
            content: CSV file content as bytes

        Returns:
            Tuple of (valid_urls, processing_report)
        """
        processing_report = {
            "total_rows": 0,
            "valid_urls": 0,
            "duplicates_removed": 0,
            "blank_rows_removed": 0,
            "invalid_urls": [],
            "malformed_urls": [],
            "suspicious_domains": [],
            "headers": [],
            "errors": [],
            "warnings": [],
            "statistics": {},
        }

        try:
            # Decode content with BOM handling
            text_content = content.decode("utf-8-sig")

            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(text_content))
            headers = csv_reader.fieldnames or []
            processing_report["headers"] = headers

            # Find URL column
            url_column = CSVParserService._identify_url_column(headers)

            if not url_column:
                processing_report["errors"].append("No URL column found in CSV")
                return [], processing_report

            # Process all rows first
            raw_urls = []
            blank_count = 0

            for row_num, row in enumerate(csv_reader, start=2):
                processing_report["total_rows"] += 1

                # Check if row is blank
                if not any(row.values()):
                    blank_count += 1
                    continue

                url = row.get(url_column, "").strip()

                if not url:
                    blank_count += 1
                    continue

                raw_urls.append({"url": url, "row": row_num, "original": url})

            processing_report["blank_rows_removed"] = blank_count

            # Process and validate URLs
            valid_urls = []
            seen_urls = set()
            duplicate_count = 0

            for url_data in raw_urls:
                url = url_data["url"]
                row_num = url_data["row"]

                # Clean and normalize URL
                cleaned_url = CSVParserService._clean_url(url)

                if not cleaned_url:
                    processing_report["invalid_urls"].append(
                        {
                            "row": row_num,
                            "url": url,
                            "reason": "Empty or whitespace only",
                        }
                    )
                    continue

                # Validate URL format
                validation_result = CSVParserService._validate_url(cleaned_url)

                if not validation_result["valid"]:
                    if validation_result["reason"] == "malformed":
                        processing_report["malformed_urls"].append(
                            {
                                "row": row_num,
                                "url": url,
                                "cleaned": cleaned_url,
                                "issue": validation_result["issue"],
                            }
                        )
                    elif validation_result["reason"] == "suspicious":
                        processing_report["suspicious_domains"].append(
                            {
                                "row": row_num,
                                "url": cleaned_url,
                                "domain": validation_result["domain"],
                            }
                        )
                    else:
                        processing_report["invalid_urls"].append(
                            {
                                "row": row_num,
                                "url": url,
                                "reason": validation_result["reason"],
                            }
                        )
                    continue

                # Normalize URL
                normalized_url = validation_result["normalized"]

                # Check for duplicates
                if normalized_url in seen_urls:
                    duplicate_count += 1
                    continue

                seen_urls.add(normalized_url)
                valid_urls.append(normalized_url)

            processing_report["duplicates_removed"] = duplicate_count
            processing_report["valid_urls"] = len(valid_urls)

            # Generate statistics
            processing_report["statistics"] = CSVParserService._generate_statistics(
                valid_urls, processing_report
            )

            # Add warnings
            if duplicate_count > 0:
                processing_report["warnings"].append(
                    f"Removed {duplicate_count} duplicate URLs"
                )

            if len(processing_report["suspicious_domains"]) > 0:
                processing_report["warnings"].append(
                    f'Found {len(processing_report["suspicious_domains"])} suspicious domains'
                )

            if len(valid_urls) == 0 and processing_report["total_rows"] > 0:
                processing_report["errors"].append(
                    "No valid URLs found in the CSV file"
                )

            logger.info(
                f"CSV Processing complete: {len(valid_urls)} valid URLs from {processing_report['total_rows']} rows"
            )

        except UnicodeDecodeError:
            # Try alternative encoding
            try:
                text_content = content.decode("latin-1")
                return await CSVParserService._parse_with_encoding(text_content)
            except Exception as e:
                processing_report["errors"].append(
                    f"Failed to decode CSV file: {str(e)}"
                )

        except Exception as e:
            processing_report["errors"].append(f"Failed to parse CSV: {str(e)}")
            logger.error(f"CSV parsing error: {e}")

        return valid_urls, processing_report

    @staticmethod
    def _identify_url_column(headers: List[str]) -> Optional[str]:
        """Identify the column containing URLs"""
        if not headers:
            return None

        # Priority order for URL column names
        url_keywords = [
            ("url", 10),
            ("website", 9),
            ("web_site", 8),
            ("site", 7),
            ("link", 6),
            ("domain", 5),
            ("homepage", 4),
            ("web", 3),
            ("address", 2),
            ("www", 1),
        ]

        best_match = None
        best_score = 0

        for header in headers:
            header_lower = header.lower().strip()

            for keyword, score in url_keywords:
                if keyword in header_lower and score > best_score:
                    best_match = header
                    best_score = score

        # If no keyword match, check if first column looks like URLs
        if not best_match and headers:
            # We'll use the first column as fallback
            best_match = headers[0]

        return best_match

    @staticmethod
    def _clean_url(url: str) -> Optional[str]:
        """Clean and prepare URL for validation"""
        if not url:
            return None

        # Remove whitespace
        url = url.strip()

        # Remove quotes if present
        url = url.strip("\"'")

        # Remove common prefixes that aren't part of URL
        prefixes_to_remove = ["Website:", "URL:", "Site:", "www:"]
        for prefix in prefixes_to_remove:
            if url.lower().startswith(prefix.lower()):
                url = url[len(prefix) :].strip()

        # Remove trailing punctuation
        url = url.rstrip(".,;:")

        # Handle encoded characters
        url = url.replace("%20", " ").replace(" ", "")

        # Remove any control characters
        url = "".join(char for char in url if ord(char) >= 32)

        return url if url else None

    @staticmethod
    def _validate_url(url: str) -> Dict[str, Any]:
        """
        Comprehensive URL validation

        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": False,
            "normalized": None,
            "reason": None,
            "issue": None,
            "domain": None,
        }

        if not url:
            result["reason"] = "empty"
            return result

        # Add scheme if missing
        if not url.startswith(("http://", "https://", "ftp://")):
            url = "https://" + url

        try:
            # Parse URL
            parsed = urlparse(url)

            # Extract domain
            domain = parsed.netloc.lower()
            result["domain"] = domain

            # Check for missing domain
            if not domain:
                result["reason"] = "malformed"
                result["issue"] = "No domain found"
                return result

            # Check for spaces in domain
            if " " in domain:
                result["reason"] = "malformed"
                result["issue"] = "Spaces in domain"
                return result

            # Check for invalid characters in domain
            if not re.match(r"^[a-zA-Z0-9.-]+$", domain.replace(":", "")):
                result["reason"] = "malformed"
                result["issue"] = "Invalid characters in domain"
                return result

            # Check for valid TLD
            if not CSVParserService.VALID_TLD_PATTERN.search(domain):
                result["reason"] = "malformed"
                result["issue"] = "Invalid or missing TLD"
                return result

            # Check for suspicious domains
            base_domain = domain.split(":")[0]  # Remove port if present
            if base_domain in CSVParserService.INVALID_DOMAINS:
                result["reason"] = "suspicious"
                return result

            # Check for localhost/IP addresses
            if re.match(r"^(\d{1,3}\.){3}\d{1,3}", base_domain):
                result["reason"] = "suspicious"
                return result

            # Check minimum domain length
            if len(base_domain) < 4:  # e.g., "a.co" would be minimum
                result["reason"] = "malformed"
                result["issue"] = "Domain too short"
                return result

            # Normalize URL
            normalized = urlunparse(
                (
                    parsed.scheme or "https",
                    domain,
                    parsed.path.rstrip("/"),
                    parsed.params,
                    parsed.query,
                    "",  # Remove fragment
                )
            )

            result["valid"] = True
            result["normalized"] = normalized

        except Exception as e:
            result["reason"] = "malformed"
            result["issue"] = str(e)

        return result

    @staticmethod
    def _generate_statistics(
        valid_urls: List[str], report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate statistics about the processed data"""
        stats = {
            "success_rate": 0,
            "duplicate_rate": 0,
            "invalid_rate": 0,
            "top_domains": [],
            "protocol_distribution": {"https": 0, "http": 0, "other": 0},
        }

        total = report["total_rows"]
        if total > 0:
            stats["success_rate"] = round((len(valid_urls) / total) * 100, 2)
            stats["duplicate_rate"] = round(
                (report["duplicates_removed"] / total) * 100, 2
            )

            invalid_count = (
                len(report["invalid_urls"])
                + len(report["malformed_urls"])
                + len(report["suspicious_domains"])
            )
            stats["invalid_rate"] = round((invalid_count / total) * 100, 2)

        # Analyze domains
        if valid_urls:
            domains = []
            for url in valid_urls:
                parsed = urlparse(url)
                domain = parsed.netloc.split(":")[0]
                domains.append(domain)

                # Protocol distribution
                if parsed.scheme == "https":
                    stats["protocol_distribution"]["https"] += 1
                elif parsed.scheme == "http":
                    stats["protocol_distribution"]["http"] += 1
                else:
                    stats["protocol_distribution"]["other"] += 1

            # Top domains
            domain_counts = Counter(domains)
            stats["top_domains"] = [
                {"domain": domain, "count": count}
                for domain, count in domain_counts.most_common(10)
            ]

        return stats

    @staticmethod
    def generate_user_report(processing_report: Dict[str, Any]) -> str:
        """Generate a user-friendly report of CSV processing"""
        lines = []
        lines.append("CSV Processing Report")
        lines.append("=" * 50)
        lines.append(f"Total rows processed: {processing_report['total_rows']}")
        lines.append(f"Valid URLs found: {processing_report['valid_urls']}")
        lines.append(f"Duplicates removed: {processing_report['duplicates_removed']}")
        lines.append(f"Blank rows removed: {processing_report['blank_rows_removed']}")

        if processing_report["invalid_urls"]:
            lines.append(f"\nInvalid URLs ({len(processing_report['invalid_urls'])}):")
            for item in processing_report["invalid_urls"][:10]:  # Show first 10
                lines.append(f"  Row {item['row']}: {item['url']} - {item['reason']}")

        if processing_report["malformed_urls"]:
            lines.append(
                f"\nMalformed URLs ({len(processing_report['malformed_urls'])}):"
            )
            for item in processing_report["malformed_urls"][:10]:
                lines.append(f"  Row {item['row']}: {item['url']} - {item['issue']}")

        if processing_report["suspicious_domains"]:
            lines.append(
                f"\nSuspicious domains ({len(processing_report['suspicious_domains'])}):"
            )
            for item in processing_report["suspicious_domains"][:10]:
                lines.append(f"  Row {item['row']}: {item['domain']}")

        stats = processing_report.get("statistics", {})
        if stats:
            lines.append(f"\nStatistics:")
            lines.append(f"  Success rate: {stats.get('success_rate', 0)}%")
            lines.append(f"  Duplicate rate: {stats.get('duplicate_rate', 0)}%")
            lines.append(f"  Invalid rate: {stats.get('invalid_rate', 0)}%")

        return "\n".join(lines)
