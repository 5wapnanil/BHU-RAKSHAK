"""Repository for EmergencyRequest — the critical path for mobile sync.

IMPORTANT: `client_op_id` is the mobile request.id and serves as the
idempotency key. The same operation MUST NOT be stored twice.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.database.models import EmergencyRequest
from .base import BaseRepository


class EmergencyRequestRepository(BaseRepository[EmergencyRequest]):
    def __init__(self, db: Session):
        super().__init__(EmergencyRequest, db)

    def get_by_client_op_id(self, client_op_id: str) -> Optional[EmergencyRequest]:
        """Primary lookup for idempotency checks during sync."""
        return (
            self.db.query(EmergencyRequest)
            .filter(EmergencyRequest.client_op_id == client_op_id)
            .first()
        )

    def exists_client_op_id(self, client_op_id: str) -> bool:
        """Fast idempotency check — returns True if already synced."""
        return (
            self.db.query(EmergencyRequest.id)
            .filter(EmergencyRequest.client_op_id == client_op_id)
            .first()
            is not None
        )

    def create_from_mobile(
        self,
        client_op_id: str,
        request_type: str,
        payload: dict,
        latitude: float = None,
        longitude: float = None,
        location_text: str = None,
        severity: str = None,
        people_affected: int = None,
        contact_name: str = None,
        contact_phone: str = None,
        incident_id: UUID = None,
        requester_id: UUID = None,
    ) -> EmergencyRequest:
        """Create an emergency request from a mobile sync payload."""
        location_wkt = None
        if latitude is not None and longitude is not None:
            location_wkt = f"POINT({longitude} {latitude})"

        return self.create(
            client_op_id=client_op_id,
            request_type=request_type,
            payload=payload,
            location=location_wkt,
            location_text=location_text,
            severity=severity,
            people_affected=people_affected,
            contact_name=contact_name,
            contact_phone=contact_phone,
            incident_id=incident_id,
            requester_id=requester_id,
            status="pending",
            server_status="received",
            synced_at=datetime.now(timezone.utc),
        )

    def update_server_status(self, id: UUID, server_status: str) -> Optional[EmergencyRequest]:
        return self.update(id, server_status=server_status)

    def update_status(self, id: UUID, status: str) -> Optional[EmergencyRequest]:
        return self.update(id, status=status)

    def get_by_request_type(self, request_type: str) -> list[EmergencyRequest]:
        return (
            self.db.query(EmergencyRequest)
            .filter(EmergencyRequest.request_type == request_type)
            .all()
        )

    def get_pending_requests(self) -> list[EmergencyRequest]:
        return (
            self.db.query(EmergencyRequest)
            .filter(EmergencyRequest.status == "pending")
            .all()
        )
