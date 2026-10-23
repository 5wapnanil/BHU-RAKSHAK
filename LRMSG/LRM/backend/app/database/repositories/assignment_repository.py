from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.database.models import Assignment
from .base import BaseRepository


class AssignmentRepository(BaseRepository[Assignment]):
    def __init__(self, db: Session):
        super().__init__(Assignment, db)

    def get_by_request(self, request_id: UUID) -> list[Assignment]:
        return (
            self.db.query(Assignment)
            .filter(Assignment.request_id == request_id)
            .all()
        )

    def get_by_volunteer(self, volunteer_id: UUID) -> list[Assignment]:
        return (
            self.db.query(Assignment)
            .filter(Assignment.volunteer_id == volunteer_id)
            .all()
        )

    def get_by_status(self, status: str) -> list[Assignment]:
        return (
            self.db.query(Assignment)
            .filter(Assignment.status == status)
            .all()
        )
