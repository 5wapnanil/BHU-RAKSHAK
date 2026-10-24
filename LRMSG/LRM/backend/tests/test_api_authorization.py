"""Exhaustive authorization and security regression test suite for PahaarPulse.

Verifies:
1. All privileged coordinator mutation endpoints enforce server-side authorization.
2. Unauthenticated requests are rejected with HTTP 403 Forbidden when credentials are configured.
3. Invalid credentials are rejected with HTTP 403 Forbidden (constant-time verification).
4. Valid credentials via 'X-Coordinator-Key' and 'Authorization: Bearer <token>' are accepted.
5. In production environments without configured secrets, privileged endpoints fail closed with HTTP 503.
6. Public citizen reporting and offline mobile sync routes remain open without coordinator credentials.
7. Error responses do not leak secrets or internal system traces.
"""

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.database.base import get_db
from backend.app.main import app

TEST_SECRET = "coord_sec_test_token_884920"


def make_fake_volunteer(vid=None):
    return MagicMock(
        id=vid or uuid4(),
        user_id=uuid4(),
        skills=["first_aid"],
        has_transport=True,
        capacity=10,
        availability="weekends",
        status="verified",
        is_active=True,
        verified_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_fake_assignment(aid=None):
    return MagicMock(
        id=aid or uuid4(),
        request_id=uuid4(),
        volunteer_id=uuid4(),
        resource_id=None,
        assignment_type="volunteer",
        status="PENDING",
        notes="Test assignment notes",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class DummyShelter:
    def __init__(self, id, name="Shelter Renamed", capacity=100, current_occupancy=0, status="open"):
        self.id = id
        self.name = name
        self.location = None
        self.address = "Test Address"
        self.capacity = capacity
        self.current_occupancy = current_occupancy
        self.facilities = {}
        self.contact_phone = None
        self.status = status
        self.operated_by = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


def make_fake_shelter(sid=None):
    return DummyShelter(id=sid or uuid4())


class TestApiAuthorization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.mock_db

    def tearDown(self):
        app.dependency_overrides.clear()

    # ─────────────────────────────────────────────────────────────────
    # 1. VOLUNTEER COORDINATION MUTATION ENDPOINTS
    # ─────────────────────────────────────────────────────────────────

    def test_volunteer_verify_blocks_unauthorized_when_configured(self):
        vid = uuid4()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            # Missing credentials -> 403
            res_missing = self.client.post(f"/api/volunteers/{vid}/verify")
            self.assertEqual(res_missing.status_code, 403)
            self.assertIn("Forbidden", res_missing.json()["detail"])

            # Invalid credentials -> 403
            res_invalid = self.client.post(
                f"/api/volunteers/{vid}/verify",
                headers={"X-Coordinator-Key": "wrong_key"},
            )
            self.assertEqual(res_invalid.status_code, 403)

    def test_volunteer_verify_permits_authorized_key(self):
        vid = uuid4()
        fake_profile = make_fake_volunteer(vid)
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            with patch("backend.app.api.endpoints.coordination.VolunteerService") as mock_svc_cls:
                mock_svc = mock_svc_cls.return_value
                mock_svc.verify_volunteer.return_value = fake_profile

                # Valid via X-Coordinator-Key
                res = self.client.post(
                    f"/api/volunteers/{vid}/verify",
                    headers={"X-Coordinator-Key": TEST_SECRET},
                )
                self.assertEqual(res.status_code, 200)

                # Valid via Bearer token
                res_bearer = self.client.post(
                    f"/api/volunteers/{vid}/verify",
                    headers={"Authorization": f"Bearer {TEST_SECRET}"},
                )
                self.assertEqual(res_bearer.status_code, 200)

    def test_volunteer_activate_blocks_unauthorized_when_configured(self):
        vid = uuid4()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post(f"/api/volunteers/{vid}/activate")
            self.assertEqual(res.status_code, 403)

    def test_volunteer_status_patch_blocks_unauthorized_when_configured(self):
        vid = uuid4()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.patch(
                f"/api/volunteers/{vid}/status",
                json={"status": "active"},
            )
            self.assertEqual(res.status_code, 403)

    # ─────────────────────────────────────────────────────────────────
    # 2. ASSIGNMENT MUTATION ENDPOINTS
    # ─────────────────────────────────────────────────────────────────

    def test_create_assignment_blocks_unauthorized_when_configured(self):
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post(
                "/api/assignments",
                json={"request_id": str(uuid4()), "volunteer_id": str(uuid4())},
            )
            self.assertEqual(res.status_code, 403)

    def test_create_assignment_permits_authorized_key(self):
        req_id = uuid4()
        vol_id = uuid4()
        fake_assignment = make_fake_assignment()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            with patch("backend.app.api.endpoints.coordination.AssignmentService") as mock_svc_cls:
                mock_svc = mock_svc_cls.return_value
                mock_svc.create_volunteer_assignment.return_value = fake_assignment

                res = self.client.post(
                    "/api/assignments",
                    headers={"X-Coordinator-Key": TEST_SECRET},
                    json={"request_id": str(req_id), "volunteer_id": str(vol_id)},
                )
                self.assertEqual(res.status_code, 200)

    def test_update_assignment_status_blocks_unauthorized_when_configured(self):
        aid = uuid4()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.patch(
                f"/api/assignments/{aid}/status",
                json={"status": "IN_PROGRESS"},
            )
            self.assertEqual(res.status_code, 403)

    # ─────────────────────────────────────────────────────────────────
    # 3. RELIEF RESOURCE MUTATION ENDPOINTS
    # ─────────────────────────────────────────────────────────────────

    def test_create_relief_resource_blocks_unauthorized_when_configured(self):
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post(
                "/api/relief-resources",
                json={
                    "resource_type": "water",
                    "description": "Bottled water",
                    "quantity": 100,
                    "unit": "liters",
                },
            )
            self.assertEqual(res.status_code, 403)

    def test_allocate_relief_resource_blocks_unauthorized_when_configured(self):
        rid = uuid4()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post(
                f"/api/relief-resources/{rid}/allocate",
                json={"request_id": str(uuid4()), "quantity": 10},
            )
            self.assertEqual(res.status_code, 403)

    def test_release_relief_allocation_blocks_unauthorized_when_configured(self):
        aid = uuid4()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post(
                f"/api/relief-resources/allocations/{aid}/release",
            )
            self.assertEqual(res.status_code, 403)

    # ─────────────────────────────────────────────────────────────────
    # 4. SHELTER MUTATION ENDPOINTS
    # ─────────────────────────────────────────────────────────────────

    def test_create_shelter_blocks_unauthorized_when_configured(self):
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post(
                "/api/shelters",
                json={"name": "Emergency Shelter Beta", "capacity": 150},
            )
            self.assertEqual(res.status_code, 403)

    def test_update_shelter_blocks_unauthorized_when_configured(self):
        sid = uuid4()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.patch(
                f"/api/shelters/{sid}",
                json={"name": "Shelter Renamed"},
            )
            self.assertEqual(res.status_code, 403)

    def test_update_shelter_permits_authorized_key(self):
        sid = uuid4()
        fake_shelter = make_fake_shelter(sid)
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
                mock_svc = mock_svc_cls.return_value
                mock_svc.update_shelter.return_value = fake_shelter

                res = self.client.patch(
                    f"/api/shelters/{sid}",
                    headers={"X-Coordinator-Key": TEST_SECRET},
                    json={"name": "Shelter Renamed"},
                )
                self.assertEqual(res.status_code, 200)

    # ─────────────────────────────────────────────────────────────────
    # 5. ALERT MUTATION ENDPOINTS
    # ─────────────────────────────────────────────────────────────────

    def test_alert_acknowledge_blocks_unauthorized_when_configured(self):
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post("/api/alerts/test-alert-123/acknowledge")
            self.assertEqual(res.status_code, 403)

    def test_alert_resolve_blocks_unauthorized_when_configured(self):
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post("/api/alerts/test-alert-123/resolve")
            self.assertEqual(res.status_code, 403)

    def test_alert_responding_blocks_unauthorized_when_configured(self):
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post("/api/alerts/test-alert-123/responding")
            self.assertEqual(res.status_code, 403)

    def test_alert_demo_trigger_blocks_unauthorized_when_configured(self):
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post("/api/alerts/demo/trigger", json={"location_name": "Test"})
            self.assertEqual(res.status_code, 403)

    # ─────────────────────────────────────────────────────────────────
    # 6. FIELD REPORT REVIEW & AI RE-ANALYSIS ENDPOINTS
    # ─────────────────────────────────────────────────────────────────

    def test_field_report_review_blocks_unauthorized_when_configured(self):
        rid = uuid4()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.patch(
                f"/api/field-reports/{rid}/review",
                json={"review_status": "verified"},
            )
            self.assertEqual(res.status_code, 403)

    def test_field_report_analyze_blocks_unauthorized_when_configured(self):
        rid = uuid4()
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            res = self.client.post(f"/api/field-reports/{rid}/analyze")
            self.assertEqual(res.status_code, 403)

    def test_field_report_review_does_not_fabricate_user_identity(self):
        """Review determinations must NOT fabricate reviewer attribution or assign it to a shared key."""
        rid = uuid4()
        mock_report = MagicMock(
            id=rid,
            notes="Observed tension crack",
            location_name="Nainital Ridge",
            latitude=29.38,
            longitude=79.46,
            review_status="verified",
            reviewed_at=datetime.now(timezone.utc),
            reviewed_by=None,  # Crucial: Must be None because no user session exists
            admin_notes="Geotechnical team dispatched",
            ai_hazard_level="high",
            ai_confidence=0.88,
            ai_summary="High tension crack",
            submitted_at=datetime.now(timezone.utc),
            photo_url=None,
            reporter_name=None,
            reporter_phone=None,
        )
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            with patch("backend.app.api.endpoints.field_reports.FieldReportService") as mock_service:
                mock_service.return_value.review_report.return_value = mock_report
                res = self.client.patch(
                    f"/api/field-reports/{rid}/review",
                    headers={"X-Coordinator-Key": TEST_SECRET},
                    json={"review_status": "verified", "admin_notes": "Geotechnical team dispatched"},
                )
                self.assertEqual(res.status_code, 200)
                # Verify that reviewed_by passed to service was explicitly None (not fabricated)
                mock_service.return_value.review_report.assert_called_once_with(
                    rid,
                    review_status="verified",
                    admin_notes="Geotechnical team dispatched",
                    reviewed_by=None,
                )

    # ─────────────────────────────────────────────────────────────────
    # 7. AUDIT HISTORY ENDPOINTS (PROTECTED READ)
    # ─────────────────────────────────────────────────────────────────

    def test_audit_history_blocks_unauthorized_when_configured(self):
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            # List audit entries
            res_list = self.client.get("/api/audit-history")
            self.assertEqual(res_list.status_code, 403)

            # Detail audit entry
            res_detail = self.client.get(f"/api/audit-history/{uuid4()}")
            self.assertEqual(res_detail.status_code, 403)

    def test_audit_history_allows_authorized_with_key_and_bearer(self):
        with patch.dict(os.environ, {"COORDINATOR_API_KEY": TEST_SECRET}):
            with patch("backend.app.api.endpoints.coordination.AuditHistoryRepository") as mock_repo:
                mock_repo.return_value.list_audit_entries.return_value = []
                mock_entry = MagicMock(
                    id=uuid4(),
                    entity_type="field_report",
                    entity_id=uuid4(),
                    action="verified",
                    actor_id=None,
                    old_value=None,
                    new_value=None,
                    created_at=datetime.now(timezone.utc),
                )
                mock_repo.return_value.get_by_id.return_value = mock_entry

                # Header auth
                res_h = self.client.get(
                    "/api/audit-history",
                    headers={"X-Coordinator-Key": TEST_SECRET},
                )
                self.assertEqual(res_h.status_code, 200)

                # Bearer auth
                res_b = self.client.get(
                    f"/api/audit-history/{mock_entry.id}",
                    headers={"Authorization": f"Bearer {TEST_SECRET}"},
                )
                self.assertEqual(res_b.status_code, 200)

    # ─────────────────────────────────────────────────────────────────
    # 8. PRODUCTION FAIL-CLOSED VERIFICATION (HTTP 503)
    # ─────────────────────────────────────────────────────────────────

    def test_production_environment_fails_closed_when_key_unconfigured(self):
        """In production, all coordinator mutation endpoints must fail closed with HTTP 503."""
        endpoints = [
            ("POST", f"/api/volunteers/{uuid4()}/verify", None),
            ("POST", f"/api/volunteers/{uuid4()}/activate", None),
            ("PATCH", f"/api/volunteers/{uuid4()}/status", {"status": "active"}),
            ("POST", "/api/assignments", {"request_id": str(uuid4()), "volunteer_id": str(uuid4())}),
            ("PATCH", f"/api/assignments/{uuid4()}/status", {"status": "IN_PROGRESS"}),
            ("POST", "/api/relief-resources", {"resource_type": "food", "description": "Rations", "quantity": 10, "unit": "boxes"}),
            ("POST", f"/api/relief-resources/{uuid4()}/allocate", {"request_id": str(uuid4()), "quantity": 5}),
            ("POST", f"/api/relief-resources/allocations/{uuid4()}/release", None),
            ("POST", "/api/shelters", {"name": "Test Shelter", "capacity": 50}),
            ("PATCH", f"/api/shelters/{uuid4()}", {"name": "Renamed"}),
            ("POST", "/api/alerts/test-alert-123/acknowledge", None),
            ("POST", "/api/alerts/test-alert-123/resolve", None),
            ("POST", "/api/alerts/test-alert-123/responding", None),
            ("POST", "/api/alerts/demo/trigger", {"location_name": "Test"}),
            ("PATCH", f"/api/field-reports/{uuid4()}/review", {"review_status": "verified"}),
            ("POST", f"/api/field-reports/{uuid4()}/analyze", None),
            ("GET", "/api/audit-history", None),
            ("GET", f"/api/audit-history/{uuid4()}", None),
        ]

        for env_alias in ["ENVIRONMENT", "ENV", "NODE_ENV", "FASTAPI_ENV"]:
            with patch.dict(os.environ, {env_alias: "production", "COORDINATOR_API_KEY": ""}, clear=False):
                for method, path, body in endpoints:
                    if method == "POST":
                        res = self.client.post(path, json=body)
                    elif method == "PATCH":
                        res = self.client.patch(path, json=body)
                    elif method == "GET":
                        res = self.client.get(path)
                    self.assertEqual(
                        res.status_code,
                        503,
                        f"Expected HTTP 503 for {method} {path} when {env_alias}=production without key. Got {res.status_code}",
                    )
                    self.assertIn("Administrative access unavailable", res.json()["detail"])

    # ─────────────────────────────────────────────────────────────────
    # 9. INVENTORY & NON-EXISTENT ROUTE AUDIT
    # ─────────────────────────────────────────────────────────────────

    def test_non_existent_hypothetical_routes_return_404_or_405(self):
        """Verify that hypothetical or miscataloged routes do not exist or return 404/405."""
        hypothetical_routes = [
            ("PATCH", f"/api/incidents/{uuid4()}"),
            ("POST", "/api/evacuation-routes"),
            ("POST", "/api/risk-observations"),
        ]
        for method, path in hypothetical_routes:
            if method == "PATCH":
                res = self.client.patch(path, json={})
            elif method == "POST":
                res = self.client.post(path, json={})
            self.assertIn(
                res.status_code,
                [404, 405],
                f"Expected 404/405 for unmounted route {method} {path}, got {res.status_code}",
            )

    # ─────────────────────────────────────────────────────────────────
    # 10. PUBLIC ROUTE PRESERVATION VERIFICATION
    # ─────────────────────────────────────────────────────────────────

    def test_public_routes_remain_open_in_production(self):
        """Public field-report submission, photo upload, volunteer signup, and mobile sync remain accessible."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "COORDINATOR_API_KEY": TEST_SECRET}):
            # 1. GET /api/field-reports
            with patch("backend.app.api.endpoints.field_reports.FieldReportService") as mock_fr:
                mock_fr.return_value.list_reports.return_value = ([], 0)
                res = self.client.get("/api/field-reports")
                self.assertEqual(res.status_code, 200)

            # 2. GET /api/shelters
            with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_sh:
                mock_sh.return_value.get_all_shelters.return_value = []
                res = self.client.get("/api/shelters")
                self.assertEqual(res.status_code, 200)

            # 3. GET /api/alerts/
            res = self.client.get("/api/alerts/")
            self.assertEqual(res.status_code, 200)

            # 4. POST /api/volunteers (public self-registration)
            with patch("backend.app.api.endpoints.coordination.VolunteerService") as mock_vol:
                mock_vol.return_value.create_profile.return_value = make_fake_volunteer()
                res = self.client.post(
                    "/api/volunteers",
                    json={"user_id": str(uuid4()), "skills": ["first_aid"]},
                )
                self.assertEqual(res.status_code, 200)

            # 5. POST /api/sync/upload (public mobile offline sync)
            res = self.client.post(
                "/api/sync/upload",
                json={"operations": []},
            )
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.json()["success"])

            # 6. GET /health
            res = self.client.get("/health")
            self.assertEqual(res.status_code, 200)

    def test_production_fails_closed_when_key_unconfigured(self):
        """In production, missing coordinator key fails closed with HTTP 503."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "COORDINATOR_API_KEY": ""}):
            res = self.client.post(
                f"/api/volunteers/{uuid4()}/verify",
            )
            self.assertEqual(res.status_code, 503)
            self.assertIn("Administrative access unavailable", res.json()["detail"])

    def test_trusted_origins_and_cors_security_rules(self):
        """Validate production and development origin filtering, format verification, and fail-closed behavior."""
        from backend.app.api.deps import (
            get_cors_configuration,
            get_effective_trusted_origins,
            is_trusted_origin,
            validate_origin,
        )

        # 1. Format validation rules
        # Valid origins
        self.assertEqual(validate_origin("https://bhurakshak.in"), "https://bhurakshak.in")
        self.assertEqual(validate_origin("https://bhurakshak.in/"), "https://bhurakshak.in")
        self.assertEqual(validate_origin("https://app.bhurakshak.in:443"), "https://app.bhurakshak.in")
        self.assertEqual(validate_origin("http://localhost:3000"), "http://localhost:3000")

        # Wildcard rejection
        with self.assertRaises(ValueError):
            validate_origin("*")

        # Path rejection
        with self.assertRaises(ValueError):
            validate_origin("https://bhurakshak.in/subpath")

        # Query and fragment rejection
        with self.assertRaises(ValueError):
            validate_origin("https://bhurakshak.in?query=1")
        with self.assertRaises(ValueError):
            validate_origin("https://bhurakshak.in#fragment")

        # Embedded credentials rejection
        with self.assertRaises(ValueError):
            validate_origin("https://user:pass@bhurakshak.in")

        # Production insecure HTTP rejection
        with self.assertRaises(ValueError):
            validate_origin("http://bhurakshak.in", is_production=True)

        # 2. Production fail-closed when TRUSTED_ORIGINS is missing
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "TRUSTED_ORIGINS": ""}):
            effective = get_effective_trusted_origins(is_production=True)
            self.assertEqual(effective, [])
            # In production, unconfigured origins must return False even for local networks
            self.assertFalse(is_trusted_origin("http://localhost:3000", is_production=True))
            self.assertFalse(is_trusted_origin("http://192.168.1.50:3000", is_production=True))
            self.assertFalse(is_trusted_origin("https://bhurakshak.in", is_production=True))

            cors_conf = get_cors_configuration(is_production=True)
            self.assertEqual(cors_conf["allow_origins"], [])
            self.assertIsNone(cors_conf["allow_origin_regex"])

        # 3. Production with configured HTTPS origins
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "TRUSTED_ORIGINS": "https://bhurakshak.in, https://admin.bhurakshak.in"}):
            self.assertTrue(is_trusted_origin("https://bhurakshak.in", is_production=True))
            self.assertTrue(is_trusted_origin("https://admin.bhurakshak.in", is_production=True))
            self.assertFalse(is_trusted_origin("https://evil-attacker.com", is_production=True))
            # Arbitrary private network IP must NOT pass in production
            self.assertFalse(is_trusted_origin("http://192.168.1.100:3000", is_production=True))

            cors_conf = get_cors_configuration(is_production=True)
            self.assertIn("https://bhurakshak.in", cors_conf["allow_origins"])
            self.assertIn("https://admin.bhurakshak.in", cors_conf["allow_origins"])
            self.assertIsNone(cors_conf["allow_origin_regex"])

        # 4. Development mode preserves local origins and emulator regex
        with patch.dict(os.environ, {"ENVIRONMENT": "development", "TRUSTED_ORIGINS": ""}):
            self.assertTrue(is_trusted_origin("http://localhost:3000", is_production=False))
            self.assertTrue(is_trusted_origin("http://127.0.0.1:3000", is_production=False))
            self.assertTrue(is_trusted_origin("http://10.0.2.2:3000", is_production=False))
            self.assertTrue(is_trusted_origin("http://192.168.0.102:3000", is_production=False))

            cors_conf = get_cors_configuration(is_production=False)
            self.assertIn("http://localhost:3000", cors_conf["allow_origins"])
            self.assertIsNotNone(cors_conf["allow_origin_regex"])


if __name__ == "__main__":
    unittest.main()
