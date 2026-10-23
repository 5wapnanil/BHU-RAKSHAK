from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.database.models import ReliefResource
from .base import BaseRepository


class ReliefResourceRepository(BaseRepository[ReliefResource]):
    def __init__(self, db: Session):
        super().__init__(ReliefResource, db)

    def get_by_status(self, status: str) -> list[ReliefResource]:
        return (
            self.db.query(ReliefResource)
            .filter(ReliefResource.status == status)
            .all()
        )

    def get_by_provider(self, provider_id: UUID) -> list[ReliefResource]:
        return (
            self.db.query(ReliefResource)
            .filter(ReliefResource.provider_id == provider_id)
            .all()
        )

    def get_available_resources(self) -> list[ReliefResource]:
        return (
            self.db.query(ReliefResource)
            .filter(ReliefResource.status == "available")
            .all()
        )
