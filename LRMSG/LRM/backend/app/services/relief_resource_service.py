"""Relief resource coordination service.

Handles resource allocation to emergency requests, quantity tracking,
concurrency protection, and release/cancellation.
"""

import json
import logging
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database.repositories.relief_resource_repository import ReliefResourceRepository
from backend.app.database.repositories.emergency_request_repository import EmergencyRequestRepository
from backend.app.database.repositories.assignment_repository import AssignmentRepository
from backend.app.database.repositories.audit_history_repository import AuditHistoryRepository
from backend.app.database.models import ReliefResource

logger = logging.getLogger(__name__)


class ReliefResourceService:
    def __init__(self, db: Session):
        self.db = db
        self.resource_repo = ReliefResourceRepository(db)
        self.request_repo = EmergencyRequestRepository(db)
        self.assignment_repo = AssignmentRepository(db)
        self.audit_repo = AuditHistoryRepository(db)

    def create_resource(
        self,
        resource_type: str,
        description: str = None,
        quantity: float = None,
        unit: str = None,
        provider_id: UUID = None,
        latitude: float = None,
        longitude: float = None,
    ) -> ReliefResource:
        """Create a new relief resource."""
        location_wkt = None
        if latitude is not None and longitude is not None:
            location_wkt = f"SRID=4326;POINT({longitude} {latitude})"

        resource = self.resource_repo.create(
            resource_type=resource_type,
            description=description,
            quantity=Decimal(str(quantity)) if quantity is not None else None,
            unit=unit,
            available_quantity=Decimal(str(quantity)) if quantity is not None else None,
            provider_id=provider_id,
            location=location_wkt,
            status="available",
        )

        self.audit_repo.log(
            entity_type="resource",
            entity_id=resource.id,
            action="created",
            new_value={
                "resource_type": resource_type,
                "quantity": str(quantity),
                "status": "available",
            },
        )

        logger.info(f"Relief resource created: {resource.id} (type={resource_type})")
        return resource

    def allocate_resource(
        self,
        resource_id: UUID,
        request_id: UUID,
        quantity: float,
        notes: str = None,
        actor_id: UUID = None,
    ):
        """Allocate a quantity of a resource to an emergency request.

        Uses PostgreSQL SELECT FOR UPDATE to prevent concurrent over-allocation.
        """
        # 1. Verify request exists
        request = self.request_repo.get_by_id(request_id)
        if not request:
            raise ValueError(f"Emergency request {request_id} not found")

        # 2. Lock the resource row and verify availability
        resource_row = self.db.execute(
            text(
                "SELECT id, resource_type, available_quantity, status "
                "FROM relief_resources WHERE id = :rid FOR UPDATE"
            ),
            {"rid": str(resource_id)},
        ).fetchone()

        if not resource_row:
            raise ValueError(f"Relief resource {resource_id} not found")

        resource_status = resource_row[3]
        available_qty = resource_row[2]

        if resource_status not in ("available", "allocated"):
            raise ValueError(
                f"Resource is not available for allocation (status='{resource_status}')"
            )

        if available_qty is None:
            raise ValueError("Resource has no trackable quantity")

        req_qty = Decimal(str(quantity))
        if req_qty <= 0:
            raise ValueError("Allocation quantity must be positive")

        if req_qty > available_qty:
            raise ValueError(
                f"Insufficient quantity: requested {req_qty}, "
                f"available {available_qty}"
            )

        # 3. Deduct quantity atomically
        new_available = available_qty - req_qty
        self.db.execute(
            text(
                "UPDATE relief_resources "
                "SET available_quantity = :new_qty, "
                "    status = CASE WHEN :new_qty <= 0 THEN 'depleted' ELSE 'allocated' END, "
                "    updated_at = now() "
                "WHERE id = :rid"
            ),
            {"new_qty": float(new_available), "rid": str(resource_id)},
        )

        # 4. Create assignment linking resource to request
        # Store allocated quantity as structured JSON in notes for reliable recovery on release.
        allocation_notes = {
            "_allocated_qty": float(quantity),
            "_resource_type": resource_row[1],
            "_user_notes": notes or "",
        }
        assignment = self.assignment_repo.create(
            request_id=request_id,
            resource_id=resource_id,
            assignment_type="resource",
            status="accepted",
            notes=json.dumps(allocation_notes),
        )

        # 5. Audit log
        self.audit_repo.log(
            entity_type="resource",
            entity_id=resource_id,
            action="allocated",
            actor_id=actor_id,
            new_value={
                "request_id": str(request_id),
                "quantity_allocated": str(quantity),
                "remaining": str(new_available),
            },
        )

        logger.info(
            f"Resource {resource_id} allocated: {quantity} to request {request_id} "
            f"(remaining: {new_available})"
        )
        return assignment

    def release_allocation(
        self,
        assignment_id: UUID,
        actor_id: UUID = None,
    ):
        """Release a resource allocation — returns quantity to available inventory."""
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        if assignment.assignment_type != "resource":
            raise ValueError("Assignment is not a resource allocation")
        if assignment.status == "cancelled":
            raise ValueError("Allocation is already cancelled")

        resource_id = assignment.resource_id
        if not resource_id:
            raise ValueError("Assignment has no linked resource")

        # Recover allocated quantity from structured JSON in notes.
        # Falls back to legacy text parsing for pre-fix assignments.
        notes = assignment.notes or ""
        released_qty = Decimal("0")
        try:
            parsed = json.loads(notes)
            if isinstance(parsed, dict) and "_allocated_qty" in parsed:
                released_qty = Decimal(str(parsed["_allocated_qty"]))
        except (json.JSONDecodeError, TypeError, KeyError):
            # Legacy format: "Allocated {qty} {type}"
            parts = notes.split()
            try:
                released_qty = Decimal(parts[1]) if len(parts) >= 2 else Decimal("0")
            except (IndexError, Exception):
                released_qty = Decimal("0")

        # Lock and update resource
        resource_row = self.db.execute(
            text(
                "SELECT available_quantity, status FROM relief_resources "
                "WHERE id = :rid FOR UPDATE"
            ),
            {"rid": str(resource_id)},
        ).fetchone()

        if resource_row:
            current_available = resource_row[0] or Decimal("0")
            new_available = current_available + released_qty
            self.db.execute(
                text(
                    "UPDATE relief_resources "
                    "SET available_quantity = :new_qty, "
                    "    status = 'available', "
                    "    updated_at = now() "
                    "WHERE id = :rid"
                ),
                {"new_qty": float(new_available), "rid": str(resource_id)},
            )

        # Cancel the assignment
        self.assignment_repo.update(assignment_id, status="cancelled")

        self.audit_repo.log(
            entity_type="resource",
            entity_id=resource_id,
            action="released",
            actor_id=actor_id,
            new_value={
                "assignment_id": str(assignment_id),
                "quantity_released": str(released_qty),
            },
        )

        logger.info(f"Resource allocation {assignment_id} released ({released_qty} returned)")
        return assignment

    def get_resource(self, resource_id: UUID) -> Optional[ReliefResource]:
        return self.resource_repo.get_by_id(resource_id)

    def get_available_resources(self) -> list[ReliefResource]:
        return self.resource_repo.get_available_resources()

    def get_all_resources(self, skip: int = 0, limit: int = 100) -> list[ReliefResource]:
        return self.resource_repo.get_all(skip=skip, limit=limit)
