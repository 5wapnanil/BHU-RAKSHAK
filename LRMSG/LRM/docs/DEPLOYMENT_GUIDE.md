# BhuRakshak / PahaarPulse — Production Deployment & Operations Guide

This guide details the verified deployment architecture, security hardening, container packaging, and operational procedures for the BhuRakshak Landslide Risk Management platform.

---

## 1. Prerequisites & Tooling

* **Container Runtime**: Docker Engine 24.0+ and Docker Compose v2.20+.
* **Database**: PostgreSQL 16 with PostGIS 3.4 (provided via `postgis/postgis:16-3.4` container).
* **Backend Runtime**: Python 3.12.
* **Web Runtime**: Node.js 20+ (LTS) and npm.
* **Mobile Tooling**: Expo CLI (`sdkVersion: 57.0.0`) and React Native runtime.

---

## 2. Repository Architecture & Layout

```text
C:\Users\Swapnanil\Desktop\app2
├── LRMSG/LRM/
│   ├── backend/                     # FastAPI backend application
│   │   ├── app/                     # Routers, schemas, database models, services
│   │   ├── requirements.txt         # Pinned Python dependencies
│   │   └── .env.example             # Backend non-secret template
│   ├── frontend/                    # Next.js App Router web platform
│   │   ├── src/                     # React components, pages, API clients
│   │   └── .env.example             # Web non-secret template
│   ├── Dockerfile                   # Non-root backend container packaging
│   ├── .dockerignore                # Build context isolation
│   ├── docker-compose.yml           # Local development database infrastructure
│   └── docker-compose.prod.yml      # Production deployment compose configuration
└── landslide-app/                   # React Native / Expo mobile application
    ├── src/                         # Mobile screens, offline sync queue, navigation
    └── .env.example                 # Mobile non-secret template
```

---

## 3. Environment Variable Matrix

| Variable | Service | Scope | Required in Prod | Safe Dev Default | Production Behavior & Enforcement |
|---|---|---|---|---|---|
| `ENVIRONMENT` | Backend | Server | Optional | `development` | Setting to `production` enforces fail-closed checks for secrets and HTTPS origins. |
| `DB_NAME` | Database / Backend | Server | **YES** | `lrm_db` | Enforced fail-closed in Compose (`${DB_NAME:?}`). Configures PostgreSQL database name and backend `DATABASE_URL`. |
| `DB_USER` | Database / Backend | Server | **YES** | `lrm` | Enforced fail-closed in Compose (`${DB_USER:?}`). Configures PostgreSQL user and backend `DATABASE_URL`. |
| `DB_PASSWORD` | Database / Backend | Secret | **YES** | None | Enforced fail-closed in Compose (`${DB_PASSWORD:?}`). Configures PostgreSQL password and backend `DATABASE_URL`. |
| `DB_PORT` | Database / Backend | Server | Optional | `5432` | Exposed on `127.0.0.1:${DB_PORT:-5432}` on the host for loopback administration. |
| `DATABASE_URL` | Backend | Secret | **YES** | `postgresql://lrm:...@localhost:5432/lrm_db` | Enforced in code (`app.database.config.Settings`). Constructed by Compose from `DB_USER`, `DB_PASSWORD`, `DB_NAME`. |
| `DATABASE_URL_SYNC` | Backend | Secret | **YES** | `postgresql://lrm:...@localhost:5432/lrm_db` | Used by Alembic migration scripts. |
| `COORDINATOR_API_KEY` | Backend | Secret | **YES** | None (permissive with warning in dev) | Enforced fail-closed in Compose (`:?`) and code (`app.api.deps`). Fails closed with HTTP 503 if missing. Min 16 chars. |
| `TRUSTED_ORIGINS` | Backend | Server | **YES** | Localhost & LAN regex | Enforced fail-closed in Compose (`:?`) and code. Fails closed with 0 allowed origins if missing. Must be explicit HTTPS. |
| `SESSION_SIGNING_KEY` | Backend | Secret | **YES** | Deterministic dev key | Enforced fail-closed in Compose (`:?`) and code (`BackboardService`). Must be >= 32 characters in production. |
| `BACKBOARD_API_KEY` | Backend | Secret | Optional (Mock) | None | Backboard RAG provider API credential. Backend-only; never exposed to web or mobile clients. |
| `BACKBOARD_ASSISTANT_ID` | Backend | Secret | Optional (Mock) | None | Backboard assistant identifier. |
| `BACKBOARD_PROVIDER` | Backend | Server | Optional | `mock` | Selects `mock` (deterministic local offline) or `live` (upstream Backboard API). |
| `FIELD_REPORT_UPLOAD_DIR` | Backend | Server | Optional | `backend/uploads/field_reports` | Container upload storage path. Mapped to persistent named volume `lrm_lrm_uploads` in Compose. |
| `TRUSTED_PROXIES` | Backend | Server | Optional | None | Comma-separated upstream reverse proxy IPs (Nginx/Cloudflare) for spoof-resistant client IP extraction. |
| `NEXT_PUBLIC_API_URL` | Web | Public | **YES** | `http://localhost:8000` | Compiled into browser fetch client; must be an explicit HTTPS endpoint in production. |
| `BACKEND_INTERNAL_URL` | Web | Server | Optional | `http://backend:8000` | Server-only. Used by Next.js App Router server routes across the internal Docker bridge network. |
| `EXPO_PUBLIC_API_URL` | Mobile | Public | **YES** | None (auto-detects emulator/LAN in dev) | **Mandatory** for release builds (`!__DEV__`); fails closed with configuration error if missing or non-HTTPS. |

> [!IMPORTANT]
> **Session Signing Key Reconciliation**: The authoritative environment variable recognized by the backend application is strictly **`SESSION_SIGNING_KEY`**.
> Do not use `ASSISTANT_SESSION_SECRET` — it is not recognized by backend configuration loaders, and configuring it instead of `SESSION_SIGNING_KEY` will result in startup fail-closed rejection.

---

## 4. Safe Environment Setup

1. **Backend**:
   ```bash
   cp LRMSG/LRM/backend/.env.example LRMSG/LRM/backend/.env
   # Edit backend/.env and populate actual secrets
   ```
2. **Website**:
   ```bash
   cp LRMSG/LRM/frontend/.env.example LRMSG/LRM/frontend/.env.local
   # Edit frontend/.env.local with production public API endpoint
   ```
3. **Mobile App**:
   ```bash
   cp landslide-app/.env.example landslide-app/.env
   # Configure EXPO_PUBLIC_API_URL for release builds
   ```

> [!CAUTION]
> Never commit `.env`, `.env.local`, or credentials to Git. Ensure `.gitignore` continues to exclude all environment files.

---

## 5. Coordinator Secret Generation & Injection

Generate high-entropy 32-byte cryptographic keys using Python's `secrets` module:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Inject the output into `COORDINATOR_API_KEY` and `SESSION_SIGNING_KEY` via your server's secret manager or protected `.env`.

---

## 6. Docker Deployment Packaging

### Architecture & Rate Limiter Constraint
> [!IMPORTANT]
> The AI Assistant endpoints utilize an in-memory sliding-window rate limiter:
> - **Thread Creation**: Exactly 5 requests per hour per client IP (`THREAD_CREATION_RATE_LIMIT_REQUESTS = 5`, window = 3600s).
> - **Assistant Queries**: Exactly 10 requests per minute per verified session (`QUERY_RATE_LIMIT_REQUESTS = 10`, window = 60s).
>
> *(Note: Any previous mention of 30 queries/minute in artifact diagrams was an erroneous documentation typo; the codebase, unit tests, and runtime enforcement have strictly enforced 10 queries/minute since inception).*
>
> The backend Docker container is configured to run a **single Uvicorn worker process** (`--workers 1`). Do NOT scale the backend across multiple container replicas or multiple Uvicorn workers until a centralized Redis rate limiter is attached.

### Starting Production Containers
You can start the production containers from either the repository root or the `LRMSG/LRM` directory:

```bash
# Option A: From repository root (C:\Users\Swapnanil\Desktop\app2)
docker compose -f LRMSG/LRM/docker-compose.prod.yml up -d

# Option B: From LRM directory (LRMSG/LRM)
cd LRMSG/LRM
docker compose -f docker-compose.prod.yml up -d

# Check service status
docker compose -f docker-compose.prod.yml ps

# Stream backend logs
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## 7. Database Lifecycle, Backup & Disaster Recovery Runbook

### Volume Identity & Storage Preservation
Docker Compose prefixes declared volumes with the project name `<project>_<volume>`.
* In development and production, the live PostgreSQL 16 + PostGIS 3.4 database storage volume is explicitly named **`lrm_lrm_pgdata`**.
* In `docker-compose.prod.yml`, the top-level configuration explicitly locks `name: lrm` and `volumes.lrm_pgdata.name: lrm_lrm_pgdata`. This prevents volume divergence or empty volume generation if Compose is invoked from differing directory contexts or with different project flags.
* The volume contains 15 public application tables (`alembic_version`, `alerts`, `assignments`, `audit_history`, `emergency_requests`, `field_reports`, `geography_columns`, `geometry_columns`, `incidents`, `relief_resources`, `risk_observations`, `shelters`, `spatial_ref_sys`, `users`, `volunteer_profiles`) and 34 PostGIS spatial extension tables (49 total relations).

> [!CAUTION]
> **Never execute `docker compose down -v`.** The `-v` flag unconditionally deletes all attached Docker volumes, permanently destroying the underlying `lrm_lrm_pgdata` volume and all recorded landslide incident history.

### Milestone 4D.18 Isolated Restore Disclosure
During Milestone 4D.18 pre-deployment verification, a live database logical backup (`lrm_db_backup_20261024_1822.sql`, 255,176 bytes) was generated and verified:
* **The backup was restored exclusively into an isolated ephemeral container (`lrm_postgres_restore_test`) on an isolated port (`5433`).**
* **The live database volume (`lrm_lrm_pgdata`) and live container (`lrm_postgres`) were preserved untouched and were never overwritten, interrupted, or reset.**
* The isolated test verified 100% schema parity and exact row counts across all 15 tables before the ephemeral test container was cleanly deleted.

### Safe Backup Creation Procedure
Logical backups must be created regularly and prior to any schema migration or maintenance:
```bash
# 1. Ensure backups directory exists
mkdir -p LRMSG/LRM/backups

# 2. Generate logical dump from the live container
docker exec lrm_postgres pg_dump -U lrm -d lrm_db --clean --if-exists > LRMSG/LRM/backups/lrm_db_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Verify backup file is non-empty and completed successfully
# Expected: ends with "-- PostgreSQL database dump complete"
tail -n 5 LRMSG/LRM/backups/lrm_db_backup_*.sql
```

### Backup Security, Off-Site Storage & Retention
* **Local Storage Caveat**: The `backups/` directory and `*.sql` files are excluded from Git via `.gitignore`. However, **local uncommitted files on the host disk do NOT protect against hardware failure, filesystem corruption, accidental host deletion, or ransomware**.
* **Off-Site Encrypted Storage**: For production environments:
  1. Backups must be immediately encrypted at rest using strong symmetric encryption (e.g., `gpg --symmetric --cipher-algo AES256`).
  2. Encrypted dumps must be replicated off-site to durable, access-controlled cloud object storage (e.g., AWS S3 Glacier, Google Cloud Storage, or private secure SFTP) with immutable object lock.
  3. Retention policy: Maintain 7 daily, 4 weekly, and 12 monthly immutable archives.
* **Prohibition on Git Storage**: NEVER commit, stage, or push `.sql`, `.dump`, or `.tar` backup files to GitHub or any unapproved external destination.

### Periodic Isolated Restoration Verification
A backup is only as good as its proven recovery. Periodically verify backups against an **isolated target**:
```bash
# 1. Start an isolated ephemeral container on a non-conflicting port (e.g., 5433)
docker run --name lrm_postgres_restore_test \
  -e POSTGRES_USER=lrm \
  -e POSTGRES_PASSWORD=restore_test_password \
  -e POSTGRES_DB=lrm_restore_db \
  -p 127.0.0.1:5433:5432 \
  -d postgis/postgis:16-3.4

# 2. Wait for isolated container to become healthy
docker exec lrm_postgres_restore_test pg_isready -U lrm -d lrm_restore_db

# 3. Restore dump into isolated test database
docker exec -i lrm_postgres_restore_test psql -U lrm -d lrm_restore_db < LRMSG/LRM/backups/lrm_db_backup_<timestamp>.sql

# 4. Verify table count and schema integrity in isolated test container
docker exec -i lrm_postgres_restore_test psql -U lrm -d lrm_restore_db -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"

# 5. Cleanly remove the test container (live database remains untouched)
docker rm -f lrm_postgres_restore_test
```

### Strict Prohibition on Live Database Overwrite
> [!CAUTION]
> **Restoring a backup directly over the live production database (`lrm_postgres` / `lrm_lrm_pgdata`) is strictly prohibited without:**
> 1. A documented, authorized incident-recovery ticket and change-management approval.
> 2. A freshly taken, verified pre-restoration snapshot of the live database volume.
> 3. An intentional maintenance window during which the backend application is stopped (`docker compose -f docker-compose.prod.yml stop backend`) to prevent split-brain writes during restore.

### Alembic Migrations & Reversibility Risk
1. **Verify Database Health**:
   ```bash
   docker compose -f docker-compose.prod.yml exec db pg_isready -U lrm -d lrm_db
   ```
2. **Run Alembic Migrations**:
   ```bash
   docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```
3. **Rollback Warning**: Current migration `007_field_reports` executes `op.drop_table("field_reports")` on downgrade. Never run `alembic downgrade` in production without taking a verified logical dump first. Restoration from backup is the approved rollback strategy.

---

## 8. Backend Health & Verification

Verify the live backend health status:
```bash
curl -f http://localhost:8000/health
```
Expected response:
```json
{
  "status": "healthy",
  "database": {
    "postgresql": "connected",
    "postgis": "available",
    "table_count": 15
  }
}
```

---

## 9. Website Production Build & Deployment

```bash
cd LRMSG/LRM/frontend

# Build optimized Next.js production bundle
npm run build

# Start production server
npm run start
```
* Ensure `NEXT_PUBLIC_API_URL` points to the public HTTPS backend URL.
* The Next.js client relies exclusively on `HttpOnly`, `SameSite=Lax`, `Path=/api/assistant` session cookies.

---

## 10. Mobile Release Build Configuration

For Expo / React Native release builds:
1. Provide `EXPO_PUBLIC_API_URL=https://api.yourdomain.com` in your build environment (e.g. EAS Build secrets).
2. The runtime validator in `apiConfig.ts` will:
   * Reject empty or missing URLs with a configuration error.
   * Reject unencrypted `http://` URLs with a security error.
   * Accept valid `https://` production endpoints.

---

## 11. Security Hardening Summary

1. **CORS & CSRF Origin Restrictions**:
   * In production (`ENVIRONMENT=production`), only explicit HTTPS origins in `TRUSTED_ORIGINS` are accepted.
   * Wildcards (`*`), path segments, and query parameters are rejected.
   * Local-network regular expressions are disabled in production.
2. **Backend-Only Secrets**:
   * Backboard API credentials, PostgreSQL passwords, and session-signing keys reside strictly on the backend.
   * Automated tests enforce that client bundles contain zero Backboard credentials.
3. **Fail-Closed Access Control**:
   * Coordinator mutation endpoints (`PATCH /api/field-reports/{id}/review`, etc.) fail closed with HTTP 503 if `COORDINATOR_API_KEY` is not configured or is `< 16` characters.
4. **Photo Upload Safeguards**:
   * 10 MB maximum file size limit.
   * Strict MIME type allowlist (`jpeg`, `png`, `webp`).
   * Binary magic byte verification.
   * Path traversal guards on disk writes.
5. **AI Safety Boundaries**:
   * Field report AI triage is purely advisory and never auto-approves reports.
   * Legacy ML prediction endpoints explicitly return `prediction_status: "UNAVAILABLE"` with retired notice.
   * Assistant responses enforce `memory="off"` and persistent safety disclaimers.

---

## 12. Troubleshooting & Common Failures

* **HTTP 503 on Coordinator Endpoints**: Check that `COORDINATOR_API_KEY` is set in `backend/.env` with at least 16 characters.
* **HTTP 403 on Assistant Queries**: Verify the browser origin matches an entry in `TRUSTED_ORIGINS`.
* **Mobile Build Error: Configuration Error**: Ensure `EXPO_PUBLIC_API_URL` is configured in release build secrets.
* **Database Connection Refused**: Confirm container `lrm_postgres` is running and healthy on internal port 5432.

---

## 13. Deployment Readiness Hierarchy & Operational Verification Boundaries

Operational and deployment teams must distinguish between the following five readiness tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Deployment Readiness Tiers                         │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 1: Configuration & Packaging Audit (Complete)                     │
│         - Dockerfile non-root user, single worker, explicit volume     │
│         - Environment contract alignment & fail-closed security        │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 2: Isolated Backup & Disaster Recovery Verification (Complete)    │
│         - Logical backup integrity & ephemeral isolated restoration    │
│         - 100% schema parity, 15 tables, 49 relations preserved        │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 3: Staging Deployment & Multi-Client Smoke Testing (Next Phase)   │
│         - Deploying stack in air-gapped staging matching production    │
│         - End-to-end web & mobile assistant verification on staging    │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 4: Production Infrastructure & Network Security (Pending Deploy)  │
│         - Domain DNS, valid TLS 1.3 certificates, reverse proxy        │
│         - KMS/Secret-manager secret injection & off-site backup sync   │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 5: Scientific ML & Physical Hardware Field Validation (Life-Safety)│
│         - Scientific calibration for automated landslide hazard models │
│         - Real physical camera sensors, mountain GPS, multi-agency SOP │
└────────────────────────────────────────────────────────────────────────┘
```

### Critical Life-Safety Advisory: Automated Warning Status
> [!CAUTION]
> **The current project is NOT ready for operational automated landslide hazard warnings.**
> - All legacy ML prediction endpoints (`/api/predict/*`, `/prediction/*`) remain **retired and disabled** (returning `HTTP 503 Service Unavailable`).
> - The application in its current state provides:
>   1. Citizen and field intelligence crowd-sourcing (`/api/field-reports`).
>   2. Coordinator dispatch, shelter mapping, and resource management (`/app-backend/*`).
>   3. Grounded knowledge-base conversational safety assistance (`/api/assistant/*`).
> - Operational automated landslide warnings require a newly architected, peer-reviewed scientific machine-learning pipeline, calibrated geological telemetry, and multi-agency civil defense operational sign-off.

### Operational Boundaries
1. **Physical Hardware Field Validation**:
   - Automated verification has been completed across simulated environments, Android emulators, and browsers.
   - Physical field verification with actual device camera sensors (varying focal lengths and lighting), hardware GPS receivers (high-altitude satellite fix accuracy), and cellular SMS gateways remains required prior to life-safety deployment.
2. **Single-Worker Process Invariant**:
   - In-memory rate limiting (5 threads/hr/IP, 10 queries/min/session) is process-local. The container runs a single Uvicorn worker process (`--workers 1`).
   - For multi-replica or multi-worker horizontal scaling, a distributed store (e.g. Redis) must be introduced before removing this constraint.
3. **Rollback via Backup Restore**:
   - Alembic migration `007` drops the `field_reports` table on downgrade.
   - In production emergencies, restore from a verified logical backup rather than running `alembic downgrade`.
