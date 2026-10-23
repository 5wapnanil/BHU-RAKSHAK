"""FastAPI route endpoints for FieldReport operations.

Endpoints:
- POST  /api/field-reports              Create a field report (JSON or multipart with photo)
- POST  /api/field-reports/upload-photo Standalone photo upload endpoint
- GET   /api/field-reports              List reports with filtering and pagination
- GET   /api/field-reports/{report_id}  Get report by UUID
- PATCH /api/field-reports/{report_id}/review
                                        Update review status and admin notes

SECURITY / AUTHORIZATION NOTE:
The project currently has no global authentication/RBAC middleware. The review
endpoint is documented as coordinator-only and does not trust client-supplied user
identities. Do NOT expose this endpoint to unauthenticated public networks without
auth middleware.
"""

from datetime import datetime
import json
import logging
import os
import secrets
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.api.schemas.field_report import (
    FieldReportCreate,
    FieldReportListResponse,
    FieldReportResponse,
    FieldReportReviewRequest,
    PhotoUploadResponse,
)
from backend.app.api.schemas.gemma_analysis import FieldReportAIAnalysisResponse
from backend.app.database.base import SessionLocal, get_db
from backend.app.services.field_report_service import FieldReportService
from backend.app.services.gemma_analysis_service import GemmaAnalysisService
from backend.app.services.photo_storage_service import photo_storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_background_ai_analysis(report_id: UUID) -> None:
    """Asynchronously execute Gemma hazard analysis in background."""
    db = SessionLocal()
    try:
        service = GemmaAnalysisService(db)
        await service.analyze_report(report_id)
    except Exception as e:
        logger.error(f"Background AI analysis failed for report {report_id}: {e}", exc_info=True)
    finally:
        db.close()


@router.post(
    "",
    response_model=FieldReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a landslide field report",
    description="Submit an observation from mobile or web. Accepts either JSON payload or multipart/form-data with an attached photograph.",
)
async def create_field_report(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create a new field report with geospatial validation."""
    service = FieldReportService(db)
    content_type = request.headers.get("content-type", "")
    newly_saved_filename = None

    try:
        if content_type.startswith("multipart/form-data"):
            # Multipart form submission with optional file upload
            form = await request.form()
            notes = form.get("notes")
            location_name = form.get("location_name")
            reporter_name = form.get("reporter_name")
            reporter_phone = form.get("reporter_phone")
            photo_url = form.get("photo_url")

            raw_lat = form.get("latitude")
            raw_lon = form.get("longitude")
            latitude = float(raw_lat) if raw_lat is not None and str(raw_lat).strip() != "" else None
            longitude = float(raw_lon) if raw_lon is not None and str(raw_lon).strip() != "" else None

            # Handle optional uploaded photo file
            uploaded_file = form.get("photo")
            if hasattr(uploaded_file, "filename") and uploaded_file.filename:
                saved_url, saved_filename, _ = service.save_uploaded_photo(
                    uploaded_file.file,
                    uploaded_file.content_type,
                    uploaded_file.size,
                )
                photo_url = saved_url
                newly_saved_filename = saved_filename

            # Validate via Pydantic model
            create_dto = FieldReportCreate(
                notes=str(notes) if notes is not None else None,
                location_name=str(location_name) if location_name is not None else None,
                latitude=latitude,
                longitude=longitude,
                reporter_name=str(reporter_name) if reporter_name is not None else None,
                reporter_phone=str(reporter_phone) if reporter_phone is not None else None,
                photo_url=str(photo_url) if photo_url is not None else None,
            )
        else:
            # JSON payload
            try:
                body = await request.json()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON request body: {e}",
                )
            create_dto = FieldReportCreate.model_validate(body)

        report = service.create_report(
            notes=create_dto.notes,
            location_name=create_dto.location_name,
            latitude=create_dto.latitude,
            longitude=create_dto.longitude,
            reporter_name=create_dto.reporter_name,
            reporter_phone=create_dto.reporter_phone,
            photo_url=create_dto.photo_url,
        )
        db.commit()
        # Enqueue non-blocking background Gemma screening after transaction is safely committed
        background_tasks.add_task(_run_background_ai_analysis, report.id)
        return report

    except ValidationError as e:
        if newly_saved_filename:
            service.storage.delete_photo(newly_saved_filename)
        raise HTTPException(
            status_code=422,
            detail=json.loads(e.json()),
        )
    except ValueError as e:
        db.rollback()
        if newly_saved_filename:
            service.storage.delete_photo(newly_saved_filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        db.rollback()
        if newly_saved_filename:
            service.storage.delete_photo(newly_saved_filename)
        raise
    except Exception as e:
        db.rollback()
        if newly_saved_filename:
            service.storage.delete_photo(newly_saved_filename)
        logger.error(f"Failed to create field report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create field report due to an internal server error.",
        )


@router.post(
    "/upload-photo",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a field report photo",
    description="Stages an observation photograph and returns a server-controlled relative photo URL for report attachment.",
)
async def upload_field_report_photo(
    file: UploadFile = File(..., description="JPEG, PNG, or WebP photograph (max 10MB)"),
):
    """Upload and validate an observation photograph."""
    try:
        photo_url, filename, size_bytes = photo_storage_service.save_photo(
            file.file,
            file.content_type,
            file.size,
        )
        return PhotoUploadResponse(
            photo_url=photo_url,
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            size_bytes=size_bytes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Photo upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded photograph.",
        )


@router.get(
    "",
    response_model=FieldReportListResponse,
    summary="List field reports",
    description="Retrieve reports with optional status/AI screening filters and offset/limit pagination.",
)
def list_field_reports(
    review_status: Optional[str] = Query(
        None,
        description="Filter by review status: pending, verified, rejected, needs_inspection",
    ),
    ai_hazard_level: Optional[str] = Query(
        None,
        description="Filter by preliminary AI screening: low, moderate, high, critical, indeterminate",
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Filter reports submitted on or after this ISO datetime",
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Filter reports submitted on or before this ISO datetime",
    ),
    limit: int = Query(50, ge=1, le=100, description="Page limit (1-100)"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db),
):
    """List field reports with filtering and pagination."""
    service = FieldReportService(db)
    try:
        reports, total = service.list_reports(
            review_status=review_status,
            ai_hazard_level=ai_hazard_level,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        return FieldReportListResponse(
            items=reports,
            total=total,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{report_id}",
    response_model=FieldReportResponse,
    summary="Get single field report",
    description="Fetch a report by its UUID.",
)
def get_field_report(
    report_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve report by ID."""
    service = FieldReportService(db)
    report = service.get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field report not found.",
        )
    return report


from backend.app.api.deps import verify_coordinator_authorization


@router.patch(
    "/{report_id}/review",
    response_model=FieldReportResponse,
    summary="Review a field report",
    description="Update review status and administrative commentary. (COORDINATOR ONLY — requires authorization in production).",
)
def review_field_report(
    report_id: UUID,
    body: FieldReportReviewRequest,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Apply administrative review decision."""
    service = FieldReportService(db)
    try:
        # NOTE: When auth middleware is implemented, extract authenticated actor ID:
        # reviewed_by = current_user.id
        reviewed_by = None

        updated = service.review_report(
            report_id,
            review_status=body.review_status,
            admin_notes=body.admin_notes,
            reviewed_by=reviewed_by,
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Field report not found.",
            )

        db.commit()
        return updated

    except HTTPException:
        db.rollback()
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update report review status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update report review due to internal server error.",
        )


@router.post(
    "/{report_id}/analyze",
    response_model=FieldReportResponse,
    summary="Trigger or retry Gemma AI hazard analysis",
    description="Executes or re-triggers multimodal hazard analysis using the configured Gemma model.",
)
async def analyze_field_report(
    report_id: UUID,
    force: bool = Query(False, description="Force re-analysis even if previously completed"),
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Trigger or retry Gemma hazard analysis for a specific field report."""
    analysis_service = GemmaAnalysisService(db)
    try:
        report = await analysis_service.analyze_report(report_id, force=force)
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze report {report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference processing error: {e}",
        )


@router.get(
    "/{report_id}/ai-analysis",
    response_model=FieldReportAIAnalysisResponse,
    summary="Get detailed AI hazard screening analysis",
    description="Returns detailed model screening indicators, limitations, and confidence metadata.",
)
def get_field_report_ai_analysis(
    report_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve detailed AI screening metadata."""
    analysis_service = GemmaAnalysisService(db)
    details = analysis_service.get_analysis_details(report_id)
    if details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field report {report_id} not found",
        )
    return details
