"""Repository layer for FieldReport entities in PostgreSQL/PostGIS."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database.models import FieldReport
from backend.app.database.repositories.base import BaseRepository


class FieldReportRepository(BaseRepository[FieldReport]):
    """Data-access repository for citizen and responder ground field reports."""

    def __init__(self, db: Session):
        super().__init__(FieldReport, db)

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
        """Create a new field report with geospatial point generation."""
        # Location spatial construction: ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        location_val = None
        if latitude is not None and longitude is not None:
            # Check database dialect to support both PostgreSQL PostGIS and test environments
            dialect = self.db.bind.dialect.name if self.db.bind else "postgresql"
            if dialect == "postgresql":
                location_val = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
            else:
                location_val = f"SRID=4326;POINT({longitude} {latitude})"

        report = FieldReport(
            photo_url=photo_url,
            notes=notes,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            location=location_val,
            reporter_name=reporter_name,
            reporter_phone=reporter_phone,
            # AI Screening defaults (untrusted client cannot populate)
            ai_hazard_level="indeterminate",
            ai_detected_hazards=[],
            ai_confidence=None,
            ai_summary=None,
            ai_analyzed_at=None,
            # Review defaults
            review_status="pending",
            reviewed_at=None,
            reviewed_by=None,
            admin_notes=None,
        )

        self.db.add(report)
        self.db.flush()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: UUID) -> Optional[FieldReport]:
        """Fetch report by UUID primary key."""
        stmt = select(FieldReport).where(FieldReport.id == report_id)
        return self.db.execute(stmt).scalar_one_or_none()

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
        """Query reports with filtering, pagination, and total count."""
        base_query = select(FieldReport)
        count_query = select(func.count(FieldReport.id))

        if review_status:
            base_query = base_query.where(FieldReport.review_status == review_status)
            count_query = count_query.where(FieldReport.review_status == review_status)

        if ai_hazard_level:
            base_query = base_query.where(FieldReport.ai_hazard_level == ai_hazard_level)
            count_query = count_query.where(FieldReport.ai_hazard_level == ai_hazard_level)

        if start_date:
            base_query = base_query.where(FieldReport.submitted_at >= start_date)
            count_query = count_query.where(FieldReport.submitted_at >= start_date)

        if end_date:
            base_query = base_query.where(FieldReport.submitted_at <= end_date)
            count_query = count_query.where(FieldReport.submitted_at <= end_date)

        total = self.db.execute(count_query).scalar() or 0

        # Most recently submitted first
        ordered_query = (
            base_query.order_by(FieldReport.submitted_at.desc())
            .offset(offset)
            .limit(limit)
        )
        reports = list(self.db.execute(ordered_query).scalars().all())

        return reports, total

    def update_review(
        self,
        report_id: UUID,
        *,
        review_status: str,
        admin_notes: Optional[str] = None,
        reviewed_by: Optional[UUID] = None,
    ) -> Optional[FieldReport]:
        """Apply administrative review status transition."""
        report = self.get_by_id(report_id)
        if report is None:
            return None

        report.review_status = review_status
        report.reviewed_at = datetime.now(timezone.utc)
        if reviewed_by is not None:
            report.reviewed_by = reviewed_by
        if admin_notes is not None:
            report.admin_notes = admin_notes

        self.db.flush()
        self.db.refresh(report)
        return report

    def update_ai_analysis(
        self,
        report_id: UUID,
        *,
        ai_hazard_level: str,
        ai_detected_hazards: List[str],
        ai_confidence: Optional[float],
        ai_summary: Optional[str],
        ai_analyzed_at: Optional[datetime],
    ) -> Optional[FieldReport]:
        """Atomically update AI preliminary screening fields."""
        report = self.get_by_id(report_id)
        if report is None:
            return None

        report.ai_hazard_level = ai_hazard_level
        report.ai_detected_hazards = list(ai_detected_hazards) if ai_detected_hazards else []
        report.ai_confidence = ai_confidence
        report.ai_summary = ai_summary
        report.ai_analyzed_at = ai_analyzed_at

        self.db.flush()
        self.db.refresh(report)
        return report
