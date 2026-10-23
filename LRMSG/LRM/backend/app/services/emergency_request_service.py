"""Service layer for EmergencyRequest — bridges mobile sync payloads to PostgreSQL.

The mobile app sends operation batches with payloads shaped like:
  Relief (citizen requesting humanitarian assistance):
    {
      "request_type": "relief",
      "location": "...",
      "reliefCategory": "food",
      "requiredItems": "rice, water, blankets",
      "quantity": "10 families",
      "peopleAffected": "15",
      "severity": "high",
      "hasVulnerable": true,
      "contactName": "...",
      "contactPhone": "...",
      "additionalInfo": "...",
      "gpsCoords": {"latitude": 27.0, "longitude": 93.0}
    }
  Evacuation:
    {
      "request_type": "evacuation",
      "location": "...",
      "numberOfPeople": "8",
      "emergencyType": "flood",
      "hasVulnerable": true,
      "contactName": "...",
      "contactPhone": "...",
      "additionalInfo": "...",
      "gpsCoords": {"latitude": 26.5, "longitude": 93.0}
    }

This service normalises the payload and persists to PostgreSQL via the repository.
"""

from typing import Dict, Any, Optional
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from backend.app.database.repositories.emergency_request_repository import EmergencyRequestRepository
from backend.app.database.models import EmergencyRequest

logger = logging.getLogger(__name__)


class EmergencyRequestService:
    """Business logic for mobile emergency request sync."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = EmergencyRequestRepository(db)

    # ── helpers ──────────────────────────────────────────────

    @staticmethod
    def _extract_coords(payload: Dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
        """Extract lat/lng from either flat fields or nested gpsCoords."""
        # Try flat fields first (legacy format)
        lat = payload.get("latitude")
        lng = payload.get("longitude")
        if lat is not None and lng is not None:
            try:
                return float(lat), float(lng)
            except (TypeError, ValueError):
                pass
        # Try nested gpsCoords (mobile format)
        gps = payload.get("gpsCoords")
        if isinstance(gps, dict):
            lat = gps.get("latitude")
            lng = gps.get("longitude")
            if lat is not None and lng is not None:
                try:
                    return float(lat), float(lng)
                except (TypeError, ValueError):
                    pass
        return None, None

    @staticmethod
    def _map_request_type(raw: str) -> str:
        mapping = {
            "evacuation": "evacuation",
            "help": "relief",
            "relief": "relief",
            "evacuation_volunteer": "evacuation_volunteer",
            "relief_volunteer": "relief_volunteer",
            "volunteer": "evacuation_volunteer",
        }
        return mapping.get(raw, "relief")

    # ── public API ──────────────────────────────────────────

    # Fields that indicate a meaningful emergency request.
    # Includes both legacy backend field names AND mobile-sync field names
    # (request_type, location, gpsCoords, numberOfPeople, emergencyType, etc.)
    _MEANINGFUL_FIELDS = frozenset({
        # Legacy backend fields
        "type", "title", "description", "severity",
        "latitude", "longitude", "locationText",
        "peopleAffected", "details",
        # Mobile-sync relief fields
        "request_type", "location", "contactName", "contactPhone",
        "gpsCoords", "category",
        # Relief-specific fields
        "reliefCategory", "requiredItems", "quantity",
        # Evacuation-specific fields
        "numberOfPeople", "emergencyType", "hasVulnerable", "additionalInfo",
    })

    def process_operation(self, op_id: str, payload: Dict[str, Any]) -> dict:
        """Process a single sync operation.

        Returns:
            {"status": "synced", "db_id": "...", "idempotent": False}
            or {"status": "idempotent", "db_id": "..."}
            or {"status": "error", "message": "..."}
        """
        client_op_id = op_id

        # Reject empty or informationless payloads
        if not payload or not self._MEANINGFUL_FIELDS.intersection(payload):
            return {"status": "error", "message": "Payload contains no meaningful emergency-request data"}

        # Idempotency check
        if self.repo.exists_client_op_id(client_op_id):
            existing = self.repo.get_by_client_op_id(client_op_id)
            logger.info(f"Idempotent sync: {client_op_id} already in DB")
            return {"status": "idempotent", "db_id": str(existing.id)}

        try:
            # Support both legacy "type" and mobile "request_type"
            raw_type = payload.get("request_type") or payload.get("type", "help")
            request_type = self._map_request_type(raw_type)
            lat, lng = self._extract_coords(payload)

            # Support both legacy field names and mobile field names
            location_text = payload.get("locationText") or payload.get("location")
            severity = payload.get("severity") or payload.get("emergencyType")
            people_affected = payload.get("peopleAffected")
            if people_affected is None and payload.get("numberOfPeople") is not None:
                try:
                    people_affected = int(payload["numberOfPeople"])
                except (TypeError, ValueError):
                    people_affected = None

            contact_name = payload.get("contactName")
            contact_phone = payload.get("contactPhone")

            db_record = self.repo.create_from_mobile(
                client_op_id=client_op_id,
                request_type=request_type,
                payload=payload,
                latitude=lat,
                longitude=lng,
                location_text=location_text,
                severity=severity,
                people_affected=people_affected,
                contact_name=contact_name,
                contact_phone=contact_phone,
            )

            logger.info(
                f"Synced emergency request {client_op_id} -> DB {db_record.id} "
                f"(type={request_type}, severity={payload.get('severity')})"
            )
            return {"status": "synced", "db_id": str(db_record.id), "idempotent": False}

        except Exception as e:
            logger.error(f"Failed to sync emergency request {client_op_id}: {e}")
            self.db.rollback()
            return {"status": "error", "message": "Sync processing failed"}

    def get_request_by_client_op_id(self, client_op_id: str) -> Optional[EmergencyRequest]:
        return self.repo.get_by_client_op_id(client_op_id)

    def get_request_by_db_id(self, db_id: UUID) -> Optional[EmergencyRequest]:
        return self.repo.get_by_id(db_id)

    def update_status(self, db_id: UUID, status: str) -> Optional[EmergencyRequest]:
        return self.repo.update_status(db_id, status)

    def update_server_status(self, db_id: UUID, server_status: str) -> Optional[EmergencyRequest]:
        return self.repo.update_server_status(db_id, server_status)

    def get_pending_requests(self) -> list[EmergencyRequest]:
        return self.repo.get_pending_requests()

    def get_all_requests(self, skip: int = 0, limit: int = 100) -> list[EmergencyRequest]:
        return self.repo.get_all(skip=skip, limit=limit)
