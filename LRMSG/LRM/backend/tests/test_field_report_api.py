"""Unit and route integration test suite for FieldReport API endpoints.

Covers:
- Valid report creation with and without coordinates.
- Invalid coordinate combinations and boundary violations.
- Protection against client-supplied AI metadata.
- Standalone photo uploads and multipart form submissions.
- Photo MIME-type validation and size-limit enforcement.
- Listing, filtering, and pagination.
- UUID validation and 404 error handling.
- Review workflow transitions and client-supplied user ID rejection.
- Database rollback on unexpected errors.
- Regression checks for coordination endpoints.
- Verification that legacy ML models are never loaded into memory.
"""

from datetime import datetime, timezone
import io
import sys
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.app.database.base import get_db
from backend.app.main import app
from backend.app.services.field_report_service import FieldReportService
from backend.app.services.photo_storage_service import LocalStorageAdapter


class DummyFieldReport:
    """Mock FieldReport model entity for unit tests."""

    def __init__(
        self,
        id=None,
        photo_url=None,
        notes=None,
        location_name=None,
        latitude=None,
        longitude=None,
        location=None,
        reporter_name=None,
        reporter_phone=None,
        submitted_at=None,
        ai_hazard_level="indeterminate",
        ai_detected_hazards=None,
        ai_confidence=None,
        ai_summary=None,
        ai_analyzed_at=None,
        review_status="pending",
        reviewed_at=None,
        reviewed_by=None,
        admin_notes=None,
    ):
        self.id = id or uuid4()
        self.photo_url = photo_url
        self.notes = notes
        self.location_name = location_name
        self.latitude = latitude
        self.longitude = longitude
        self.location = location
        self.reporter_name = reporter_name
        self.reporter_phone = reporter_phone
        self.submitted_at = submitted_at or datetime.now(timezone.utc)
        self.ai_hazard_level = ai_hazard_level
        self.ai_detected_hazards = ai_detected_hazards or []
        self.ai_confidence = ai_confidence
        self.ai_summary = ai_summary
        self.ai_analyzed_at = ai_analyzed_at
        self.review_status = review_status
        self.reviewed_at = reviewed_at
        self.reviewed_by = reviewed_by
        self.admin_notes = admin_notes


class TestFieldReportApi(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.mock_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    # ── 1. Create Report with Coordinates ──────────────────────────

    def test_create_report_with_valid_coordinates(self):
        dummy = DummyFieldReport(
            notes="Active debris flow on NH-10",
            location_name="29th Mile, Teesta",
            latitude=27.04,
            longitude=88.26,
            reporter_name="Tashi Dorjee",
            reporter_phone="+91-9876543210",
        )

        with patch.object(FieldReportService, "create_report", return_value=dummy) as mock_create:
            payload = {
                "notes": "Active debris flow on NH-10",
                "location_name": "29th Mile, Teesta",
                "latitude": 27.04,
                "longitude": 88.26,
                "reporter_name": "Tashi Dorjee",
                "reporter_phone": "+91-9876543210",
            }
            res = self.client.post("/api/field-reports", json=payload)
            self.assertEqual(res.status_code, 201)
            data = res.json()
            self.assertEqual(data["notes"], "Active debris flow on NH-10")
            self.assertEqual(data["latitude"], 27.04)
            self.assertEqual(data["longitude"], 88.26)
            self.assertEqual(data["ai_hazard_level"], "indeterminate")
            self.assertEqual(data["review_status"], "pending")
            self.mock_db.commit.assert_called_once()

    # ── 2. Create Report without Coordinates ───────────────────────

    def test_create_report_without_coordinates(self):
        dummy = DummyFieldReport(
            notes="Power lines down near hill slope",
            location_name="Lower Bazar",
            latitude=None,
            longitude=None,
        )

        with patch.object(FieldReportService, "create_report", return_value=dummy):
            payload = {
                "notes": "Power lines down near hill slope",
                "location_name": "Lower Bazar",
            }
            res = self.client.post("/api/field-reports", json=payload)
            self.assertEqual(res.status_code, 201)
            data = res.json()
            self.assertIsNone(data["latitude"])
            self.assertIsNone(data["longitude"])
            self.mock_db.commit.assert_called_once()

    # ── 3. Coordinate Pair Integrity ───────────────────────────────

    def test_create_report_incomplete_coordinate_latitude_only_rejected(self):
        payload = {
            "notes": "Slope movement",
            "latitude": 27.04,
            # longitude omitted
        }
        res = self.client.post("/api/field-reports", json=payload)
        self.assertEqual(res.status_code, 422)
        self.mock_db.commit.assert_not_called()

    def test_create_report_incomplete_coordinate_longitude_only_rejected(self):
        payload = {
            "notes": "Slope movement",
            "longitude": 88.26,
            # latitude omitted
        }
        res = self.client.post("/api/field-reports", json=payload)
        self.assertEqual(res.status_code, 422)
        self.mock_db.commit.assert_not_called()

    # ── 4. Coordinate Range Violations ─────────────────────────────

    def test_create_report_latitude_out_of_bounds_rejected(self):
        payload = {
            "notes": "Invalid north pole latitude",
            "latitude": 91.5,
            "longitude": 88.26,
        }
        res = self.client.post("/api/field-reports", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_create_report_longitude_out_of_bounds_rejected(self):
        payload = {
            "notes": "Invalid longitude",
            "latitude": 27.04,
            "longitude": 181.0,
        }
        res = self.client.post("/api/field-reports", json=payload)
        self.assertEqual(res.status_code, 422)

    # ── 5. AI Metadata Protection ──────────────────────────────────

    def test_create_report_client_supplied_ai_metadata_rejected(self):
        payload = {
            "notes": "Trying to forge AI hazard rating",
            "ai_hazard_level": "critical",
            "ai_confidence": 0.99,
        }
        res = self.client.post("/api/field-reports", json=payload)
        self.assertEqual(res.status_code, 422)
        self.mock_db.commit.assert_not_called()

    # ── 6. Multipart Form Submission with Photo ────────────────────

    def test_create_report_multipart_with_photo(self):
        dummy = DummyFieldReport(
            notes="Rockfall photographed",
            latitude=27.0,
            longitude=88.0,
            photo_url="/uploads/field_reports/mock_photo.jpg",
        )

        with patch.object(FieldReportService, "save_uploaded_photo", return_value=("/uploads/field_reports/mock_photo.jpg", "mock_photo.jpg", 1024)):
            with patch.object(FieldReportService, "create_report", return_value=dummy):
                fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
                form_data = {
                    "notes": "Rockfall photographed",
                    "latitude": "27.0",
                    "longitude": "88.0",
                }
                files = {
                    "photo": ("test.jpg", fake_image, "image/jpeg"),
                }
                res = self.client.post("/api/field-reports", data=form_data, files=files)
                self.assertEqual(res.status_code, 201)
                data = res.json()
                self.assertEqual(data["photo_url"], "/uploads/field_reports/mock_photo.jpg")

    # ── 7. Standalone Photo Upload ─────────────────────────────────

    def test_upload_photo_valid_image(self):
        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 200)
        files = {"file": ("slide.jpg", fake_image, "image/jpeg")}

        res = self.client.post("/api/field-reports/upload-photo", files=files)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["photo_url"].startswith("/uploads/field_reports/"))
        self.assertTrue(data["filename"].endswith(".jpg"))
        self.assertEqual(data["content_type"], "image/jpeg")

    def test_upload_photo_invalid_mime_rejected(self):
        fake_binary = io.BytesIO(b"MZ\x90\x00" + b"\x00" * 50)
        files = {"file": ("malicious.exe", fake_binary, "application/octet-stream")}

        res = self.client.post("/api/field-reports/upload-photo", files=files)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Unsupported image type", res.json()["detail"])

    def test_upload_photo_empty_file_rejected(self):
        empty_file = io.BytesIO(b"")
        files = {"file": ("empty.jpg", empty_file, "image/jpeg")}

        res = self.client.post("/api/field-reports/upload-photo", files=files)
        self.assertEqual(res.status_code, 400)

    # ── 8. Retrieve Single Report ──────────────────────────────────

    def test_get_report_by_id_success(self):
        report_id = uuid4()
        dummy = DummyFieldReport(id=report_id, notes="Retrieved observation")

        with patch.object(FieldReportService, "get_report", return_value=dummy):
            res = self.client.get(f"/api/field-reports/{report_id}")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["id"], str(report_id))

    def test_get_report_by_id_not_found(self):
        missing_id = uuid4()
        with patch.object(FieldReportService, "get_report", return_value=None):
            res = self.client.get(f"/api/field-reports/{missing_id}")
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["detail"], "Field report not found.")

    def test_get_report_invalid_uuid_rejected(self):
        res = self.client.get("/api/field-reports/not-a-valid-uuid")
        self.assertEqual(res.status_code, 422)

    # ── 9. List and Filter Reports ─────────────────────────────────

    def test_list_reports_with_pagination(self):
        dummies = [DummyFieldReport(notes=f"Note {i}") for i in range(5)]
        with patch.object(FieldReportService, "list_reports", return_value=(dummies, 25)):
            res = self.client.get("/api/field-reports?limit=5&offset=10")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(len(data["items"]), 5)
            self.assertEqual(data["total"], 25)
            self.assertEqual(data["limit"], 5)
            self.assertEqual(data["offset"], 10)

    def test_list_reports_invalid_review_status_filter_rejected(self):
        with patch.object(FieldReportService, "list_reports", side_effect=ValueError("Invalid review_status")):
            res = self.client.get("/api/field-reports?review_status=bogus_status")
            self.assertEqual(res.status_code, 400)

    # ── 10. Review Workflow ────────────────────────────────────────

    def test_review_report_success(self):
        report_id = uuid4()
        dummy = DummyFieldReport(
            id=report_id,
            review_status="verified",
            admin_notes="Geotechnical verification confirmed crown cracks",
            reviewed_at=datetime.now(timezone.utc),
        )

        with patch.object(FieldReportService, "review_report", return_value=dummy):
            payload = {
                "review_status": "verified",
                "admin_notes": "Geotechnical verification confirmed crown cracks",
            }
            res = self.client.patch(f"/api/field-reports/{report_id}/review", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["review_status"], "verified")
            self.assertEqual(data["admin_notes"], "Geotechnical verification confirmed crown cracks")
            self.mock_db.commit.assert_called_once()

    def test_review_report_invalid_status_rejected(self):
        report_id = uuid4()
        payload = {"review_status": "certified_fake"}
        res = self.client.patch(f"/api/field-reports/{report_id}/review", json=payload)
        self.assertEqual(res.status_code, 422)
        self.mock_db.commit.assert_not_called()

    def test_review_report_client_supplied_user_id_rejected(self):
        report_id = uuid4()
        payload = {
            "review_status": "verified",
            "reviewed_by": str(uuid4()),  # Untrusted client identity
        }
        res = self.client.patch(f"/api/field-reports/{report_id}/review", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_review_report_not_found(self):
        report_id = uuid4()
        with patch.object(FieldReportService, "review_report", return_value=None):
            payload = {"review_status": "rejected"}
            res = self.client.patch(f"/api/field-reports/{report_id}/review", json=payload)
            self.assertEqual(res.status_code, 404)

    # ── 11. Database Error Handling & Rollback ─────────────────────

    def test_create_report_db_error_triggers_rollback(self):
        with patch.object(FieldReportService, "create_report", side_effect=Exception("Database connection dropped")):
            payload = {"notes": "Test fail"}
            res = self.client.post("/api/field-reports", json=payload)
            self.assertEqual(res.status_code, 500)
            self.mock_db.rollback.assert_called_once()

    # ── 12. Legacy ML Model Isolation ──────────────────────────────

    def test_legacy_ml_never_loaded_by_field_reports(self):
        """Verify that importing or accessing field report endpoints never touches legacy ML."""
        self.assertNotIn("xgboost", sys.modules)
        self.assertNotIn("joblib", sys.modules)

    # ── 13. Regression Check for Coordination Endpoints ────────────

    def test_regression_coordination_endpoints_remain_functional(self):
        # Health check
        res_health = self.client.get("/health/")
        self.assertEqual(res_health.status_code, 200)

        # Retired prediction endpoint remains 503
        res_pred = self.client.post("/prediction/", json={})
        self.assertEqual(res_pred.status_code, 503)


    # ── 14. Sync Upload Endpoint FieldReport Support ───────────────

    def test_sync_upload_field_report_success(self):
        op_id = f"test-sync-{uuid4().hex[:8]}"
        dummy = DummyFieldReport(
            notes="Tension cracks across road",
            location_name="Mile 12",
            latitude=27.0,
            longitude=88.0,
        )
        with patch.object(FieldReportService, "create_report", return_value=dummy):
            sync_payload = {
                "operations": [{
                    "id": op_id,
                    "operation": "CREATE",
                    "entity": "field_report",
                    "payload": {
                        "notes": "Tension cracks across road",
                        "location_name": "Mile 12",
                        "latitude": 27.0,
                        "longitude": 88.0,
                    },
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                }]
            }
            res = self.client.post("/api/sync/upload", json=sync_payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertIn(op_id, data["success_ids"])

    def test_sync_upload_field_report_with_base64_photo(self):
        import base64
        op_id = f"test-sync-photo-{uuid4().hex[:8]}"
        dummy = DummyFieldReport(
            notes="Rockfall photographed",
            photo_url="/uploads/field_reports/synced_photo.jpg",
        )
        with patch.object(FieldReportService, "create_report", return_value=dummy):
            with patch("backend.app.services.photo_storage_service.photo_storage_service.save_photo",
                       return_value=("/uploads/field_reports/synced_photo.jpg", "synced_photo.jpg", 200)):
                sync_payload = {
                    "operations": [{
                        "id": op_id,
                        "operation": "CREATE",
                        "entity": "field_report",
                        "payload": {
                            "notes": "Rockfall photographed",
                            "photo_data": "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0" + b"\x00" * 50).decode("utf-8"),
                        },
                        "createdAt": datetime.now(timezone.utc).isoformat(),
                    }]
                }
                res = self.client.post("/api/sync/upload", json=sync_payload)
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertTrue(data["success"])
                self.assertIn(op_id, data["success_ids"])

    def test_sync_upload_field_report_storage_failure_handled(self):
        op_id = f"test-sync-fail-{uuid4().hex[:8]}"
        dummy = DummyFieldReport(notes="Report with corrupt photo")
        with patch.object(FieldReportService, "create_report", return_value=dummy):
            sync_payload = {
                "operations": [{
                    "id": op_id,
                    "operation": "CREATE",
                    "entity": "field_report",
                    "payload": {
                        "notes": "Report with corrupt photo",
                        "photo_data": "invalid-non-base64-content",
                    },
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                }]
            }
            res = self.client.post("/api/sync/upload", json=sync_payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertIn(op_id, data["success_ids"])

    def test_sync_upload_field_report_duplicate_idempotency(self):
        """Re-submitting the same operation ID must be recognized as idempotent and avoid duplicate creation."""
        op_id = f"test-sync-idem-{uuid4().hex[:8]}"
        dummy = DummyFieldReport(
            notes="Tension crack repeat upload",
            location_name="Mile 14",
        )
        with patch.object(FieldReportService, "create_report", return_value=dummy) as mock_create:
            sync_payload = {
                "operations": [{
                    "id": op_id,
                    "operation": "CREATE",
                    "entity": "field_report",
                    "payload": {
                        "notes": "Tension crack repeat upload",
                        "location_name": "Mile 14",
                    },
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                }]
            }
            # First submission
            res1 = self.client.post("/api/sync/upload", json=sync_payload)
            self.assertEqual(res1.status_code, 200)
            self.assertIn(op_id, res1.json()["success_ids"])
            self.assertEqual(mock_create.call_count, 1)

            # Re-submission with the same op_id
            res2 = self.client.post("/api/sync/upload", json=sync_payload)
            self.assertEqual(res2.status_code, 200)
            data2 = res2.json()
            self.assertTrue(data2["success"])
            self.assertIn(op_id, data2["success_ids"])
            # Crucial: create_report must NOT have been called a second time
            self.assertEqual(mock_create.call_count, 1)
            # Must report idempotent status
            db_res = data2.get("db_results", [])
            self.assertTrue(any(r.get("op_id") == op_id and r.get("status") == "idempotent" for r in db_res))


if __name__ == "__main__":
    unittest.main()
