"""Apply STEP 7L indexes directly."""
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://lrm:LrmLocal_2026_Pg_7H!@localhost:5432/lrm_db")
with engine.connect() as conn:
    stmts = [
        "CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments (status)",
        "CREATE INDEX IF NOT EXISTS idx_volunteer_profiles_status ON volunteer_profiles (status, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_relief_resources_status ON relief_resources (status)",
        "CREATE INDEX IF NOT EXISTS idx_emergency_requests_status ON emergency_requests (status)",
        "CREATE INDEX IF NOT EXISTS idx_audit_history_entity ON audit_history (entity_type, entity_id)",
    ]
    for s in stmts:
        conn.execute(text(s))
        print(f"OK: {s}")
    conn.commit()
print("All indexes applied.")
