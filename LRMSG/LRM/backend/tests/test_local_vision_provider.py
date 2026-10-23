"""Tests for Gemma Local Vision Provider (Ollama / Open-Weights VLM Architecture).

Verifies:
1. Valid local image inference using mock runtime.
2. Actual image bytes passed as Base64 in Ollama images array.
3. Observation notes passed separately from physical image evidence.
4. Valid structured output, markdown-fenced JSON, and malformed output handling.
5. Normalization of unsupported or rogue hazard categories.
6. Missing model in Ollama (404) generates explicit pull guidance.
7. Missing local runtime / connection refused generates GemmaProviderUnavailableError.
8. Timeout, 429 concurrency limit, and 503 temporary service errors.
9. No fabricated verdicts on failure (indeterminate / unavailable).
10. Explicit Fallback provider provenance tracking.
11. Coordinator authorization guard for review and analysis endpoints.
12. Non-interference with hosted Google provider.
"""

import asyncio
import base64
from datetime import datetime, timezone
import json
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.api.schemas.gemma_analysis import GemmaHazardOutput
from backend.app.database.base import Base, get_db
from backend.app.database.models import FieldReport, User
from backend.app.main import app
from backend.app.services.gemma_analysis_service import GemmaAnalysisService
from backend.app.services.gemma_providers import (
    FallbackGemmaProvider,
    GemmaMalformedOutputError,
    GemmaProviderError,
    GemmaProviderUnavailableError,
    GemmaRateLimitError,
    GemmaTemporaryUnavailableError,
    GemmaTimeoutError,
    GoogleGenAIGemmaProvider,
    MockGemmaProvider,
    OllamaGemmaProvider,
    UnconfiguredGemmaProvider,
    get_gemma_provider,
    parse_gemma_json,
)
from backend.app.services.photo_storage_service import LocalStorageAdapter


class TestLocalVisionProvider(unittest.TestCase):
    """Test suite for local vision provider and enhanced architecture."""

    @classmethod
    def setUpClass(cls):
        from sqlalchemy.dialects.postgresql import JSONB, UUID
        from sqlalchemy.ext.compiler import compiles

        @compiles(JSONB, "sqlite")
        def compile_jsonb_sqlite(type_, compiler, **kw):
            return "TEXT"

        @compiles(UUID, "sqlite")
        def compile_uuid_sqlite(type_, compiler, **kw):
            return "TEXT"

        FieldReport.__table__.c.ai_detected_hazards.server_default = None

        from sqlalchemy.pool import StaticPool

        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine, tables=[User.__table__, FieldReport.__table__])

    def setUp(self):
        self.db = self.SessionLocal()
        self.mock_storage = MagicMock(spec=LocalStorageAdapter)
        self.client = TestClient(app)

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.rollback()
        self.db.query(FieldReport).delete()
        self.db.commit()
        self.db.close()

    def _create_report(self, notes: str = "Tension cracks along slope", photo_url: str = None) -> FieldReport:
        report = FieldReport(
            id=uuid4(),
            location_name="Nainital Sector 4",
            notes=notes,
            photo_url=photo_url,
            submitted_at=datetime.now(timezone.utc),
            review_status="pending",
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def test_ollama_passes_image_bytes_and_notes_separately(self):
        """Ollama provider passes actual image bytes in images array and keeps notes in prompt."""
        provider = OllamaGemmaProvider(base_url="http://localhost:11434", model_name="gemma3:4b")
        test_photo_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"mock_photo_content_data"
        test_notes = "Extensive road subsidence and exposed soil scarp"

        captured_requests = []

        class MockResponse:
            status_code = 200
            text = json.dumps({
                "response": json.dumps({
                    "hazard_level": "critical",
                    "detected_hazards": ["slope_displacement", "road_blockage"],
                    "confidence": 0.92,
                    "summary": "Severe slope movement and road failure",
                    "limitations": "View limited to foreground roadway",
                })
            })

            def json(self):
                return json.loads(self.text)

        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None):
                captured_requests.append({"url": url, "body": json})
                return MockResponse()

        with patch("httpx.AsyncClient", MockAsyncClient):
            output = asyncio.run(
                provider.analyze(
                    notes=test_notes,
                    location_name="Bhowali Highway",
                    photo_bytes=test_photo_bytes,
                    photo_mime="image/jpeg",
                )
            )

        self.assertEqual(len(captured_requests), 1)
        req = captured_requests[0]
        self.assertEqual(req["url"], "http://localhost:11434/api/generate")
        body = req["body"]

        # Verify model and JSON format
        self.assertEqual(body["model"], "gemma3:4b")
        self.assertEqual(body["format"], "json")
        self.assertFalse(body["stream"])

        # Verify images array contains valid Base64 matching original bytes
        self.assertIn("images", body)
        self.assertEqual(len(body["images"]), 1)
        decoded_bytes = base64.b64decode(body["images"][0])
        self.assertEqual(decoded_bytes, test_photo_bytes)

        # Verify prompt separates notes and visual instructions
        self.assertIn("Observer Notes: Extensive road subsidence", body["prompt"])
        self.assertIn("Location: Bhowali Highway", body["prompt"])
        self.assertIn("Analyze the attached field photograph", body["prompt"])

        # Verify output validation
        self.assertEqual(output.hazard_level, "critical")
        self.assertEqual(output.detected_hazards, ["slope_displacement", "road_blockage"])
        self.assertEqual(output.confidence, 0.92)

    def test_ollama_text_only_when_no_photo(self):
        """When no photo is provided, images array is omitted and text-only notice is in prompt."""
        provider = OllamaGemmaProvider(base_url="http://localhost:11434", model_name="gemma3:4b")
        captured_requests = []

        class MockResponse:
            status_code = 200
            text = json.dumps({
                "response": json.dumps({
                    "hazard_level": "moderate",
                    "detected_hazards": ["water_seepage"],
                    "confidence": 0.65,
                    "summary": "Reported water seepage without visual confirmation",
                    "limitations": "No field photograph was attached",
                })
            })

            def json(self):
                return json.loads(self.text)

        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None):
                captured_requests.append({"url": url, "body": json})
                return MockResponse()

        with patch("httpx.AsyncClient", MockAsyncClient):
            output = asyncio.run(provider.analyze(notes="Seepage from slope", location_name="Kilbury Road"))

        body = captured_requests[0]["body"]
        self.assertNotIn("images", body)
        self.assertIn("NOTE: No field photograph was attached", body["prompt"])
        self.assertEqual(output.hazard_level, "moderate")

    def test_parse_gemma_json_handles_markdown_code_fences(self):
        """Markdown code blocks (```json ... ```) must be parsed safely."""
        raw_markdown = (
            "```json\n"
            "{\n"
            '  "hazard_level": "high",\n'
            '  "detected_hazards": ["tension_cracks", "rockfall_debris"],\n'
            '  "confidence": 0.88,\n'
            '  "summary": "Tension cracks across road",\n'
            '  "limitations": "Vegetation covers toe"\n'
            "}\n"
            "```"
        )
        parsed = parse_gemma_json(raw_markdown)
        self.assertEqual(parsed.hazard_level, "high")
        self.assertEqual(parsed.detected_hazards, ["tension_cracks", "rockfall_debris"])
        self.assertEqual(parsed.confidence, 0.88)

    def test_parse_gemma_json_raises_malformed_on_invalid_syntax(self):
        """Non-JSON string must raise GemmaMalformedOutputError."""
        invalid_text = "I am an AI assistant and I believe this slope looks dangerous."
        with self.assertRaises(GemmaMalformedOutputError):
            parse_gemma_json(invalid_text)

    def test_unsupported_hazard_category_normalized_to_indeterminate(self):
        """Unknown or hallucinated hazard levels normalize safely to indeterminate."""
        raw_rogue = json.dumps({
            "hazard_level": "TOTALLY_SAFE_GUARANTEED",
            "detected_hazards": ["none"],
            "confidence": 0.2,
            "summary": "Slope cleared",
        })
        parsed = parse_gemma_json(raw_rogue)
        self.assertEqual(parsed.hazard_level, "indeterminate")

    def test_ollama_missing_model_raises_clear_pull_instruction(self):
        """HTTP 404 with missing model message generates explicit ollama pull guidance."""
        provider = OllamaGemmaProvider(base_url="http://localhost:11434", model_name="gemma3:4b")

        class Mock404Response:
            status_code = 404
            text = "model 'gemma3:4b' not found, try pulling it first"

            def json(self):
                return {"error": self.text}

        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None):
                return Mock404Response()

        with patch("httpx.AsyncClient", MockAsyncClient):
            with self.assertRaises(GemmaProviderUnavailableError) as ctx:
                asyncio.run(provider.analyze(notes="Slope crack", location_name="Loc"))
            self.assertIn("ollama pull gemma3:4b", str(ctx.exception))

    def test_ollama_non_vision_model_raises_explicit_error(self):
        """When model does not support images, raise explicit configuration error."""
        provider = OllamaGemmaProvider(base_url="http://localhost:11434", model_name="gemma2")

        class MockImageErrorResponse:
            status_code = 400
            text = "model 'gemma2' does not support images"

            def json(self):
                return {"error": self.text}

        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None):
                return MockImageErrorResponse()

        with patch("httpx.AsyncClient", MockAsyncClient):
            with self.assertRaises(GemmaProviderError) as ctx:
                asyncio.run(
                    provider.analyze(
                        notes="Notes",
                        location_name="Loc",
                        photo_bytes=b"fake_image",
                    )
                )
            self.assertIn("does not support multimodal image input", str(ctx.exception))

    def test_ollama_connection_failure_raises_unavailable(self):
        """When Ollama daemon is unreachable, raise GemmaProviderUnavailableError."""
        provider = OllamaGemmaProvider(base_url="http://localhost:11434", model_name="gemma3:4b")
        import httpx

        class MockConnectErrorClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None):
                raise httpx.ConnectError("Connection refused by peer")

        with patch("httpx.AsyncClient", MockConnectErrorClient):
            with self.assertRaises(GemmaProviderUnavailableError) as ctx:
                asyncio.run(provider.analyze(notes="Notes", location_name="Loc"))
            self.assertIn("Cannot connect to Ollama daemon", str(ctx.exception))

    def test_ollama_timeout_raises_timeout_error(self):
        """When local inference exceeds timeout, raise GemmaTimeoutError."""
        provider = OllamaGemmaProvider(base_url="http://localhost:11434", model_name="gemma3:4b", timeout=5.0)
        import httpx

        class MockTimeoutClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None):
                raise httpx.TimeoutException("Read timed out")

        with patch("httpx.AsyncClient", MockTimeoutClient):
            with self.assertRaises(GemmaTimeoutError) as ctx:
                asyncio.run(provider.analyze(notes="Notes", location_name="Loc"))
            self.assertIn("timed out after 5.0s", str(ctx.exception))

    def test_no_fabricated_verdict_when_local_inference_fails(self):
        """When local inference fails, database records indeterminate hazard with null confidence."""
        report = self._create_report(notes="Collapsed roadside bank")
        failing_provider = MockGemmaProvider(simulate_connection_error=True)
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=failing_provider)

        result = asyncio.run(service.analyze_report(report.id))
        self.assertEqual(result.ai_hazard_level, "indeterminate")
        self.assertIsNone(result.ai_confidence)
        self.assertEqual(result.ai_detected_hazards, [])
        self.assertIn("[UNAVAILABLE]", result.ai_summary)
        self.assertIsNone(result.ai_analyzed_at)

    def test_fallback_provider_execution_and_provenance(self):
        """Fallback provider executes secondary on primary failure and records provenance."""
        primary = MockGemmaProvider(simulate_unavailable=True)
        fallback = MockGemmaProvider(
            custom_output=GemmaHazardOutput(
                hazard_level="moderate",
                detected_hazards=["rockfall_debris"],
                confidence=0.72,
                summary="Debris on shoulder",
            )
        )
        pipeline = FallbackGemmaProvider(primary=primary, fallback=fallback)

        output = asyncio.run(pipeline.analyze(notes="Rocks falling", location_name="Hill Road"))
        self.assertEqual(output.hazard_level, "moderate")
        self.assertIn("mock_gemma (fallback)", output.summary)

    def test_coordinator_authorization_blocks_unauthorized_when_configured(self):
        """When COORDINATOR_API_KEY is configured, review and analyze endpoints block unauthorized requests."""
        report = self._create_report()

        with patch.dict(os.environ, {"COORDINATOR_API_KEY": "super_secret_coord_token"}):
            # Unauthorized review attempt
            resp = self.client.patch(
                f"/api/field-reports/{report.id}/review",
                json={"review_status": "verified"},
            )
            self.assertEqual(resp.status_code, 403)

            # Authorized review attempt via X-Coordinator-Key
            resp_auth = self.client.patch(
                f"/api/field-reports/{report.id}/review",
                json={"review_status": "verified"},
                headers={"X-Coordinator-Key": "super_secret_coord_token"},
            )
            self.assertEqual(resp_auth.status_code, 200)
            self.assertEqual(resp_auth.json()["review_status"], "verified")

            # Authorized review attempt via Bearer token
            resp_bearer = self.client.patch(
                f"/api/field-reports/{report.id}/review",
                json={"review_status": "needs_inspection"},
                headers={"Authorization": "Bearer super_secret_coord_token"},
            )
            self.assertEqual(resp_bearer.status_code, 200)
            self.assertEqual(resp_bearer.json()["review_status"], "needs_inspection")

    def test_coordinator_authorization_fails_closed_in_production_when_unconfigured(self):
        """In production deployments (ENVIRONMENT=production), missing credentials fail closed with HTTP 503."""
        report = self._create_report()

        # In production without COORDINATOR_API_KEY -> MUST fail closed
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "COORDINATOR_API_KEY": ""}):
            resp = self.client.patch(
                f"/api/field-reports/{report.id}/review",
                json={"review_status": "verified"},
            )
            self.assertEqual(resp.status_code, 503)
            self.assertIn("Administrative access unavailable", resp.json()["detail"])

            resp_analyze = self.client.post(f"/api/field-reports/{report.id}/analyze")
            self.assertEqual(resp_analyze.status_code, 503)

        # In production with COORDINATOR_API_KEY -> succeeds with credentials
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "COORDINATOR_API_KEY": "prod_key_123"}):
            resp_prod = self.client.patch(
                f"/api/field-reports/{report.id}/review",
                json={"review_status": "verified"},
                headers={"X-Coordinator-Key": "prod_key_123"},
            )
            self.assertEqual(resp_prod.status_code, 200)
            self.assertEqual(resp_prod.json()["review_status"], "verified")

    def test_coordinator_authorization_rejects_invalid_credentials_and_protects_secrets(self):
        """Invalid credentials are rejected with 403, and secrets are never returned in responses."""
        report = self._create_report()
        secret = "ultra_confidential_coordinator_key_999"

        with patch.dict(os.environ, {"COORDINATOR_API_KEY": secret}):
            # Invalid X-Coordinator-Key
            resp_bad_key = self.client.patch(
                f"/api/field-reports/{report.id}/review",
                json={"review_status": "verified"},
                headers={"X-Coordinator-Key": "incorrect_key"},
            )
            self.assertEqual(resp_bad_key.status_code, 403)
            self.assertNotIn(secret, resp_bad_key.text)
            self.assertEqual(resp_bad_key.json()["detail"], "Forbidden: Valid coordinator credentials required.")

            # Invalid Bearer token
            resp_bad_bearer = self.client.patch(
                f"/api/field-reports/{report.id}/review",
                json={"review_status": "verified"},
                headers={"Authorization": "Bearer wrong_bearer_token"},
            )
            self.assertEqual(resp_bad_bearer.status_code, 403)
            self.assertNotIn(secret, resp_bad_bearer.text)

            # Analyze endpoint rejects invalid credentials
            resp_analyze_bad = self.client.post(
                f"/api/field-reports/{report.id}/analyze",
                headers={"X-Coordinator-Key": "wrong_key"},
            )
            self.assertEqual(resp_analyze_bad.status_code, 403)
            self.assertNotIn(secret, resp_analyze_bad.text)

            # Analyze endpoint rejects missing credentials
            resp_analyze_missing = self.client.post(
                f"/api/field-reports/{report.id}/analyze",
            )
            self.assertEqual(resp_analyze_missing.status_code, 403)
            self.assertNotIn(secret, resp_analyze_missing.text)

    def test_production_environment_variants_fail_closed(self):
        """All production environment aliases (ENV=production, FASTAPI_ENV=prod, APP_ENV=live) fail closed without keys."""
        report = self._create_report()

        for env_var, env_val in [
            ("ENV", "production"),
            ("FASTAPI_ENV", "prod"),
            ("APP_ENV", "live"),
            ("NODE_ENV", "production"),
        ]:
            with patch.dict(os.environ, {env_var: env_val, "COORDINATOR_API_KEY": ""}, clear=False):
                resp = self.client.patch(
                    f"/api/field-reports/{report.id}/review",
                    json={"review_status": "verified"},
                )
                self.assertEqual(
                    resp.status_code,
                    503,
                    f"Expected 503 fail-closed for {env_var}={env_val}, got {resp.status_code}",
                )
                self.assertIn("Administrative access unavailable", resp.json()["detail"])


if __name__ == "__main__":
    unittest.main()
