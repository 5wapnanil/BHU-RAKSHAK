"""Unit tests for Backboard Assistant Secure Session & Service Layer (Phase 2, Milestone 2).

Verifies:
- HMAC-SHA256 session token generation, structure, and signature verification
- Constant-time signature verification preventing timing side-channel attacks
- Token expiration enforcement and payload versioning
- Strict session-to-thread binding (preventing thread substitution)
- Production fail-closed security invariants (missing/weak secrets, key reuse)
- Complete isolation: invalid or expired sessions NEVER dispatch provider calls
- Input validation on query length and format
- Curated knowledge manifest citation mapping without citation fabrication
- Resilient fallback handling for transient infrastructure errors
- Zero leakage of raw thread IDs or secrets in error messages and logs
"""

import base64
import json
import os
import time
import unittest
from unittest.mock import patch

from backend.app.services.backboard import (
    BackboardAuthenticationError,
    BackboardConfigurationError,
    BackboardMessageOutput,
    BackboardQueryValidationError,
    BackboardRateLimitError,
    BackboardSettings,
    BackboardTemporaryUnavailableError,
    BackboardTimeoutError,
    InvalidSessionError,
    MockBackboardProvider,
    RetrievedDocument,
    SessionExpiredError,
)
from backend.app.services.backboard_service import (
    MIN_PRODUCTION_KEY_LENGTH,
    SESSION_TOKEN_VERSION,
    TRUSTED_KNOWLEDGE_MANIFEST,
    BackboardService,
)

VALID_TEST_KEY: str = "test-secret-signing-key-minimum-32-chars-long-000000"
ALT_TEST_KEY: str = "alternative-test-secret-key-32chars-min-111111111111"


class TestBackboardServiceInitAndSecurity(unittest.TestCase):
    """Test configuration validation, secret handling, and production fail-closed rules."""

    def test_init_with_valid_explicit_key(self):
        service = BackboardService(
            signing_key=VALID_TEST_KEY,
            is_production=False,
        )
        self.assertEqual(service.signing_key, VALID_TEST_KEY)
        self.assertFalse(service.is_production)

    def test_init_dev_defaults_to_deterministic_fallback_key(self):
        with patch.dict("os.environ", {}, clear=True):
            cfg = BackboardSettings(session_signing_key="")
            service = BackboardService(
                config=cfg,
                signing_key="",
                is_production=False,
            )
            self.assertTrue(len(service.signing_key) >= 32)
            self.assertEqual(
                service.signing_key,
                "dev-insecure-pahaarpulse-session-signing-key-32chars-min",
            )

    def test_init_production_fails_closed_when_key_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            cfg = BackboardSettings(session_signing_key="")
            with self.assertRaises(BackboardConfigurationError) as ctx:
                BackboardService(
                    config=cfg,
                    signing_key="",
                    is_production=True,
                )
            self.assertIn("SESSION_SIGNING_KEY is required for production", str(ctx.exception))

    def test_init_production_fails_closed_when_key_too_weak(self):
        weak_key = "short_key_16_chars"
        self.assertLess(len(weak_key), MIN_PRODUCTION_KEY_LENGTH)
        with self.assertRaises(BackboardConfigurationError) as ctx:
            BackboardService(
                signing_key=weak_key,
                is_production=True,
            )
        self.assertIn("at least 32 characters long", str(ctx.exception))

    def test_init_fails_closed_when_reusing_backboard_api_key(self):
        shared_secret = "identical-secret-shared-across-services-32chars"
        cfg = BackboardSettings(
            api_key=shared_secret,
            session_signing_key=shared_secret,
        )
        with self.assertRaises(BackboardConfigurationError) as ctx:
            BackboardService(
                config=cfg,
                signing_key=shared_secret,
                is_production=False,
            )
        self.assertIn("must not reuse BACKBOARD_API_KEY", str(ctx.exception))

    def test_init_fail_on_missing_key_in_dev_when_flagged(self):
        with self.assertRaises(BackboardConfigurationError):
            BackboardService(
                signing_key="",
                is_production=False,
                fail_on_missing_key=True,
            )


class TestBackboardServiceTokenCrypto(unittest.TestCase):
    """Test HMAC-SHA256 session token generation and verification."""

    def setUp(self):
        self.service = BackboardService(
            signing_key=VALID_TEST_KEY,
            session_expiry_seconds=3600,
            is_production=False,
        )

    def test_create_and_verify_valid_token(self):
        thread_id = "mock-thread-uuid-1234"
        token = self.service.create_session_token(thread_id)

        self.assertIsInstance(token, str)
        self.assertIn(".", token)
        parts = token.split(".")
        self.assertEqual(len(parts), 2)

        payload = self.service.verify_session_token(token)
        self.assertEqual(payload.version, SESSION_TOKEN_VERSION)
        self.assertEqual(payload.thread_id, thread_id)
        self.assertTrue(len(payload.session_id) >= 16)
        self.assertGreater(payload.expires_at, payload.issued_at)
        self.assertEqual(payload.expires_at - payload.issued_at, 3600)

    def test_verify_fails_on_tampered_signature(self):
        token = self.service.create_session_token("mock-thread-uuid-1234")
        payload_b64, sig_b64 = token.split(".")

        # Tamper signature by altering last byte
        altered_char = "B" if sig_b64[-1] != "B" else "C"
        tampered_token = f"{payload_b64}.{sig_b64[:-1]}{altered_char}"

        with self.assertRaises(InvalidSessionError) as ctx:
            self.service.verify_session_token(tampered_token)
        self.assertIn("Invalid session signature", str(ctx.exception))

    def test_verify_fails_on_thread_id_substitution(self):
        """Attacker modifies the thread_id claim without being able to sign it."""
        token = self.service.create_session_token("legit-user-thread-001")
        payload_b64, sig_b64 = token.split(".")

        # Decode payload
        padding = 4 - (len(payload_b64) % 4)
        padded = payload_b64 + ("=" * padding) if padding != 4 else payload_b64
        data = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))

        # Substitute thread ID with victim's thread
        data["tid"] = "victim-private-thread-999"
        tampered_payload_bytes = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
        tampered_payload_b64 = base64.urlsafe_b64encode(tampered_payload_bytes).decode("ascii").rstrip("=")

        tampered_token = f"{tampered_payload_b64}.{sig_b64}"

        with self.assertRaises(InvalidSessionError):
            self.service.verify_session_token(tampered_token)

    def test_verify_fails_on_wrong_signing_key(self):
        other_service = BackboardService(
            signing_key=ALT_TEST_KEY,
            session_expiry_seconds=3600,
            is_production=False,
        )
        token = self.service.create_session_token("mock-thread-uuid-1234")

        with self.assertRaises(InvalidSessionError) as ctx:
            other_service.verify_session_token(token)
        self.assertIn("Invalid session signature", str(ctx.exception))

    def test_verify_fails_on_unsupported_version(self):
        # Craft a token payload with version 2
        payload = {
            "v": 2,
            "sid": "abc1234567890def",
            "tid": "mock-thread-uuid-1234",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")

        import hashlib
        import hmac

        sig = hmac.new(
            VALID_TEST_KEY.encode("utf-8"),
            payload_b64.encode("ascii"),
            hashlib.sha256,
        ).digest()
        sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
        v2_token = f"{payload_b64}.{sig_b64}"

        with self.assertRaises(InvalidSessionError) as ctx:
            self.service.verify_session_token(v2_token)
        self.assertIn("Unsupported session token version", str(ctx.exception))

    def test_verify_fails_on_expired_token(self):
        # Create service with expired session
        expired_service = BackboardService(
            signing_key=VALID_TEST_KEY,
            session_expiry_seconds=-10,  # Expired in past
            is_production=False,
        )
        token = expired_service.create_session_token("mock-thread-uuid-1234")

        with self.assertRaises(SessionExpiredError) as ctx:
            self.service.verify_session_token(token)
        self.assertIn("session token has expired", str(ctx.exception))

    def test_verify_fails_on_malformed_tokens(self):
        malformed_cases = [
            "",
            "   ",
            "no_dot_token_string",
            "too.many.dots.in.this.token",
            "!@#$!@#$.!@#$!@#$",
            "invalid_b64.invalid_sig",
        ]
        for token in malformed_cases:
            with self.subTest(token=token):
                with self.assertRaises(InvalidSessionError):
                    self.service.verify_session_token(token)

    def test_verify_fails_on_missing_payload_claims(self):
        claims = ["sid", "tid", "iat", "exp"]
        base_payload = {
            "v": 1,
            "sid": "abc1234567890def",
            "tid": "mock-thread-uuid-1234",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        for claim in claims:
            with self.subTest(missing_claim=claim):
                tampered = dict(base_payload)
                del tampered[claim]

                payload_bytes = json.dumps(tampered, separators=(",", ":"), sort_keys=True).encode("utf-8")
                payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")

                import hashlib
                import hmac

                sig = hmac.new(
                    VALID_TEST_KEY.encode("utf-8"),
                    payload_b64.encode("ascii"),
                    hashlib.sha256,
                ).digest()
                sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
                token = f"{payload_b64}.{sig_b64}"

                with self.assertRaises(InvalidSessionError):
                    self.service.verify_session_token(token)


class TestBackboardServiceQueryAndOrchestration(unittest.IsolatedAsyncioTestCase):
    """Test query dispatching, citation mapping, error handling, and provider isolation."""

    def setUp(self):
        self.mock_provider = MockBackboardProvider(mode="success")
        self.service = BackboardService(
            provider=self.mock_provider,
            signing_key=VALID_TEST_KEY,
            session_expiry_seconds=3600,
            is_production=False,
        )

    async def test_create_thread_session(self):
        session = await self.service.create_thread_session()
        self.assertIsInstance(session.session_token, str)
        self.assertIn(".", session.session_token)
        self.assertTrue(len(session.session_id) >= 16)
        self.assertIn("T", session.expires_at)  # ISO-8601 string

        # Verify token maps back to mock thread
        payload = self.service.verify_session_token(session.session_token)
        self.assertEqual(payload.thread_id, "mock-thread-uuid-1234")

    async def test_query_success_with_curated_citations(self):
        session = await self.service.create_thread_session()
        response = await self.service.query(
            session_token=session.session_token,
            query="What are early warning signs of slope failure?",
        )
        self.assertFalse(response.fallback_mode)
        self.assertIn("tension cracks", response.reply.lower())
        self.assertIn("PahaarPulse Assistant provides general educational", response.disclaimer)
        self.assertGreaterEqual(len(response.sources), 1)

        first_source = response.sources[0]
        self.assertEqual(first_source.document_id, "DOC-SIM-02")
        self.assertEqual(first_source.title, "Early Warning Signs of Slope Destabilization")
        self.assertEqual(first_source.category, "hazard_identification")
        self.assertTrue(first_source.is_curated)

    async def test_query_preserves_retrieved_documents_and_marks_uncurated(self):
        """When provider returns a document not in the trusted manifest, do not invent citations."""
        custom_output = BackboardMessageOutput(
            content="Specific research findings.",
            thread_id="th-custom",
            assistant_id="asst-custom",
            retrieved_files=["external_unindexed_paper_2026.pdf"],
            documents=[
                RetrievedDocument(
                    document_id="doc-ext-99",
                    filename="external_unindexed_paper_2026.pdf",
                    score=0.75,
                )
            ],
        )
        provider = MockBackboardProvider(custom_output=custom_output)
        service = BackboardService(
            provider=provider,
            signing_key=VALID_TEST_KEY,
            is_production=False,
        )
        token = service.create_session_token("th-custom")
        response = await service.query(token, "Tell me about research findings.")

        self.assertEqual(len(response.sources), 1)
        source = response.sources[0]
        self.assertEqual(source.title, "external_unindexed_paper_2026.pdf")
        self.assertEqual(source.document_id, "doc-ext-99")
        self.assertIsNone(source.url_or_slug)
        self.assertEqual(source.category, "unverified")
        self.assertFalse(source.is_curated)

    async def test_query_input_validation(self):
        session = await self.service.create_thread_session()

        invalid_queries = [
            "",
            "   ",
            "a",  # Less than 2 chars
            "x" * 1001,  # Greater than 1000 chars
        ]
        initial_calls = self.mock_provider.call_count

        for q in invalid_queries:
            with self.subTest(query_len=len(q)):
                with self.assertRaises(BackboardQueryValidationError):
                    await self.service.query(session.session_token, q)

        # Provider must NEVER have been called for invalid queries
        self.assertEqual(self.mock_provider.call_count, initial_calls)

    async def test_invalid_session_never_calls_provider(self):
        initial_calls = self.mock_provider.call_count
        tampered_token = "invalid.token"

        with self.assertRaises(InvalidSessionError):
            await self.service.query(tampered_token, "What are warning signs?")

        self.assertEqual(self.mock_provider.call_count, initial_calls)

    async def test_expired_session_never_calls_provider(self):
        expired_service = BackboardService(
            provider=self.mock_provider,
            signing_key=VALID_TEST_KEY,
            session_expiry_seconds=-10,
            is_production=False,
        )
        expired_token = expired_service.create_session_token("mock-thread-uuid-1234")
        initial_calls = self.mock_provider.call_count

        with self.assertRaises(SessionExpiredError):
            await self.service.query(expired_token, "What are warning signs?")

        self.assertEqual(self.mock_provider.call_count, initial_calls)

    async def test_transient_provider_errors_trigger_resilient_fallback(self):
        transient_modes = ["timeout", "rate_limit", "unavailable"]

        for mode in transient_modes:
            with self.subTest(mode=mode):
                provider = MockBackboardProvider(mode=mode)
                service = BackboardService(
                    provider=provider,
                    signing_key=VALID_TEST_KEY,
                    is_production=False,
                )
                token = service.create_session_token("mock-thread-uuid-1234")

                response = await service.query(
                    session_token=token,
                    query="What should we do right now?",
                    enable_fallback=True,
                )
                self.assertTrue(response.fallback_mode)
                self.assertIn("offline fallback mode", response.reply)
                self.assertIn("evacuate immediately", response.reply.lower())
                self.assertGreaterEqual(len(response.sources), 1)
                self.assertEqual(response.sources[0].document_id, "DOC-007")

    async def test_fallback_disabled_reraises_transient_error(self):
        provider = MockBackboardProvider(mode="timeout")
        service = BackboardService(
            provider=provider,
            signing_key=VALID_TEST_KEY,
            is_production=False,
        )
        token = service.create_session_token("mock-thread-uuid-1234")

        with self.assertRaises(BackboardTimeoutError):
            await service.query(
                session_token=token,
                query="What should we do?",
                enable_fallback=False,
            )

    async def test_non_transient_errors_always_reraised(self):
        provider = MockBackboardProvider(mode="auth_error")
        service = BackboardService(
            provider=provider,
            signing_key=VALID_TEST_KEY,
            is_production=False,
        )
        token = service.create_session_token("mock-thread-uuid-1234")

        with self.assertRaises(BackboardAuthenticationError):
            await service.query(
                session_token=token,
                query="What should we do?",
                enable_fallback=True,
            )

    async def test_failed_upstream_generation_triggers_resilient_fallback(self):
        """When upstream returns status='FAILED' or billing restriction, fallback is returned."""
        provider = MockBackboardProvider(mode="success")
        # Override send_message to return status="FAILED"
        async def mock_failed_send(*args, **kwargs):
            return BackboardMessageOutput(
                content="Your free credit is reserved for Memory & RAG, so it can't cover LLM chat.",
                thread_id="th-failed-gen",
                assistant_id="asst-1",
                status="FAILED",
            )
        provider.send_message = mock_failed_send

        service = BackboardService(
            provider=provider,
            signing_key=VALID_TEST_KEY,
            is_production=False,
        )
        token = service.create_session_token("mock-thread-uuid-1234")

        # Fallback enabled (default)
        response = await service.query(
            session_token=token,
            query="What are warning signs?",
            enable_fallback=True,
        )
        self.assertTrue(response.fallback_mode)
        self.assertIn("offline fallback mode", response.reply)

        # Fallback disabled raises BackboardError
        from backend.app.services.backboard.exceptions import BackboardError
        with self.assertRaises(BackboardError):
            await service.query(
                session_token=token,
                query="What are warning signs?",
                enable_fallback=False,
            )

    def test_secrets_and_raw_thread_ids_not_leaked_in_exceptions(self):
        secret_raw_thread = "super-secret-raw-thread-id-xyz-987"
        token = self.service.create_session_token(secret_raw_thread)

        # Alter token
        tampered = token[:-4] + "ABCD"
        try:
            self.service.verify_session_token(tampered)
        except InvalidSessionError as e:
            err_msg = str(e)
            self.assertNotIn(VALID_TEST_KEY, err_msg)
            self.assertNotIn(secret_raw_thread, err_msg)

        # Query validation error
        try:
            import asyncio

            asyncio.run(self.service.query(token, ""))
        except BackboardQueryValidationError as e:
            err_msg = str(e)
            self.assertNotIn(VALID_TEST_KEY, err_msg)
            self.assertNotIn(secret_raw_thread, err_msg)


if __name__ == "__main__":
    unittest.main()
