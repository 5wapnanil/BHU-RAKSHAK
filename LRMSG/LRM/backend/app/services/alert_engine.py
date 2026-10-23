import json
import uuid
from datetime import datetime, timezone
import asyncio
from backend.app.services.sms_service import sms_service
from backend.app.services.contacts_service import contacts_service
import time
from typing import Dict, Any, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

ALERTS_DB_PATH = "alerts_db.json"


def severity_level(sev: str) -> int:
    return {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}.get(sev, 0)


class AlertEngine:
    def __init__(self):
        self.alerts: Dict[str, dict] = {}
        self.load_alerts()
        self.listeners = []
        # DB persistence (dual-write) — set via attach_db_session()
        self._db_session_factory = None

    # ── DB persistence helpers ──────────────────────────────

    def attach_db_session(self, session_factory):
        """Attach a SQLAlchemy sessionmaker for dual-write to PostgreSQL.

        Called once at startup from main.py or via a startup event.
        """
        self._db_session_factory = session_factory
        logger.info("AlertEngine: PostgreSQL dual-write attached")

    def _try_db_upsert(self, alert_data: dict):
        """Attempt to upsert an alert to PostgreSQL. Logs errors but never crashes."""
        if self._db_session_factory is None:
            return
        try:
            from backend.app.services.db_alert_service import DBAlertService
            db = self._db_session_factory()
            try:
                svc = DBAlertService(db)
                svc.upsert_from_engine(
                    location_id=alert_data["location_id"],
                    location_name=alert_data["location_name"],
                    district=alert_data["district"],
                    state=alert_data["state"],
                    latitude=alert_data["latitude"],
                    longitude=alert_data["longitude"],
                    severity=alert_data["severity"],
                    risk_probability=alert_data["risk_probability"],
                    trigger=alert_data["trigger"],
                    contributing_factors=alert_data["contributing_factors"],
                    rainfall=alert_data["rainfall"],
                    soil_condition=alert_data["soil_condition"],
                    slope_condition=alert_data["slope_condition"],
                    response_priority=alert_data["response_priority"],
                    status=alert_data["status"],
                    title=alert_data.get("title"),
                )
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"DB alert upsert failed: {e}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"DBAlertService import/init failed: {e}")

    def _try_db_status_update(self, alert_id: str, status: str):
        """Attempt to update alert status in PostgreSQL."""
        if self._db_session_factory is None:
            return
        try:
            from backend.app.services.db_alert_service import DBAlertService
            from sqlalchemy import text
            db = self._db_session_factory()
            try:
                svc = DBAlertService(db)
                # Find alert by location-based UUID pattern or by matching fields
                # Since in-memory alerts use UUID strings, we do a text search
                result = db.execute(
                    text("SELECT id FROM alerts WHERE location_id = :lid AND status != 'RESOLVED' ORDER BY created_at DESC LIMIT 1"),
                    {"lid": alert_id[:50] if len(alert_id) > 50 else alert_id},
                ).fetchone()
                if result:
                    from uuid import UUID
                    svc.update_status(UUID(str(result[0])), status)
                    db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"DB alert status update failed: {e}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"DB alert status update init failed: {e}")

    # ── JSON persistence ────────────────────────────────────

    def load_alerts(self):
        if os.path.exists(ALERTS_DB_PATH):
            try:
                with open(ALERTS_DB_PATH, 'r') as f:
                    self.alerts = json.load(f)
            except Exception:
                self.alerts = {}

    def save_alerts(self):
        try:
            with open(ALERTS_DB_PATH, 'w') as f:
                json.dump(self.alerts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")

    # ── Listeners ───────────────────────────────────────────

    def add_listener(self, queue: asyncio.Queue):
        self.listeners.append(queue)

    def remove_listener(self, queue: asyncio.Queue):
        if queue in self.listeners:
            self.listeners.remove(queue)

    # ── SMS ─────────────────────────────────────────────────

    async def _dispatch_sms(self, alert: dict, severity: str):
        if severity not in ["HIGH", "CRITICAL"]:
            return

        contacts = contacts_service.get_affected_contacts(alert["latitude"], alert["longitude"])
        msg = ""
        if severity == "CRITICAL":
            msg = f"CRITICAL LANDSLIDE ALERT: Very high landslide risk ({alert['risk_probability']}%) detected near {alert['location_name']}. Move away from vulnerable slopes immediately. District: {alert['district']}."
        else:
            msg = f"LANDSLIDE ALERT: HIGH risk detected at {alert['location_name']}. Risk probability: {alert['risk_probability']}%. District: {alert['district']}. Please follow local safety advisories."

        now = time.time()
        for c in contacts:
            cid = c["id"]

            if "contact_history" not in alert:
                alert["contact_history"] = {}
            if cid not in alert["contact_history"]:
                alert["contact_history"][cid] = {"last_time": 0, "last_sev": "LOW"}

            history = alert["contact_history"][cid]

            escalated = severity_level(severity) > severity_level(history["last_sev"])
            cooldown_passed = (now - history["last_time"]) > (4 * 3600)

            if escalated or cooldown_passed:
                success = await sms_service.send_sms(c["phone_number"], msg)
                if success:
                    history["last_time"] = now
                    history["last_sev"] = severity

    # ── WebSocket broadcast ─────────────────────────────────

    async def broadcast(self, message: dict):
        for q in self.listeners:
            await q.put(message)

    # ── Core evaluation ─────────────────────────────────────

    def _determine_severity(self, probability: float) -> str:
        prob = probability * 100
        if prob >= 95.0:
            return "CRITICAL"
        if prob >= 60.0:
            return "HIGH"
        if prob >= 30.0:
            return "MODERATE"
        return "LOW"

    def _get_response_priority(self, severity: str) -> str:
        return {
            "CRITICAL": "IMMEDIATE",
            "HIGH": "URGENT",
            "MODERATE": "MONITOR",
            "LOW": "ROUTINE",
        }.get(severity, "ROUTINE")

    async def evaluate_prediction(
        self,
        location_id: str,
        location_name: str,
        district: str,
        state: str,
        lat: float,
        lng: float,
        probability: float,
        rainfall: float,
        soil: float,
        slope: float,
        demo_mode: bool = False,
        title: str = None,
    ):
        severity = self._determine_severity(probability)
        if severity == "LOW":
            return

        prob_pct = round(probability * 100)

        existing_alert_id = None
        for aid, alert in self.alerts.items():
            if (
                alert["location_id"] == location_id
                and alert["status"] in ["ACTIVE", "ACKNOWLEDGED", "UNDER_RESPONSE"]
            ):
                existing_alert_id = aid
                break

        now = datetime.now(timezone.utc).isoformat()

        trigger = "High risk conditions detected"
        if rainfall > 50:
            trigger = "Heavy rainfall"
        if rainfall > 100:
            trigger = "Extreme rainfall"

        factors = []
        if rainfall > 50:
            factors.append("High rainfall")
        if slope > 25:
            factors.append("Unstable slope")
        if soil > 0.6:
            factors.append("High soil saturation")

        if existing_alert_id:
            alert = self.alerts[existing_alert_id]
            old_severity = alert["severity"]

            if old_severity != severity or abs(alert["risk_probability"] - prob_pct) >= 5:
                alert["severity"] = severity
                alert["risk_probability"] = prob_pct
                alert["updated_at"] = now
                alert["trigger"] = trigger
                alert["contributing_factors"] = " + ".join(factors) if factors else "Elevated risk parameters"
                alert["response_priority"] = self._get_response_priority(severity)
                alert["rainfall"] = rainfall
                alert["soil_condition"] = soil
                alert["slope_condition"] = slope

                if severity == "CRITICAL":
                    alert["notifications"] = {
                        "district_admin": "NOTIFIED",
                        "disaster_management": "NOTIFIED",
                        "local_community": "WARNING SENT",
                    }

                await self._dispatch_sms(alert, severity)
                self.save_alerts()

                # ── Dual-write: persist to PostgreSQL ───────
                self._try_db_upsert(alert)

                event_type = (
                    "ALERT_ESCALATED"
                    if severity_level(severity) > severity_level(old_severity)
                    else "ALERT_UPDATED"
                )
                await self.broadcast({"type": event_type, "alert": alert, "demo": demo_mode})
        else:
            if severity in ["MODERATE", "HIGH", "CRITICAL"]:
                alert_id = str(uuid.uuid4())
                new_alert = {
                    "id": alert_id,
                    "title": title,
                    "location_id": location_id,
                    "location_name": location_name,
                    "district": district,
                    "state": state,
                    "latitude": lat,
                    "longitude": lng,
                    "severity": severity,
                    "risk_probability": prob_pct,
                    "trigger": trigger,
                    "contributing_factors": " + ".join(factors) if factors else "Elevated risk parameters",
                    "rainfall": rainfall,
                    "soil_condition": soil,
                    "slope_condition": slope,
                    "road_status": "Monitoring active",
                    "response_priority": self._get_response_priority(severity),
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                    "lifecycle": [{"state": "GENERATED", "timestamp": now}],
                    "notifications": {
                        "district_admin": "NOTIFIED" if severity in ["HIGH", "CRITICAL"] else "PENDING",
                        "disaster_management": "NOTIFIED" if severity == "CRITICAL" else "PENDING",
                        "local_community": "WARNING SENT" if severity == "CRITICAL" else "PENDING",
                    },
                }
                self.alerts[alert_id] = new_alert
                await self._dispatch_sms(new_alert, severity)
                self.save_alerts()

                # ── Dual-write: persist to PostgreSQL ───────
                self._try_db_upsert(new_alert)

                await self.broadcast({"type": "NEW_ALERT", "alert": new_alert, "demo": demo_mode})

    async def update_status(self, alert_id: str, status: str):
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert["status"] = status
            now = datetime.now(timezone.utc).isoformat()
            if status == "ACKNOWLEDGED":
                alert["acknowledged_at"] = now
            if status == "RESOLVED":
                alert["resolved_at"] = now

            alert["lifecycle"].append({"state": status, "timestamp": now})

            self.save_alerts()

            # ── Dual-write: update status in PostgreSQL ─────
            self._try_db_status_update(alert_id, status)

            event_type = f"ALERT_{status}"
            await self.broadcast({"type": event_type, "alert": alert})
            return alert
        return None


alert_engine = AlertEngine()
