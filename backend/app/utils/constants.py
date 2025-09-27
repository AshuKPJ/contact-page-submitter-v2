from __future__ import annotations

# User agent strings for browser automation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# Browser arguments for stealth mode
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-web-security",
    "--disable-extensions",
    "--no-first-run",
    "--disable-default-apps",
    "--disable-setuid-sandbox",
    "--disable-gpu",
]

# Form field patterns for detection
FORM_FIELD_PATTERNS = {
    "email": [
        'input[type="email"]',
        'input[name*="email" i]',
        'input[id*="email" i]',
        'input[placeholder*="email" i]',
        'input[aria-label*="email" i]',
    ],
    "name": [
        'input[name*="name" i]:not([name*="first"]):not([name*="last"]):not([name*="company"])',
        'input[id*="name" i]:not([id*="first"]):not([id*="last"]):not([id*="company"])',
        'input[placeholder*="full name" i]',
        'input[aria-label*="name" i]',
    ],
    "first_name": [
        'input[name*="first" i]',
        'input[id*="first" i]',
        'input[placeholder*="first" i]',
        'input[aria-label*="first" i]',
    ],
    "last_name": [
        'input[name*="last" i]',
        'input[id*="last" i]',
        'input[placeholder*="last" i]',
        'input[aria-label*="last" i]',
    ],
    "phone": [
        'input[type="tel"]',
        'input[name*="phone" i]',
        'input[id*="phone" i]',
        'input[placeholder*="phone" i]',
        'input[aria-label*="phone" i]',
    ],
    "company": [
        'input[name*="company" i]',
        'input[id*="company" i]',
        'input[name*="organization" i]',
        'input[placeholder*="company" i]',
        'input[aria-label*="company" i]',
    ],
    "message": [
        "textarea",
        'textarea[name*="message" i]',
        'textarea[id*="message" i]',
        'textarea[placeholder*="message" i]',
        'textarea[aria-label*="message" i]',
        'div[contenteditable="true"]',
    ],
    "subject": [
        'input[name*="subject" i]',
        'input[id*="subject" i]',
        'input[placeholder*="subject" i]',
        'input[aria-label*="subject" i]',
    ],
}

# Contact form indicators
CONTACT_FORM_INDICATORS = [
    "contact",
    "get in touch",
    "reach out",
    "message us",
    "send us",
    "inquiry",
    "enquiry",
    "feedback",
    "support",
    "help",
    "question",
    "comment",
]

# Success message indicators
SUCCESS_INDICATORS = [
    "thank you",
    "thanks for",
    "successfully",
    "success",
    "submitted",
    "received your",
    "we'll get back",
    "we will get back",
    "confirmation",
    "message sent",
    "form submitted",
    "inquiry received",
    "request received",
]

# Error message indicators
ERROR_INDICATORS = [
    "error",
    "failed",
    "invalid",
    "required",
    "please enter",
    "please provide",
    "must be",
    "cannot be",
    "wrong",
    "incorrect",
]

# Submit button selectors
SUBMIT_BUTTON_SELECTORS = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("send")',
    'button:has-text("submit")',
    'button:has-text("contact")',
    'button:has-text("get in touch")',
    'button:has-text("send message")',
    'button:has-text("send inquiry")',
    'button[aria-label*="submit" i]',
    'button[aria-label*="send" i]',
]

# Email regex pattern
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# URL regex pattern
URL_REGEX = r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"

# Phone regex pattern
PHONE_REGEX = r"^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$"

# Maximum retries for various operations
MAX_NAVIGATION_RETRIES = 3
MAX_FORM_SUBMISSION_RETRIES = 2
MAX_CAPTCHA_SOLVE_RETRIES = 3

# Timeout values (in milliseconds)
NAVIGATION_TIMEOUT = 30000
FORM_FILL_TIMEOUT = 10000
SUBMIT_TIMEOUT = 15000
SUCCESS_CHECK_TIMEOUT = 5000

# Rate limiting
DEFAULT_RATE_LIMIT = 60  # requests per minute
BURST_RATE_LIMIT = 100  # burst allowance

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# File upload limits
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".txt"}

# Campaign status values
CAMPAIGN_STATUS_VALUES = ["DRAFT", "ACTIVE", "PAUSED", "COMPLETED", "FAILED"]

# Submission status values
SUBMISSION_STATUS_VALUES = ["pending", "processing", "success", "failed", "skipped"]
