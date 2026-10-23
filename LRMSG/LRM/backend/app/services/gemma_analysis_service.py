"""Orchestration service for Gemma AI field report analysis.

Loads trusted persisted reports and photographs from storage, runs analysis through
the active provider, enforces structured output validation, updates PostgreSQL
records atomically, and prevents duplicate jobs or stale overwrites.
"""

from datetime import datetime, timezone
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.api.schemas.gemma_analysis import (
    FieldReportAIAnalysisResponse,
    GemmaHazardOutput,
)
from backend.app.database.models import FieldReport
from backend.app.database.repositories.field_report_repository import FieldReportRepository
from backend.app.services.gemma_providers import (
    AnalysisProvider,
    GemmaMalformedOutputError,
    GemmaProviderError,
    GemmaProviderUnavailableError,
    GemmaRateLimitError,
    GemmaTemporaryUnavailableError,
    GemmaTimeoutError,
    get_gemma_provider,
)
from backend.app.services.photo_storage_service import (
    LocalStorageAdapter,
    photo_storage_service,
)

logger = logging.getLogger(__name__)


class GemmaAnalysisService:
    """Service orchestrating AI multimodal landslide hazard screening."""

    def __init__(
        self,
        db: Session,
        storage: Optional[LocalStorageAdapter] = None,
        provider: Optional[AnalysisProvider] = None,
    ):
        self.db = db
        self.repo = FieldReportRepository(db)
        self.storage = storage or photo_storage_service
        self.provider = provider or get_gemma_provider()

    async def analyze_report(
        self,
        report_id: UUID,
        *,
        force: bool = False,
    ) -> FieldReport:
        """Execute multimodal hazard screening for a persisted field report.

        - Idempotent: Skips re-analysis if already completed unless `force=True`.
        - Non-blocking: Can be dispatched as a background task.
        - Fail-safe: Records explicit error messages without overwriting valid data
          or fabricating low-risk predictions.
        """
        report = self.repo.get_by_id(report_id)
        if report is None:
            raise ValueError(f"Field report with ID '{report_id}' not found.")

        # Duplicate job prevention: do not rerun completed analysis unless explicitly requested
        if report.ai_analyzed_at is not None and not force:
            logger.info(f"Report {report_id} is already analyzed (completed at {report.ai_analyzed_at}). Skipping.")
            return report

        # Concurrent in-flight job prevention: do not stampede provider if already processing
        if (
            report.ai_summary
            and report.ai_summary.startswith("[PROCESSING]")
            and not force
        ):
            logger.info(
                f"Report {report_id} is currently being processed by another worker. Skipping concurrent invocation."
            )
            return report

        # Atomically record processing state to signal in-flight status; clear stale indicators
        self.repo.update_ai_analysis(
            report_id=report_id,
            ai_hazard_level="indeterminate",
            ai_detected_hazards=[],
            ai_confidence=None,
            ai_summary=f"[PROCESSING] Preliminary screening dispatched via {self.provider.provider_name}...",
            ai_analyzed_at=None,
        )
        self.db.commit()

        # Read photo bytes safely from configured storage adapter
        photo_bytes: Optional[bytes] = None
        photo_mime: Optional[str] = None
        if report.photo_url:
            photo_data = self.storage.read_photo(report.photo_url)
            if photo_data:
                photo_bytes, photo_mime = photo_data

        try:
            logger.info(f"Starting Gemma analysis for report {report_id} using {self.provider.provider_name}...")
            output: GemmaHazardOutput = await self.provider.analyze(
                notes=report.notes,
                location_name=report.location_name,
                photo_bytes=photo_bytes,
                photo_mime=photo_mime,
            )

            # Atomic database update with validated output
            now_utc = datetime.now(timezone.utc)
            updated = self.repo.update_ai_analysis(
                report_id=report_id,
                ai_hazard_level=output.hazard_level,
                ai_detected_hazards=output.detected_hazards,
                ai_confidence=output.confidence,
                ai_summary=output.summary,
                ai_analyzed_at=now_utc,
            )
            self.db.commit()
            logger.info(f"Successfully saved Gemma analysis for report {report_id}: {output.hazard_level}")
            return updated or report

        except GemmaProviderUnavailableError as e:
            logger.warning(f"AI provider unconfigured for report {report_id}: {e}")
            updated = self.repo.update_ai_analysis(
                report_id=report_id,
                ai_hazard_level="indeterminate",
                ai_detected_hazards=[],
                ai_confidence=None,
                ai_summary="[UNAVAILABLE] AI provider is not configured. Configure GEMINI_API_KEY or local runtime.",
                ai_analyzed_at=None,
            )
            self.db.commit()
            return updated or report

        except GemmaTemporaryUnavailableError as e:
            logger.warning(f"AI provider temporarily unavailable for report {report_id}: {e}", exc_info=True)
            updated = self.repo.update_ai_analysis(
                report_id=report_id,
                ai_hazard_level="indeterminate",
                ai_detected_hazards=[],
                ai_confidence=None,
                ai_summary="[UNAVAILABLE] AI screening temporarily unavailable -- retry later.",
                ai_analyzed_at=None,
            )
            self.db.commit()
            return updated or report

        except GemmaRateLimitError as e:
            logger.warning(f"AI rate limit exceeded for report {report_id}: {e}", exc_info=True)
            updated = self.repo.update_ai_analysis(
                report_id=report_id,
                ai_hazard_level="indeterminate",
                ai_detected_hazards=[],
                ai_confidence=None,
                ai_summary="[UNAVAILABLE] AI screening temporarily unavailable (rate limit exceeded) -- retry later.",
                ai_analyzed_at=None,
            )
            self.db.commit()
            return updated or report

        except GemmaTimeoutError as e:
            logger.warning(f"AI inference timed out for report {report_id}: {e}", exc_info=True)
            updated = self.repo.update_ai_analysis(
                report_id=report_id,
                ai_hazard_level="indeterminate",
                ai_detected_hazards=[],
                ai_confidence=None,
                ai_summary="[UNAVAILABLE] AI screening temporarily unavailable (request timed out) -- retry later.",
                ai_analyzed_at=None,
            )
            self.db.commit()
            return updated or report

        except GemmaMalformedOutputError as e:
            logger.error(f"AI model output malformed for report {report_id}: {e}", exc_info=True)
            updated = self.repo.update_ai_analysis(
                report_id=report_id,
                ai_hazard_level="indeterminate",
                ai_detected_hazards=[],
                ai_confidence=None,
                ai_summary="[FAILED] Malformed model output -- validation failed.",
                ai_analyzed_at=None,
            )
            self.db.commit()
            return updated or report

        except (GemmaProviderError, Exception) as e:
            logger.error(f"AI analysis failed for report {report_id}: {e}", exc_info=True)
            updated = self.repo.update_ai_analysis(
                report_id=report_id,
                ai_hazard_level="indeterminate",
                ai_detected_hazards=[],
                ai_confidence=None,
                ai_summary="[FAILED] AI screening failed due to an unexpected error. Please retry later.",
                ai_analyzed_at=None,
            )
            self.db.commit()
            return updated or report

    def get_analysis_details(self, report_id: UUID) -> Optional[FieldReportAIAnalysisResponse]:
        """Fetch dedicated analysis metadata for a field report."""
        report = self.repo.get_by_id(report_id)
        if report is None:
            return None

        # Resolve status
        if report.ai_analyzed_at is not None:
            status = "completed"
        elif report.ai_summary and report.ai_summary.startswith("[FAILED]"):
            status = "failed"
        elif report.ai_summary and (
            report.ai_summary.startswith("[UNAVAILABLE]")
            or report.ai_summary.startswith("[NOT_CONFIGURED]")
        ):
            status = "unavailable"
        elif report.ai_summary and report.ai_summary.startswith("[PROCESSING]"):
            status = "processing"
        else:
            status = "pending"

        provider_name = self.provider.provider_name
        if report.ai_summary and "[Inference Provider: " in report.ai_summary:
            try:
                prov = report.ai_summary.split("[Inference Provider: ")[1].split("]")[0]
                if prov:
                    provider_name = prov.strip()
            except Exception:
                pass

        return FieldReportAIAnalysisResponse(
            report_id=report.id,
            ai_status=status,
            ai_hazard_level=report.ai_hazard_level,
            ai_detected_hazards=report.ai_detected_hazards or [],
            ai_confidence=report.ai_confidence,
            ai_summary=report.ai_summary,
            ai_analyzed_at=report.ai_analyzed_at,
            provider_name=provider_name,
            has_photo=bool(report.photo_url),
        )
