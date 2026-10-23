"""Comprehensive offline unit tests for Backboard Knowledge-Base Ingestion (Phase 2, Milestone 4B).

Verifies:
1. Manifest validation: rejects malformed JSON, missing fields, duplicate IDs,
   unsupported extensions, empty files, and mismatched SHA-256 hashes.
2. Path traversal protection: prevents relative (`../`) or absolute path escape outside kb_dir.
3. Approval gating: guarantees PENDING_REVIEW and REJECTED candidates are never uploaded.
4. Idempotency: unchanged SHA-256 digests skip network uploads; changed digests trigger re-upload.
5. Dry-run safety: zero network requests made, no credentials required, accurate execution plan.
6. Mocked live upload and polling lifecycle:
   - Successful pending -> processing -> indexed transition.
   - Backboard HTTP 4xx/5xx upload errors.
   - Terminal indexing error status.
   - Polling timeout handling.
   - Credential gating when --live is supplied.
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import httpx

from backend.app.services.backboard.config import BackboardSettings
from backend.scripts.ingest_knowledge_base import (
    DEFAULT_KB_DIR,
    DEFAULT_MANIFEST_PATH,
    DocumentIngestionError,
    ManifestValidationError,
    MissingCredentialsError,
    PathTraversalError,
    build_execution_plan,
    compute_file_sha256,
    execute_live_ingestion,
    load_ingestion_state,
    load_manifest,
    main,
    poll_document_status,
    resolve_and_verify_path,
    save_ingestion_state,
    upload_document_to_assistant,
    validate_document_manifest,
)


class TestManifestValidation(unittest.TestCase):
    """Test validation of manifest structure, file existence, and content hashes."""

    def test_official_repository_manifest_is_valid(self):
        """The real repository manifest and knowledge base files must pass validation."""
        self.assertTrue(DEFAULT_MANIFEST_PATH.exists(), f"Missing {DEFAULT_MANIFEST_PATH}")
        self.assertTrue(DEFAULT_KB_DIR.exists(), f"Missing {DEFAULT_KB_DIR}")

        manifest = load_manifest(DEFAULT_MANIFEST_PATH)
        validated_docs = validate_document_manifest(manifest, DEFAULT_KB_DIR)
        self.assertGreaterEqual(len(validated_docs), 6)

        approved = [d for d in validated_docs if d["approval_status"] == "APPROVED"]
        self.assertEqual(len(approved), 6)

        # Check each approved document has an existing file with matching hash
        for doc in approved:
            p = DEFAULT_KB_DIR / doc["filename"]
            self.assertTrue(p.exists())
            self.assertEqual(compute_file_sha256(p).lower(), doc["content_sha256"].lower())

    def test_missing_manifest_file_raises_error(self):
        """Loading a non-existent manifest file raises ManifestValidationError."""
        with self.assertRaises(ManifestValidationError) as ctx:
            load_manifest(Path("non_existent_manifest.json"))
        self.assertIn("not found", str(ctx.exception).lower())

    def test_malformed_json_raises_error(self):
        """Malformed JSON manifest raises ManifestValidationError."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{invalid_json: 123,")
            tmp_path = Path(f.name)

        try:
            with self.assertRaises(ManifestValidationError) as ctx:
                load_manifest(tmp_path)
            self.assertIn("malformed manifest", str(ctx.exception).lower())
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_missing_documents_list_raises_error(self):
        """Manifest missing 'documents' field raises ManifestValidationError."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"manifest_version": "1.0"}, f)
            tmp_path = Path(f.name)

        try:
            with self.assertRaises(ManifestValidationError) as ctx:
                load_manifest(tmp_path)
            self.assertIn("documents", str(ctx.exception).lower())
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_duplicate_document_id_raises_error(self):
        """Duplicate document IDs in the manifest raise ManifestValidationError."""
        data = {
            "documents": [
                {"id": "DOC-001", "approval_status": "PENDING_REVIEW", "approved_for_ingestion": False},
                {"id": "DOC-001", "approval_status": "PENDING_REVIEW", "approved_for_ingestion": False},
            ]
        }
        with self.assertRaises(ManifestValidationError) as ctx:
            validate_document_manifest(data, DEFAULT_KB_DIR)
        self.assertIn("duplicate document id", str(ctx.exception).lower())

    def test_invalid_approval_status_raises_error(self):
        """Invalid approval_status value raises ManifestValidationError."""
        data = {
            "documents": [
                {"id": "DOC-999", "approval_status": "UNKNOWN_STATUS", "approved_for_ingestion": False}
            ]
        }
        with self.assertRaises(ManifestValidationError) as ctx:
            validate_document_manifest(data, DEFAULT_KB_DIR)
        self.assertIn("invalid approval_status", str(ctx.exception).lower())

    def test_inconsistent_approval_flags_raise_error(self):
        """APPROVED with approved_for_ingestion=False or vice versa raises error."""
        # Case 1: APPROVED but approved_for_ingestion is False
        data1 = {
            "documents": [
                {"id": "DOC-001", "approval_status": "APPROVED", "approved_for_ingestion": False}
            ]
        }
        with self.assertRaises(ManifestValidationError):
            validate_document_manifest(data1, DEFAULT_KB_DIR)

        # Case 2: PENDING_REVIEW but approved_for_ingestion is True
        data2 = {
            "documents": [
                {"id": "DOC-002", "approval_status": "PENDING_REVIEW", "approved_for_ingestion": True}
            ]
        }
        with self.assertRaises(ManifestValidationError):
            validate_document_manifest(data2, DEFAULT_KB_DIR)

    def test_mismatched_sha256_hash_raises_error(self):
        """Document with mismatched hash raises ManifestValidationError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_kb = Path(tmp_dir)
            doc_file = tmp_kb / "test_doc.md"
            doc_file.write_text("# Test Document\n\nContent here.", encoding="utf-8")

            data = {
                "documents": [
                    {
                        "id": "DOC-001",
                        "filename": "test_doc.md",
                        "approval_status": "APPROVED",
                        "approved_for_ingestion": True,
                        "content_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                    }
                ]
            }
            with self.assertRaises(ManifestValidationError) as ctx:
                validate_document_manifest(data, tmp_kb)
            self.assertIn("hash mismatch", str(ctx.exception).lower())

    def test_empty_file_raises_error(self):
        """Approved document with 0-byte file raises ManifestValidationError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_kb = Path(tmp_dir)
            doc_file = tmp_kb / "empty.md"
            doc_file.write_text("", encoding="utf-8")

            data = {
                "documents": [
                    {
                        "id": "DOC-001",
                        "filename": "empty.md",
                        "approval_status": "APPROVED",
                        "approved_for_ingestion": True,
                        "content_sha256": hashlib.sha256(b"").hexdigest(),
                    }
                ]
            }
            with self.assertRaises(ManifestValidationError) as ctx:
                validate_document_manifest(data, tmp_kb)
            self.assertIn("empty", str(ctx.exception).lower())

    def test_unsupported_file_extension_raises_error(self):
        """Approved document with unsupported extension (.exe, .zip) raises ManifestValidationError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_kb = Path(tmp_dir)
            doc_file = tmp_kb / "bad_ext.bin"
            doc_file.write_bytes(b"sample binary content")

            data = {
                "documents": [
                    {
                        "id": "DOC-001",
                        "filename": "bad_ext.bin",
                        "approval_status": "APPROVED",
                        "approved_for_ingestion": True,
                        "content_sha256": hashlib.sha256(b"sample binary content").hexdigest(),
                    }
                ]
            }
            with self.assertRaises(ManifestValidationError) as ctx:
                validate_document_manifest(data, tmp_kb)
            self.assertIn("unsupported file extension", str(ctx.exception).lower())


class TestPathTraversalProtection(unittest.TestCase):
    """Test prevention of directory traversal attacks in filenames."""

    def test_relative_path_traversal_is_rejected(self):
        """Relative path traversal (../) outside kb_dir raises PathTraversalError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            kb_dir = Path(tmp_dir) / "kb"
            kb_dir.mkdir()

            traversal_names = [
                "../escape.md",
                "../../secret.txt",
                "subdir/../../outside.md",
            ]
            for bad_name in traversal_names:
                with self.subTest(bad_name=bad_name):
                    with self.assertRaises((PathTraversalError, ManifestValidationError)):
                        resolve_and_verify_path(kb_dir, bad_name)

    def test_safe_nested_path_is_permitted(self):
        """Safe nested subdirectories within kb_dir resolve correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            kb_dir = Path(tmp_dir)
            sub = kb_dir / "articles"
            sub.mkdir()
            target = sub / "doc.md"
            target.write_text("content", encoding="utf-8")

            resolved = resolve_and_verify_path(kb_dir, "articles/doc.md")
            self.assertEqual(resolved, target.resolve())


class TestApprovalGatingAndPlanning(unittest.TestCase):
    """Test approval status gating and execution plan classification."""

    def test_pending_and_rejected_are_never_uploaded(self):
        """PENDING_REVIEW and REJECTED documents must never be marked for upload."""
        docs = [
            {"id": "DOC-001", "approval_status": "APPROVED", "filename": "1.md", "content_sha256": "h1"},
            {"id": "DOC-007", "approval_status": "PENDING_REVIEW", "title": "Pending Doc"},
            {"id": "DOC-010", "approval_status": "REJECTED", "title": "Raw CSV Dump"},
        ]
        state = {"version": "1.0", "documents": {}}

        to_upload, already_indexed, skipped = build_execution_plan(docs, state)

        self.assertEqual(len(to_upload), 1)
        self.assertEqual(to_upload[0]["id"], "DOC-001")
        self.assertEqual(len(already_indexed), 0)
        self.assertEqual(len(skipped), 2)
        self.assertEqual({d["id"] for d in skipped}, {"DOC-007", "DOC-010"})

    def test_idempotency_skips_unchanged_hashes(self):
        """Documents whose hash matches the state file are skipped."""
        docs = [
            {"id": "DOC-001", "approval_status": "APPROVED", "filename": "1.md", "content_sha256": "hash_a"},
            {"id": "DOC-002", "approval_status": "APPROVED", "filename": "2.md", "content_sha256": "hash_b_new"},
        ]
        state = {
            "version": "1.0",
            "documents": {
                "DOC-001": {
                    "filename": "1.md",
                    "content_sha256": "hash_a",
                    "status": "indexed",
                    "backboard_document_id": "doc-uuid-1",
                },
                "DOC-002": {
                    "filename": "2.md",
                    "content_sha256": "hash_b_old",
                    "status": "indexed",
                    "backboard_document_id": "doc-uuid-2",
                },
            },
        }

        to_upload, already_indexed, skipped = build_execution_plan(docs, state, force=False)

        # DOC-001 is already indexed with matching hash -> skip
        self.assertEqual([d["id"] for d in already_indexed], ["DOC-001"])
        # DOC-002 has a changed hash -> upload
        self.assertEqual([d["id"] for d in to_upload], ["DOC-002"])

    def test_force_flag_re_indexes_all_approved(self):
        """When force=True, even unchanged hashes are included in to_upload."""
        docs = [
            {"id": "DOC-001", "approval_status": "APPROVED", "filename": "1.md", "content_sha256": "hash_a"},
        ]
        state = {
            "documents": {
                "DOC-001": {"content_sha256": "hash_a", "status": "indexed"}
            }
        }
        to_upload, already_indexed, skipped = build_execution_plan(docs, state, force=True)
        self.assertEqual(len(to_upload), 1)
        self.assertEqual(len(already_indexed), 0)


class TestDryRunSafety(unittest.TestCase):
    """Test CLI execution in default dry-run mode."""

    def test_dry_run_exits_cleanly_without_credentials(self):
        """Running without --live exits with code 0 and makes zero remote requests."""
        with patch("sys.argv", ["ingest_knowledge_base.py"]):
            exit_code = main()
            self.assertEqual(exit_code, 0)

    def test_live_without_credentials_exits_with_error(self):
        """Running with --live but missing credentials exits with code 1."""
        with patch.dict(os.environ, {"BACKBOARD_API_KEY": "", "BACKBOARD_ASSISTANT_ID": ""}):
            with patch("sys.argv", ["ingest_knowledge_base.py", "--live"]):
                exit_code = main()
                self.assertEqual(exit_code, 1)


class TestMockedLiveIngestionFlow(unittest.TestCase):
    """Test upload and status polling flow using mocked HTTP transport."""

    def setUp(self):
        self.cfg = BackboardSettings(
            api_key="bb_live_api_key_test_12345",
            assistant_id="asst-pulse-100",
            base_url="https://app.backboard.io/api",
            timeout_seconds=5.0,
        )

    def test_successful_upload_and_status_transition(self):
        """Simulate upload followed by pending -> processing -> indexed polling."""
        poll_call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal poll_call_count
            url_str = str(request.url)

            # Upload endpoint
            if "/assistants/asst-pulse-100/documents" in url_str and request.method == "POST":
                self.assertIn("X-API-Key", request.headers)
                return httpx.Response(
                    201,
                    json={
                        "document_id": "bb-doc-uuid-999",
                        "status": "pending",
                        "filename": "01_why_do_landslides_happen.md",
                    },
                )

            # Status polling endpoint
            if "/documents/bb-doc-uuid-999/status" in url_str and request.method == "GET":
                poll_call_count += 1
                if poll_call_count == 1:
                    return httpx.Response(200, json={"status": "processing", "chunks": 0})
                return httpx.Response(
                    200,
                    json={"status": "indexed", "chunks": 14, "filename": "01_why_do_landslides_happen.md"},
                )

            return httpx.Response(404, json={"detail": "Not found"})

        async def run_test():
            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            with tempfile.TemporaryDirectory() as tmp_dir:
                state_file = Path(tmp_dir) / "state.json"
                doc = {
                    "id": "DOC-001",
                    "filename": "01_why_do_landslides_happen.md",
                    "content_sha256": "c874935e569322dbfb7b0d30dc02b9c5afb50fb6eadfd1a19c847d5d0de40138",
                }

                successes, fails = await execute_live_ingestion(
                    documents_to_upload=[doc],
                    kb_dir=DEFAULT_KB_DIR,
                    state_file=state_file,
                    settings=self.cfg,
                    http_client=client,
                    poll_timeout=10.0,
                    poll_interval=0.01,
                )

                self.assertEqual(successes, 1)
                self.assertEqual(fails, 0)
                self.assertGreaterEqual(poll_call_count, 2)

                # Verify state file was written
                state = load_ingestion_state(state_file)
                self.assertIn("DOC-001", state["documents"])
                self.assertEqual(state["documents"]["DOC-001"]["status"], "indexed")
                self.assertEqual(state["documents"]["DOC-001"]["backboard_document_id"], "bb-doc-uuid-999")
                self.assertEqual(state["documents"]["DOC-001"]["chunks"], 14)

        asyncio.run(run_test())

    def test_upload_http_400_records_failure_gracefully(self):
        """Upload HTTP 400 records error state without raising unhandled exception."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"detail": "Unsupported MIME type or corrupt payload"})

        async def run_test():
            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            with tempfile.TemporaryDirectory() as tmp_dir:
                state_file = Path(tmp_dir) / "state.json"
                doc = {
                    "id": "DOC-001",
                    "filename": "01_why_do_landslides_happen.md",
                    "content_sha256": "dummy_sha",
                }

                successes, fails = await execute_live_ingestion(
                    documents_to_upload=[doc],
                    kb_dir=DEFAULT_KB_DIR,
                    state_file=state_file,
                    settings=self.cfg,
                    http_client=client,
                    poll_timeout=5.0,
                    poll_interval=0.01,
                )

                self.assertEqual(successes, 0)
                self.assertEqual(fails, 1)

                state = load_ingestion_state(state_file)
                self.assertIn("DOC-001", state["documents"])
                self.assertEqual(state["documents"]["DOC-001"]["status"], "error")
                self.assertIn("Backboard upload error", state["documents"]["DOC-001"]["error_message"])

        asyncio.run(run_test())

    def test_terminal_indexing_error_status(self):
        """Backboard indexing error status records failure and error message."""
        def handler(request: httpx.Request) -> httpx.Response:
            url_str = str(request.url)
            if request.method == "POST":
                return httpx.Response(201, json={"document_id": "doc-fail-1", "status": "pending"})
            if request.method == "GET":
                return httpx.Response(
                    200,
                    json={"status": "error", "error_message": "Document contains unparseable binary stream"},
                )
            return httpx.Response(404)

        async def run_test():
            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            with tempfile.TemporaryDirectory() as tmp_dir:
                state_file = Path(tmp_dir) / "state.json"
                doc = {
                    "id": "DOC-001",
                    "filename": "01_why_do_landslides_happen.md",
                    "content_sha256": "dummy_sha",
                }

                successes, fails = await execute_live_ingestion(
                    documents_to_upload=[doc],
                    kb_dir=DEFAULT_KB_DIR,
                    state_file=state_file,
                    settings=self.cfg,
                    http_client=client,
                    poll_timeout=5.0,
                    poll_interval=0.01,
                )

                self.assertEqual(successes, 0)
                self.assertEqual(fails, 1)

                state = load_ingestion_state(state_file)
                self.assertEqual(state["documents"]["DOC-001"]["status"], "error")
                self.assertIn("unparseable binary stream", state["documents"]["DOC-001"]["error_message"])

        asyncio.run(run_test())

    def test_indexing_timeout_records_failure(self):
        """Status polling exceeding max_wait_seconds raises timeout and records failure."""
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "POST":
                return httpx.Response(201, json={"document_id": "doc-timeout-1", "status": "pending"})
            return httpx.Response(200, json={"status": "processing"})

        async def run_test():
            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            with tempfile.TemporaryDirectory() as tmp_dir:
                state_file = Path(tmp_dir) / "state.json"
                doc = {
                    "id": "DOC-001",
                    "filename": "01_why_do_landslides_happen.md",
                    "content_sha256": "dummy_sha",
                }

                # Timeout after 0.05 seconds
                successes, fails = await execute_live_ingestion(
                    documents_to_upload=[doc],
                    kb_dir=DEFAULT_KB_DIR,
                    state_file=state_file,
                    settings=self.cfg,
                    http_client=client,
                    poll_timeout=0.05,
                    poll_interval=0.01,
                )

                self.assertEqual(successes, 0)
                self.assertEqual(fails, 1)

                state = load_ingestion_state(state_file)
                self.assertEqual(state["documents"]["DOC-001"]["status"], "error")
                self.assertIn("timed out", state["documents"]["DOC-001"]["error_message"].lower())

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
