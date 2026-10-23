from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.database.models import RiskObservation
from .base import BaseRepository


class RiskObservationRepository(BaseRepository[RiskObservation]):
    def __init__(self, db: Session):
        super().__init__(RiskObservation, db)

    def get_by_risk_level(self, risk_level: str) -> list[RiskObservation]:
        return (
            self.db.query(RiskObservation)
            .filter(RiskObservation.risk_level == risk_level)
            .all()
        )

    def get_by_district(self, district: str) -> list[RiskObservation]:
        return (
            self.db.query(RiskObservation)
            .filter(RiskObservation.district == district)
            .all()
        )

    def get_latest_by_location(self, location_name: str) -> Optional[RiskObservation]:
        return (
            self.db.query(RiskObservation)
            .filter(RiskObservation.location_name == location_name)
            .order_by(RiskObservation.predicted_at.desc())
            .first()
        )
