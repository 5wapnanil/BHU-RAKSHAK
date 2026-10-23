"""Deterministic offline unit tests for Backboard Smoke Test Script (Milestone 4C.2).

Verifies:
- Safety gate enforcement: Aborts with code 1 if '--live' is not provided.
- Layer 1 HTTP Transport verification: Succeeded/Failed handling for network/HTTP errors.
- Layer 2 Response Parsing verification: Succeeded/Failed handling for malformed JSON or schemas.
- Layer 3 Upstream LLM Generation verification: Succeeded on COMPLETED, Failed on FAILED status.
- Specific detection and actionable diagnostics for Backboard free-tier billing restrictions.
- Layer 4 RAG retrieval reporting (cited documents vs unverified when 0 docs cited).
- Strict credential redaction (no raw API keys or secrets in stdout).
- Strict enforcement of memory="off".
"""

import asyncio
from io import StringIO
import sys
import unittest
from unittest.mock import AsyncMock, patch

from backend.app.services.backboard.config import BackboardSettings
from backend.app.services.backboard.exceptions import (
    BackboardAuthenticationError,
    BackboardConnectionError,
    BackboardMalformedOutputError,
    BackboardNotFoundError,
    BackboardRateLimitError,
    BackboardTimeoutError,
)
from backend.app.services.backboard.models import BackboardMessageOutput
from backend.app.services.backboard.providers import BackboardProvider
from backend.scripts.smoke_test_backboard import redact_secret, run_smoke_test


class MockedProvider(BackboardProvider):
    """Deterministic in-memory provider for smoke test scenario verification."""

    def __init__(
        self,
        thread_id: str = "th_disposable_smoke_999",
        message_output: BackboardMessageOutput = None,
        thread_error: Exception = None,
        message_error: Exception = None,
    ):
        self._thread_id = thread_id
        self._message_output = message_output
        self._thread_error = thread_error
        self._message_error = message_error
        self.sent_messages = []

    async def create_thread(self, assistant_id: str = None) -> str:
        if self._thread_error:
            raise self._thread_error
        return self._thread_id

    async def send_message(
        self,
        thread_id: str,
        assistant_id: str = None,
        content: str = "",
        *,
        stream: bool = False,
        memory: str = "off",
    ) -> BackboardMessageOutput:
        self.sent_messages.append({
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "content": content,
            "memory": memory,
        })
        if self._message_error:
            raise self._message_error
        return self._message_output


class TestSmokeTestScript(unittest.TestCase):
    """Deterministic tests for run_smoke_test and its 4 validation layers."""

    def setUp(self):
        self.cfg = BackboardSettings(
            api_key="espr_test_secret_api_key_1234567890",
            assistant_id="asst_landslide_science_test_456",
            provider="live",
        )

    def test_safety_gate_fails_without_live_flag(self):
        """Live smoke test must abort with exit code 1 if live_flag is False."""
        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=False))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[SAFETY GATE]", output)
        self.assertIn("--live", output)

    def test_fails_when_unconfigured_and_no_provider(self):
        """Smoke test must abort with code 1 when credentials are missing and no provider is passed."""
        empty_cfg = BackboardSettings(api_key="", assistant_id="")
        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, config=empty_cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[ERROR] Missing required Backboard credentials.", output)

    def test_smoke_test_full_success_layers_1_to_3(self):
        """When HTTP, parsing, and upstream generation succeed, all layers pass (exit code 0)."""
        valid_response = BackboardMessageOutput(
            content=(
                "Three common warning signs of landslide activity are: "
                "1. Tension cracks forming on slopes or roads. "
                "2. Bulging ground at the toe of a slope. "
                "3. Sudden muddiness in clear mountain streams. "
                "People observing these signs should evacuate to stable high ground immediately."
            ),
            thread_id="th_disposable_smoke_999",
            assistant_id="asst_landslide_science_test_456",
            status="COMPLETED",
            retrieved_files=["01_why_do_landslides_happen.md"],
        )
        provider = MockedProvider(message_output=valid_response)

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: PASSED", output)
        self.assertIn("[LAYER 2 - RESPONSE PARSING]: PASSED", output)
        self.assertIn("[LAYER 3 - UPSTREAM GENERATION]: PASSED", output)
        self.assertIn("[LAYER 4 - RAG RETRIEVAL]: PASSED (1 document(s) cited)", output)
        self.assertIn("SMOKE TEST RESULT: PASSED", output)

        # Confirm memory="off" was strictly sent
        self.assertEqual(len(provider.sent_messages), 1)
        self.assertEqual(provider.sent_messages[0]["memory"], "off")

    def test_smoke_test_layer_4_unverified_when_zero_citations(self):
        """When 0 documents are cited (pre-ingestion), Layer 4 is UNVERIFIED but test passes."""
        valid_response = BackboardMessageOutput(
            content=(
                "Warning signs include ground cracks, tilting trees, and jammed doors. "
                "Residents should evacuate immediately away from the path of the slope."
            ),
            thread_id="th_disposable_smoke_999",
            assistant_id="asst_landslide_science_test_456",
            status="COMPLETED",
            retrieved_files=[],
        )
        provider = MockedProvider(message_output=valid_response)

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("[LAYER 4 - RAG RETRIEVAL]: UNVERIFIED (0 documents cited - Knowledge base not yet ingested)", output)
        self.assertIn("SMOKE TEST RESULT: PASSED", output)

    def test_smoke_test_fails_on_status_failed_billing_restriction(self):
        """Billing restriction response must fail Layer 3, output diagnostic, and exit code 1."""
        billing_content = (
            "Your free credit is reserved for Memory & RAG, so it can't cover LLM chat. "
            "Add credits or start a subscription on the Billing page to continue. "
            "Turn on auto-reload on the Billing page to prevent interruptions."
        )
        restricted_response = BackboardMessageOutput(
            content=billing_content,
            thread_id="th_disposable_smoke_999",
            assistant_id="asst_landslide_science_test_456",
            status="FAILED",
            retrieved_files=[],
        )
        provider = MockedProvider(message_output=restricted_response)

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        # HTTP and Parsing succeeded
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: PASSED", output)
        self.assertIn("[LAYER 2 - RESPONSE PARSING]: PASSED", output)
        # Layer 3 failed specifically on billing restriction
        self.assertIn("[LAYER 3 - UPSTREAM GENERATION]: FAILED (Billing / Credit Restriction Detected)", output)
        self.assertIn("[ACTIONABLE DIAGNOSTIC]", output)
        self.assertIn("free credit is reserved for Memory & RAG", output)
        self.assertIn("SMOKE TEST RESULT: FAILED", output)

    def test_smoke_test_fails_on_status_failed_generic(self):
        """Upstream status='FAILED' with non-billing error must fail Layer 3 with exit code 1."""
        failed_response = BackboardMessageOutput(
            content="Internal upstream model inference timeout.",
            thread_id="th_disposable_smoke_999",
            assistant_id="asst_landslide_science_test_456",
            status="FAILED",
        )
        provider = MockedProvider(message_output=failed_response)

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: PASSED", output)
        self.assertIn("[LAYER 2 - RESPONSE PARSING]: PASSED", output)
        self.assertIn("[LAYER 3 - UPSTREAM GENERATION]: FAILED (Upstream status: 'FAILED')", output)
        self.assertIn("SMOKE TEST RESULT: FAILED", output)

    def test_smoke_test_fails_on_empty_content(self):
        """Empty or suspiciously short content must fail Layer 3 with exit code 1."""
        empty_response = BackboardMessageOutput(
            content="Too short",
            thread_id="th_disposable_smoke_999",
            assistant_id="asst_landslide_science_test_456",
            status="COMPLETED",
        )
        provider = MockedProvider(message_output=empty_response)

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 3 - UPSTREAM GENERATION]: FAILED", output)
        self.assertIn("SMOKE TEST RESULT: FAILED", output)

    def test_smoke_test_fails_on_auth_failure_401(self):
        """HTTP 401 must fail Layer 1 with exit code 1."""
        provider = MockedProvider(thread_error=BackboardAuthenticationError("Invalid API key provided."))

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: FAILED (Authentication Failure)", output)

    def test_smoke_test_fails_on_not_found_404(self):
        """HTTP 404 must fail Layer 1 with exit code 1."""
        provider = MockedProvider(thread_error=BackboardNotFoundError("Assistant not found."))

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: FAILED (Resource Not Found - HTTP 404)", output)

    def test_smoke_test_fails_on_rate_limit_429(self):
        """HTTP 429 must fail Layer 1 with exit code 1."""
        provider = MockedProvider(message_error=BackboardRateLimitError("Rate limit exceeded. Retry-After: 30."))

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: FAILED (Rate Limit Exceeded - HTTP 429)", output)

    def test_smoke_test_fails_on_timeout(self):
        """Connection or read timeout must fail Layer 1 with exit code 1."""
        provider = MockedProvider(message_error=BackboardTimeoutError("Connection timed out after 30s."))

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: FAILED (BackboardTimeoutError)", output)

    def test_smoke_test_fails_on_connection_error(self):
        """Connection refused must fail Layer 1 with exit code 1."""
        provider = MockedProvider(thread_error=BackboardConnectionError("Failed to establish TCP connection."))

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: FAILED (BackboardConnectionError)", output)

    def test_smoke_test_fails_on_malformed_response(self):
        """Malformed output must pass Layer 1 (HTTP received) and fail Layer 2."""
        provider = MockedProvider(message_error=BackboardMalformedOutputError("missing required 'content' field"))

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: PASSED", output)
        self.assertIn("[LAYER 2 - RESPONSE PARSING]: FAILED", output)

    def test_secret_redaction(self):
        """Tokens and secrets must be redacted to prevent credential leakage."""
        self.assertEqual(redact_secret(""), "<unset>")
        self.assertEqual(redact_secret("12345"), "***")
        self.assertEqual(redact_secret("espr_1234567890abcdef12345678"), "esp...5678")

        stdout_capture = StringIO()
        valid_response = BackboardMessageOutput(
            content="Warning signs include cracks and ground movement. Evacuate immediately.",
            thread_id="th_super_secret_thread_id_999",
            assistant_id="asst_super_secret_assistant_id_888",
            status="COMPLETED",
        )
        provider = MockedProvider(thread_id="th_super_secret_thread_id_999", message_output=valid_response)

        with patch("sys.stdout", stdout_capture):
            asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        # Verify full secrets do not appear
        self.assertNotIn("espr_test_secret_api_key_1234567890", output)
        self.assertNotIn("th_super_secret_thread_id_999", output)
        self.assertNotIn("asst_landslide_science_test_456", output)
        # Redacted form should appear
        self.assertIn("esp...7890", output)
        self.assertIn("th_..._999", output)

    def test_smoke_test_fails_on_thread_creation_malformed(self):
        """Malformed output during thread creation must fail Layer 2."""
        provider = MockedProvider(thread_error=BackboardMalformedOutputError("Missing valid 'thread_id'"))

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: PASSED", output)
        self.assertIn("[LAYER 2 - RESPONSE PARSING]: FAILED", output)

    def test_smoke_test_fails_on_thread_creation_generic_exception(self):
        """Unexpected generic error during thread creation must fail Layer 1."""
        provider = MockedProvider(thread_error=RuntimeError("Unexpected OS socket error"))

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: FAILED (RuntimeError: Unexpected OS socket error)", output)

    def test_smoke_test_fails_on_send_message_generic_exception(self):
        """Unexpected generic error during message dispatch must fail Layer 1."""
        provider = MockedProvider(message_error=RuntimeError("Unexpected TLS pipeline failure"))

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[LAYER 1 - HTTP TRANSPORT]: FAILED (RuntimeError: Unexpected TLS pipeline failure)", output)

    def test_smoke_test_truncates_long_content_display(self):
        """Content exceeding 300 characters is cleanly truncated in stdout preview."""
        long_content = "Landslide warning signs detailed response: " + ("x" * 400)
        valid_response = BackboardMessageOutput(
            content=long_content,
            thread_id="th_12345678",
            assistant_id="asst_12345678",
            status="COMPLETED",
        )
        provider = MockedProvider(message_output=valid_response)

        stdout_capture = StringIO()
        with patch("sys.stdout", stdout_capture):
            code = asyncio.run(run_smoke_test(live_flag=True, provider=provider, config=self.cfg))

        output = stdout_capture.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("... [TRUNCATED]", output)


if __name__ == "__main__":
    unittest.main()

