"""Assignment coordination service.

Handles assignment creation, lifecycle transitions, concurrency protection,
and audit logging.
"""

import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database.repositories.assignment_repository import AssignmentRepository
from backend.app.database.repositories.emergency_request_repository import EmergencyRequestRepository
from backend.app.database.repositories.volunteer_profile_repository import VolunteerProfileRepository
from backend.app.database.repositories.audit_history_repository import AuditHistoryRepository
from backend.app.database.models import Assignment

logger = logging.getLogger(__name__)

# Valid assignment status transitions
VALID_ASSIGNMENT_TRANSITIONS = {
    "pending": ["accepted", "rejected", "cancelled"],
    "created": ["accepted", "cancelled"],
    "accepted": ["started", "in_progress", "cancelled"],
    "rejected": [],
    "started": ["completed", "cancelled"],
    "in_progress": ["completed", "cancelled"],
    "completed": [],
    "cancelled": [],
}


class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.request_repo = EmergencyRequestRepository(db)
        self.volunteer_repo = VolunteerProfileRepository(db)
        self.audit_repo = AuditHistoryRepository(db)

    def create_volunteer_assignment(
        self,
        request_id: UUID,
        volunteer_id: UUID,
        notes: str = None,
        actor_id: UUID = None,
    ) -> Assignment:
        """Create a volunteer assignment with full validation.

        Uses PostgreSQL row-level locking to prevent duplicate assignments.
        """
        # 1. Verify request exists and is assignable
        request = self.request_repo.get_by_id(request_id)
        if not request:
            raise ValueError(f"Emergency request {request_id} not found")
        if request.status not in ("pending", "in_progress"):
            raise ValueError(
                f"Request is not assignable (status='{request.status}'). "
                f"Must be 'pending' or 'in_progress'."
            )

        # 2. Verify volunteer exists and is eligible
        volunteer = self.volunteer_repo.get_by_id(volunteer_id)
        if not volunteer:
            raise ValueError(f"Volunteer profile {volunteer_id} not found")
        if volunteer.status != "active" or not volunteer.is_active:
            raise ValueError(
                f"Volunteer is not eligible for assignment "
                f"(status='{volunteer.status}', is_active={volunteer.is_active})"
            )

        # 3. Check for conflicting active assignments using SELECT FOR UPDATE
        #    This prevents two concurrent coordinators from assigning the same volunteer
        existing_active = self.db.execute(
            text(
                "SELECT id FROM assignments "
                "WHERE volunteer_id = :vid "
                "AND status IN ('pending', 'created', 'accepted', 'started', 'in_progress') "
                "FOR UPDATE"
            ),
            {"vid": str(volunteer_id)},
        ).fetchall()

        if existing_active:
            raise ValueError(
                f"Volunteer {volunteer_id} already has an active assignment "
                f"({len(existing_active)} active)"
            )

        # 4. Create the assignment
        assignment = self.assignment_repo.create(
            request_id=request_id,
            volunteer_id=volunteer_id,
            assignment_type="volunteer",
            status="pending",
            notes=notes,
        )

        # 5. Update request status to in_progress if currently pending
        if request.status == "pending":
            self.request_repo.update_status(request_id, "in_progress")

        # 6. Audit log
        self.audit_repo.log(
            entity_type="assignment",
            entity_id=assignment.id,
            action="created",
            actor_id=actor_id,
            new_value={
                "request_id": str(request_id),
                "volunteer_id": str(volunteer_id),
                "status": "pending",
            },
        )

        logger.info(
            f"Assignment created: {assignment.id} "
            f"(request={request_id}, volunteer={volunteer_id})"
        )
        return assignment

    def transition_status(
        self,
        assignment_id: UUID,
        new_status: str,
        actor_id: UUID = None,
        notes: str = None,
    ) -> Assignment:
        """Transition assignment status with validation."""
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")

        old_status = assignment.status
        allowed = VALID_ASSIGNMENT_TRANSITIONS.get(old_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {old_status} -> {new_status}. "
                f"Allowed: {allowed}"
            )

        update_kwargs = {"status": new_status}
        if notes:
            update_kwargs["notes"] = notes

        assignment = self.assignment_repo.update(assignment_id, **update_kwargs)

        # Audit log
        action = f"status_{new_status}"
        self.audit_repo.log(
            entity_type="assignment",
            entity_id=assignment_id,
            action=action,
            actor_id=actor_id,
            old_value={"status": old_status},
            new_value={"status": new_status},
        )

        logger.info(f"Assignment {assignment_id}: {old_status} -> {new_status}")
        return assignment

    def accept_assignment(
        self, assignment_id: UUID, actor_id: UUID = None
    ) -> Assignment:
        return self.transition_status(assignment_id, "accepted", actor_id)

    def reject_assignment(
        self, assignment_id: UUID, actor_id: UUID = None
    ) -> Assignment:
        return self.transition_status(assignment_id, "rejected", actor_id)

    def start_assignment(
        self, assignment_id: UUID, actor_id: UUID = None
    ) -> Assignment:
        return self.transition_status(assignment_id, "in_progress", actor_id)

    def complete_assignment(
        self, assignment_id: UUID, actor_id: UUID = None
    ) -> Assignment:
        assignment = self.transition_status(assignment_id, "completed", actor_id)

        # Check if all assignments for this request are completed
        request_id = assignment.request_id
        remaining = self.db.execute(
            text(
                "SELECT COUNT(*) FROM assignments "
                "WHERE request_id = :rid "
                "AND status IN ('pending', 'created', 'accepted', 'started', 'in_progress')"
            ),
            {"rid": str(request_id)},
        ).scalar()

        if remaining == 0:
            self.request_repo.update_status(request_id, "resolved")
            self.audit_repo.log(
                entity_type="request",
                entity_id=request_id,
                action="auto_resolved",
                actor_id=actor_id,
                new_value={"status": "resolved"},
            )

        return assignment

    def cancel_assignment(
        self, assignment_id: UUID, actor_id: UUID = None
    ) -> Assignment:
        return self.transition_status(assignment_id, "cancelled", actor_id)

    def get_assignment(self, assignment_id: UUID) -> Optional[Assignment]:
        return self.assignment_repo.get_by_id(assignment_id)

    def get_all_assignments(self, skip: int = 0, limit: int = 100) -> list[Assignment]:
        return self.assignment_repo.get_all(skip=skip, limit=limit)

    def get_assignments_for_request(self, request_id: UUID) -> list[Assignment]:
        return self.assignment_repo.get_by_request(request_id)

    def get_assignments_for_volunteer(self, volunteer_id: UUID) -> list[Assignment]:
        return self.assignment_repo.get_by_volunteer(volunteer_id)

    def get_active_assignments_for_volunteer(self, volunteer_id: UUID) -> list[Assignment]:
        """Return non-terminal assignments for a volunteer."""
        return (
            self.db.query(Assignment)
            .filter(
                Assignment.volunteer_id == volunteer_id,
                Assignment.status.in_(
                    ["pending", "created", "accepted", "started", "in_progress"]
                ),
            )
            .all()
        )
