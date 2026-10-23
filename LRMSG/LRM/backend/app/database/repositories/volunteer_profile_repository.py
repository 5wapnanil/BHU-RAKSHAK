from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.database.models import VolunteerProfile
from .base import BaseRepository


class VolunteerProfileRepository(BaseRepository[VolunteerProfile]):
    def __init__(self, db: Session):
        super().__init__(VolunteerProfile, db)

    def get_by_user_id(self, user_id: UUID) -> Optional[VolunteerProfile]:
        return (
            self.db.query(VolunteerProfile)
            .filter(VolunteerProfile.user_id == user_id)
            .first()
        )

    def get_by_status(self, status: str) -> list[VolunteerProfile]:
        return (
            self.db.query(VolunteerProfile)
            .filter(VolunteerProfile.status == status)
            .all()
        )

    def get_active_volunteers(self) -> list[VolunteerProfile]:
        return (
            self.db.query(VolunteerProfile)
            .filter(VolunteerProfile.is_active == True)
            .all()
        )
