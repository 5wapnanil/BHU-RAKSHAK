from sqlalchemy.orm import Session

from backend.app.database.models import Shelter
from .base import BaseRepository


class ShelterRepository(BaseRepository[Shelter]):
    def __init__(self, db: Session):
        super().__init__(Shelter, db)

    def get_open_shelters(self) -> list[Shelter]:
        return (
            self.db.query(Shelter)
            .filter(Shelter.status == "open")
            .all()
        )

    def get_with_capacity(self) -> list[Shelter]:
        return (
            self.db.query(Shelter)
            .filter(Shelter.current_occupancy < Shelter.capacity)
            .all()
        )
