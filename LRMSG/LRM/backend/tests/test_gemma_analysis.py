"""Unit and integration tests for Gemma AI FieldReport analysis pipeline.

Verifies:
- Multimodal and text-only analysis pipelines.
- Provider abstraction boundary and error handling (timeout, rate-limit, malformed output).
- Unconfigured provider graceful degradation.
- Safe retries and duplicate job prevention.
- Atomic persistence of AI screening fields.
- Complete isolation from legacy ML models.
"""

from datetime import datetime, timezone
import json
import os
import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.api.schemas.gemma_analysis import GemmaHazardOutput
from backend.app.database.base import Base, get_db
from backend.app.database.models import FieldReport
from backend.app.main import app
from backend.app.services.gemma_analysis_service import GemmaAnalysisService
from backend.app.services.gemma_providers import (
    GemmaMalformedOutputError,
    GemmaProviderError,
    GemmaProviderUnavailableError,
    GemmaRateLimitError,
    GemmaTemporaryUnavailableError,
    GemmaTimeoutError,
    GoogleGenAIGemmaProvider,
    MockGemmaProvider,
    UnconfiguredGemmaProvider,
)
from backend.app.services.photo_storage_service import LocalStorageAdapter


class TestGemmaAnalysisPipeline(unittest.TestCase):
    """Test suite for Gemma AI FieldReport hazard screening."""

    @classmethod
    def setUpClass(cls):
        # Register SQLite dialect mappings for PostgreSQL JSONB and UUID
        from sqlalchemy.dialects.postgresql import JSONB, UUID
        from sqlalchemy.ext.compiler import compiles

        @compiles(JSONB, "sqlite")
        def compile_jsonb_sqlite(type_, compiler, **kw):
            return "TEXT"

        @compiles(UUID, "sqlite")
        def compile_uuid_sqlite(type_, compiler, **kw):
            return "TEXT"

        # Remove postgres-specific cast server_default for sqlite creation
        FieldReport.__table__.c.ai_detected_hazards.server_default = None

        # In-memory SQLite for isolated unit testing
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        cls.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )
        from backend.app.database.models import User
        Base.metadata.create_all(bind=cls.engine, tables=[User.__table__, FieldReport.__table__])

    def setUp(self):
        self.db = self.SessionLocal()
        self.mock_storage = MagicMock(spec=LocalStorageAdapter)
        self.client = TestClient(app)

        # Override dependency
        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.rollback()
        # Clean reports table
        self.db.query(FieldReport).delete()
        self.db.commit()
        self.db.close()

    def _create_test_report(
        self,
        notes: str = "Tension cracks across road shoulder",
        photo_url: str = None,
    ) -> FieldReport:
        report = FieldReport(
            id=uuid4(),
            notes=notes,
            location_name="Peshok Hill Road",
            latitude=27.04,
            longitude=88.26,
            photo_url=photo_url,
            ai_hazard_level="indeterminate",
            ai_detected_hazards=[],
            ai_confidence=None,
            ai_summary=None,
            ai_analyzed_at=None,
            review_status="pending",
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def test_text_only_analysis_with_mock_provider(self):
        """Report without photo should perform text analysis with explicit limitations noted."""
        report = self._create_test_report(notes="Significant cracks and slope slump detected")
        provider = MockGemmaProvider()
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        updated = asyncio.run(service.analyze_report(report.id))

        self.assertEqual(updated.ai_hazard_level, "moderate")
        self.assertIn("tension_cracks", updated.ai_detected_hazards)
        self.assertIsNotNone(updated.ai_confidence)
        self.assertGreater(updated.ai_confidence, 0.5)
        self.assertIsNotNone(updated.ai_analyzed_at)
        self.assertIn("text-only", updated.ai_summary.lower())

    def test_multimodal_analysis_with_photo(self):
        """Report with photo should load bytes from storage and perform multimodal screening."""
        fake_photo_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100
        self.mock_storage.read_photo.return_value = (fake_photo_bytes, "image/jpeg")

        report = self._create_test_report(
            notes="Massive debris flow completely blocked highway",
            photo_url="/uploads/field_reports/landslide_1.jpg",
        )
        provider = MockGemmaProvider()
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        updated = asyncio.run(service.analyze_report(report.id))

        self.mock_storage.read_photo.assert_called_once_with("/uploads/field_reports/landslide_1.jpg")
        self.assertEqual(updated.ai_hazard_level, "critical")
        self.assertIn("road_blockage", updated.ai_detected_hazards)
        self.assertIn("slope_displacement", updated.ai_detected_hazards)
        self.assertIsNotNone(updated.ai_analyzed_at)
        self.assertIn("multimodal", updated.ai_summary.lower())

    def test_unconfigured_provider_fails_safely_without_crashing(self):
        """When no Gemma provider is configured, report records UNAVAILABLE state without low-risk default."""
        report = self._create_test_report()
        provider = UnconfiguredGemmaProvider()
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        updated = asyncio.run(service.analyze_report(report.id))

        self.assertEqual(updated.ai_hazard_level, "indeterminate")
        self.assertIsNone(updated.ai_analyzed_at)
        self.assertIsNone(updated.ai_confidence)
        self.assertIn("[UNAVAILABLE]", updated.ai_summary)

    def test_timeout_error_handling(self):
        """Inference timeout sets temporary unavailable summary and retains indeterminate level."""
        report = self._create_test_report()
        provider = MockGemmaProvider(simulate_timeout=True)
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        updated = asyncio.run(service.analyze_report(report.id))

        self.assertEqual(updated.ai_hazard_level, "indeterminate")
        self.assertEqual(updated.ai_detected_hazards, [])
        self.assertIsNone(updated.ai_analyzed_at)
        self.assertIsNone(updated.ai_confidence)
        self.assertIn("[UNAVAILABLE]", updated.ai_summary)
        self.assertIn("timed out", updated.ai_summary.lower())

    def test_rate_limit_error_handling(self):
        """Rate limit error sets temporary unavailable summary and retains indeterminate level."""
        report = self._create_test_report()
        provider = MockGemmaProvider(simulate_rate_limit=True)
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        updated = asyncio.run(service.analyze_report(report.id))

        self.assertEqual(updated.ai_hazard_level, "indeterminate")
        self.assertEqual(updated.ai_detected_hazards, [])
        self.assertIsNone(updated.ai_analyzed_at)
        self.assertIsNone(updated.ai_confidence)
        self.assertIn("[UNAVAILABLE]", updated.ai_summary)
        self.assertIn("rate limit", updated.ai_summary.lower())

    def test_503_temporary_unavailable_error_handling(self):
        """Provider 503 unavailable error sets clean temporary status without leaking internal dicts."""
        report = self._create_test_report()
        provider = MockGemmaProvider(simulate_unavailable=True)
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        updated = asyncio.run(service.analyze_report(report.id))

        self.assertEqual(updated.ai_hazard_level, "indeterminate")
        self.assertEqual(updated.ai_detected_hazards, [])
        self.assertIsNone(updated.ai_analyzed_at)
        self.assertIsNone(updated.ai_confidence)
        self.assertIn("[UNAVAILABLE]", updated.ai_summary)
        self.assertIn("temporarily unavailable", updated.ai_summary.lower())
        # Confirm no raw stack trace or raw JSON error dict leaks
        self.assertNotIn("{'error':", updated.ai_summary)
        self.assertNotIn("Traceback", updated.ai_summary)

    def test_stale_hazards_cleared_on_reanalysis_failure(self):
        """Re-analyzing an existing report that encounters a failure must clear previously detected hazards."""
        report = self._create_test_report(notes="Tension crack with initial detection")
        report.ai_hazard_level = "high"
        report.ai_detected_hazards = ["tension_cracks", "slope_displacement"]
        report.ai_confidence = 0.88
        report.ai_summary = "High risk slope failure"
        report.ai_analyzed_at = datetime.now(timezone.utc)
        self.db.commit()

        # Re-run with force=True, but provider encounters 503 temporary unavailable
        provider = MockGemmaProvider(simulate_unavailable=True)
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        updated = asyncio.run(service.analyze_report(report.id, force=True))

        self.assertEqual(updated.ai_hazard_level, "indeterminate")
        # Critical safety check: old hazards must NOT be retained
        self.assertEqual(updated.ai_detected_hazards, [])
        self.assertIsNone(updated.ai_confidence)
        self.assertIsNone(updated.ai_analyzed_at)
        self.assertIn("[UNAVAILABLE]", updated.ai_summary)

    def test_successful_retry_after_temporary_failure(self):
        """A report in temporary unavailable state can be successfully retried and populated with fresh results."""
        report = self._create_test_report(notes="Toe erosion along river bank")
        report.ai_hazard_level = "indeterminate"
        report.ai_detected_hazards = []
        report.ai_confidence = None
        report.ai_summary = "[UNAVAILABLE] AI screening temporarily unavailable -- retry later."
        report.ai_analyzed_at = None
        self.db.commit()

        provider = MockGemmaProvider(
            custom_output=GemmaHazardOutput(
                hazard_level="moderate",
                detected_hazards=["toe_erosion"],
                confidence=0.81,
                summary="Active toe erosion identified along embankment.",
            )
        )
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        updated = asyncio.run(service.analyze_report(report.id, force=True))

        self.assertEqual(updated.ai_hazard_level, "moderate")
        self.assertEqual(updated.ai_detected_hazards, ["toe_erosion"])
        self.assertAlmostEqual(updated.ai_confidence, 0.81)
        self.assertIsNotNone(updated.ai_analyzed_at)
        self.assertIn("Active toe erosion", updated.ai_summary)

    def test_google_provider_maps_503_and_429_cleanly(self):
        """Google provider correctly catches 503 UNAVAILABLE and 429 quota errors into typed exceptions."""
        provider = GoogleGenAIGemmaProvider(api_key="test-api-key")

        # Mock genai client to raise 503 ServerError
        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            
            # Simulate 503 UNAVAILABLE
            class FakeServerError(Exception):
                code = 503
                message = "503 UNAVAILABLE: This model is currently experiencing high demand."
                def __str__(self):
                    return self.message

            mock_client.models.generate_content.side_effect = FakeServerError()

            import asyncio
            with self.assertRaises(GemmaTemporaryUnavailableError):
                asyncio.run(provider.analyze(notes="Test notes", location_name="Loc"))

            # Simulate 429 ResourceExhausted
            class FakeRateLimitError(Exception):
                code = 429
                message = "429 Resource Exhausted: Quota exceeded"
                def __str__(self):
                    return self.message

            mock_client.models.generate_content.side_effect = FakeRateLimitError()
            with self.assertRaises(GemmaRateLimitError):
                asyncio.run(provider.analyze(notes="Test notes", location_name="Loc"))

    def test_malformed_output_error_handling(self):
        """Malformed model output sets failure summary without crashing."""
        report = self._create_test_report()
        provider = MockGemmaProvider(simulate_malformed=True)
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        updated = asyncio.run(service.analyze_report(report.id))

        self.assertEqual(updated.ai_hazard_level, "indeterminate")
        self.assertEqual(updated.ai_detected_hazards, [])
        self.assertIsNone(updated.ai_analyzed_at)
        self.assertIn("[FAILED] Malformed model output", updated.ai_summary)

    def test_duplicate_job_skipped_unless_forced(self):
        """Already analyzed reports should not be re-processed unless force=True."""
        report = self._create_test_report(notes="Minor soil movement")
        report.ai_hazard_level = "low"
        report.ai_detected_hazards = ["soil_erosion"]
        report.ai_confidence = 0.85
        report.ai_summary = "Initial valid analysis"
        report.ai_analyzed_at = datetime(2026, 10, 22, 8, 0, 0, tzinfo=timezone.utc)
        self.db.commit()

        # Provider configured with critical output
        provider = MockGemmaProvider(
            custom_output=GemmaHazardOutput(
                hazard_level="critical",
                detected_hazards=["catastrophic_failure"],
                confidence=0.99,
                summary="Should not overwrite unless forced",
            )
        )
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        # Run without force
        res = asyncio.run(service.analyze_report(report.id, force=False))
        self.assertEqual(res.ai_hazard_level, "low")
        self.assertEqual(res.ai_summary, "Initial valid analysis")

        # Run with force
        res_forced = asyncio.run(service.analyze_report(report.id, force=True))
        self.assertEqual(res_forced.ai_hazard_level, "critical")
        self.assertEqual(res_forced.ai_summary, "Should not overwrite unless forced")

    def test_trigger_analyze_endpoint(self):
        """POST /api/field-reports/{id}/analyze triggers analysis."""
        report = self._create_test_report(notes="Active mudflow threatening road")

        with patch("backend.app.api.endpoints.field_reports.GemmaAnalysisService") as mock_srv_cls:
            mock_srv = MagicMock()
            mock_srv_cls.return_value = mock_srv

            # Setup analyzed report return
            report.ai_hazard_level = "high"
            report.ai_detected_hazards = ["mudflow"]
            report.ai_confidence = 0.82
            report.ai_summary = "Active mudflow detected"
            report.ai_analyzed_at = datetime.now(timezone.utc)

            import asyncio
            async def mock_analyze(*args, **kwargs):
                return report

            mock_srv.analyze_report.side_effect = mock_analyze

            resp = self.client.post(f"/api/field-reports/{report.id}/analyze")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["ai_hazard_level"], "high")
            self.assertEqual(data["ai_status"], "completed")

    def test_get_ai_analysis_endpoint(self):
        """GET /api/field-reports/{id}/ai-analysis returns detailed screening metadata."""
        report = self._create_test_report(notes="Crack in retaining wall")
        report.ai_hazard_level = "moderate"
        report.ai_detected_hazards = ["structural_damage"]
        report.ai_confidence = 0.77
        report.ai_summary = "Retaining wall displacement"
        report.ai_analyzed_at = datetime.now(timezone.utc)
        self.db.commit()

        resp = self.client.get(f"/api/field-reports/{report.id}/ai-analysis")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["report_id"], str(report.id))
        self.assertEqual(data["ai_status"], "completed")
        self.assertEqual(data["ai_hazard_level"], "moderate")
        self.assertIn("structural_damage", data["ai_detected_hazards"])
        self.assertIn("Preliminary AI hazard screening", data["disclaimer"])

    def test_legacy_ml_never_loaded_during_analysis(self):
        """Confirm legacy ML models and heavy runtimes (xgboost, joblib) remain completely unloaded."""
        import sys
        self.assertNotIn("xgboost", sys.modules)
        self.assertNotIn("joblib", sys.modules)

    def test_in_flight_processing_skips_concurrent_duplicate(self):
        """A report marked as [PROCESSING] should be protected against concurrent duplication unless forced."""
        report = self._create_test_report(notes="Active slope creep")
        report.ai_summary = "[PROCESSING] In flight with worker A"
        self.db.commit()

        provider = MockGemmaProvider(
            custom_output=GemmaHazardOutput(
                hazard_level="critical",
                detected_hazards=["mudflow"],
                confidence=0.95,
                summary="Overwritten output",
            )
        )
        service = GemmaAnalysisService(self.db, storage=self.mock_storage, provider=provider)

        import asyncio
        # Concurrent invocation without force should be skipped
        res_skipped = asyncio.run(service.analyze_report(report.id, force=False))
        self.assertTrue(res_skipped.ai_summary.startswith("[PROCESSING]"))

        # Explicit forced re-analysis proceeds
        res_forced = asyncio.run(service.analyze_report(report.id, force=True))
        self.assertEqual(res_forced.ai_hazard_level, "critical")
        self.assertIn("Overwritten output", res_forced.ai_summary)

    def test_prompt_injection_safety_and_schema_normalization(self):
        """Prompt injection attempts or rogue category strings must normalize safely to indeterminate."""
        malicious_output = GemmaHazardOutput(
            hazard_level="EXTREME_SAFE_ALL_CLEAR",  # Non-standard rogue string
            detected_hazards=["all_clear_no_danger"],
            confidence=0.1,
            summary="Attacker asserts site is completely safe",
        )
        # Normalizer must map unknown levels to indeterminate
        self.assertEqual(malicious_output.hazard_level, "indeterminate")


if __name__ == "__main__":
    unittest.main()
