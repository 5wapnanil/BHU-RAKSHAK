"""Tests for BhuRakshak AI Assistant in-memory rate limiter and rate limit policies.

Verifies:
1. Exact policy limits: 5 threads/hr/IP and 10 queries/min/session.
2. Sliding-window enforcement and HTTP 429 Retry-After response.
3. Multi-session and multi-IP isolation.
4. Window reset and timestamp expiration.
"""

import time
import unittest
from fastapi import HTTPException, status

from backend.app.api.deps import InMemoryRateLimiter
from backend.app.api.endpoints.assistant import (
    THREAD_CREATION_RATE_LIMIT_REQUESTS,
    THREAD_CREATION_RATE_LIMIT_WINDOW_SECONDS,
    QUERY_RATE_LIMIT_REQUESTS,
    QUERY_RATE_LIMIT_WINDOW_SECONDS,
)


class TestRateLimiterPolicies(unittest.TestCase):
    """Verify rate limit constants and invariants approved in architecture."""

    def test_rate_limit_policy_constants(self):
        """Confirm thread creation is 5 req/hr and queries are 10 req/min."""
        self.assertEqual(THREAD_CREATION_RATE_LIMIT_REQUESTS, 5)
        self.assertEqual(THREAD_CREATION_RATE_LIMIT_WINDOW_SECONDS, 3600)  # 1 hour
        self.assertEqual(QUERY_RATE_LIMIT_REQUESTS, 10)
        self.assertEqual(QUERY_RATE_LIMIT_WINDOW_SECONDS, 60)  # 1 minute


class TestInMemoryRateLimiter(unittest.TestCase):
    """Verify behavior of the thread-safe InMemoryRateLimiter sliding window."""

    def setUp(self):
        self.limiter = InMemoryRateLimiter()

    def test_query_rate_limiter_allows_up_to_limit(self):
        """Verify exactly 10 requests are allowed in a 60-second window."""
        key = "queries:session:sess-test-allow"
        for i in range(10):
            # Should not raise
            self.limiter.check_rate_limit(
                key=key,
                max_requests=10,
                window_seconds=60,
            )

    def test_query_rate_limiter_blocks_11th_request_with_429(self):
        """Verify the 11th request triggers HTTP 429 with Retry-After header."""
        key = "queries:session:sess-test-block"
        for i in range(10):
            self.limiter.check_rate_limit(
                key=key,
                max_requests=10,
                window_seconds=60,
            )

        with self.assertRaises(HTTPException) as ctx:
            self.limiter.check_rate_limit(
                key=key,
                max_requests=10,
                window_seconds=60,
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Rate limit exceeded", exc.detail)
        self.assertIn("10 requests per 60 seconds", exc.detail)
        self.assertIn("Retry-After", exc.headers)
        retry_after = int(exc.headers["Retry-After"])
        self.assertGreaterEqual(retry_after, 1)
        self.assertLessEqual(retry_after, 61)

    def test_thread_creation_rate_limiter_blocks_6th_request(self):
        """Verify thread creation allows 5 requests and blocks the 6th with HTTP 429."""
        key = "threads:ip:198.51.100.1"
        for i in range(5):
            self.limiter.check_rate_limit(
                key=key,
                max_requests=5,
                window_seconds=3600,
            )

        with self.assertRaises(HTTPException) as ctx:
            self.limiter.check_rate_limit(
                key=key,
                max_requests=5,
                window_seconds=3600,
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("5 requests per 3600 seconds", exc.detail)

    def test_rate_limiter_isolates_different_keys(self):
        """Verify hitting the limit on session A does not affect session B or IP B."""
        key_a = "queries:session:session-alpha"
        key_b = "queries:session:session-beta"

        # Saturate key A
        for _ in range(10):
            self.limiter.check_rate_limit(key=key_a, max_requests=10, window_seconds=60)

        # Key A is now blocked
        with self.assertRaises(HTTPException):
            self.limiter.check_rate_limit(key=key_a, max_requests=10, window_seconds=60)

        # Key B is completely unaffected
        for _ in range(10):
            self.limiter.check_rate_limit(key=key_b, max_requests=10, window_seconds=60)

    def test_rate_limiter_clear_resets_counters(self):
        """Verify clear() empties all windows, allowing subsequent requests immediately."""
        key = "queries:session:session-reset"
        for _ in range(10):
            self.limiter.check_rate_limit(key=key, max_requests=10, window_seconds=60)

        # Blocked
        with self.assertRaises(HTTPException):
            self.limiter.check_rate_limit(key=key, max_requests=10, window_seconds=60)

        # Reset
        self.limiter.clear()

        # Allowed again
        self.limiter.check_rate_limit(key=key, max_requests=10, window_seconds=60)

    def test_rate_limiter_sliding_window_expiration(self):
        """Verify old requests outside the sliding window roll off and allow new requests."""
        key = "queries:session:session-expire"
        now = time.time()

        # Artificially inject 10 timestamps that occurred 65 seconds ago
        with self.limiter._lock:
            for _ in range(10):
                self.limiter._windows[key].append(now - 65)

        # A new request should succeed because the older requests are pruned
        self.limiter.check_rate_limit(key=key, max_requests=10, window_seconds=60)
        with self.limiter._lock:
            # 10 expired requests were pruned, 1 current request remains
            self.assertEqual(len(self.limiter._windows[key]), 1)


if __name__ == "__main__":
    unittest.main()
