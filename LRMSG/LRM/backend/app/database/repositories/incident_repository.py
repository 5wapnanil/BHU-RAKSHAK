from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.database.models import Incident
from .base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self, db: Session):
        super().__init__(Incident, db)

    def get_by_status(self, status: str) -> list[Incident]:
        return (
            self.db.query(Incident)
            .filter(Incident.status == status)
            .all()
        )

    def get_by_district(self, district: str) -> list[Incident]:
        return (
            self.db.query(Incident)
            .filter(Incident.district == district)
            .all()
        )

    def get_active_incidents(self) -> list[Incident]:
        return (
            self.db.query(Incident)
            .filter(Incident.status.in_(["reported", "active"]))
            .all()
        )
