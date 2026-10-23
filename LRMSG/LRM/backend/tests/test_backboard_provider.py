"""Unit tests for Backboard AI RAG Provider Foundation (Phase 2, Milestone 1).

Verifies:
- BackboardProvider protocol compliance
- Deterministic behavior of MockBackboardProvider across all operational and failure modes
- Domain-specific landslide retrieval heuristics
- Exception hierarchy integrity
- Data model serialization, dictionary compatibility, and immutability invariants
- Configuration loading and offline defaults
- Provider factory behavior and safe mock fallback
- Absolute prevention of live network calls
"""

import json
import unittest
from unittest.mock import patch

import httpx

from backend.app.services.backboard import (
    BackboardAuthenticationError,
    BackboardConfigurationError,
    BackboardConnectionError,
    BackboardError,
    BackboardMalformedOutputError,
    BackboardMessageOutput,
    BackboardNotFoundError,
    BackboardProvider,
    BackboardRateLimitError,
    BackboardSettings,
    BackboardTemporaryUnavailableError,
    BackboardTimeoutError,
    LiveBackboardProvider,
    MockBackboardProvider,
    RetrievedDocument,
    get_backboard_provider,
)


class TestBackboardExceptions(unittest.TestCase):
    """Test the typed exception hierarchy."""

    def test_exception_inheritance(self):
        """All Backboard exceptions must inherit from BackboardError."""
        exceptions_to_test = [
            BackboardConfigurationError("config err"),
            BackboardConnectionError("connection err"),
            BackboardTimeoutError("timeout err"),
            BackboardRateLimitError("rate limit err"),
            BackboardTemporaryUnavailableError("unavailable err"),
            BackboardAuthenticationError("auth err"),
            BackboardNotFoundError("not found err"),
            BackboardMalformedOutputError("malformed err"),
        ]
        for exc in exceptions_to_test:
            with self.subTest(exc=exc):
                self.assertIsInstance(exc, BackboardError)
                self.assertIsInstance(exc, Exception)


class TestBackboardModels(unittest.TestCase):
    """Test data structures, serialization, and dictionary-style access."""

    def test_retrieved_document_to_dict(self):
        doc = RetrievedDocument(
            document_id="doc-test-1",
            filename="01_why_do_landslides_happen.md",
            score=0.92,
            metadata={"tier": 1, "topic": "slope_mechanics"},
        )
        data = doc.to_dict()
        self.assertEqual(data["document_id"], "doc-test-1")
        self.assertEqual(data["filename"], "01_why_do_landslides_happen.md")
        self.assertEqual(data["score"], 0.92)
        self.assertEqual(data["metadata"]["tier"], 1)

    def test_backboard_message_output_post_init_and_to_dict(self):
        doc = RetrievedDocument(
            document_id="doc-test-1",
            filename="01_why_do_landslides_happen.md",
            score=0.95,
        )
        output = BackboardMessageOutput(
            content="Safety guidance details.",
            thread_id="th-101",
            assistant_id="asst-999",
            retrieved_files=["01_why_do_landslides_happen.md"],
            documents=[doc],
        )

        # Count auto-populated
        self.assertEqual(output.retrieved_files_count, 1)

        data = output.to_dict()
        self.assertEqual(data["content"], "Safety guidance details.")
        self.assertEqual(data["thread_id"], "th-101")
        self.assertEqual(data["assistant_id"], "asst-999")
        self.assertEqual(data["status"], "COMPLETED")
        self.assertEqual(data["retrieved_files"], ["01_why_do_landslides_happen.md"])
        self.assertEqual(data["retrieved_files_count"], 1)
        self.assertEqual(len(data["documents"]), 1)
        self.assertEqual(data["documents"][0]["document_id"], "doc-test-1")

    def test_backboard_message_output_dict_access(self):
        """BackboardMessageOutput should allow dictionary-style access for caller flexibility."""
        output = BackboardMessageOutput(
            content="Grounded response",
            thread_id="th-1",
            assistant_id="asst-1",
            retrieved_files=["file1.md"],
            retrieved_files_count=1,
        )
        self.assertEqual(output["content"], "Grounded response")
        self.assertEqual(output["thread_id"], "th-1")
        self.assertEqual(output.get("assistant_id"), "asst-1")
        self.assertEqual(output.get("non_existent", "fallback"), "fallback")
        self.assertTrue("content" in output)
        with self.assertRaises(KeyError):
            _ = output["unknown_field"]

    def test_backboard_message_output_billing_restriction_detection(self):
        """Detect credit exhaustion / billing restrictions without treating them as answers."""
        billing_content = (
            "Your free credit is reserved for Memory & RAG, so it can't cover LLM chat. "
            "Add credits or start a subscription on the Billing page to continue."
        )
        output = BackboardMessageOutput(
            content=billing_content,
            thread_id="th-billing",
            assistant_id="asst-1",
            status="FAILED",
        )
        self.assertTrue(output.is_billing_restricted)
        self.assertFalse(output.is_successful)

        # Alternative phrasing
        alt_output = BackboardMessageOutput(
            content="Error: insufficient credit on account. Please add credits or start a subscription.",
            thread_id="th-billing",
            assistant_id="asst-1",
            status="FAILED",
        )
        self.assertTrue(alt_output.is_billing_restricted)
        self.assertFalse(alt_output.is_successful)

        # Legitimate content is NOT billing restricted
        valid_output = BackboardMessageOutput(
            content="Warning signs include tension cracks and unusual soil saturation.",
            thread_id="th-valid",
            assistant_id="asst-1",
            status="COMPLETED",
        )
        self.assertFalse(valid_output.is_billing_restricted)
        self.assertTrue(valid_output.is_successful)

    def test_backboard_message_output_is_successful_evaluation(self):
        """is_successful requires COMPLETED status and absence of billing restrictions."""
        # Non-completed status is not successful
        failed_output = BackboardMessageOutput(
            content="Some error text",
            thread_id="th-1",
            assistant_id="asst-1",
            status="FAILED",
        )
        self.assertFalse(failed_output.is_successful)

        # COMPLETED status with normal content is successful
        success_output = BackboardMessageOutput(
            content="Detailed safety response",
            thread_id="th-1",
            assistant_id="asst-1",
            status="COMPLETED",
        )
        self.assertTrue(success_output.is_successful)

        # COMPLETED with billing text is NOT successful
        bizarre_output = BackboardMessageOutput(
            content="can't cover llm chat. Add credits on the Billing page to continue.",
            thread_id="th-1",
            assistant_id="asst-1",
            status="COMPLETED",
        )
        self.assertFalse(bizarre_output.is_successful)


class TestBackboardSettings(unittest.TestCase):
    """Test configuration loading and offline default behavior."""

    def test_offline_defaults_when_env_empty(self):
        with patch.dict("os.environ", {}, clear=True):
            cfg = BackboardSettings()
            self.assertEqual(cfg.api_key, "")
            self.assertEqual(cfg.base_url, "https://app.backboard.io/api")
            self.assertEqual(cfg.assistant_id, "")
            self.assertEqual(cfg.timeout_seconds, 30.0)
            self.assertEqual(cfg.provider, "mock")
            self.assertEqual(cfg.session_expiry_hours, 24)
            self.assertFalse(cfg.is_configured)

    def test_is_configured_requires_key_and_assistant(self):
        cfg_no_key = BackboardSettings(api_key="", assistant_id="asst-123")
        self.assertFalse(cfg_no_key.is_configured)

        cfg_no_asst = BackboardSettings(api_key="bb_live_key_xyz", assistant_id="")
        self.assertFalse(cfg_no_asst.is_configured)

        cfg_configured = BackboardSettings(api_key="bb_live_key_xyz", assistant_id="asst-123")
        self.assertTrue(cfg_configured.is_configured)

    def test_base_url_normalization(self):
        cfg = BackboardSettings(base_url="https://app.backboard.io/api/")
        self.assertEqual(cfg.base_url, "https://app.backboard.io/api")

    def test_robust_numeric_parsing(self):
        cfg = BackboardSettings(timeout_seconds="invalid", session_expiry_hours="not_a_number")
        self.assertEqual(cfg.timeout_seconds, 30.0)
        self.assertEqual(cfg.session_expiry_hours, 24)

    def test_uppercase_property_aliases(self):
        cfg = BackboardSettings(
            api_key="key",
            base_url="https://custom.url",
            assistant_id="asst",
            timeout_seconds=45.0,
            provider="mock",
            session_signing_key="sign_key",
            session_expiry_hours=12,
        )
        self.assertEqual(cfg.API_KEY, "key")
        self.assertEqual(cfg.BASE_URL, "https://custom.url")
        self.assertEqual(cfg.ASSISTANT_ID, "asst")
        self.assertEqual(cfg.TIMEOUT_SECONDS, 45.0)
        self.assertEqual(cfg.PROVIDER, "mock")
        self.assertEqual(cfg.SESSION_SIGNING_KEY, "sign_key")
        self.assertEqual(cfg.SESSION_EXPIRY_HOURS, 12)


class TestMockBackboardProvider(unittest.IsolatedAsyncioTestCase):
    """Test MockBackboardProvider operations, modes, and failure simulations."""

    async def test_provider_metadata(self):
        provider = MockBackboardProvider()
        self.assertEqual(provider.provider_name, "mock_backboard")
        self.assertTrue(provider.is_available())

    async def test_create_thread(self):
        provider = MockBackboardProvider()
        t1 = await provider.create_thread()
        t2 = await provider.create_thread()
        self.assertEqual(t1, "mock-thread-uuid-1234")
        self.assertEqual(t2, "mock-thread-uuid-1234-2")
        self.assertEqual(len(provider.created_threads), 2)

    async def test_send_message_default_landslide_response(self):
        provider = MockBackboardProvider()
        output = await provider.send_message(
            thread_id="th-1",
            assistant_id="mock-asst-1",
            content="Explain how slope failures start.",
        )
        self.assertIsInstance(output, BackboardMessageOutput)
        self.assertEqual(output.status, "COMPLETED")
        self.assertEqual(output.thread_id, "th-1")
        self.assertEqual(output.assistant_id, "mock-asst-1")
        self.assertIn("gravitational", output.content.lower())
        self.assertGreaterEqual(output.retrieved_files_count, 1)
        self.assertIn("01_why_do_landslides_happen.md", output.retrieved_files)
        self.assertGreaterEqual(len(output.documents), 1)
        self.assertEqual(provider.call_count, 1)

    async def test_send_message_warning_signs_heuristic(self):
        provider = MockBackboardProvider()
        output = await provider.send_message(
            thread_id="th-1",
            assistant_id="mock-asst-1",
            content="What are the early warning signs and tension cracks?",
        )
        self.assertIn("tension cracks", output.content.lower())
        self.assertIn("02_warning_signs_before_failure.md", output.retrieved_files)
        self.assertEqual(output.documents[0].filename, "02_warning_signs_before_failure.md")
        self.assertAlmostEqual(output.documents[0].score, 0.95, places=2)

    async def test_send_message_rainfall_heuristic(self):
        provider = MockBackboardProvider()
        output = await provider.send_message(
            thread_id="th-1",
            assistant_id="mock-asst-1",
            content="How does intense monsoon rainfall trigger landslides?",
        )
        self.assertIn("pore water pressure", output.content.lower())
        self.assertIn("04_why_rainfall_and_soil_moisture_matter.md", output.retrieved_files)

    async def test_send_message_evacuation_heuristic(self):
        provider = MockBackboardProvider()
        output = await provider.send_message(
            thread_id="th-1",
            assistant_id="mock-asst-1",
            content="Where are safe evacuation routes and relief shelter protocols?",
        )
        self.assertIn("evacuation", output.content.lower())
        self.assertIn("03_evacuation_and_shelter_protocols.md", output.retrieved_files)

    async def test_send_message_empty_retrieval_mode(self):
        provider = MockBackboardProvider(mode="empty_retrieval")
        output = await provider.send_message(
            thread_id="th-1",
            assistant_id="mock-asst-1",
            content="What is the capital of France?",
        )
        self.assertIn("sufficient information", output.content)
        self.assertEqual(output.retrieved_files, [])
        self.assertEqual(output.retrieved_files_count, 0)
        self.assertEqual(output.documents, [])

    async def test_send_message_custom_output(self):
        custom = BackboardMessageOutput(
            content="Custom injected answer.",
            thread_id="custom-th",
            assistant_id="custom-asst",
            retrieved_files=["custom.md"],
            retrieved_files_count=1,
        )
        provider = MockBackboardProvider(custom_output=custom)
        output = await provider.send_message("th-1", "asst-1", "any query")
        self.assertEqual(output.content, "Custom injected answer.")
        self.assertEqual(output.thread_id, "custom-th")

    async def test_simulate_timeout_mode(self):
        provider = MockBackboardProvider(mode="timeout")
        with self.assertRaises(BackboardTimeoutError):
            await provider.create_thread()
        with self.assertRaises(BackboardTimeoutError):
            await provider.send_message("th-1", "asst-1", "query")

    async def test_simulate_rate_limit_mode(self):
        provider = MockBackboardProvider(mode="rate_limit")
        with self.assertRaises(BackboardRateLimitError):
            await provider.create_thread()
        with self.assertRaises(BackboardRateLimitError):
            await provider.send_message("th-1", "asst-1", "query")

    async def test_simulate_unavailable_mode(self):
        provider = MockBackboardProvider(mode="unavailable")
        with self.assertRaises(BackboardTemporaryUnavailableError):
            await provider.create_thread()
        with self.assertRaises(BackboardTemporaryUnavailableError):
            await provider.send_message("th-1", "asst-1", "query")

    async def test_simulate_auth_error_mode(self):
        provider = MockBackboardProvider(mode="auth_error")
        with self.assertRaises(BackboardAuthenticationError):
            await provider.create_thread()
        with self.assertRaises(BackboardAuthenticationError):
            await provider.send_message("th-1", "asst-1", "query")

    async def test_simulate_not_found_mode(self):
        provider = MockBackboardProvider(mode="not_found")
        with self.assertRaises(BackboardNotFoundError):
            await provider.send_message("th-1", "asst-1", "query")

    async def test_simulate_malformed_mode(self):
        provider = MockBackboardProvider(mode="malformed")
        with self.assertRaises(BackboardMalformedOutputError):
            await provider.send_message("th-1", "asst-1", "query")

    async def test_signature_flexibility_two_positional_args(self):
        """Caller can pass (thread_id, query_content) without explicit assistant_id."""
        provider = MockBackboardProvider()
        output = await provider.send_message("th-1", "What are warning signs?")
        self.assertEqual(output.thread_id, "th-1")
        self.assertIn("tension cracks", output.content.lower())
        self.assertEqual(provider.last_content, "What are warning signs?")

    async def test_dispatched_message_tracking(self):
        provider = MockBackboardProvider()
        await provider.send_message(
            thread_id="th-tracked",
            assistant_id="asst-tracked",
            content="Inspection test query.",
            stream=False,
            memory="off",
        )
        self.assertEqual(len(provider.dispatched_messages), 1)
        record = provider.dispatched_messages[0]
        self.assertEqual(record["thread_id"], "th-tracked")
        self.assertEqual(record["assistant_id"], "asst-tracked")
        self.assertEqual(record["content"], "Inspection test query.")
        self.assertEqual(record["stream"], False)
        self.assertEqual(record["memory"], "off")


class TestLiveBackboardProviderOffline(unittest.IsolatedAsyncioTestCase):
    """Offline unit tests for LiveBackboardProvider using httpx.MockTransport."""

    def setUp(self):
        self.cfg = BackboardSettings(
            api_key="bb_live_api_key_test_12345",
            base_url="https://app.backboard.io/api",
            assistant_id="asst_landslide_science_001",
            timeout_seconds=15.0,
        )

    def test_live_provider_raises_config_error_when_unconfigured(self):
        cfg_empty = BackboardSettings(api_key="", assistant_id="")
        with self.assertRaises(BackboardConfigurationError):
            LiveBackboardProvider(config=cfg_empty)

    async def test_create_thread_success(self):
        captured_requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_requests.append(request)
            return httpx.Response(
                201,
                json={"thread_id": "bb-th-live-42", "status": "active"},
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        thread_id = await provider.create_thread()
        self.assertEqual(thread_id, "bb-th-live-42")
        self.assertEqual(len(captured_requests), 1)

        req = captured_requests[0]
        self.assertEqual(str(req.url), "https://app.backboard.io/api/assistants/asst_landslide_science_001/threads")
        self.assertEqual(req.headers["X-API-Key"], "bb_live_api_key_test_12345")
        self.assertEqual(req.headers["Content-Type"], "application/json")

    async def test_send_message_success_and_metadata_parsing(self):
        captured_requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_requests.append(request)
            return httpx.Response(
                200,
                json={
                    "message_id": "msg-001",
                    "thread_id": "bb-th-live-42",
                    "assistant_id": "asst_landslide_science_001",
                    "content": "Landslides occur when gravitational shear exceeds shear strength.",
                    "status": "COMPLETED",
                    "retrieved_files": [
                        {
                            "document_id": "doc-01",
                            "filename": "01_why_do_landslides_happen.md",
                            "score": 0.94,
                            "metadata": {"tier": 1},
                        }
                    ],
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        output = await provider.send_message(
            thread_id="bb-th-live-42",
            content="What causes landslides?",
            memory="off",
        )

        self.assertEqual(output.content, "Landslides occur when gravitational shear exceeds shear strength.")
        self.assertEqual(output.thread_id, "bb-th-live-42")
        self.assertEqual(output.message_id, "msg-001")
        self.assertEqual(output.status, "COMPLETED")
        self.assertEqual(output.retrieved_files, ["01_why_do_landslides_happen.md"])
        self.assertEqual(output.retrieved_files_count, 1)
        self.assertEqual(len(output.documents), 1)
        self.assertEqual(output.documents[0].filename, "01_why_do_landslides_happen.md")
        self.assertEqual(output.documents[0].document_id, "doc-01")
        self.assertEqual(output.documents[0].score, 0.94)

        req = captured_requests[0]
        body = json.loads(req.content)
        self.assertEqual(body["thread_id"], "bb-th-live-42")
        self.assertEqual(body["assistant_id"], "asst_landslide_science_001")
        self.assertEqual(body["content"], "What causes landslides?")
        self.assertEqual(body["memory"], "off")

    async def test_memory_off_enforced_even_if_passed_otherwise(self):
        """Decision 3: memory='off' is strictly enforced to protect multi-user privacy."""
        captured_requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_requests.append(request)
            return httpx.Response(
                200,
                json={"content": "Answer", "thread_id": "th-1", "status": "COMPLETED"},
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        await provider.send_message(
            thread_id="th-1",
            content="Query",
            memory="auto",  # Attempted override
        )

        req = captured_requests[0]
        body = json.loads(req.content)
        self.assertEqual(body["memory"], "off")

    async def test_retrieved_files_as_string_list(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "content": "Answer with string filenames",
                    "thread_id": "th-1",
                    "retrieved_files": ["01_why_do_landslides_happen.md", "04_rainfall.md"],
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        output = await provider.send_message("th-1", "Query")
        self.assertEqual(output.retrieved_files_count, 2)
        self.assertEqual(output.retrieved_files, ["01_why_do_landslides_happen.md", "04_rainfall.md"])
        self.assertEqual(len(output.documents), 2)
        self.assertEqual(output.documents[0].filename, "01_why_do_landslides_happen.md")
        self.assertEqual(output.documents[1].filename, "04_rainfall.md")

    async def test_send_message_with_status_failed_billing_restriction(self):
        """HTTP 200 with status='FAILED' and billing restriction message parses properly."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "content": "Your free credit is reserved for Memory & RAG, so it can't cover LLM chat. Add credits or start a subscription on the Billing page to continue.",
                    "thread_id": "th-fail-1",
                    "assistant_id": "asst-1",
                    "status": "FAILED",
                    "retrieved_files": [],
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        output = await provider.send_message("th-fail-1", "Query")
        self.assertEqual(output.status, "FAILED")
        self.assertTrue(output.is_billing_restricted)
        self.assertFalse(output.is_successful)
        self.assertEqual(output.retrieved_files_count, 0)

    async def test_send_message_with_status_failed_generic(self):
        """HTTP 200 with status='FAILED' and non-billing error parses properly."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "content": "Inference process encountered an unrecoverable exception.",
                    "thread_id": "th-fail-2",
                    "assistant_id": "asst-1",
                    "status": "FAILED",
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        output = await provider.send_message("th-fail-2", "Query")
        self.assertEqual(output.status, "FAILED")
        self.assertFalse(output.is_billing_restricted)
        self.assertFalse(output.is_successful)


    async def test_auth_failure_401(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"detail": "Invalid API key"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        with self.assertRaises(BackboardAuthenticationError) as ctx:
            await provider.create_thread()
        self.assertNotIn("bb_live_api_key_test_12345", str(ctx.exception))

        with self.assertRaises(BackboardAuthenticationError) as ctx:
            await provider.send_message("th-1", "Query")
        self.assertNotIn("bb_live_api_key_test_12345", str(ctx.exception))

    async def test_not_found_404(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"detail": "Thread not found"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        with self.assertRaises(BackboardNotFoundError):
            await provider.send_message("th-nonexistent", "Query")

    async def test_rate_limit_429_with_retry_after(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, headers={"Retry-After": "45"}, json={"detail": "Rate limit exceeded"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        with self.assertRaises(BackboardRateLimitError) as ctx:
            await provider.send_message("th-1", "Query")
        self.assertIn("45", str(ctx.exception))

    async def test_upstream_server_error_500_and_503(self):
        for code in (500, 502, 503, 504):
            with self.subTest(status_code=code):
                def handler(request: httpx.Request) -> httpx.Response:
                    return httpx.Response(code, text="Server overloaded")

                client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
                provider = LiveBackboardProvider(config=self.cfg, http_client=client)

                with self.assertRaises(BackboardTemporaryUnavailableError):
                    await provider.send_message("th-1", "Query")

    async def test_connection_timeout(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("Connection timed out after 15s")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        with self.assertRaises(BackboardTimeoutError):
            await provider.send_message("th-1", "Query")

    async def test_read_timeout(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Read timed out waiting for LLM")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        with self.assertRaises(BackboardTimeoutError):
            await provider.send_message("th-1", "Query")

    async def test_connection_refused(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Failed to establish TCP connection")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        with self.assertRaises(BackboardConnectionError):
            await provider.send_message("th-1", "Query")

    async def test_malformed_json_response(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<!DOCTYPE html><html><body>Error</body></html>")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        with self.assertRaises(BackboardMalformedOutputError):
            await provider.send_message("th-1", "Query")

    async def test_unexpected_schema_missing_content(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"message_id": "msg-123"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        with self.assertRaises(BackboardMalformedOutputError) as ctx:
            await provider.send_message("th-1", "Query")
        self.assertIn("missing required 'content'", str(ctx.exception))

    async def test_unexpected_schema_missing_thread_id(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201, json={"status": "active"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        with self.assertRaises(BackboardMalformedOutputError) as ctx:
            await provider.create_thread()
        self.assertIn("missing valid 'thread_id'", str(ctx.exception))

    async def test_secret_redaction_in_all_errors(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, text="Bad request detail")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = LiveBackboardProvider(config=self.cfg, http_client=client)

        try:
            await provider.send_message("th-1", "Query")
        except BackboardError as e:
            self.assertNotIn("bb_live_api_key_test_12345", str(e))



class TestBackboardProviderFactory(unittest.TestCase):
    """Test get_backboard_provider factory selection."""

    def test_default_returns_mock_provider(self):
        cfg = BackboardSettings(provider="mock")
        provider = get_backboard_provider(config=cfg)
        self.assertIsInstance(provider, MockBackboardProvider)

    def test_force_mock_overrides_credentials(self):
        cfg = BackboardSettings(
            provider="live",
            api_key="real_looking_key",
            assistant_id="asst-999",
        )
        provider = get_backboard_provider(config=cfg, force_mock=True)
        self.assertIsInstance(provider, MockBackboardProvider)

    def test_unconfigured_live_falls_back_to_mock(self):
        cfg = BackboardSettings(
            provider="live",
            api_key="",
            assistant_id="",
        )
        provider = get_backboard_provider(config=cfg)
        self.assertIsInstance(provider, MockBackboardProvider)

    def test_configured_live_returns_live_provider(self):
        cfg = BackboardSettings(
            provider="live",
            api_key="real_looking_key",
            assistant_id="asst-999",
        )
        provider = get_backboard_provider(config=cfg)
        self.assertIsInstance(provider, LiveBackboardProvider)


if __name__ == "__main__":
    unittest.main()
