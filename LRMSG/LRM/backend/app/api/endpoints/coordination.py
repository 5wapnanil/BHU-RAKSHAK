"""Coordination API routes — volunteers, matching, assignments, relief resources, requests.

STEP 7K: Backend coordination foundation.
STEP 8A: Added GET /api/requests for dashboard consumption.

IMPORTANT: Coordinator endpoints (verify, assign, allocate) require authorization.
Currently marked with TODO for auth middleware. Do NOT expose without auth in production.
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.database.base import get_db
from backend.app.api.deps import verify_coordinator_authorization
from backend.app.services.volunteer_service import VolunteerService
from backend.app.services.assignment_service import AssignmentService
from backend.app.services.relief_resource_service import ReliefResourceService
from backend.app.services.shelter_service import ShelterService
from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.emergency_request_service import EmergencyRequestService
from backend.app.database.repositories.audit_history_repository import AuditHistoryRepository
from backend.app.api.schemas.coordination import (
    VolunteerProfileCreate,
    VolunteerProfileResponse,
    VolunteerStatusUpdate,
    CandidateVolunteerResponse,
    MatchingRequest,
    AssignmentCreate,
    AssignmentStatusUpdate,
    AssignmentResponse,
    ReliefResourceCreate,
    ReliefResourceResponse,
    ResourceAllocationRequest,
    ShelterCreate,
    ShelterUpdate,
    ShelterResponse,
    AuditResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ────────────────────────────────────────────────────────────
# VOLUNTEER ENDPOINTS
# ────────────────────────────────────────────────────────────

@router.post("/volunteers", response_model=VolunteerProfileResponse, tags=["volunteers"])
def create_volunteer_profile(
    body: VolunteerProfileCreate,
    db: Session = Depends(get_db),
):
    """Register a new volunteer profile."""
    svc = VolunteerService(db)
    try:
        profile = svc.create_profile(
            user_id=body.user_id,
            skills=body.skills,
            has_transport=body.has_transport,
            capacity=body.capacity,
            availability=body.availability,
            latitude=body.latitude,
            longitude=body.longitude,
        )
        db.commit()
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/volunteers", response_model=list[VolunteerProfileResponse], tags=["volunteers"])
def list_volunteers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all volunteer profiles."""
    svc = VolunteerService(db)
    return svc.get_all_profiles(skip=skip, limit=limit)


@router.get("/volunteers/{volunteer_id}", response_model=VolunteerProfileResponse, tags=["volunteers"])
def get_volunteer(
    volunteer_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a volunteer profile by ID."""
    svc = VolunteerService(db)
    profile = svc.get_profile(volunteer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return profile


# ── Coordinator-only endpoints (enforces verify_coordinator_authorization) ──

@router.post("/volunteers/{volunteer_id}/verify", response_model=VolunteerProfileResponse, tags=["volunteers"])
def verify_volunteer(
    volunteer_id: UUID,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Verify a volunteer. COORDINATOR ONLY — requires coordinator authorization."""
    svc = VolunteerService(db)
    try:
        profile = svc.verify_volunteer(volunteer_id)
        db.commit()
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/volunteers/{volunteer_id}/activate", response_model=VolunteerProfileResponse, tags=["volunteers"])
def activate_volunteer(
    volunteer_id: UUID,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Activate a verified volunteer. COORDINATOR ONLY — requires coordinator authorization."""
    svc = VolunteerService(db)
    try:
        profile = svc.activate_volunteer(volunteer_id)
        db.commit()
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/volunteers/{volunteer_id}/status", response_model=VolunteerProfileResponse, tags=["volunteers"])
def update_volunteer_status(
    volunteer_id: UUID,
    body: VolunteerStatusUpdate,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Update volunteer status. COORDINATOR ONLY — requires coordinator authorization."""
    svc = VolunteerService(db)
    try:
        profile = svc.update_status(volunteer_id, body.status)
        db.commit()
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ────────────────────────────────────────────────────────────
# MATCHING ENDPOINTS
# ────────────────────────────────────────────────────────────

@router.get(
    "/requests/{request_id}/candidates",
    response_model=list[CandidateVolunteerResponse],
    tags=["matching"],
)
def get_candidates(
    request_id: UUID,
    radius_km: float = 25.0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Find candidate volunteers for an emergency request."""
    engine = MatchingEngine(db)
    candidates = engine.find_candidates(
        request_id=request_id,
        radius_km=radius_km,
        limit=limit,
    )
    return candidates


# ────────────────────────────────────────────────────────────
# ASSIGNMENT ENDPOINTS
# ────────────────────────────────────────────────────────────

@router.get("/assignments", response_model=list[AssignmentResponse], tags=["assignments"])
def list_assignments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all assignments."""
    svc = AssignmentService(db)
    return svc.get_all_assignments(skip=skip, limit=limit)


@router.post("/assignments", response_model=AssignmentResponse, tags=["assignments"])
def create_assignment(
    body: AssignmentCreate,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Create a volunteer assignment. COORDINATOR ONLY — requires coordinator authorization."""
    svc = AssignmentService(db)
    try:
        assignment = svc.create_volunteer_assignment(
            request_id=body.request_id,
            volunteer_id=body.volunteer_id,
            notes=body.notes,
        )
        db.commit()
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse, tags=["assignments"])
def get_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
):
    """Get an assignment by ID."""
    svc = AssignmentService(db)
    assignment = svc.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.patch(
    "/assignments/{assignment_id}/status",
    response_model=AssignmentResponse,
    tags=["assignments"],
)
def update_assignment_status(
    assignment_id: UUID,
    body: AssignmentStatusUpdate,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Update assignment status. COORDINATOR ONLY — requires coordinator authorization."""
    svc = AssignmentService(db)
    try:
        assignment = svc.transition_status(
            assignment_id,
            body.status,
            notes=body.notes,
        )
        db.commit()
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/requests/{request_id}/assignments",
    response_model=list[AssignmentResponse],
    tags=["assignments"],
)
def get_assignments_for_request(
    request_id: UUID,
    db: Session = Depends(get_db),
):
    """Get all assignments for a specific request."""
    svc = AssignmentService(db)
    return svc.get_assignments_for_request(request_id)


# ────────────────────────────────────────────────────────────
# RELIEF RESOURCE ENDPOINTS
# ────────────────────────────────────────────────────────────

@router.post("/relief-resources", response_model=ReliefResourceResponse, tags=["resources"])
def create_resource(
    body: ReliefResourceCreate,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Create a relief resource. COORDINATOR ONLY — requires coordinator authorization."""
    svc = ReliefResourceService(db)
    try:
        resource = svc.create_resource(
            resource_type=body.resource_type,
            description=body.description,
            quantity=body.quantity,
            unit=body.unit,
            provider_id=body.provider_id,
            latitude=body.latitude,
            longitude=body.longitude,
        )
        db.commit()
        return resource
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/relief-resources", response_model=list[ReliefResourceResponse], tags=["resources"])
def list_resources(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all relief resources."""
    svc = ReliefResourceService(db)
    return svc.get_all_resources(skip=skip, limit=limit)


@router.get("/relief-resources/{resource_id}", response_model=ReliefResourceResponse, tags=["resources"])
def get_resource(
    resource_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a relief resource by ID."""
    svc = ReliefResourceService(db)
    resource = svc.get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Relief resource not found")
    return resource


@router.post(
    "/relief-resources/{resource_id}/allocate",
    response_model=AssignmentResponse,
    tags=["resources"],
)
def allocate_resource(
    resource_id: UUID,
    body: ResourceAllocationRequest,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Allocate a resource to a request. COORDINATOR ONLY — requires coordinator authorization."""
    svc = ReliefResourceService(db)
    try:
        assignment = svc.allocate_resource(
            resource_id=resource_id,
            request_id=body.request_id,
            quantity=body.quantity,
            notes=body.notes,
        )
        db.commit()
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/relief-resources/allocations/{assignment_id}/release",
    response_model=AssignmentResponse,
    tags=["resources"],
)
def release_allocation(
    assignment_id: UUID,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Release a resource allocation. COORDINATOR ONLY — requires coordinator authorization."""
    svc = ReliefResourceService(db)
    try:
        assignment = svc.release_allocation(assignment_id)
        db.commit()
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ────────────────────────────────────────────────────────────
# EMERGENCY REQUEST ENDPOINTS (STEP 8A)
# ────────────────────────────────────────────────────────────

class EmergencyRequestResponse(BaseModel):
    id: str
    client_op_id: Optional[str] = None
    request_type: str
    status: str
    server_status: Optional[str] = None
    severity: Optional[str] = None
    location_text: Optional[str] = None
    people_affected: Optional[int] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    payload: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/requests", response_model=list[EmergencyRequestResponse], tags=["requests"])
def list_emergency_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all emergency requests from the database."""
    svc = EmergencyRequestService(db)
    records = svc.get_all_requests(skip=skip, limit=limit)
    return [
        EmergencyRequestResponse(
            id=str(r.id),
            client_op_id=r.client_op_id,
            request_type=r.request_type,
            status=r.status,
            server_status=r.server_status,
            severity=r.severity,
            location_text=r.location_text,
            people_affected=r.people_affected,
            contact_name=r.contact_name,
            contact_phone=r.contact_phone,
            payload=r.payload,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
        )
        for r in records
    ]


@router.get("/requests/{request_id}", response_model=EmergencyRequestResponse, tags=["requests"])
def get_emergency_request(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Get a single emergency request by ID."""
    svc = EmergencyRequestService(db)
    from uuid import UUID as _UUID
    try:
        uid = _UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
    record = svc.get_request_by_db_id(uid)
    if not record:
        raise HTTPException(status_code=404, detail="Emergency request not found")
    return EmergencyRequestResponse(
        id=str(record.id),
        client_op_id=record.client_op_id,
        request_type=record.request_type,
        status=record.status,
        server_status=record.server_status,
        severity=record.severity,
        location_text=record.location_text,
        people_affected=record.people_affected,
        contact_name=record.contact_name,
        contact_phone=record.contact_phone,
        payload=record.payload,
        created_at=record.created_at.isoformat() if record.created_at else None,
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
    )


# ────────────────────────────────────────────────────────────
# SHELTER ENDPOINTS
# ────────────────────────────────────────────────────────────

@router.get("/shelters", response_model=list[ShelterResponse], tags=["shelters"])
def list_shelters(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all shelters."""
    svc = ShelterService(db)
    return svc.get_all_shelters(skip=skip, limit=limit)


@router.get("/shelters/{shelter_id}", response_model=ShelterResponse, tags=["shelters"])
def get_shelter(
    shelter_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a shelter by ID."""
    svc = ShelterService(db)
    shelter = svc.get_shelter(shelter_id)
    if not shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
    return shelter


@router.post("/shelters", response_model=ShelterResponse, tags=["shelters"])
def create_shelter(
    body: ShelterCreate,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Create a new shelter. COORDINATOR ONLY — requires coordinator authorization."""
    svc = ShelterService(db)
    try:
        shelter = svc.create_shelter(
            name=body.name,
            address=body.address,
            capacity=body.capacity,
            current_occupancy=body.current_occupancy,
            facilities=body.facilities,
            contact_phone=body.contact_phone,
            operated_by=body.operated_by,
            latitude=body.latitude,
            longitude=body.longitude,
        )
        db.commit()
        return shelter
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/shelters/{shelter_id}", response_model=ShelterResponse, tags=["shelters"])
def update_shelter(
    shelter_id: UUID,
    body: ShelterUpdate,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Update a shelter. COORDINATOR ONLY — requires coordinator authorization."""
    svc = ShelterService(db)
    update_fields = body.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        shelter = svc.update_shelter(shelter_id, **update_fields)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
    db.commit()
    return shelter


# ────────────────────────────────────────────────────────────
# AUDIT HISTORY ENDPOINTS
# ────────────────────────────────────────────────────────────

VALID_AUDIT_ENTITY_TYPES = {"request", "volunteer", "assignment", "alert", "resource", "shelter", "incident"}


@router.get("/audit-history", response_model=list[AuditResponse], tags=["audit"])
def list_audit_history(
    entity_type: Optional[str] = Query(default=None),
    entity_id: Optional[UUID] = Query(default=None),
    action: Optional[str] = Query(default=None),
    actor_id: Optional[UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """List audit history records with optional filtering. (COORDINATOR ONLY)."""
    if entity_type is not None and entity_type not in VALID_AUDIT_ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity_type. Must be one of: {sorted(VALID_AUDIT_ENTITY_TYPES)}",
        )
    repo = AuditHistoryRepository(db)
    return repo.list_audit_entries(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.get("/audit-history/{audit_id}", response_model=AuditResponse, tags=["audit"])
def get_audit_entry(
    audit_id: UUID,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    """Get a single audit history record by ID. (COORDINATOR ONLY)."""
    repo = AuditHistoryRepository(db)
    entry = repo.get_by_id(audit_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    return entry
