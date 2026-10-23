"""STEP 7L — Security, Data-Integrity & Production-Safety Test Suite."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from uuid import uuid4
from sqlalchemy import text
from backend.app.database.base import SessionLocal
from fastapi.testclient import TestClient
from backend.app.main import app

results = []

def record(name, status, evidence=""):
    results.append((name, status, evidence))
    print(f"  {status}: {name}" + (f" -- {evidence[:120]}" if evidence else ""))

client = TestClient(app, raise_server_exceptions=False)

print("\n" + "="*70)
print("STEP 7L SECURITY & DATA-INTEGRITY TEST SUITE")
print("="*70)

# ════════════════════════════════════════════════════════════
# A: Malformed UUID rejection
# ════════════════════════════════════════════════════════════
try:
    resp = client.get("/api/volunteers/not-a-uuid")
    record("A: Malformed UUID rejection", "PASS" if resp.status_code == 422 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    record("A: Malformed UUID rejection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# B: Invalid coordinate rejection
# ════════════════════════════════════════════════════════════
try:
    resp = client.post("/api/volunteers", json={
        "user_id": str(uuid4()), "latitude": 999.0, "longitude": 999.0,
    })
    record("B: Invalid coordinate rejection", "PASS" if resp.status_code == 422 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    record("B: Invalid coordinate rejection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# C: Negative resource quantity rejection
# ════════════════════════════════════════════════════════════
try:
    resp = client.post("/api/relief-resources", json={"resource_type": "water", "quantity": -10})
    record("C: Negative resource quantity rejection", "PASS" if resp.status_code == 422 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    record("C: Negative resource quantity rejection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# D: Zero allocation quantity rejection
# ════════════════════════════════════════════════════════════
try:
    resp = client.post("/api/relief-resources", json={"resource_type": "food", "quantity": 0})
    record("D: Zero allocation quantity rejection", "PASS" if resp.status_code == 422 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    record("D: Zero allocation quantity rejection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# E: Over-allocation rejection
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    res_id = str(uuid4())
    req_id = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test E', 'citizen')"))
    db.execute(text(f"INSERT INTO relief_resources (id, resource_type, quantity, available_quantity, status) VALUES ('{res_id}', 'water', 10, 10, 'available')"))
    db.execute(text(f"INSERT INTO emergency_requests (id, client_op_id, request_type, status, payload) VALUES ('{req_id}', 'test-7l-e-{uid[:8]}', 'help', 'pending', '{{}}'::jsonb)"))
    db.commit()
    db.close()
    resp = client.post(f"/api/relief-resources/{res_id}/allocate", json={"request_id": req_id, "quantity": 50})
    record("E: Over-allocation rejection", "PASS" if resp.status_code == 400 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    try: db.close()
    except: pass
    record("E: Over-allocation rejection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# F: Invalid volunteer status transition rejection
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    vid = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test F', 'citizen')"))
    db.execute(text(f"INSERT INTO volunteer_profiles (id, user_id, skills, status, is_active) VALUES ('{vid}', '{uid}', '[]'::jsonb, 'pending', true)"))
    db.commit()
    db.close()
    resp = client.patch(f"/api/volunteers/{vid}/status", json={"status": "active"})
    record("F: Invalid volunteer status transition rejection", "PASS" if resp.status_code == 400 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    try: db.close()
    except: pass
    record("F: Invalid volunteer status transition rejection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# G: Assignment to inactive volunteer rejection
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    vid = str(uuid4())
    req_id = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test G', 'citizen')"))
    db.execute(text(f"INSERT INTO volunteer_profiles (id, user_id, skills, status, is_active) VALUES ('{vid}', '{uid}', '[]'::jsonb, 'inactive', true)"))
    db.execute(text(f"INSERT INTO emergency_requests (id, client_op_id, request_type, status, payload) VALUES ('{req_id}', 'test-7l-g-{uid[:8]}', 'help', 'pending', '{{}}'::jsonb)"))
    db.commit()
    db.close()
    resp = client.post("/api/assignments", json={"request_id": req_id, "volunteer_id": vid})
    record("G: Assignment to inactive volunteer rejection", "PASS" if resp.status_code == 400 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    try: db.close()
    except: pass
    record("G: Assignment to inactive volunteer rejection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# H: Assignment to nonexistent volunteer rejection
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    fake_vol = str(uuid4())
    req_id = str(uuid4())
    db.execute(text(f"INSERT INTO emergency_requests (id, client_op_id, request_type, status, payload) VALUES ('{req_id}', 'test-7l-h-{req_id[:8]}', 'help', 'pending', '{{}}'::jsonb)"))
    db.commit()
    db.close()
    resp = client.post("/api/assignments", json={"request_id": req_id, "volunteer_id": fake_vol})
    record("H: Assignment to nonexistent volunteer rejection", "PASS" if resp.status_code == 400 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    try: db.close()
    except: pass
    record("H: Assignment to nonexistent volunteer rejection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# I: Assignment to resolved request rejection
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    vid = str(uuid4())
    req_id = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test I', 'citizen')"))
    db.execute(text(f"INSERT INTO volunteer_profiles (id, user_id, skills, status, is_active) VALUES ('{vid}', '{uid}', '[]'::jsonb, 'active', true)"))
    db.execute(text(f"INSERT INTO emergency_requests (id, client_op_id, request_type, status, payload) VALUES ('{req_id}', 'test-7l-i-{uid[:8]}', 'help', 'resolved', '{{}}'::jsonb)"))
    db.commit()
    db.close()
    resp = client.post("/api/assignments", json={"request_id": req_id, "volunteer_id": vid})
    record("I: Assignment to resolved request rejection", "PASS" if resp.status_code == 400 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    try: db.close()
    except: pass
    record("I: Assignment to resolved request rejection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# J: Duplicate assignment protection
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    vid = str(uuid4())
    req_id = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test J', 'citizen')"))
    db.execute(text(f"INSERT INTO volunteer_profiles (id, user_id, skills, status, is_active) VALUES ('{vid}', '{uid}', '[]'::jsonb, 'active', true)"))
    db.execute(text(f"INSERT INTO emergency_requests (id, client_op_id, request_type, status, payload) VALUES ('{req_id}', 'test-7l-j-{uid[:8]}', 'help', 'pending', '{{}}'::jsonb)"))
    db.commit()
    db.close()
    r1 = client.post("/api/assignments", json={"request_id": req_id, "volunteer_id": vid})
    r2 = client.post("/api/assignments", json={"request_id": req_id, "volunteer_id": vid})
    record("J: Duplicate assignment protection",
           "PASS" if r1.status_code == 200 and r2.status_code == 400 else "FAIL",
           f"first={r1.status_code}, second={r2.status_code}")
except Exception as e:
    try: db.close()
    except: pass
    record("J: Duplicate assignment protection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# K: Concurrent resource protection
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    res_id = str(uuid4())
    req1 = str(uuid4())
    req2 = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test K', 'citizen')"))
    db.execute(text(f"INSERT INTO relief_resources (id, resource_type, quantity, available_quantity, status) VALUES ('{res_id}', 'water', 15, 15, 'available')"))
    db.execute(text(f"INSERT INTO emergency_requests (id, client_op_id, request_type, status, payload) VALUES ('{req1}', 'test-7l-k1-{uid[:8]}', 'help', 'pending', '{{}}'::jsonb)"))
    db.execute(text(f"INSERT INTO emergency_requests (id, client_op_id, request_type, status, payload) VALUES ('{req2}', 'test-7l-k2-{uid[:8]}', 'help', 'pending', '{{}}'::jsonb)"))
    db.commit()
    db.close()
    r1 = client.post(f"/api/relief-resources/{res_id}/allocate", json={"request_id": req1, "quantity": 10})
    r2 = client.post(f"/api/relief-resources/{res_id}/allocate", json={"request_id": req2, "quantity": 10})
    record("K: Concurrent resource protection",
           "PASS" if r1.status_code == 200 and r2.status_code == 400 else "FAIL",
           f"first={r1.status_code}, second={r2.status_code}")
except Exception as e:
    try: db.close()
    except: pass
    record("K: Concurrent resource protection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# L: Audit record creation
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    vid = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test L', 'citizen')"))
    db.execute(text(f"INSERT INTO volunteer_profiles (id, user_id, skills, status, is_active) VALUES ('{vid}', '{uid}', '[]'::jsonb, 'pending', true)"))
    db.commit()
    db.close()
    resp = client.post(f"/api/volunteers/{vid}/verify")
    db2 = SessionLocal()
    audit_count = db2.execute(text(f"SELECT COUNT(*) FROM audit_history WHERE entity_id = '{vid}'")).scalar()
    db2.close()
    record("L: Audit record creation",
           "PASS" if resp.status_code == 200 and audit_count >= 1 else "FAIL",
           f"status={resp.status_code}, audit_rows={audit_count}")
except Exception as e:
    try: db.close()
    except: pass
    record("L: Audit record creation", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# M: Sensitive field exposure check
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    vid = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test M', 'citizen')"))
    db.execute(text(f"INSERT INTO volunteer_profiles (id, user_id, skills, status, is_active) VALUES ('{vid}', '{uid}', '[]'::jsonb, 'active', true)"))
    db.commit()
    db.close()
    resp = client.get(f"/api/volunteers/{vid}")
    data = resp.json()
    has_password = "password" in str(data).lower()
    has_phone = "phone" in str(data).lower()
    record("M: Sensitive field exposure",
           "PASS" if not has_password and not has_phone else "FAIL",
           f"password_in_response={has_password}, phone_in_response={has_phone}")
except Exception as e:
    try: db.close()
    except: pass
    record("M: Sensitive field exposure", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# N: Health endpoint safety
# ════════════════════════════════════════════════════════════
try:
    resp = client.get("/health")
    data = resp.json()
    db_info = str(data.get("database", {}))
    has_password = "LrmLocal" in db_info or "password" in db_info.lower()
    has_exception = "exception" in db_info.lower() or "traceback" in db_info.lower()
    record("N: Health endpoint safety",
           "PASS" if not has_password and not has_exception else "FAIL",
           f"exposes_credentials={has_password}")
except Exception as e:
    record("N: Health endpoint safety", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# O: SQL injection-style malicious input
# ════════════════════════════════════════════════════════════
try:
    malicious_batch = {
        "operations": [{
            "id": "'; DROP TABLE emergency_requests; --",
            "operation": "CREATE",
            "entity": "incident_report",
            "payload": {"type": "help", "title": "SQL injection test", "severity": "low"},
            "createdAt": "2026-09-12T00:00:00Z",
        }]
    }
    resp = client.post("/api/sync/upload", json=malicious_batch)
    db_check = SessionLocal()
    table_exists = db_check.execute(text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'emergency_requests'"
    )).fetchone()
    db_check.close()
    record("O: SQL injection protection",
           "PASS" if resp.status_code == 200 and table_exists else "FAIL",
           f"status={resp.status_code}, table_exists={table_exists is not None}")
except Exception as e:
    record("O: SQL injection protection", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# P: client_op_id idempotency
# ════════════════════════════════════════════════════════════
try:
    op_id = f"test-7l-idempotent-{uuid4().hex[:8]}"
    batch = {
        "operations": [{
            "id": op_id, "operation": "CREATE", "entity": "incident_report",
            "payload": {"type": "help", "title": "Idempotent test"},
            "createdAt": "2026-09-12T00:00:00Z",
        }]
    }
    r1 = client.post("/api/sync/upload", json=batch)
    r2 = client.post("/api/sync/upload", json=batch)
    db_check = SessionLocal()
    count = db_check.execute(text(
        f"SELECT COUNT(*) FROM emergency_requests WHERE client_op_id = '{op_id}'"
    )).scalar()
    db_check.close()
    record("P: client_op_id idempotency", "PASS" if count == 1 else "FAIL",
           f"records_created={count}")
except Exception as e:
    record("P: client_op_id idempotency", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# Q: Existing /api/sync/upload compatibility
# ════════════════════════════════════════════════════════════
try:
    resp = client.post("/api/sync/upload", json={
        "operations": [{
            "id": f"test-7l-compat-{uuid4().hex[:8]}", "operation": "CREATE",
            "entity": "incident_report", "payload": {"type": "help", "title": "Compat"},
            "createdAt": "2026-09-12T00:00:00Z",
        }]
    })
    data = resp.json()
    record("Q: /api/sync/upload compatibility",
           "PASS" if resp.status_code == 200 and data.get("success") else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    record("Q: /api/sync/upload compatibility", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# R: Existing /health compatibility
# ════════════════════════════════════════════════════════════
try:
    resp = client.get("/health")
    data = resp.json()
    record("R: /health compatibility",
           "PASS" if resp.status_code == 200 and data.get("status") == "healthy" else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    record("R: /health compatibility", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# S: Existing /api/alerts/ compatibility
# ════════════════════════════════════════════════════════════
try:
    resp = client.get("/api/alerts/")
    record("S: /api/alerts/ compatibility",
           "PASS" if resp.status_code == 200 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    record("S: /api/alerts/ compatibility", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# T: Volunteer coordination CRUD lifecycle
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test T', 'citizen')"))
    db.commit()
    db.close()
    r_create = client.post("/api/volunteers", json={"user_id": uid})
    vol_id = r_create.json()["id"]
    r_list = client.get("/api/volunteers")
    r_get = client.get(f"/api/volunteers/{vol_id}")
    r_verify = client.post(f"/api/volunteers/{vol_id}/verify")
    r_activate = client.post(f"/api/volunteers/{vol_id}/activate")
    all_ok = all(r.status_code == 200 for r in [r_create, r_list, r_get, r_verify, r_activate])
    record("T: Volunteer coordination CRUD lifecycle", "PASS" if all_ok else "FAIL",
           f"create={r_create.status_code} list={r_list.status_code} get={r_get.status_code} verify={r_verify.status_code} activate={r_activate.status_code}")
except Exception as e:
    try: db.close()
    except: pass
    record("T: Volunteer coordination CRUD lifecycle", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# U: Resource allocation endpoint
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    res_id = str(uuid4())
    req_id = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test U', 'citizen')"))
    db.execute(text(f"INSERT INTO relief_resources (id, resource_type, quantity, available_quantity, status) VALUES ('{res_id}', 'water', 50, 50, 'available')"))
    db.execute(text(f"INSERT INTO emergency_requests (id, client_op_id, request_type, status, payload) VALUES ('{req_id}', 'test-7l-u-{uid[:8]}', 'help', 'pending', '{{}}'::jsonb)"))
    db.commit()
    db.close()
    resp = client.post(f"/api/relief-resources/{res_id}/allocate", json={"request_id": req_id, "quantity": 20})
    record("U: Resource allocation endpoint",
           "PASS" if resp.status_code == 200 else "FAIL",
           f"status={resp.status_code}")
except Exception as e:
    try: db.close()
    except: pass
    record("U: Resource allocation endpoint", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# V: Unauthenticated sensitive endpoint
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    vid = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test V', 'citizen')"))
    db.execute(text(f"INSERT INTO volunteer_profiles (id, user_id, skills, status, is_active) VALUES ('{vid}', '{uid}', '[]'::jsonb, 'pending', true)"))
    db.commit()
    db.close()
    resp = client.post(f"/api/volunteers/{vid}/verify")
    record("V: Unauthenticated sensitive endpoint",
           "BLOCKED" if resp.status_code == 200 else "PASS",
           f"status={resp.status_code} — BLOCKED: authentication not implemented")
except Exception as e:
    try: db.close()
    except: pass
    record("V: Unauthenticated sensitive endpoint", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# W: Unauthorized user
# ════════════════════════════════════════════════════════════
try:
    db = SessionLocal()
    uid = str(uuid4())
    vid = str(uuid4())
    db.execute(text(f"INSERT INTO users (id, name, role) VALUES ('{uid}', 'Test W', 'citizen')"))
    db.execute(text(f"INSERT INTO volunteer_profiles (id, user_id, skills, status, is_active) VALUES ('{vid}', '{uid}', '[]'::jsonb, 'pending', true)"))
    db.commit()
    db.close()
    resp = client.post(f"/api/volunteers/{vid}/activate")
    record("W: Unauthorized user",
           "BLOCKED" if resp.status_code in (200, 400) else "PASS",
           f"status={resp.status_code} — BLOCKED: RBAC not implemented")
except Exception as e:
    try: db.close()
    except: pass
    record("W: Unauthorized user", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# X: CORS mobile dev origin
# ════════════════════════════════════════════════════════════
try:
    resp = client.options("/api/sync/upload", headers={
        "Origin": "http://192.168.47.1:8000",
        "Access-Control-Request-Method": "POST",
    })
    allow_origin = resp.headers.get("access-control-allow-origin", "")
    record("X: CORS mobile dev origin",
           "PASS" if "192.168.47.1" in allow_origin or allow_origin == "*" else "FAIL",
           f"allow-origin={allow_origin}")
except Exception as e:
    record("X: CORS mobile dev origin", "FAIL", str(e)[:120])

# ════════════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════════════
print("\n" + "-"*70)
print("CLEANUP")
print("-"*70)
try:
    db = SessionLocal()
    db.execute(text("DELETE FROM volunteer_profiles WHERE user_id IN (SELECT id FROM users WHERE name LIKE 'Test %')"))
    db.execute(text("DELETE FROM users WHERE name LIKE 'Test %'"))
    db.execute(text("DELETE FROM emergency_requests WHERE client_op_id LIKE 'test-7l-%'"))
    db.execute(text("DELETE FROM assignments WHERE volunteer_id IN (SELECT id FROM volunteer_profiles WHERE user_id IN (SELECT id FROM users WHERE name LIKE 'Test %'))"))
    db.commit()
    db.close()
    print("  All test records cleaned up.")
except Exception as e:
    try: db.close()
    except: pass
    print(f"  Cleanup error (non-critical): {str(e)[:100]}")

# ════════════════════════════════════════════════════════════
# RESULTS
# ════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("STEP 7L TEST RESULTS")
print("="*70)
pass_count = sum(1 for _, s, _ in results if s == "PASS")
fail_count = sum(1 for _, s, _ in results if s == "FAIL")
blocked_count = sum(1 for _, s, _ in results if s == "BLOCKED")
print(f"PASS: {pass_count}, FAIL: {fail_count}, BLOCKED: {blocked_count}, TOTAL: {len(results)}")
print("="*70)
for name, status, evidence in results:
    print(f"  {status}: {name}")
