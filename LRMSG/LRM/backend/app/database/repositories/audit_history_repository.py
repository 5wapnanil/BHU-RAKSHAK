from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.database.models import AuditHistory
from .base import BaseRepository


class AuditHistoryRepository(BaseRepository[AuditHistory]):
    def __init__(self, db: Session):
        super().__init__(AuditHistory, db)

    def get_by_entity(self, entity_type: str, entity_id: UUID) -> list[AuditHistory]:
        return (
            self.db.query(AuditHistory)
            .filter(
                AuditHistory.entity_type == entity_type,
                AuditHistory.entity_id == entity_id,
            )
            .order_by(AuditHistory.created_at.desc())
            .all()
        )

    def get_by_actor(self, actor_id: UUID) -> list[AuditHistory]:
        return (
            self.db.query(AuditHistory)
            .filter(AuditHistory.actor_id == actor_id)
            .order_by(AuditHistory.created_at.desc())
            .all()
        )

    def list_audit_entries(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        action: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AuditHistory]:
        q = self.db.query(AuditHistory)

        if entity_type is not None:
            q = q.filter(AuditHistory.entity_type == entity_type)
        if entity_id is not None:
            q = q.filter(AuditHistory.entity_id == entity_id)
        if action is not None:
            q = q.filter(AuditHistory.action == action)
        if actor_id is not None:
            q = q.filter(AuditHistory.actor_id == actor_id)
        if start_date is not None:
            q = q.filter(AuditHistory.created_at >= start_date)
        if end_date is not None:
            q = q.filter(AuditHistory.created_at <= end_date)

        return (
            q.order_by(AuditHistory.created_at.desc())
            .offset(skip)
            .limit(min(limit, 500))
            .all()
        )

    def log(
        self,
        entity_type: str,
        entity_id: UUID,
        action: str,
        actor_id: UUID = None,
        old_value: dict = None,
        new_value: dict = None,
    ) -> AuditHistory:
        return self.create(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            old_value=old_value,
            new_value=new_value,
        )
