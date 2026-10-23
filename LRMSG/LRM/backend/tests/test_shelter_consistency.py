"""Persistent regression test suite for shelter consistency in PahaarPulse / LRM.

Covers:
- Phase 1 state-transition rules (zero-capacity rejection, explicit open rejection when at capacity,
  auto-full transitions, auto-reopening when physical constraint relieved, administrative hold preservation,
  closed status preservation).
- Phase 2 metadata-only updates on legacy over-capacity records without false-positive rejection.
- Mocked DB sessions so tests never mutate real database records.
- Route-level HTTP integration tests for shelter endpoints using FastAPI TestClient with mocked dependencies.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.app.database.base import get_db
from backend.app.main import app
from backend.app.services.shelter_service import ShelterService


class DummyShelter:
    def __init__(
        self,
        id,
        name,
        capacity,
        current_occupancy,
        status,
        address="Test Address",
        contact_phone=None,
        facilities=None,
        location=None,
        operated_by=None,
        created_at=None,
        updated_at=None,
    ):
        self.id = id
        self.name = name
        self.capacity = capacity
        self.current_occupancy = current_occupancy
        self.status = status
        self.address = address
        self.contact_phone = contact_phone
        self.facilities = facilities or {}
        self.location = location
        self.operated_by = operated_by
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)


class TestShelterConsistency(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShelterService(self.mock_db)
        self.service.shelter_repo = MagicMock()
        self.service.audit_repo = MagicMock()

    # ────────────────────────────────────────────────────────────
    # 1. create_shelter validation tests
    # ────────────────────────────────────────────────────────────

    def test_create_shelter_zero_capacity_open_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_shelter(
                name="Zero Cap Shelter",
                capacity=0,
                current_occupancy=0,
                status="open",
            )
        self.assertIn("zero capacity cannot be assigned 'open' status", str(ctx.exception))

    def test_create_shelter_at_capacity_open_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_shelter(
                name="At Capacity Shelter",
                capacity=100,
                current_occupancy=100,
                status="open",
            )
        self.assertIn("greater than or equal to capacity", str(ctx.exception))

    def test_create_shelter_overflow_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_shelter(
                name="Overflow Shelter",
                capacity=100,
                current_occupancy=150,
                status="full",
            )
        self.assertIn("cannot exceed capacity", str(ctx.exception))

    def test_create_shelter_negative_occupancy_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_shelter(
                name="Negative Occ",
                capacity=100,
                current_occupancy=-1,
                status="open",
            )
        self.assertIn("current_occupancy cannot be negative", str(ctx.exception))

    def test_create_shelter_negative_capacity_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_shelter(
                name="Negative Cap",
                capacity=-10,
                current_occupancy=0,
                status="open",
            )
        self.assertIn("capacity cannot be negative", str(ctx.exception))

    def test_create_shelter_zero_capacity_closed_allowed(self):
        fake_id = uuid4()
        dummy = DummyShelter(id=fake_id, name="Zero Cap Closed", capacity=0, current_occupancy=0, status="closed")
        self.service.shelter_repo.create.return_value = dummy

        result = self.service.create_shelter(
            name="Zero Cap Closed",
            capacity=0,
            current_occupancy=0,
            status="closed",
        )
        self.assertEqual(result.status, "closed")
        self.service.audit_repo.log.assert_called_once()

    def test_create_shelter_valid_open_allowed(self):
        fake_id = uuid4()
        dummy = DummyShelter(id=fake_id, name="Valid Open", capacity=100, current_occupancy=40, status="open")
        self.service.shelter_repo.create.return_value = dummy

        result = self.service.create_shelter(
            name="Valid Open",
            capacity=100,
            current_occupancy=40,
            status="open",
        )
        self.assertEqual(result.status, "open")
        self.service.audit_repo.log.assert_called_once()

    # ────────────────────────────────────────────────────────────
    # 2. update_shelter explicit status tests
    # ────────────────────────────────────────────────────────────

    def test_update_shelter_explicit_open_when_at_capacity_rejected(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=100, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter

        with self.assertRaises(ValueError) as ctx:
            self.service.update_shelter(shelter_id, status="open")
        self.assertIn("greater than or equal to capacity", str(ctx.exception))

    def test_update_shelter_explicit_open_when_zero_capacity_rejected(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=0, current_occupancy=0, status="closed")
        self.service.shelter_repo.get_by_id.return_value = old_shelter

        with self.assertRaises(ValueError) as ctx:
            self.service.update_shelter(shelter_id, status="open")
        self.assertIn("zero capacity cannot be assigned 'open' status", str(ctx.exception))

    def test_update_shelter_explicit_open_on_legacy_overcapacity_rejected(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="Legacy Overcapacity", capacity=100, current_occupancy=101, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter

        with self.assertRaises(ValueError) as ctx:
            self.service.update_shelter(shelter_id, status="open")
        self.assertIn("greater than or equal to capacity", str(ctx.exception))

    def test_update_shelter_explicit_open_when_capacity_increased_succeeds(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=100, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=150, current_occupancy=100, status="open")
        self.service.shelter_repo.update.return_value = updated_shelter

        result = self.service.update_shelter(shelter_id, capacity=150, status="open")
        self.assertEqual(result.status, "open")
        self.service.shelter_repo.update.assert_called_with(shelter_id, capacity=150, status="open")

    def test_update_shelter_explicit_closed_succeeds(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=40, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=40, status="closed")
        self.service.shelter_repo.update.return_value = updated_shelter

        result = self.service.update_shelter(shelter_id, status="closed")
        self.assertEqual(result.status, "closed")
        self.service.shelter_repo.update.assert_called_with(shelter_id, status="closed")

    def test_update_shelter_explicit_full_succeeds(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=300, current_occupancy=0, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=300, current_occupancy=0, status="full")
        self.service.shelter_repo.update.return_value = updated_shelter

        result = self.service.update_shelter(shelter_id, status="full")
        self.assertEqual(result.status, "full")
        self.service.shelter_repo.update.assert_called_with(shelter_id, status="full")

    # ────────────────────────────────────────────────────────────
    # 3. update_shelter automatic transitions (no explicit status)
    # ────────────────────────────────────────────────────────────

    def test_update_shelter_auto_full_when_occupancy_reaches_capacity(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=80, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=100, status="full")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, current_occupancy=100)
        self.service.shelter_repo.update.assert_called_with(shelter_id, current_occupancy=100, status="full")

    def test_update_shelter_auto_full_when_capacity_reduced_to_occupancy(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=150, current_occupancy=100, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=100, status="full")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, capacity=100)
        self.service.shelter_repo.update.assert_called_with(shelter_id, capacity=100, status="full")

    def test_update_shelter_preserves_closed_when_reaching_capacity(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=50, status="closed")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=100, status="closed")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, current_occupancy=100)
        # kwargs should NOT have status="full"
        self.service.shelter_repo.update.assert_called_with(shelter_id, current_occupancy=100)

    def test_update_shelter_preserves_closed_when_occupancy_reduced(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=50, status="closed")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=20, status="closed")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, current_occupancy=20)
        # kwargs should NOT have status="open"
        self.service.shelter_repo.update.assert_called_with(shelter_id, current_occupancy=20)

    def test_update_shelter_auto_reopens_full_shelter_when_below_capacity(self):
        shelter_id = uuid4()
        # Previously full at 100/100
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=100, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=80, status="open")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, current_occupancy=80)
        self.service.shelter_repo.update.assert_called_with(shelter_id, current_occupancy=80, status="open")

    def test_update_shelter_auto_reopens_full_shelter_when_capacity_increased(self):
        shelter_id = uuid4()
        # Previously full at 100/100
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=100, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=200, current_occupancy=100, status="open")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, capacity=200)
        self.service.shelter_repo.update.assert_called_with(shelter_id, capacity=200, status="open")

    def test_update_shelter_preserves_administrative_hold_full_status_on_capacity_increase(self):
        shelter_id = uuid4()
        # Administrative hold: status="full" while occupancy was 0 out of 300 (occupancy < capacity)
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=300, current_occupancy=0, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=350, current_occupancy=0, status="full")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, capacity=350)
        # Should NOT reopen because old_occupancy (0) < old_capacity (300)
        self.service.shelter_repo.update.assert_called_with(shelter_id, capacity=350)

    def test_update_shelter_preserves_administrative_hold_full_status_on_occupancy_change(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=300, current_occupancy=0, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="S1", capacity=300, current_occupancy=50, status="full")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, current_occupancy=50)
        # Still < 300 and old was 0 < 300 -> preserves full
        self.service.shelter_repo.update.assert_called_with(shelter_id, current_occupancy=50)

    # ────────────────────────────────────────────────────────────
    # 4. update_shelter capacity / occupancy validation
    # ────────────────────────────────────────────────────────────

    def test_update_shelter_rejects_occupancy_exceeding_capacity(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=50, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter

        with self.assertRaises(ValueError) as ctx:
            self.service.update_shelter(shelter_id, current_occupancy=120)
        self.assertIn("cannot exceed capacity", str(ctx.exception))

    def test_update_shelter_rejects_negative_occupancy(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=50, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter

        with self.assertRaises(ValueError) as ctx:
            self.service.update_shelter(shelter_id, current_occupancy=-1)
        self.assertIn("current_occupancy cannot be negative", str(ctx.exception))

    def test_update_shelter_rejects_negative_capacity(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="S1", capacity=100, current_occupancy=50, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter

        with self.assertRaises(ValueError) as ctx:
            self.service.update_shelter(shelter_id, capacity=-10)
        self.assertIn("capacity cannot be negative", str(ctx.exception))

    # ────────────────────────────────────────────────────────────
    # 5. Metadata-only updates on legacy over-capacity records
    # ────────────────────────────────────────────────────────────

    def test_legacy_overcapacity_name_update_succeeds(self):
        shelter_id = uuid4()
        # Legacy record with 500 occupied out of 200 capacity
        old_shelter = DummyShelter(id=shelter_id, name="Old Name", capacity=200, current_occupancy=500, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="New Name", capacity=200, current_occupancy=500, status="full")
        self.service.shelter_repo.update.return_value = updated_shelter

        result = self.service.update_shelter(shelter_id, name="New Name")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "New Name")
        self.service.shelter_repo.update.assert_called_with(shelter_id, name="New Name")
        self.service.audit_repo.log.assert_called_once()

    def test_legacy_overcapacity_address_update_succeeds(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="E7", capacity=200, current_occupancy=500, status="full", address="Old Addr")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="E7", capacity=200, current_occupancy=500, status="full", address="New Addr")
        self.service.shelter_repo.update.return_value = updated_shelter

        result = self.service.update_shelter(shelter_id, address="New Addr")
        self.assertIsNotNone(result)
        self.assertEqual(result.address, "New Addr")
        self.service.shelter_repo.update.assert_called_with(shelter_id, address="New Addr")

    def test_legacy_overcapacity_contact_phone_update_succeeds(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="E7", capacity=100, current_occupancy=101, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="E7", capacity=100, current_occupancy=101, status="open", contact_phone="+91-1234567890")
        self.service.shelter_repo.update.return_value = updated_shelter

        result = self.service.update_shelter(shelter_id, contact_phone="+91-1234567890")
        self.assertIsNotNone(result)
        self.assertEqual(result.contact_phone, "+91-1234567890")
        self.service.shelter_repo.update.assert_called_with(shelter_id, contact_phone="+91-1234567890")

    def test_legacy_overcapacity_facilities_update_succeeds(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="E7", capacity=200, current_occupancy=500, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        new_fac = {"generator": True, "medical_kit": True}
        updated_shelter = DummyShelter(id=shelter_id, name="E7", capacity=200, current_occupancy=500, status="full", facilities=new_fac)
        self.service.shelter_repo.update.return_value = updated_shelter

        result = self.service.update_shelter(shelter_id, facilities=new_fac)
        self.assertIsNotNone(result)
        self.assertEqual(result.facilities, new_fac)
        self.service.shelter_repo.update.assert_called_with(shelter_id, facilities=new_fac)

    def test_legacy_overcapacity_changing_capacity_still_overflowing_rejected(self):
        shelter_id = uuid4()
        # Attempting to change capacity from 200 to 300 while occupancy is 500
        old_shelter = DummyShelter(id=shelter_id, name="E7", capacity=200, current_occupancy=500, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter

        with self.assertRaises(ValueError) as ctx:
            self.service.update_shelter(shelter_id, capacity=300)
        self.assertIn("current_occupancy (500) cannot exceed capacity (300)", str(ctx.exception))

    def test_legacy_overcapacity_healed_via_capacity_increase_reopens(self):
        shelter_id = uuid4()
        # Increasing capacity to 600 heals the 500-occupancy overflow and auto-reopens
        old_shelter = DummyShelter(id=shelter_id, name="E7", capacity=200, current_occupancy=500, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="E7", capacity=600, current_occupancy=500, status="open")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, capacity=600)
        self.service.shelter_repo.update.assert_called_with(shelter_id, capacity=600, status="open")

    def test_legacy_overcapacity_healed_via_occupancy_reduction_reopens(self):
        shelter_id = uuid4()
        # Decreasing occupancy to 150 heals the 200-capacity overflow and auto-reopens
        old_shelter = DummyShelter(id=shelter_id, name="E7", capacity=200, current_occupancy=500, status="full")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="E7", capacity=200, current_occupancy=150, status="open")
        self.service.shelter_repo.update.return_value = updated_shelter

        self.service.update_shelter(shelter_id, current_occupancy=150)
        self.service.shelter_repo.update.assert_called_with(shelter_id, current_occupancy=150, status="open")

    # ────────────────────────────────────────────────────────────
    # 6. None handling and nonexistent shelter
    # ────────────────────────────────────────────────────────────

    def test_update_shelter_nonexistent_returns_none(self):
        unknown_id = uuid4()
        self.service.shelter_repo.get_by_id.return_value = None
        result = self.service.update_shelter(unknown_id, name="Does Not Exist")
        self.assertIsNone(result)

    def test_update_shelter_cleans_up_none_capacity_and_occupancy(self):
        shelter_id = uuid4()
        old_shelter = DummyShelter(id=shelter_id, name="E7", capacity=100, current_occupancy=50, status="open")
        self.service.shelter_repo.get_by_id.return_value = old_shelter
        updated_shelter = DummyShelter(id=shelter_id, name="Updated", capacity=100, current_occupancy=50, status="open")
        self.service.shelter_repo.update.return_value = updated_shelter

        result = self.service.update_shelter(shelter_id, name="Updated", capacity=None, current_occupancy=None)
        self.assertIsNotNone(result)
        self.service.shelter_repo.update.assert_called_with(shelter_id, name="Updated")


# ────────────────────────────────────────────────────────────
# 7. Route-level HTTP Integration Tests (FastAPI TestClient)
# ────────────────────────────────────────────────────────────

class TestShelterHttpRoutes(unittest.TestCase):
    """Route-level integration tests for shelter HTTP endpoints.

    Uses FastAPI TestClient with mocked dependencies to test HTTP contracts,
    status codes, validation rules, error handling, and transaction commits
    without touching a live database or running server.
    """

    def setUp(self):
        self.mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.mock_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    # ── POST /api/shelters ──

    def test_post_shelter_success_shape_and_commit(self):
        shelter_id = uuid4()
        fake_shelter = DummyShelter(
            id=shelter_id,
            name="Hillview Safe Haven",
            capacity=200,
            current_occupancy=45,
            status="open",
            address="Upper Mall Road, Shimla",
            contact_phone="+91-9876543210",
            facilities={"generator": True, "first_aid": True},
        )
        payload = {
            "name": "Hillview Safe Haven",
            "address": "Upper Mall Road, Shimla",
            "capacity": 200,
            "current_occupancy": 45,
            "facilities": {"generator": True, "first_aid": True},
            "contact_phone": "+91-9876543210",
            "latitude": 31.1048,
            "longitude": 77.1734,
        }
        with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.create_shelter.return_value = fake_shelter

            response = self.client.post("/api/shelters", json=payload)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["id"], str(shelter_id))
            self.assertEqual(data["name"], "Hillview Safe Haven")
            self.assertEqual(data["capacity"], 200)
            self.assertEqual(data["current_occupancy"], 45)
            self.assertEqual(data["status"], "open")
            self.assertEqual(data["address"], "Upper Mall Road, Shimla")
            self.assertEqual(data["contact_phone"], "+91-9876543210")
            self.assertEqual(data["facilities"], {"generator": True, "first_aid": True})

            mock_svc.create_shelter.assert_called_once_with(
                name="Hillview Safe Haven",
                address="Upper Mall Road, Shimla",
                capacity=200,
                current_occupancy=45,
                facilities={"generator": True, "first_aid": True},
                contact_phone="+91-9876543210",
                operated_by=None,
                latitude=31.1048,
                longitude=77.1734,
            )
            self.mock_db.commit.assert_called_once()

    def test_post_shelter_value_error_returns_400_and_no_commit(self):
        payload = {
            "name": "Zero Cap Shelter",
            "capacity": 0,
            "current_occupancy": 0,
        }
        with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.create_shelter.side_effect = ValueError(
                "Shelter with zero capacity cannot be assigned 'open' status"
            )

            response = self.client.post("/api/shelters", json=payload)

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json()["detail"],
                "Shelter with zero capacity cannot be assigned 'open' status",
            )
            self.mock_db.commit.assert_not_called()

    def test_post_shelter_missing_required_name_returns_422(self):
        payload = {
            "capacity": 100,
            "current_occupancy": 10,
        }
        response = self.client.post("/api/shelters", json=payload)
        self.assertEqual(response.status_code, 422)
        self.mock_db.commit.assert_not_called()

    def test_post_shelter_invalid_coordinates_returns_422(self):
        # Invalid latitude (> 90)
        res_lat = self.client.post(
            "/api/shelters",
            json={"name": "Bad Lat Shelter", "latitude": 91.5},
        )
        self.assertEqual(res_lat.status_code, 422)

        # Invalid longitude (> 180)
        res_lng = self.client.post(
            "/api/shelters",
            json={"name": "Bad Lng Shelter", "longitude": 185.0},
        )
        self.assertEqual(res_lng.status_code, 422)

        self.mock_db.commit.assert_not_called()

    # ── PATCH /api/shelters/{shelter_id} ──

    def test_patch_shelter_success_shape_and_commit(self):
        shelter_id = uuid4()
        fake_shelter = DummyShelter(
            id=shelter_id,
            name="Hillview Safe Haven",
            capacity=200,
            current_occupancy=45,
            status="closed",
            address="Upper Mall Road, Shimla",
            contact_phone="+91-9999999999",
        )
        payload = {
            "status": "closed",
            "contact_phone": "+91-9999999999",
        }
        with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.update_shelter.return_value = fake_shelter

            response = self.client.patch(f"/api/shelters/{shelter_id}", json=payload)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["id"], str(shelter_id))
            self.assertEqual(data["status"], "closed")
            self.assertEqual(data["contact_phone"], "+91-9999999999")

            mock_svc.update_shelter.assert_called_once_with(
                shelter_id,
                status="closed",
                contact_phone="+91-9999999999",
            )
            self.mock_db.commit.assert_called_once()

    def test_patch_shelter_metadata_only_update_success(self):
        shelter_id = uuid4()
        fake_shelter = DummyShelter(
            id=shelter_id,
            name="E7 Shelter (Archived - Duplicate)",
            capacity=200,
            current_occupancy=500,
            status="closed",
        )
        payload = {
            "name": "E7 Shelter (Archived - Duplicate)",
        }
        with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.update_shelter.return_value = fake_shelter

            response = self.client.patch(f"/api/shelters/{shelter_id}", json=payload)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["name"], "E7 Shelter (Archived - Duplicate)")
            mock_svc.update_shelter.assert_called_once_with(
                shelter_id,
                name="E7 Shelter (Archived - Duplicate)",
            )
            self.mock_db.commit.assert_called_once()

    def test_patch_shelter_value_error_returns_400_and_no_commit(self):
        shelter_id = uuid4()
        payload = {"status": "open"}
        with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.update_shelter.side_effect = ValueError(
                "explicit 'open' status rejected: shelter is at full capacity"
            )

            response = self.client.patch(f"/api/shelters/{shelter_id}", json=payload)

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json()["detail"],
                "explicit 'open' status rejected: shelter is at full capacity",
            )
            self.mock_db.commit.assert_not_called()

    def test_patch_shelter_not_found_returns_404_and_no_commit(self):
        shelter_id = uuid4()
        payload = {"name": "Nonexistent Shelter"}
        with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.update_shelter.return_value = None

            response = self.client.patch(f"/api/shelters/{shelter_id}", json=payload)

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["detail"], "Shelter not found")
            self.mock_db.commit.assert_not_called()

    def test_patch_shelter_empty_payload_rejected_400(self):
        shelter_id = uuid4()
        response = self.client.patch(f"/api/shelters/{shelter_id}", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "No fields to update")
        self.mock_db.commit.assert_not_called()

    def test_patch_shelter_invalid_status_pattern_returns_422(self):
        shelter_id = uuid4()
        response = self.client.patch(
            f"/api/shelters/{shelter_id}",
            json={"status": "invalid_status"},
        )
        self.assertEqual(response.status_code, 422)
        self.mock_db.commit.assert_not_called()

    def test_patch_shelter_invalid_uuid_param_returns_422(self):
        response = self.client.patch(
            "/api/shelters/not-a-valid-uuid",
            json={"name": "Valid Name"},
        )
        self.assertEqual(response.status_code, 422)
        self.mock_db.commit.assert_not_called()

    # ── GET /api/shelters and GET /api/shelters/{shelter_id} ──

    def test_get_shelter_by_id_success(self):
        shelter_id = uuid4()
        fake_shelter = DummyShelter(
            id=shelter_id,
            name="Shelter Alpha",
            capacity=100,
            current_occupancy=20,
            status="open",
        )
        with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.get_shelter.return_value = fake_shelter

            response = self.client.get(f"/api/shelters/{shelter_id}")

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["id"], str(shelter_id))
            self.assertEqual(data["name"], "Shelter Alpha")
            mock_svc.get_shelter.assert_called_once_with(shelter_id)

    def test_get_shelter_by_id_not_found_returns_404(self):
        shelter_id = uuid4()
        with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.get_shelter.return_value = None

            response = self.client.get(f"/api/shelters/{shelter_id}")

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["detail"], "Shelter not found")

    def test_list_shelters_success(self):
        shelter_id = uuid4()
        fake_shelter = DummyShelter(
            id=shelter_id,
            name="Shelter Alpha",
            capacity=100,
            current_occupancy=20,
            status="open",
        )
        with patch("backend.app.api.endpoints.coordination.ShelterService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.get_all_shelters.return_value = [fake_shelter]

            response = self.client.get("/api/shelters")

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], str(shelter_id))
            mock_svc.get_all_shelters.assert_called_once_with(skip=0, limit=100)


if __name__ == "__main__":
    unittest.main()
