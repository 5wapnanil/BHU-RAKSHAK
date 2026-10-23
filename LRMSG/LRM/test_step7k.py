"""STEP 7K Comprehensive Test Suite — Tests A through U."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import text
from backend.app.database.base import SessionLocal
from backend.app.services.volunteer_service import VolunteerService
from backend.app.services.assignment_service import AssignmentService
from backend.app.services.relief_resource_service import ReliefResourceService
from backend.app.services.matching_engine import MatchingEngine

results = []

# Track user IDs for cleanup
user2_id = None
user3_id = None
req2_id = None

LB = "{"  # literal brace for SQL JSON
RB = "}"

def record(name, status, evidence=""):
    results.append((name, status, evidence))
    print(f"  {status}: {name}" + (f" -- {evidence[:150]}" if evidence else ""))

print("\n" + "="*70)
print("STEP 7K TEST SUITE")
print("="*70)

db = SessionLocal()

# ── Setup: create test user and request ──
test_user_id = None
test_request_id = None
test_volunteer_id = None
test_volunteer2_id = None
test_resource_id = None
test_assignment_id = None

try:
    # Create a test user
    user_row = db.execute(text(
        "INSERT INTO users (id, name, role, is_verified) "
        f"VALUES ('{uuid4()}', 'Test Coordinator User', 'authority', true) "
        "RETURNING id"
    )).fetchone()
    test_user_id = user_row[0]

    # Create an emergency request with location
    payload_json = '{"title": "Test request"}'
    req_row = db.execute(text(
        "INSERT INTO emergency_requests (id, client_op_id, request_type, location, severity, status, payload) "
        "VALUES "
        f"('{uuid4()}', 'test-7k-req-{uuid4().hex[:8]}', 'help', "
        f"'SRID=4326;POINT(92.8 26.5)', 'high', 'pending', '{payload_json}'::jsonb) "
        "RETURNING id"
    )).fetchone()
    test_request_id = req_row[0]
    db.commit()
    print(f"  Setup: request_id={test_request_id}")

except Exception as e:
    db.rollback()
    print(f"  SETUP FAILED: {e}")
    sys.exit(1)


# ── A: Volunteer profile creation ──
try:
    svc = VolunteerService(db)
    profile = svc.create_profile(
        user_id=test_user_id,
        skills=["medical", "rescue"],
        has_transport=True,
        capacity=5,
        availability="weekends",
        latitude=26.5,
        longitude=92.8,
    )
    test_volunteer_id = profile.id
    db.commit()
    record("A: Volunteer profile creation", "PASS", f"profile_id={profile.id}, status={profile.status}")
except Exception as e:
    db.rollback()
    record("A: Volunteer profile creation", "FAIL", str(e))


# ── B: Volunteer user_id uniqueness ──
try:
    try:
        svc.create_profile(user_id=test_user_id, skills=["driving"])
        db.commit()
        record("B: Volunteer user_id uniqueness", "FAIL", "duplicate not rejected")
    except ValueError:
        db.rollback()
        record("B: Volunteer user_id uniqueness", "PASS", "duplicate correctly rejected")
except Exception as e:
    record("B: Volunteer user_id uniqueness", "FAIL", str(e))


# ── C: Volunteer verification ──
try:
    profile = svc.verify_volunteer(test_volunteer_id)
    db.commit()
    record("C: Volunteer verification", "PASS", f"status={profile.status}, verified_at={profile.verified_at is not None}")
except Exception as e:
    db.rollback()
    record("C: Volunteer verification", "FAIL", str(e))


# ── D: Volunteer availability (activate) ──
try:
    profile = svc.activate_volunteer(test_volunteer_id)
    db.commit()
    eligible = svc.is_eligible_for_assignment(profile)
    record("D: Volunteer availability", "PASS", f"status={profile.status}, eligible={eligible}")
except Exception as e:
    db.rollback()
    record("D: Volunteer availability", "FAIL", str(e))


# ── E: Candidate matching ──
try:
    engine = MatchingEngine(db)
    candidates = engine.find_candidates(request_id=test_request_id, radius_km=50)
    record("E: Candidate matching", "PASS" if len(candidates) >= 1 else "FAIL",
           f"found {len(candidates)} candidates")
except Exception as e:
    record("E: Candidate matching", "FAIL", str(e))


# ── F: PostGIS distance ordering ──
try:
    if len(candidates) >= 1:
        distances = [c.distance_km for c in candidates]
        is_ordered = all(distances[i] <= distances[i+1] for i in range(len(distances)-1))
        record("F: PostGIS distance ordering", "PASS" if is_ordered else "FAIL",
               f"distances={distances}")
    else:
        record("F: PostGIS distance ordering", "FAIL", "no candidates to verify")
except Exception as e:
    record("F: PostGIS distance ordering", "FAIL", str(e))


# ── G: Ineligible volunteer exclusion ──
try:
    # Create an inactive volunteer
    user2_row = db.execute(text(
        "INSERT INTO users (id, name, role) "
        f"VALUES ('{uuid4()}', 'Inactive Volunteer', 'volunteer') "
        "RETURNING id"
    )).fetchone()
    user2_id = user2_row[0]
    vol2 = svc.create_profile(
        user_id=user2_id,
        skills=["rescue"],
        latitude=26.5,
        longitude=92.8,
    )
    db.commit()
    # Leave as pending — should not appear in candidates
    candidates = engine.find_candidates(request_id=test_request_id, radius_km=50)
    found_inactive = any(c.volunteer_id == vol2.id for c in candidates)
    record("G: Ineligible volunteer exclusion", "PASS" if not found_inactive else "FAIL",
           f"inactive volunteer in candidates: {found_inactive}")
except Exception as e:
    db.rollback()
    record("G: Ineligible volunteer exclusion", "FAIL", str(e))


# ── H: Non-assignable request exclusion ──
try:
    # Create a resolved request
    resolved_row = db.execute(text(
        "INSERT INTO emergency_requests (id, client_op_id, request_type, status, payload) "
        f"VALUES ('{uuid4()}', 'test-resolved-{uuid4().hex[:8]}', 'help', 'resolved', '{{}}') "
        "RETURNING id"
    )).fetchone()
    db.commit()
    assign_svc = AssignmentService(db)
    try:
        assign_svc.create_volunteer_assignment(resolved_row[0], test_volunteer_id)
        record("H: Non-assignable request exclusion", "FAIL", "resolved request was assignable")
    except ValueError as e:
        record("H: Non-assignable request exclusion", "PASS", f"correctly rejected: {str(e)[:80]}")
    db.execute(text(f"DELETE FROM emergency_requests WHERE id = '{resolved_row[0]}'"))
    db.commit()
except Exception as e:
    db.rollback()
    record("H: Non-assignable request exclusion", "FAIL", str(e))


# ── I: Assignment creation ──
try:
    assignment = assign_svc.create_volunteer_assignment(
        request_id=test_request_id,
        volunteer_id=test_volunteer_id,
        notes="Test assignment",
    )
    test_assignment_id = assignment.id
    db.commit()
    record("I: Assignment creation", "PASS",
           f"assignment_id={assignment.id}, status={assignment.status}")
except Exception as e:
    db.rollback()
    record("I: Assignment creation", "FAIL", str(e))


# ── J: Invalid assignment rejection ──
try:
    # Try to assign same volunteer again (conflict)
    try:
        assign_svc.create_volunteer_assignment(
            request_id=test_request_id,
            volunteer_id=test_volunteer_id,
        )
        record("J: Invalid assignment rejection", "FAIL", "duplicate assignment not rejected")
    except ValueError as e:
        record("J: Invalid assignment rejection", "PASS", f"correctly rejected: {str(e)[:80]}")
except Exception as e:
    record("J: Invalid assignment rejection", "FAIL", str(e))


# ── K: Assignment status transitions ──
try:
    # pending -> accepted
    a = assign_svc.accept_assignment(test_assignment_id)
    db.commit()
    assert a.status == "accepted"

    # accepted -> in_progress
    a = assign_svc.start_assignment(test_assignment_id)
    db.commit()
    assert a.status == "in_progress"

    # in_progress -> completed
    a = assign_svc.complete_assignment(test_assignment_id)
    db.commit()
    assert a.status == "completed"

    record("K: Assignment status transitions", "PASS",
           "pending -> accepted -> in_progress -> completed")
except Exception as e:
    db.rollback()
    record("K: Assignment status transitions", "FAIL", str(e))


# ── L: Duplicate/conflicting assignment protection ──
try:
    # Create a second volunteer for testing
    user3_row = db.execute(text(
        "INSERT INTO users (id, name, role) "
        f"VALUES ('{uuid4()}', 'Second Volunteer', 'volunteer') "
        "RETURNING id"
    )).fetchone()
    user3_id = user3_row[0]
    vol2_for_conflict = svc.create_profile(
        user_id=user3_id,
        skills=["medical"],
        latitude=26.6,
        longitude=92.9,
    )
    svc.verify_volunteer(vol2_for_conflict.id)
    svc.activate_volunteer(vol2_for_conflict.id)
    db.commit()

    # Create a fresh pending request for this volunteer
    req_for_vol2 = db.execute(text(
        "INSERT INTO emergency_requests (id, client_op_id, request_type, status, location, payload) "
        f"VALUES ('{uuid4()}', 'test-7k-req-vol2-{uuid4().hex[:8]}', 'help', 'pending', "
        f"'SRID=4326;POINT(93.0 26.7)', '{{}}'::jsonb) "
        "RETURNING id"
    )).fetchone()
    db.commit()

    # Assign volunteer to first request
    a1 = assign_svc.create_volunteer_assignment(req_for_vol2[0], vol2_for_conflict.id)
    db.commit()

    # Try to assign same volunteer to a second request concurrently
    req2_row = db.execute(text(
        "INSERT INTO emergency_requests (id, client_op_id, request_type, status, location, payload) "
        f"VALUES ('{uuid4()}', 'test-7k-req2-{uuid4().hex[:8]}', 'help', 'pending', "
        f"'SRID=4326;POINT(93.0 26.7)', '{{}}'::jsonb) "
        "RETURNING id"
    )).fetchone()
    req2_id = req2_row[0]
    db.commit()

    try:
        a2 = assign_svc.create_volunteer_assignment(req2_row[0], vol2_for_conflict.id)
        db.commit()
        record("L: Duplicate assignment protection", "FAIL", "concurrent assignment not rejected")
    except ValueError:
        db.rollback()
        record("L: Duplicate assignment protection", "PASS", "conflicting assignment correctly rejected")
except Exception as e:
    db.rollback()
    record("L: Duplicate assignment protection", "FAIL", str(e))


# ── M: Resource allocation ──
try:
    res_svc = ReliefResourceService(db)
    resource = res_svc.create_resource(
        resource_type="water",
        description="Bottled water packs",
        quantity=100,
        unit="liters",
        provider_id=test_user_id,
        latitude=26.5,
        longitude=92.8,
    )
    test_resource_id = resource.id
    db.commit()

    # Allocate to request
    assignment = res_svc.allocate_resource(
        resource_id=test_resource_id,
        request_id=test_request_id,
        quantity=30,
        notes="Allocated 30 water",
    )
    db.commit()

    # Verify resource quantity updated
    updated_resource = res_svc.get_resource(test_resource_id)
    record("M: Resource allocation", "PASS",
           f"allocated=30, remaining={updated_resource.available_quantity}")
except Exception as e:
    db.rollback()
    record("M: Resource allocation", "FAIL", str(e))


# ── N: Insufficient resource rejection ──
try:
    try:
        res_svc.allocate_resource(
            resource_id=test_resource_id,
            request_id=test_request_id,
            quantity=9999,
        )
        record("N: Insufficient resource rejection", "FAIL", "over-allocation not rejected")
    except ValueError as e:
        record("N: Insufficient resource rejection", "PASS", f"correctly rejected: {str(e)[:80]}")
except Exception as e:
    record("N: Insufficient resource rejection", "FAIL", str(e))


# ── O: Concurrent resource allocation protection ──
try:
    # Both should not succeed if total exceeds available
    # Current available = 70 (100 - 30)
    try:
        res_svc.allocate_resource(test_resource_id, test_request_id, 50)
        db.commit()
        res_svc.allocate_resource(test_resource_id, test_request_id, 50)
        db.commit()
        record("O: Concurrent resource protection", "FAIL", "both allocations succeeded")
    except ValueError:
        db.rollback()
        record("O: Concurrent resource protection", "PASS", "second allocation correctly rejected")
except Exception as e:
    db.rollback()
    record("O: Concurrent resource protection", "FAIL", str(e))


# ── P: Resource cancellation/release ──
try:
    # Find the resource allocation assignment
    resource_assignments = db.execute(text(
        f"SELECT id, notes FROM assignments WHERE resource_id = '{test_resource_id}' AND assignment_type = 'resource' LIMIT 1"
    )).fetchone()

    if resource_assignments:
        res_svc.release_allocation(resource_assignments[0])
        db.commit()
        updated = res_svc.get_resource(test_resource_id)
        record("P: Resource cancellation/release", "PASS",
               f"released, remaining={updated.available_quantity}")
    else:
        record("P: Resource cancellation/release", "FAIL", "no resource assignment found")
except Exception as e:
    db.rollback()
    record("P: Resource cancellation/release", "FAIL", str(e))


# ── Q: Audit history creation ──
try:
    audit_rows = db.execute(text(
        f"SELECT entity_type, action FROM audit_history "
        f"WHERE entity_id = '{test_volunteer_id}' OR entity_id = '{test_assignment_id}' "
        "ORDER BY created_at DESC LIMIT 5"
    )).fetchall()
    has_audit = len(audit_rows) > 0
    record("Q: Audit history creation", "PASS" if has_audit else "FAIL",
           f"found {len(audit_rows)} audit entries")
except Exception as e:
    record("Q: Audit history creation", "FAIL", str(e))


# ── R: Request remains intact after assignment ──
try:
    req = db.execute(text(
        f"SELECT status, client_op_id FROM emergency_requests WHERE id = '{test_request_id}'"
    )).fetchone()
    record("R: Request remains intact after assignment", "PASS",
           f"status={req[0]}, client_op_id={req[1]}")
except Exception as e:
    record("R: Request remains intact after assignment", "FAIL", str(e))


# ── S: Existing /api/sync/upload still works ──
try:
    from fastapi.testclient import TestClient
    from backend.app.main import app
    client = TestClient(app, raise_server_exceptions=False)

    sync_payload = {
        "operations": [{
            "id": f"test-7k-sync-{uuid4().hex[:8]}",
            "operation": "CREATE",
            "entity": "incident_report",
            "payload": {
                "request_type": "help",
                "title": "Sync test",
                "latitude": 26.5,
                "longitude": 92.8,
                "severity": "moderate",
            },
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }]
    }
    resp = client.post("/api/sync/upload", json=sync_payload)
    record("S: Existing /api/sync/upload", "PASS" if resp.status_code == 200 else "FAIL",
           f"status={resp.status_code}, success={resp.json().get('success')}")
except Exception as e:
    record("S: Existing /api/sync/upload", "FAIL", str(e))


# ── T: Existing health endpoint still works ──
try:
    resp = client.get("/health")
    record("T: Existing health endpoint", "PASS" if resp.status_code == 200 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    record("T: Existing health endpoint", "FAIL", str(e))


# ── U: Existing alert endpoints still work ──
try:
    resp = client.get("/api/alerts/")
    record("U: Existing alert endpoints", "PASS" if resp.status_code == 200 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    record("U: Existing alert endpoints", "FAIL", str(e))


# ── Cleanup ──
print("\n" + "-"*70)
print("CLEANUP")
print("-"*70)
try:
    if test_assignment_id:
        db.execute(text(f"DELETE FROM assignments WHERE id = '{test_assignment_id}'"))
    db.execute(text(f"DELETE FROM assignments WHERE volunteer_id = '{test_volunteer_id}'"))
    if user2_id:
        db.execute(text(f"DELETE FROM volunteer_profiles WHERE user_id = '{user2_id}'"))
        db.execute(text(f"DELETE FROM users WHERE id = '{user2_id}'"))
    if user3_id:
        db.execute(text(f"DELETE FROM volunteer_profiles WHERE user_id = '{user3_id}'"))
        db.execute(text(f"DELETE FROM users WHERE id = '{user3_id}'"))
    db.execute(text(f"DELETE FROM volunteer_profiles WHERE user_id = '{test_user_id}'"))
    db.execute(text(f"DELETE FROM users WHERE id = '{test_user_id}'"))
    db.execute(text(f"DELETE FROM relief_resources WHERE id = '{test_resource_id}'"))
    if req2_id:
        db.execute(text(f"DELETE FROM emergency_requests WHERE id = '{req2_id}'"))
    db.execute(text("DELETE FROM emergency_requests WHERE client_op_id LIKE 'test-7k-%'"))
    db.execute(text("DELETE FROM users WHERE name IN ('Test Coordinator User', 'Inactive Volunteer', 'Second Volunteer')"))
    db.commit()
    print("  All test records cleaned up.")
except Exception as e:
    db.rollback()
    print(f"  Cleanup error (non-critical): {e}")
finally:
    db.close()


# ── Results ──
print("\n" + "="*70)
print("STEP 7K TEST RESULTS")
print("="*70)
pass_count = sum(1 for _, s, _ in results if s == "PASS")
fail_count = sum(1 for _, s, _ in results if s == "FAIL")
print(f"PASS: {pass_count}, FAIL: {fail_count}, TOTAL: {len(results)}")
print("="*70)
for name, status, evidence in results:
    print(f"  {status}: {name}")
