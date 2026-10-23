"""PostgreSQL-backed alert persistence for the alert_engine.

Runs alongside the in-memory JSON persistence during the dual-write phase.
After verification, JSON persistence can be removed.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.database.repositories.alert_repository import AlertRepository
from backend.app.database.repositories.audit_history_repository import AuditHistoryRepository

logger = logging.getLogger(__name__)


class DBAlertService:
    """Thin wrapper around AlertRepository for alert_engine integration."""

    def __init__(self, db: Session):
        self.repo = AlertRepository(db)
        self.audit_repo = AuditHistoryRepository(db)

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
    ):
        try:
            alert = self.repo.upsert_from_engine(
                location_id=location_id,
                location_name=location_name,
                district=district,
                state=state,
                latitude=latitude,
                longitude=longitude,
                severity=severity,
                risk_probability=risk_probability,
                trigger=trigger,
                contributing_factors=contributing_factors,
                rainfall=rainfall,
                soil_condition=soil_condition,
                slope_condition=slope_condition,
                response_priority=response_priority,
                status=status,
                title=title,
            )
            logger.info(f"DB alert upserted: {alert.id} (location={location_id}, severity={severity})")
            return alert
        except Exception as e:
            logger.error(f"DB alert upsert failed for {location_id}: {e}")
            self.db.rollback()
            return None

    @property
    def db(self):
        return self.repo.db

    def update_status(self, alert_db_id, status: str):
        try:
            alert_before = self.repo.get_by_id(alert_db_id)
            old_status = alert_before.status if alert_before else None

            alert = self.repo.update_alert_status(alert_db_id, status)
            logger.info(f"DB alert status updated: {alert_db_id} -> {status}")

            if alert and old_status != status:
                self.audit_repo.log(
                    entity_type="alert",
                    entity_id=alert.id,
                    action=status.lower(),
                    old_value={"status": old_status},
                    new_value={"status": status},
                )

            return alert
        except Exception as e:
            logger.error(f"DB alert status update failed for {alert_db_id}: {e}")
            self.db.rollback()
            return None

    def get_active_alerts(self):
        return self.repo.get_active_alerts()

    def get_all_alerts(self):
        return self.repo.get_all()
