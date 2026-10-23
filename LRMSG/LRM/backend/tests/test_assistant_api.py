"""Integration and security route test suite for Backboard Assistant API (Phase 2, Milestone 3).

Covers:
- POST /api/assistant/threads in cookie transport mode (HttpOnly, scoped, no token in JSON)
- POST /api/assistant/threads in bearer transport mode (token in JSON, no cookie)
- CSRF and Origin header validation for cookie-authenticated requests
- Authorization header Bearer token transport
- Rate limiting on thread creation (5 requests/hour/IP)
- Rate limiting on queries (10 requests/min/session)
- Input validation (min_length=2, max_length=1000)
- Session error handling (401 on missing, tampered, expired tokens)
- Upstream AI service error handling (502 on auth failure, 200 fallback on timeout/unavailable)
- Complete absence of secrets and raw Backboard thread IDs in client responses
- Guarantee that invalid sessions never dispatch provider queries
- Baseline regression check ensuring unrelated endpoints (/health) are unaffected
"""

import time
import unittest

from fastapi.testclient import TestClient

from backend.app.api.deps import (
    assistant_rate_limiter,
    get_assistant_rate_limiter,
    get_backboard_service,
)
from backend.app.main import app
from backend.app.services.backboard import (
    BackboardMessageOutput,
    MockBackboardProvider,
    RetrievedDocument,
)
from backend.app.services.backboard_service import BackboardService

TEST_SIGNING_KEY: str = "test-assistant-api-secret-key-32chars-min-abcdef"


class TestAssistantApiEndpoints(unittest.TestCase):
    """Route integration tests for assistant API endpoints."""

    def setUp(self):
        # Reset in-memory rate limiter windows before each test
        assistant_rate_limiter.clear()

        # Instantiate dedicated mock provider and service
        self.mock_provider = MockBackboardProvider(mode="success")
        self.service = BackboardService(
            provider=self.mock_provider,
            signing_key=TEST_SIGNING_KEY,
            session_expiry_seconds=3600,
            is_production=False,
        )

        # Override FastAPI dependencies for deterministic test execution
        app.dependency_overrides[get_backboard_service] = lambda: self.service
        app.dependency_overrides[get_assistant_rate_limiter] = lambda: assistant_rate_limiter

        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        assistant_rate_limiter.clear()

    # -----------------------------------------------------------------
    # Thread Initialization Endpoint (POST /api/assistant/threads)
    # -----------------------------------------------------------------

    def test_create_thread_cookie_mode_default(self):
        """Default thread creation sets HttpOnly cookie and omits token from body."""
        res = self.client.post(
            "/api/assistant/threads",
            headers={"Origin": "http://localhost:3000"},
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["transport"], "cookie")
        self.assertIn("expires_at", data)
        self.assertIsNone(data["session_token"])

        # Check Set-Cookie
        self.assertIn("pp_assistant_session", res.cookies)
        cookie_header = res.headers.get("set-cookie", "")
        self.assertIn("pp_assistant_session=", cookie_header)
        self.assertIn("HttpOnly", cookie_header)
        self.assertIn("Path=/api/assistant", cookie_header)
        self.assertIn("samesite=lax", cookie_header.lower())

    def test_create_thread_bearer_mode(self):
        """Native mobile bearer mode returns session_token in body and sets no cookie."""
        res = self.client.post("/api/assistant/threads?transport=bearer")
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["transport"], "bearer")
        self.assertIn("expires_at", data)
        self.assertIsNotNone(data["session_token"])
        self.assertIn(".", data["session_token"])

        # Confirm no cookie was attached
        self.assertNotIn("pp_assistant_session", res.cookies)

    def test_create_thread_rate_limiting(self):
        """Rate limit enforces maximum 5 thread creations per hour per client IP."""
        for i in range(5):
            res = self.client.post(
                "/api/assistant/threads?transport=bearer",
                headers={"X-Forwarded-For": "198.51.100.22"},
            )
            self.assertEqual(res.status_code, 201, f"Failed at call {i+1}")

        # 6th call must be blocked with HTTP 429
        blocked_res = self.client.post(
            "/api/assistant/threads?transport=bearer",
            headers={"X-Forwarded-For": "198.51.100.22"},
        )
        self.assertEqual(blocked_res.status_code, 429)
        self.assertIn("Rate limit exceeded", blocked_res.json()["detail"])
        self.assertIn("Retry-After", blocked_res.headers)

    def test_create_thread_untrusted_origin_rejected(self):
        """Cookie transport rejects untrusted origin during thread creation."""
        res = self.client.post(
            "/api/assistant/threads?transport=cookie",
            headers={"Origin": "https://malicious-phishing-site.example"},
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Forbidden", res.json()["detail"])

    # -----------------------------------------------------------------
    # Query Endpoint (POST /api/assistant/query)
    # -----------------------------------------------------------------

    def test_query_missing_session_unauthorized(self):
        """Query without cookie or Bearer header returns HTTP 401."""
        res = self.client.post(
            "/api/assistant/query",
            json={"query": "What are early warning signs?"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("Authentication required", res.json()["detail"])

    def test_query_bearer_mode_success(self):
        """Native mobile client queries with Authorization: Bearer <token>."""
        create_res = self.client.post("/api/assistant/threads?transport=bearer")
        token = create_res.json()["session_token"]

        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What are early warning signs before a landslide?"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["fallback_mode"])
        self.assertIn("tension cracks", data["reply"].lower())
        self.assertIn("PahaarPulse Assistant provides general educational", data["disclaimer"])
        self.assertGreaterEqual(len(data["sources"]), 1)
        self.assertEqual(data["sources"][0]["document_id"], "DOC-SIM-02")
        self.assertTrue(data["sources"][0]["is_curated"])

    def test_query_cookie_mode_success_with_trusted_origin(self):
        """Web browser queries with HttpOnly cookie and trusted Origin header."""
        # Create web session
        create_res = self.client.post(
            "/api/assistant/threads?transport=cookie",
            headers={"Origin": "http://localhost:3000"},
        )
        cookie_val = create_res.cookies["pp_assistant_session"]

        # Send query with cookie and Origin
        res = self.client.post(
            "/api/assistant/query",
            headers={
                "Origin": "http://localhost:3000",
                "Cookie": f"pp_assistant_session={cookie_val}",
            },
            json={"query": "Why does monsoon rainfall matter for slope stability?"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("pore water pressure", data["reply"].lower())

    def test_query_cookie_mode_untrusted_origin_forbidden(self):
        """Web cookie query with untrusted Origin header is rejected with HTTP 403."""
        create_res = self.client.post("/api/assistant/threads?transport=cookie")
        cookie_val = create_res.cookies["pp_assistant_session"]

        res = self.client.post(
            "/api/assistant/query",
            headers={
                "Origin": "http://untrusted-site.com",
                "Cookie": f"pp_assistant_session={cookie_val}",
            },
            json={"query": "Can we evacuate right now?"},
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Untrusted or missing request origin", res.json()["detail"])

    def test_query_cookie_mode_missing_origin_forbidden(self):
        """Web cookie query without Origin or Referer is rejected with HTTP 403."""
        create_res = self.client.post("/api/assistant/threads?transport=cookie")
        cookie_val = create_res.cookies["pp_assistant_session"]

        res = self.client.post(
            "/api/assistant/query",
            headers={"Cookie": f"pp_assistant_session={cookie_val}"},
            json={"query": "Can we evacuate right now?"},
        )
        self.assertEqual(res.status_code, 403)

    def test_query_tampered_token_unauthorized(self):
        """Query with tampered session signature returns HTTP 401."""
        create_res = self.client.post("/api/assistant/threads?transport=bearer")
        token = create_res.json()["session_token"]
        tampered = token[:-4] + "ZZZZ"

        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {tampered}"},
            json={"query": "What are early warning signs?"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid or tampered", res.json()["detail"])

    def test_query_expired_token_unauthorized(self):
        """Query with expired session token returns HTTP 401."""
        expired_service = BackboardService(
            provider=self.mock_provider,
            signing_key=TEST_SIGNING_KEY,
            session_expiry_seconds=-10,
            is_production=False,
        )
        app.dependency_overrides[get_backboard_service] = lambda: expired_service

        expired_token = expired_service.create_session_token("mock-thread-uuid-1234")

        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={"query": "What are early warning signs?"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("has expired", res.json()["detail"])

    def test_query_rate_limiting_per_session(self):
        """Enforces maximum 10 queries per minute per verified session."""
        create_res = self.client.post("/api/assistant/threads?transport=bearer")
        token = create_res.json()["session_token"]

        for i in range(10):
            res = self.client.post(
                "/api/assistant/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": f"Question number {i+1} regarding slope mechanics?"},
            )
            self.assertEqual(res.status_code, 200, f"Query {i+1} failed")

        # 11th query within the minute must be blocked
        blocked_res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "Excess question exceeding quota?"},
        )
        self.assertEqual(blocked_res.status_code, 429)
        self.assertIn("Rate limit exceeded", blocked_res.json()["detail"])
        self.assertIn("Retry-After", blocked_res.headers)

    def test_query_input_validation(self):
        create_res = self.client.post("/api/assistant/threads?transport=bearer")
        token = create_res.json()["session_token"]

        # Query too short (< 2 chars)
        res_short = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "a"},
        )
        self.assertEqual(res_short.status_code, 422)

        # Query too long (> 1000 chars)
        res_long = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "x" * 1001},
        )
        self.assertEqual(res_long.status_code, 422)

    def test_create_thread_provider_timeout_maps_to_504(self):
        """When provider times out during thread creation, returns HTTP 504."""
        timeout_provider = MockBackboardProvider(mode="timeout")
        service = BackboardService(
            provider=timeout_provider,
            signing_key=TEST_SIGNING_KEY,
            is_production=False,
        )
        app.dependency_overrides[get_backboard_service] = lambda: service

        res = self.client.post("/api/assistant/threads?transport=bearer")
        self.assertEqual(res.status_code, 504)
        self.assertIn("timed out during thread creation", res.json()["detail"])

    def test_create_thread_provider_unavailable_maps_to_503(self):
        """When provider is unavailable during thread creation, returns HTTP 503."""
        unavail_provider = MockBackboardProvider(mode="unavailable")
        service = BackboardService(
            provider=unavail_provider,
            signing_key=TEST_SIGNING_KEY,
            is_production=False,
        )
        app.dependency_overrides[get_backboard_service] = lambda: service

        res = self.client.post("/api/assistant/threads?transport=bearer")
        self.assertEqual(res.status_code, 503)
        self.assertIn("temporarily unavailable", res.json()["detail"])

    def test_query_provider_timeout_returns_safety_fallback(self):
        """When provider times out during query, returns 200 with fallback_mode=True and safety guidance."""
        # Pre-create valid session token
        token = self.service.create_session_token("mock-thread-uuid-1234")

        # Inject timeout provider for query processing
        timeout_provider = MockBackboardProvider(mode="timeout")
        service = BackboardService(
            provider=timeout_provider,
            signing_key=TEST_SIGNING_KEY,
            is_production=False,
        )
        app.dependency_overrides[get_backboard_service] = lambda: service

        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What should we do right now?"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["fallback_mode"])
        self.assertIn("offline fallback mode", data["reply"])
        self.assertIn("evacuate immediately", data["reply"].lower())

    def test_query_provider_unavailable_returns_safety_fallback(self):
        """When provider is unavailable (503) during query, returns 200 with fallback_mode=True."""
        # Pre-create valid session token
        token = self.service.create_session_token("mock-thread-uuid-1234")

        unavail_provider = MockBackboardProvider(mode="unavailable")
        service = BackboardService(
            provider=unavail_provider,
            signing_key=TEST_SIGNING_KEY,
            is_production=False,
        )
        app.dependency_overrides[get_backboard_service] = lambda: service

        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What should we do?"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["fallback_mode"])


    def test_query_provider_auth_error_maps_to_502(self):
        """When provider has authentication failure, returns HTTP 502 Bad Gateway."""
        auth_err_provider = MockBackboardProvider(mode="auth_error")
        service = BackboardService(
            provider=auth_err_provider,
            signing_key=TEST_SIGNING_KEY,
            is_production=False,
        )
        app.dependency_overrides[get_backboard_service] = lambda: service

        # Pre-create token with working service
        token = self.service.create_session_token("mock-thread-uuid-1234")

        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What are warning signs?"},
        )
        self.assertEqual(res.status_code, 502)
        self.assertIn("Upstream AI knowledge service authentication failure", res.json()["detail"])

    def test_zero_leakage_of_secrets_and_raw_thread_ids(self):
        """Verify raw thread IDs, API keys, and signing keys never appear in client responses."""
        raw_thread = "super-secret-raw-thread-id-xyz-987"
        token = self.service.create_session_token(raw_thread)

        # 1. Successful query
        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What are warning signs of slope failure?"},
        )
        self.assertEqual(res.status_code, 200)
        res_text = res.text
        self.assertNotIn(raw_thread, res_text)
        self.assertNotIn(TEST_SIGNING_KEY, res_text)

        # 2. Tampered token error
        tampered_res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token[:-4]}AAAA"},
            json={"query": "What are warning signs of slope failure?"},
        )
        self.assertEqual(tampered_res.status_code, 401)
        self.assertNotIn(raw_thread, tampered_res.text)
        self.assertNotIn(TEST_SIGNING_KEY, tampered_res.text)

    def test_invalid_session_never_calls_provider(self):
        """Verify provider is never dispatched when session validation fails."""
        initial_calls = self.mock_provider.call_count
        tampered_token = "invalid.token.signature"

        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {tampered_token}"},
            json={"query": "What are warning signs?"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(self.mock_provider.call_count, initial_calls)

    def test_unrelated_endpoints_remain_unaffected(self):
        """Ensure baseline endpoints like /health continue responding normally."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")

    def test_query_rejects_client_supplied_thread_or_assistant_id(self):
        """Query schema forbids extra fields like thread_id or assistant_id with HTTP 422."""
        create_res = self.client.post("/api/assistant/threads?transport=bearer")
        token = create_res.json()["session_token"]

        # Attempt to inject client-controlled thread_id
        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What are warning signs?", "thread_id": "malicious-injected-thread-id"},
        )
        self.assertEqual(res.status_code, 422)

        # Attempt to inject client-controlled assistant_id
        res2 = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What are warning signs?", "assistant_id": "malicious-injected-assistant-id"},
        )
        self.assertEqual(res2.status_code, 422)

    def test_query_failed_upstream_generation_returns_fallback_response(self):
        """When upstream returns status='FAILED', query endpoint returns safety fallback response."""
        create_res = self.client.post("/api/assistant/threads?transport=bearer")
        token = create_res.json()["session_token"]

        # Configure mock provider to return status="FAILED"
        async def mock_failed_send(*args, **kwargs):
            return BackboardMessageOutput(
                content="Credit limit exhausted.",
                thread_id="th-failed",
                assistant_id="asst-1",
                status="FAILED",
            )
        self.mock_provider.send_message = mock_failed_send

        res = self.client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What should people do during heavy rainfall?"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["fallback_mode"])
        self.assertIn("offline fallback mode", data["reply"])
        self.assertIn("Community Landslide Safety", data["sources"][0]["title"])


if __name__ == "__main__":
    unittest.main()
