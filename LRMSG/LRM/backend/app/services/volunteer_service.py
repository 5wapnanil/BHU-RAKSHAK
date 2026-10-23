"""Volunteer coordination service.

Handles volunteer profile management, verification workflow,
availability tracking, and eligibility checks.
"""

import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.database.repositories.volunteer_profile_repository import VolunteerProfileRepository
from backend.app.database.repositories.user_repository import UserRepository
from backend.app.database.repositories.audit_history_repository import AuditHistoryRepository
from backend.app.database.models import VolunteerProfile

logger = logging.getLogger(__name__)

# Valid volunteer status transitions
VALID_VOLUNTEER_TRANSITIONS = {
    "pending": ["verified", "inactive"],
    "verified": ["active", "inactive", "unavailable"],
    "active": ["unavailable", "inactive"],
    "unavailable": ["active", "inactive"],
    "inactive": ["pending"],
}


class VolunteerService:
    def __init__(self, db: Session):
        self.db = db
        self.vol_repo = VolunteerProfileRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditHistoryRepository(db)

    def create_profile(
        self,
        user_id: UUID,
        skills: list[str] = None,
        has_transport: bool = None,
        capacity: int = None,
        availability: str = None,
        latitude: float = None,
        longitude: float = None,
    ) -> VolunteerProfile:
        """Create a volunteer profile. User must exist. One profile per user."""
        existing = self.vol_repo.get_by_user_id(user_id)
        if existing:
            raise ValueError(f"Volunteer profile already exists for user {user_id}")

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        location_wkt = None
        if latitude is not None and longitude is not None:
            location_wkt = f"SRID=4326;POINT({longitude} {latitude})"

        profile = self.vol_repo.create(
            user_id=user_id,
            skills=skills or [],
            has_transport=has_transport,
            capacity=capacity,
            availability=availability,
            location=location_wkt,
            status="pending",
            is_active=True,
        )

        self.audit_repo.log(
            entity_type="volunteer",
            entity_id=profile.id,
            action="created",
            new_value={"user_id": str(user_id), "status": "pending"},
        )

        logger.info(f"Volunteer profile created: {profile.id} for user {user_id}")
        return profile

    def verify_volunteer(
        self,
        profile_id: UUID,
        actor_id: UUID = None,
    ) -> VolunteerProfile:
        """Verify a volunteer — moves from pending to verified."""
        profile = self.vol_repo.get_by_id(profile_id)
        if not profile:
            raise ValueError(f"Volunteer profile {profile_id} not found")

        if profile.status != "pending":
            raise ValueError(
                f"Cannot verify volunteer in status '{profile.status}'; must be 'pending'"
            )

        old_status = profile.status
        profile = self.vol_repo.update(
            profile_id,
            status="verified",
            verified_at=datetime.now(timezone.utc),
        )

        self.audit_repo.log(
            entity_type="volunteer",
            entity_id=profile_id,
            action="verified",
            actor_id=actor_id,
            old_value={"status": old_status},
            new_value={"status": "verified"},
        )

        logger.info(f"Volunteer {profile_id} verified")
        return profile

    def activate_volunteer(
        self,
        profile_id: UUID,
        actor_id: UUID = None,
    ) -> VolunteerProfile:
        """Activate a verified volunteer."""
        profile = self.vol_repo.get_by_id(profile_id)
        if not profile:
            raise ValueError(f"Volunteer profile {profile_id} not found")

        if profile.status != "verified":
            raise ValueError(
                f"Cannot activate volunteer in status '{profile.status}'; must be 'verified'"
            )

        old_status = profile.status
        profile = self.vol_repo.update(profile_id, status="active")

        self.audit_repo.log(
            entity_type="volunteer",
            entity_id=profile_id,
            action="activated",
            actor_id=actor_id,
            old_value={"status": old_status},
            new_value={"status": "active"},
        )

        return profile

    def update_status(
        self,
        profile_id: UUID,
        new_status: str,
        actor_id: UUID = None,
    ) -> VolunteerProfile:
        """Update volunteer status with transition validation."""
        profile = self.vol_repo.get_by_id(profile_id)
        if not profile:
            raise ValueError(f"Volunteer profile {profile_id} not found")

        allowed = VALID_VOLUNTEER_TRANSITIONS.get(profile.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {profile.status} -> {new_status}. "
                f"Allowed: {allowed}"
            )

        old_status = profile.status
        profile = self.vol_repo.update(profile_id, status=new_status)

        self.audit_repo.log(
            entity_type="volunteer",
            entity_id=profile_id,
            action="status_changed",
            actor_id=actor_id,
            old_value={"status": old_status},
            new_value={"status": new_status},
        )

        return profile

    def is_eligible_for_assignment(self, profile: VolunteerProfile) -> bool:
        """A volunteer is eligible only if verified+active AND is_active=True."""
        return (
            profile.status == "active"
            and profile.is_active is True
        )

    def get_eligible_volunteers(self) -> list[VolunteerProfile]:
        """Return all volunteers eligible for assignment."""
        return (
            self.db.query(VolunteerProfile)
            .filter(
                VolunteerProfile.status == "active",
                VolunteerProfile.is_active == True,
            )
            .all()
        )

    def get_profile(self, profile_id: UUID) -> Optional[VolunteerProfile]:
        return self.vol_repo.get_by_id(profile_id)

    def get_profile_by_user(self, user_id: UUID) -> Optional[VolunteerProfile]:
        return self.vol_repo.get_by_user_id(user_id)

    def get_all_profiles(self, skip: int = 0, limit: int = 100) -> list[VolunteerProfile]:
        return self.vol_repo.get_all(skip=skip, limit=limit)
