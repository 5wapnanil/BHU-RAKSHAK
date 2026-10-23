from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.database.models import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_role(self, role: str) -> list[User]:
        return self.db.query(User).filter(User.role == role).all()
