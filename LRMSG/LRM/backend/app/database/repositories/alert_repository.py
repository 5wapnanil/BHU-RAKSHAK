"""Repository for Alert — used by alert_engine to persist alerts to PostgreSQL."""

from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.database.models import Alert
from .base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    def __init__(self, db: Session):
        super().__init__(Alert, db)

    def get_by_location_id(self, location_id: str) -> Optional[Alert]:
        return (
            self.db.query(Alert)
            .filter(Alert.location_id == location_id)
            .first()
        )

    def get_active_alerts(self) -> list[Alert]:
        return (
            self.db.query(Alert)
            .filter(Alert.status.in_(["ACTIVE", "ACKNOWLEDGED", "UNDER_RESPONSE"]))
            .all()
        )

    def get_by_status(self, status: str) -> list[Alert]:
        return (
            self.db.query(Alert)
            .filter(Alert.status == status)
            .all()
        )

    def get_by_severity(self, severity: str) -> list[Alert]:
        return (
            self.db.query(Alert)
            .filter(Alert.severity == severity)
            .all()
        )

    def upsert_from_engine(
        self,
        location_id: str,
        location_name: str,
        district: str,
        state: str,
        latitude: float,
        longitude: float,
        severity: str,
        risk_probability: float,
        trigger: str,
        contributing_factors: str,
        rainfall: float,
        soil_condition: float,
        slope_condition: float,
        response_priority: str,
        status: str = "ACTIVE",
        title: str = None,
    ) -> Alert:
        """Insert or update an alert from the in-memory alert_engine.

        Looks up by location_id + active status. If found, updates severity/probability.
        Otherwise, creates a new alert.
        """
        existing = (
            self.db.query(Alert)
            .filter(
                Alert.location_id == location_id,
                Alert.status.in_(["ACTIVE", "ACKNOWLEDGED", "UNDER_RESPONSE"]),
            )
            .first()
        )

        now = datetime.now(timezone.utc)
        location_wkt = f"POINT({longitude} {latitude})"

        if existing:
            existing.severity = severity
            existing.risk_probability = risk_probability
            existing.trigger = trigger
            existing.contributing_factors = contributing_factors
            existing.rainfall = rainfall
            existing.soil_condition = soil_condition
            existing.slope_condition = slope_condition
            existing.response_priority = response_priority
            existing.updated_at = now
            if title is not None:
                existing.title = title
            if severity == "CRITICAL":
                existing.notifications = {
                    "district_admin": "NOTIFIED",
                    "disaster_management": "NOTIFIED",
                    "local_community": "WARNING SENT",
                }
            self.db.flush()
            self.db.refresh(existing)
            return existing

        new_alert = Alert(
            title=title,
            location_id=location_id,
            location_name=location_name,
            district=district,
            state=state,
            location=location_wkt,
            severity=severity,
            risk_probability=risk_probability,
            trigger=trigger,
            contributing_factors=contributing_factors,
            rainfall=rainfall,
            soil_condition=soil_condition,
            slope_condition=slope_condition,
            response_priority=response_priority,
            status=status,
            notifications={
                "district_admin": "NOTIFIED" if severity in ["HIGH", "CRITICAL"] else "PENDING",
                "disaster_management": "NOTIFIED" if severity == "CRITICAL" else "PENDING",
                "local_community": "WARNING SENT" if severity == "CRITICAL" else "PENDING",
            },
            triggered_at=now,
        )
        self.db.add(new_alert)
        self.db.flush()
        self.db.refresh(new_alert)
        return new_alert

    def update_alert_status(self, id: UUID, status: str) -> Optional[Alert]:
        alert = self.get_by_id(id)
        if alert is None:
            return None
        now = datetime.now(timezone.utc)
        alert.status = status
        if status == "ACKNOWLEDGED":
            alert.acknowledged_at = now
        elif status == "RESOLVED":
            alert.resolved_at = now
        alert.updated_at = now
        self.db.flush()
        self.db.refresh(alert)
        return alert
