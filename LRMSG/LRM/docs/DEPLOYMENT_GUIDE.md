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

| Variable | Service | Scope | Required in Prod | Safe Dev Default | Production Behavior |
|---|---|---|---|---|---|
| `ENVIRONMENT` | Backend | Server | Optional | `development` | Setting to `production` enforces fail-closed checks for secrets and HTTPS origins. |
| `DATABASE_URL` | Backend | Secret | **YES** | `postgresql://lrm:...@localhost:5432/lrm_db` | Used by SQLAlchemy connection pool (`pool_pre_ping=True`). |
| `DATABASE_URL_SYNC` | Backend | Secret | **YES** | `postgresql://lrm:...@localhost:5432/lrm_db` | Used by Alembic migration scripts. |
| `COORDINATOR_API_KEY` | Backend | Secret | **YES** | None (permissive with warning in dev) | Fails closed with HTTP 503 if missing or `< 16` chars. Checked via `secrets.compare_digest`. |
| `TRUSTED_ORIGINS` | Backend | Server | **YES** | Localhost & LAN regex | Fails closed with 0 allowed origins if missing in prod. Rejects wildcards, HTTP, paths, and queries. |
| `SESSION_SIGNING_KEY` | Backend | Secret | **YES** | Deterministic dev key | Fails closed on startup if missing or `< 32` characters. |
| `BACKBOARD_API_KEY` | Backend | Secret | Optional (Mock) | None | Restricted to backend; never delivered to web or mobile clients. |
| `BACKBOARD_ASSISTANT_ID` | Backend | Secret | Optional (Mock) | None | Backboard assistant identifier. |
| `NEXT_PUBLIC_API_URL` | Web | Public | **YES** | `http://localhost:8000` | Compiled into web client fetch calls; must be an HTTPS URL in production. |
| `BACKEND_INTERNAL_URL` | Web | Server | Optional | `http://backend:8000` | Used by Next.js server-side routes to communicate across Docker bridge network. |
| `EXPO_PUBLIC_API_URL` | Mobile | Public | **YES** | None (auto-detects emulator/LAN in dev) | **Mandatory** for release builds (`!__DEV__`); fails with configuration error if missing. |

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
> The AI Assistant endpoints utilize an in-memory sliding-window rate limiter (5 threads/hr/IP, 10 queries/min/session) stored within Python process memory.
> The backend Docker container is configured to run a **single Uvicorn worker process**. Do NOT scale the backend across multiple container replicas or multiple Uvicorn workers until a centralized Redis rate limiter is attached.

### Starting Production Containers
```bash
cd LRMSG/LRM

# 1. Start database and backend containers
docker compose -f docker-compose.prod.yml up -d

# 2. Check service status
docker compose -f docker-compose.prod.yml ps

# 3. Stream backend logs
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## 7. Database Migrations & Data Preservation

1. **Verify Database Health**:
   ```bash
   docker compose -f docker-compose.prod.yml exec db pg_isready -U lrm -d lrm_db
   ```
2. **Run Alembic Migrations**:
   ```bash
   docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```
3. **Backup Database Before Upgrades**:
   ```bash
   docker compose -f docker-compose.prod.yml exec db pg_dump -U lrm -d lrm_db > backup_$(date +%Y%m%d).sql
   ```
> [!WARNING]
> Never execute `docker compose down -v`. The `-v` flag deletes Docker volumes, which will destroy the `lrm_pgdata` volume and all application records.

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
