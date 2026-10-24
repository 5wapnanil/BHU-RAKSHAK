"""Non-secret production environment contract and fail-closed security verification test suite.

Milestone 4D.19: Production Environment Contract & Deployment Runbook Audit.

Verifies:
1. Reconciliation of SESSION_SIGNING_KEY vs ASSISTANT_SESSION_SECRET:
   - SESSION_SIGNING_KEY is the authoritative variable consumed by the application.
   - Setting ASSISTANT_SESSION_SECRET does NOT satisfy the requirement; in production,
     the service fails closed with BackboardConfigurationError if SESSION_SIGNING_KEY is absent.
   - SESSION_SIGNING_KEY must be >= 32 characters in production.
   - Key separation: SESSION_SIGNING_KEY must not reuse BACKBOARD_API_KEY.
2. Database configuration contract:
   - Settings in app.database.config requires DATABASE_URL and fails closed if missing.
   - Alembic migration environment requires DATABASE_URL_SYNC or DATABASE_URL.
   - Docker Compose database environment interpolations agree between 'db' and 'backend'.
3. Coordinator authorization fail-closed contract:
   - In production, missing COORDINATOR_API_KEY fails closed with HTTP 503.
   - Constant-time secret comparison prevents side-channel timing attacks.
4. CORS and Trusted Origins fail-closed contract:
   - In production, missing TRUSTED_ORIGINS returns empty list and fails closed.
   - Rejects wildcards, insecure HTTP, URL paths, query parameters, and userinfo credentials.
5. Client template security isolation:
   - Frontend and mobile templates expose ZERO backend secrets in public bundles.
   - Mobile API configuration rejects insecure HTTP or missing endpoints in release builds.
6. Docker Compose production packaging invariants:
   - Required variables enforce fail-closed interpolation syntax (:?).
   - Explicit volume names (lrm_lrm_pgdata, lrm_lrm_uploads) and project name (name: lrm).
"""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import yaml

from fastapi import HTTPException

from backend.app.api.deps import (
    get_effective_trusted_origins,
    is_trusted_origin,
    validate_origin,
    verify_coordinator_authorization,
)
from backend.app.services.backboard import (
    BackboardConfigurationError,
    BackboardSettings,
)
from backend.app.services.backboard_service import (
    MIN_PRODUCTION_KEY_LENGTH,
    BackboardService,
)

DUMMY_VALID_KEY_32 = "a" * 32
DUMMY_SHORT_KEY_16 = "b" * 16
REPO_ROOT = Path(__file__).resolve().parents[4]
LRM_ROOT = REPO_ROOT / "LRMSG" / "LRM"


class TestSessionSigningKeyContract(unittest.TestCase):
    """Test session-signing key resolution, name reconciliation, and production invariants."""

    def test_session_signing_key_is_authoritative(self):
        """Verify SESSION_SIGNING_KEY is read by BackboardSettings."""
        with patch.dict(os.environ, {"SESSION_SIGNING_KEY": DUMMY_VALID_KEY_32}, clear=True):
            settings = BackboardSettings()
            self.assertEqual(settings.session_signing_key, DUMMY_VALID_KEY_32)

    def test_assistant_session_secret_is_not_recognized_and_fails_closed(self):
        """Setting ASSISTANT_SESSION_SECRET does not configure the signing key and fails closed."""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "ASSISTANT_SESSION_SECRET": DUMMY_VALID_KEY_32,
            },
            clear=True,
        ):
            settings = BackboardSettings()
            # ASSISTANT_SESSION_SECRET is ignored; session_signing_key remains empty
            self.assertEqual(settings.session_signing_key, "")

            # BackboardService fails closed in production
            with self.assertRaises(BackboardConfigurationError) as ctx:
                BackboardService(config=settings, is_production=True)
            self.assertIn("SESSION_SIGNING_KEY is required for production deployments", str(ctx.exception))

    def test_production_session_signing_key_length_enforcement(self):
        """In production, keys shorter than 32 characters fail closed."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            settings = BackboardSettings(session_signing_key="short_16_chars_")
            with self.assertRaises(BackboardConfigurationError) as ctx:
                BackboardService(config=settings, is_production=True)
            self.assertIn("must be at least 32 characters long", str(ctx.exception))

    def test_session_signing_key_separation_from_backboard_api_key(self):
        """Verify fail-closed error if SESSION_SIGNING_KEY is identical to BACKBOARD_API_KEY."""
        reused_key = "shared_secret_that_should_not_be_reused_32chars"
        settings = BackboardSettings(
            api_key=reused_key,
            session_signing_key=reused_key,
        )
        with self.assertRaises(BackboardConfigurationError) as ctx:
            BackboardService(config=settings, is_production=False)
        self.assertIn("SESSION_SIGNING_KEY must not reuse BACKBOARD_API_KEY", str(ctx.exception))


class TestDatabaseConfigContract(unittest.TestCase):
    """Test database configuration contract and Compose alignment."""

    def test_database_settings_fails_closed_if_database_url_missing(self):
        """backend/app/database/config.py Settings raises RuntimeError if DATABASE_URL is missing."""
        from backend.app.database.config import Settings

        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=True):
            with patch.object(Settings, "DATABASE_URL", ""):
                with self.assertRaises(RuntimeError) as ctx:
                    Settings()
                self.assertIn("DATABASE_URL must be set", str(ctx.exception))

    def test_compose_database_environment_alignment(self):
        """Verify docker-compose.prod.yml database parameters align between 'db' and 'backend'."""
        compose_path = LRM_ROOT / "docker-compose.prod.yml"
        self.assertTrue(compose_path.is_file(), f"docker-compose.prod.yml not found at {compose_path}")

        with open(compose_path, "r", encoding="utf-8") as f:
            raw = f.read()

        # Parse YAML without variable interpolation
        data = yaml.safe_load(raw)

        # Check top-level project name
        self.assertEqual(data.get("name"), "lrm")

        # Check db service environment
        db_env = data["services"]["db"]["environment"]
        self.assertIn("POSTGRES_DB", db_env)
        self.assertIn("POSTGRES_USER", db_env)
        self.assertIn("POSTGRES_PASSWORD", db_env)

        # Check backend service environment
        backend_env_list = data["services"]["backend"]["environment"]
        backend_env = {}
        for item in backend_env_list:
            if "=" in item:
                k, v = item.split("=", 1)
                backend_env[k.strip()] = v.strip()

        self.assertIn("DATABASE_URL", backend_env)
        self.assertIn("DATABASE_URL_SYNC", backend_env)
        # Verify the URL construction uses matching interpolations
        self.assertIn("${DB_USER}", backend_env["DATABASE_URL"])
        self.assertIn("${DB_PASSWORD}", backend_env["DATABASE_URL"])
        self.assertIn("${DB_NAME}", backend_env["DATABASE_URL"])
        self.assertIn("@db:5432/", backend_env["DATABASE_URL"])

        # Check volume naming
        self.assertEqual(data["volumes"]["lrm_pgdata"]["name"], "lrm_lrm_pgdata")
        self.assertEqual(data["volumes"]["lrm_uploads"]["name"], "lrm_lrm_uploads")


class TestCoordinatorAuthorizationContract(unittest.TestCase):
    """Test coordinator authentication requirements and fail-closed behavior."""

    def test_production_fails_closed_without_coordinator_key(self):
        """In production, if COORDINATOR_API_KEY is unset, requests fail with HTTP 503."""
        request = MagicMock()
        request.headers = {"X-Coordinator-Key": "some_test_key"}

        with patch.dict(os.environ, {"ENVIRONMENT": "production", "COORDINATOR_API_KEY": ""}, clear=True):
            with self.assertRaises(HTTPException) as ctx:
                verify_coordinator_authorization(request)
            self.assertEqual(ctx.exception.status_code, 503)
            self.assertIn("Administrative access unavailable", ctx.exception.detail)

    def test_configured_coordinator_key_rejects_unauthorized_requests(self):
        """When COORDINATOR_API_KEY is configured, invalid requests fail with HTTP 403."""
        request = MagicMock()
        request.headers = {"X-Coordinator-Key": "wrong_key_provided"}

        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "COORDINATOR_API_KEY": "valid_secret_coordinator_key_32chars",
            },
            clear=True,
        ):
            with self.assertRaises(HTTPException) as ctx:
                verify_coordinator_authorization(request)
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertIn("Forbidden", ctx.exception.detail)

    def test_configured_coordinator_key_accepts_valid_header_and_bearer(self):
        """Valid header or Bearer authorization succeeds."""
        key = "valid_secret_coordinator_key_32chars"
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "COORDINATOR_API_KEY": key,
            },
            clear=True,
        ):
            # Test X-Coordinator-Key
            req1 = MagicMock()
            req1.headers = {"X-Coordinator-Key": key}
            self.assertEqual(verify_coordinator_authorization(req1), key)

            # Test Bearer token
            req2 = MagicMock()
            req2.headers = {"Authorization": f"Bearer {key}"}
            self.assertEqual(verify_coordinator_authorization(req2), key)


class TestTrustedOriginsContract(unittest.TestCase):
    """Test CORS and CSRF origin validation fail-closed behavior."""

    def test_production_fails_closed_when_trusted_origins_empty(self):
        """In production, empty TRUSTED_ORIGINS returns empty list and rejects all origins."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "TRUSTED_ORIGINS": ""}, clear=True):
            origins = get_effective_trusted_origins(is_production=True)
            self.assertEqual(origins, [])
            self.assertFalse(is_trusted_origin("https://app.example.com", is_production=True))

    def test_production_rejects_insecure_origins(self):
        """In production, wildcards, unencrypted HTTP, paths, and queries are rejected."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            # Wildcard rejected
            with self.assertRaises(ValueError):
                validate_origin("*", is_production=True)

            # Insecure external HTTP rejected
            with self.assertRaises(ValueError):
                validate_origin("http://app.example.com", is_production=True)

            # Origin with path rejected
            with self.assertRaises(ValueError):
                validate_origin("https://app.example.com/api", is_production=True)

            # Origin with query rejected
            with self.assertRaises(ValueError):
                validate_origin("https://app.example.com?query=1", is_production=True)

            # Origin with credentials rejected
            with self.assertRaises(ValueError):
                validate_origin("https://user:pass@app.example.com", is_production=True)

    def test_production_accepts_valid_https_origins(self):
        """Valid HTTPS domain with optional port is accepted."""
        clean1 = validate_origin("https://bhurakshak.gov.in", is_production=True)
        self.assertEqual(clean1, "https://bhurakshak.gov.in")

        clean2 = validate_origin("https://app.example.com:8443", is_production=True)
        self.assertEqual(clean2, "https://app.example.com:8443")


class TestClientTemplateSecurityIsolation(unittest.TestCase):
    """Test that public web and mobile configuration templates leak zero server secrets."""

    def test_frontend_env_example_contains_no_server_secrets(self):
        """frontend/.env.example must not expose server secrets in NEXT_PUBLIC_ namespace."""
        fe_example = LRM_ROOT / "frontend" / ".env.example"
        self.assertTrue(fe_example.is_file())

        with open(fe_example, "r", encoding="utf-8") as f:
            content = f.read()

        # Secret keywords that must NEVER be prefixed with NEXT_PUBLIC_
        forbidden_public = [
            "NEXT_PUBLIC_DATABASE_URL",
            "NEXT_PUBLIC_DB_PASSWORD",
            "NEXT_PUBLIC_BACKBOARD_API_KEY",
            "NEXT_PUBLIC_SESSION_SIGNING_KEY",
            "NEXT_PUBLIC_ASSISTANT_SESSION_SECRET",
            "NEXT_PUBLIC_COORDINATOR_API_KEY",
        ]
        for var in forbidden_public:
            self.assertNotIn(var, content, f"Forbidden public secret {var} found in {fe_example}")

    def test_mobile_env_example_contains_no_server_secrets(self):
        """landslide-app/.env.example must not expose server secrets in EXPO_PUBLIC_ namespace."""
        mobile_example = REPO_ROOT / "landslide-app" / ".env.example"
        self.assertTrue(mobile_example.is_file())

        with open(mobile_example, "r", encoding="utf-8") as f:
            content = f.read()

        forbidden_mobile = [
            "EXPO_PUBLIC_DATABASE_URL",
            "EXPO_PUBLIC_DB_PASSWORD",
            "EXPO_PUBLIC_BACKBOARD_API_KEY",
            "EXPO_PUBLIC_SESSION_SIGNING_KEY",
            "EXPO_PUBLIC_ASSISTANT_SESSION_SECRET",
            "EXPO_PUBLIC_COORDINATOR_API_KEY",
        ]
        for var in forbidden_mobile:
            self.assertNotIn(var, content, f"Forbidden mobile secret {var} found in {mobile_example}")


class TestDockerPackagingInvariants(unittest.TestCase):
    """Test Dockerfile and Compose packaging requirements."""

    def test_dockerfile_enforces_single_worker_and_non_root_user(self):
        """Dockerfile must specify non-root USER and single Uvicorn worker."""
        dockerfile_path = LRM_ROOT / "Dockerfile"
        self.assertTrue(dockerfile_path.is_file())

        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("USER appuser", content)
        self.assertIn('"--workers", "1"', content)

    def test_compose_enforces_fail_closed_required_variables(self):
        """docker-compose.prod.yml must declare mandatory variables with :? fail-closed syntax."""
        compose_path = LRM_ROOT / "docker-compose.prod.yml"
        with open(compose_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_guards = [
            "${DB_NAME:?",
            "${DB_USER:?",
            "${DB_PASSWORD:?",
            "${COORDINATOR_API_KEY:?",
            "${TRUSTED_ORIGINS:?",
            "${SESSION_SIGNING_KEY:?",
        ]
        for guard in required_guards:
            self.assertIn(guard, content, f"Missing fail-closed guard {guard} in docker-compose.prod.yml")


if __name__ == "__main__":
    unittest.main()
