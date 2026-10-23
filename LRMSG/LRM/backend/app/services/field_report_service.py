"""Business logic service for PahaarPulse FieldReport management.

Coordinates validation, geospatial checks, photo staging, AI metadata protection,
and review state machine transitions.
"""

from datetime import datetime, timezone
import logging
from typing import BinaryIO, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.database.models import FieldReport
from backend.app.database.repositories.field_report_repository import FieldReportRepository
from backend.app.services.photo_storage_service import LocalStorageAdapter, photo_storage_service

logger = logging.getLogger(__name__)

VALID_REVIEW_STATUSES = {"pending", "verified", "rejected", "needs_inspection"}
VALID_AI_HAZARD_LEVELS = {"low", "moderate", "high", "critical", "indeterminate"}


class FieldReportService:
    """Service layer managing FieldReport domain logic and transactions."""

    def __init__(
        self,
        db: Session,
        storage: Optional[LocalStorageAdapter] = None,
    ):
        self.db = db
        self.repo = FieldReportRepository(db)
        self.storage = storage or photo_storage_service

    @staticmethod
    def validate_coordinates(
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> None:
        """Validate WGS-84 coordinate bounds and pair completeness."""
        has_lat = latitude is not None
        has_lon = longitude is not None

        if has_lat != has_lon:
            raise ValueError(
                "Both latitude and longitude must be provided together, or both omitted."
            )

        if has_lat and has_lon:
            if not (-90.0 <= latitude <= 90.0):
                raise ValueError(
                    f"Latitude must be between -90.0 and 90.0, got {latitude}"
                )
            if not (-180.0 <= longitude <= 180.0):
                raise ValueError(
                    f"Longitude must be between -180.0 and 180.0, got {longitude}"
                )

    def create_report(
        self,
        *,
        notes: Optional[str] = None,
        location_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        reporter_name: Optional[str] = None,
        reporter_phone: Optional[str] = None,
        photo_url: Optional[str] = None,
    ) -> FieldReport:
        """Create a field report with verified coordinate integrity.

        Enforces system defaults for preliminary AI screening metadata and review status.
        Client-supplied AI conclusions are strictly forbidden and never accepted.
        """
        self.validate_coordinates(latitude, longitude)

        # Sanitize optional string inputs
        clean_notes = notes.strip() if notes else None
        clean_loc = location_name.strip() if location_name else None
        clean_rep_name = reporter_name.strip() if reporter_name else None
        clean_rep_phone = reporter_phone.strip() if reporter_phone else None
        clean_photo_url = photo_url.strip() if photo_url else None

        report = self.repo.create_report(
            notes=clean_notes,
            location_name=clean_loc,
            latitude=latitude,
            longitude=longitude,
            reporter_name=clean_rep_name,
            reporter_phone=clean_rep_phone,
            photo_url=clean_photo_url,
        )
        return report

    def get_report(self, report_id: UUID) -> Optional[FieldReport]:
        """Retrieve a field report by UUID."""
        return self.repo.get_by_id(report_id)

    def list_reports(
        self,
        *,
        review_status: Optional[str] = None,
        ai_hazard_level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[FieldReport], int]:
        """List reports with validation of filter parameters and pagination."""
        if review_status and review_status not in VALID_REVIEW_STATUSES:
            allowed = ", ".join(sorted(VALID_REVIEW_STATUSES))
            raise ValueError(
                f"Invalid review_status '{review_status}'. Allowed: {allowed}"
            )

        if ai_hazard_level and ai_hazard_level not in VALID_AI_HAZARD_LEVELS:
            allowed = ", ".join(sorted(VALID_AI_HAZARD_LEVELS))
            raise ValueError(
                f"Invalid ai_hazard_level '{ai_hazard_level}'. Allowed: {allowed}"
            )

        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100.")

        if offset < 0:
            raise ValueError("Offset must be non-negative.")

        return self.repo.list_reports(
            review_status=review_status,
            ai_hazard_level=ai_hazard_level,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

    def review_report(
        self,
        report_id: UUID,
        *,
        review_status: str,
        admin_notes: Optional[str] = None,
        reviewed_by: Optional[UUID] = None,
    ) -> Optional[FieldReport]:
        """Apply an administrative review decision to a field report.

        Transitions: pending -> verified | rejected | needs_inspection.
        """
        if review_status not in VALID_REVIEW_STATUSES:
            allowed = ", ".join(sorted(VALID_REVIEW_STATUSES))
            raise ValueError(
                f"Invalid review_status '{review_status}'. Allowed: {allowed}"
            )

        report = self.repo.get_by_id(report_id)
        if report is None:
            return None

        clean_notes = admin_notes.strip() if admin_notes else None

        updated = self.repo.update_review(
            report_id,
            review_status=review_status,
            admin_notes=clean_notes,
            reviewed_by=reviewed_by,
        )
        return updated

    def save_uploaded_photo(
        self,
        stream: BinaryIO,
        content_type: str,
        size_hint: Optional[int] = None,
    ) -> Tuple[str, str, int]:
        """Store an uploaded photo using the configured storage adapter."""
        return self.storage.save_photo(stream, content_type, size_hint)
