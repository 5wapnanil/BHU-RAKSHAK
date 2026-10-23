"""Base repository with common CRUD operations."""

from typing import TypeVar, Generic, Type, List, Optional, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from backend.app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic base repository providing CRUD for any SQLAlchemy model."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[ModelType]:
        return self.db.execute(
            select(self.model).where(self.model.id == id)
        ).scalar_one_or_none()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return list(
            self.db.execute(
                select(self.model).offset(skip).limit(limit)
            ).scalars().all()
        )

    def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        instance = self.get_by_id(id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def delete(self, id: UUID) -> bool:
        instance = self.get_by_id(id)
        if instance is None:
            return False
        self.db.delete(instance)
        self.db.flush()
        return True

    def exists(self, **filters) -> bool:
        stmt = select(self.model.id)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        return self.db.execute(stmt).first() is not None
