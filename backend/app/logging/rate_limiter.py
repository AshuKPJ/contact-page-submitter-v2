# app/logging/rate_limiter.py
"""
Enhanced rate limiting for logs
Provides multiple rate limiting algorithms and strategies
"""
import time
import threading
from typing import Dict, Optional, Tuple, Any, List
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import heapq


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""

    burst: int = 100  # Maximum burst size
    rate: float = 10.0  # Events per second
    window_size: int = 60  # Window size in seconds for sliding window
    strategy: str = "token_bucket"  # Algorithm to use


class TokenBucket:
    """
    Token bucket algorithm for rate limiting
    Allows burst traffic while maintaining average rate
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket

        Args:
            capacity: Maximum number of tokens (burst size)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = threading.Lock()

        # Statistics
        self.total_requests = 0
        self.allowed_requests = 0
        self.denied_requests = 0

    def allow(self, cost: float = 1.0) -> bool:
        """
        Check if request is allowed

        Args:
            cost: Number of tokens required

        Returns:
            True if request is allowed, False otherwise
        """
        with self.lock:
            now = time.time()

            # Refill tokens based on time passed
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now

            self.total_requests += 1

            # Check if we have enough tokens
            if self.tokens >= cost:
                self.tokens -= cost
                self.allowed_requests += 1
                return True

            self.denied_requests += 1
            return False

    def reset(self) -> None:
        """Reset the bucket to full capacity"""
        with self.lock:
            self.tokens = float(self.capacity)
            self.last_refill = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get bucket statistics"""
        with self.lock:
            return {
                "capacity": self.capacity,
                "current_tokens": self.tokens,
                "refill_rate": self.refill_rate,
                "total_requests": self.total_requests,
                "allowed_requests": self.allowed_requests,
                "denied_requests": self.denied_requests,
                "denial_rate": (
                    (self.denied_requests / self.total_requests * 100)
                    if self.total_requests > 0
                    else 0
                ),
            }


class SlidingWindowLog:
    """
    Sliding window log algorithm for rate limiting
    More precise than token bucket but uses more memory
    """

    def __init__(self, max_requests: int, window_size: int):
        """
        Initialize sliding window log

        Args:
            max_requests: Maximum requests in the window
            window_size: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests: List[float] = []
        self.lock = threading.Lock()

        # Statistics
        self.total_requests = 0
        self.allowed_requests = 0
        self.denied_requests = 0

    def allow(self) -> bool:
        """Check if request is allowed"""
        with self.lock:
            now = time.time()
            cutoff = now - self.window_size

            # Remove old requests outside the window
            self.requests = [t for t in self.requests if t > cutoff]

            self.total_requests += 1

            # Check if we can allow this request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                self.allowed_requests += 1
                return True

            self.denied_requests += 1
            return False

    def reset(self) -> None:
        """Reset the window"""
        with self.lock:
            self.requests.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get window statistics"""
        with self.lock:
            return {
                "max_requests": self.max_requests,
                "window_size": self.window_size,
                "current_requests": len(self.requests),
                "total_requests": self.total_requests,
                "allowed_requests": self.allowed_requests,
                "denied_requests": self.denied_requests,
                "denial_rate": (
                    (self.denied_requests / self.total_requests * 100)
                    if self.total_requests > 0
                    else 0
                ),
            }


class LeakyBucket:
    """
    Leaky bucket algorithm for rate limiting
    Smooths out burst traffic
    """

    def __init__(self, capacity: int, leak_rate: float):
        """
        Initialize leaky bucket

        Args:
            capacity: Maximum bucket capacity
            leak_rate: Rate at which bucket leaks (requests per second)
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.water_level = 0.0
        self.last_leak = time.time()
        self.lock = threading.Lock()

        # Statistics
        self.total_requests = 0
        self.allowed_requests = 0
        self.denied_requests = 0

    def allow(self, amount: float = 1.0) -> bool:
        """Check if request is allowed"""
        with self.lock:
            now = time.time()

            # Leak water based on time passed
            time_passed = now - self.last_leak
            leaked = time_passed * self.leak_rate
            self.water_level = max(0, self.water_level - leaked)
            self.last_leak = now

            self.total_requests += 1

            # Check if we can add more water
            if self.water_level + amount <= self.capacity:
                self.water_level += amount
                self.allowed_requests += 1
                return True

            self.denied_requests += 1
            return False

    def reset(self) -> None:
        """Reset the bucket"""
        with self.lock:
            self.water_level = 0.0
            self.last_leak = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get bucket statistics"""
        with self.lock:
            return {
                "capacity": self.capacity,
                "current_level": self.water_level,
                "leak_rate": self.leak_rate,
                "total_requests": self.total_requests,
                "allowed_requests": self.allowed_requests,
                "denied_requests": self.denied_requests,
                "denial_rate": (
                    (self.denied_requests / self.total_requests * 100)
                    if self.total_requests > 0
                    else 0
                ),
            }


class RateLimiter:
    """
    Main rate limiter class supporting multiple algorithms
    Manages rate limiting for different keys (e.g., user IDs, IPs)
    """

    def __init__(
        self,
        burst: int = 100,
        rate: float = 10.0,
        window_size: int = 60,
        strategy: str = "token_bucket",
        cleanup_interval: int = 300,
    ):
        """
        Initialize rate limiter

        Args:
            burst: Maximum burst size
            rate: Rate limit (events per second)
            window_size: Window size for sliding window algorithm
            strategy: Algorithm to use ("token_bucket", "sliding_window", "leaky_bucket")
            cleanup_interval: Seconds between cleanup of old limiters
        """
        self.burst = burst
        self.rate = rate
        self.window_size = window_size
        self.strategy = strategy
        self.cleanup_interval = cleanup_interval

        # Store limiters by key
        self._limiters: Dict[str, Any] = {}
        self._last_access: Dict[str, float] = {}
        self._lock = threading.Lock()

        # Statistics
        self._total_checks = 0
        self._total_allowed = 0
        self._total_denied = 0

        # Start cleanup thread
        self._start_cleanup()

    def _create_limiter(self) -> Any:
        """Create a new limiter based on strategy"""
        if self.strategy == "token_bucket":
            return TokenBucket(self.burst, self.rate)
        elif self.strategy == "sliding_window":
            max_requests = int(self.rate * self.window_size)
            return SlidingWindowLog(max_requests, self.window_size)
        elif self.strategy == "leaky_bucket":
            return LeakyBucket(self.burst, self.rate)
        else:
            # Default to token bucket
            return TokenBucket(self.burst, self.rate)

    def _start_cleanup(self) -> None:
        """Start background cleanup thread"""

        def cleanup():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_old_limiters()

        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()

    def _cleanup_old_limiters(self) -> None:
        """Remove limiters that haven't been used recently"""
        with self._lock:
            now = time.time()
            cutoff = now - (self.cleanup_interval * 2)

            keys_to_remove = [
                key
                for key, last_access in self._last_access.items()
                if last_access < cutoff
            ]

            for key in keys_to_remove:
                del self._limiters[key]
                del self._last_access[key]

    def allow(self, key: str, cost: float = 1.0) -> bool:
        """
        Check if request is allowed for given key

        Args:
            key: Identifier for rate limiting (e.g., user ID, IP)
            cost: Cost of the request (for token/leaky bucket)

        Returns:
            True if request is allowed, False otherwise
        """
        with self._lock:
            self._total_checks += 1

            # Get or create limiter for this key
            if key not in self._limiters:
                self._limiters[key] = self._create_limiter()

            limiter = self._limiters[key]
            self._last_access[key] = time.time()

            # Check with appropriate method based on limiter type
            if hasattr(limiter, "allow"):
                if self.strategy in ["token_bucket", "leaky_bucket"]:
                    allowed = limiter.allow(cost)
                else:
                    allowed = limiter.allow()
            else:
                allowed = False

            if allowed:
                self._total_allowed += 1
            else:
                self._total_denied += 1

            return allowed

    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset rate limiter for specific key or all keys

        Args:
            key: Key to reset, or None to reset all
        """
        with self._lock:
            if key:
                if key in self._limiters:
                    self._limiters[key].reset()
            else:
                for limiter in self._limiters.values():
                    limiter.reset()

    def get_stats(self, key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for a specific key or overall

        Args:
            key: Key to get stats for, or None for overall stats

        Returns:
            Dictionary containing statistics
        """
        with self._lock:
            if key and key in self._limiters:
                return self._limiters[key].get_stats()

            # Return overall stats
            return {
                "strategy": self.strategy,
                "burst": self.burst,
                "rate": self.rate,
                "window_size": self.window_size,
                "active_limiters": len(self._limiters),
                "total_checks": self._total_checks,
                "total_allowed": self._total_allowed,
                "total_denied": self._total_denied,
                "overall_denial_rate": (
                    (self._total_denied / self._total_checks * 100)
                    if self._total_checks > 0
                    else 0
                ),
            }

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all active limiters"""
        with self._lock:
            stats = {"overall": self.get_stats(), "limiters": {}}

            for key, limiter in self._limiters.items():
                stats["limiters"][key] = limiter.get_stats()

            return stats
