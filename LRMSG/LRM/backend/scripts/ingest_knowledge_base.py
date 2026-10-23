"""Controlled, idempotent knowledge-base ingestion CLI for PahaarPulse.

NON-NEGOTIABLE SAFETY CONSTRAINTS:
1. Dry-run by default: Without an explicit '--live' flag, this utility only
   validates the manifest, inspects local file integrity/hashes, reports the
   execution plan, and exits cleanly with code 0 without any network calls.
2. Manifest enforcement: Only documents explicitly marked as 'APPROVED' are
   processed for upload. 'PENDING_REVIEW' and 'REJECTED' candidates are safely skipped.
3. Path traversal protection: All document filenames must resolve strictly
   within the designated knowledge base directory.
4. Idempotency & hashing: SHA-256 hashes are compared against local ingestion
   state. Unchanged files are never re-uploaded unless '--force' is specified.
5. Secret safety: Credentials (BACKBOARD_API_KEY, BACKBOARD_ASSISTANT_ID) are
   only required in live mode and are strictly redacted in console outputs.
"""

import argparse
import asyncio
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import httpx

from backend.app.services.backboard.config import BackboardSettings

# Default locations relative to repository
DEFAULT_MANIFEST_PATH = _repo_root / "backend" / "data" / "knowledge_base_manifest.json"
DEFAULT_KB_DIR = _repo_root / "backend" / "data" / "knowledge_base"
DEFAULT_STATE_FILE = _repo_root / "backend" / "data" / "ingestion_state.json"

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".pdf"}


class ManifestValidationError(Exception):
    """Raised when manifest structure, fields, or hashes fail validation."""


class PathTraversalError(ValueError):
    """Raised when a document path escapes the authorized knowledge base directory."""


class DocumentIngestionError(Exception):
    """Raised when document upload or status polling fails."""


class MissingCredentialsError(Exception):
    """Raised when live mode is requested without required credentials."""


def redact_secret(val: str) -> str:
    """Safely redact sensitive tokens, exposing only prefix and suffix."""
    if not val:
        return "<unset>"
    if len(val) <= 8:
        return "***"
    return f"{val[:3]}...{val[-4:]}"


def compute_file_sha256(file_path: Path) -> str:
    """Compute the SHA-256 digest of a local file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_and_verify_path(kb_dir: Path, filename: str) -> Path:
    """Verify that filename resolves strictly inside kb_dir with no directory traversal."""
    if not filename:
        raise ManifestValidationError("Document filename cannot be empty.")

    # Guard against obvious path traversal patterns before resolving
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        target_candidate = (kb_dir / filename).resolve()
        kb_resolved = kb_dir.resolve()
        if not target_candidate.is_relative_to(kb_resolved):
            raise PathTraversalError(
                f"Path traversal detected: '{filename}' escapes authorized knowledge base directory '{kb_dir}'"
            )

    target_path = (kb_dir / filename).resolve()
    kb_resolved = kb_dir.resolve()

    try:
        target_path.relative_to(kb_resolved)
    except ValueError:
        raise PathTraversalError(
            f"Path traversal detected: '{filename}' resolves outside authorized directory '{kb_dir}'"
        )

    return target_path


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load and parse the JSON manifest."""
    if not manifest_path.exists():
        raise ManifestValidationError(f"Manifest file not found: {manifest_path}")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ManifestValidationError(f"Malformed manifest JSON in {manifest_path}: {e}")

    if not isinstance(data, dict) or "documents" not in data:
        raise ManifestValidationError("Manifest must be a JSON object containing a 'documents' list.")

    if not isinstance(data["documents"], list):
        raise ManifestValidationError("Manifest 'documents' field must be a list.")

    return data


def validate_document_manifest(
    manifest_data: Dict[str, Any],
    kb_dir: Path,
) -> List[Dict[str, Any]]:
    """Validate all manifest documents, checking schemas, statuses, and file integrity."""
    validated = []
    seen_ids = set()

    for idx, doc in enumerate(manifest_data.get("documents", [])):
        if not isinstance(doc, dict):
            raise ManifestValidationError(f"Manifest entry #{idx} is not a valid JSON object.")

        doc_id = doc.get("id")
        if not doc_id or not isinstance(doc_id, str):
            raise ManifestValidationError(f"Manifest entry #{idx} is missing a valid string 'id'.")

        if doc_id in seen_ids:
            raise ManifestValidationError(f"Duplicate document id found: '{doc_id}'")
        seen_ids.add(doc_id)

        status = doc.get("approval_status")
        if status not in {"APPROVED", "PENDING_REVIEW", "REJECTED"}:
            raise ManifestValidationError(
                f"Document '{doc_id}' has invalid approval_status: '{status}' (must be APPROVED, PENDING_REVIEW, or REJECTED)"
            )

        approved = doc.get("approved_for_ingestion")
        if not isinstance(approved, bool):
            raise ManifestValidationError(
                f"Document '{doc_id}' missing boolean 'approved_for_ingestion' flag."
            )

        # Enforce consistency
        if status == "APPROVED" and not approved:
            raise ManifestValidationError(
                f"Document '{doc_id}' is marked APPROVED but approved_for_ingestion is False."
            )
        if status in {"PENDING_REVIEW", "REJECTED"} and approved:
            raise ManifestValidationError(
                f"Document '{doc_id}' is {status} but approved_for_ingestion is True."
            )

        if status == "APPROVED":
            filename = doc.get("filename")
            if not filename:
                raise ManifestValidationError(f"Approved document '{doc_id}' must specify a filename.")

            file_path = resolve_and_verify_path(kb_dir, filename)

            if not file_path.exists():
                raise ManifestValidationError(
                    f"Approved document '{doc_id}' file does not exist on disk: {file_path}"
                )

            if not file_path.is_file():
                raise ManifestValidationError(
                    f"Approved document '{doc_id}' target is not a regular file: {file_path}"
                )

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise ManifestValidationError(
                    f"Approved document '{doc_id}' has unsupported file extension '{file_path.suffix}'. Supported: {SUPPORTED_EXTENSIONS}"
                )

            actual_size = file_path.stat().st_size
            if actual_size == 0:
                raise ManifestValidationError(f"Approved document '{doc_id}' file is empty (0 bytes).")

            actual_sha = compute_file_sha256(file_path)
            expected_sha = doc.get("content_sha256")
            if not expected_sha:
                raise ManifestValidationError(
                    f"Approved document '{doc_id}' is missing 'content_sha256' in manifest."
                )

            if actual_sha.lower() != expected_sha.lower():
                raise ManifestValidationError(
                    f"SHA-256 hash mismatch for document '{doc_id}' ({filename}):\n"
                    f"  Expected: {expected_sha}\n"
                    f"  Actual:   {actual_sha}"
                )

        validated.append(doc)

    return validated


def load_ingestion_state(state_file: Path) -> Dict[str, Any]:
    """Load the local ingestion state file if it exists, or return an empty template."""
    if not state_file.exists():
        return {"version": "1.0", "documents": {}}

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "documents" in data and isinstance(data["documents"], dict):
                return data
            return {"version": "1.0", "documents": {}}
    except (json.JSONDecodeError, OSError):
        return {"version": "1.0", "documents": {}}


def save_ingestion_state(state_file: Path, state_data: Dict[str, Any]) -> None:
    """Save ingestion state atomically using a temporary file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = state_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2)
    temp_file.replace(state_file)


def build_execution_plan(
    documents: List[Dict[str, Any]],
    state_data: Dict[str, Any],
    force: bool = False,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Classify documents into (to_upload, already_indexed, skipped_unapproved)."""
    indexed_docs = state_data.get("documents", {})
    to_upload = []
    already_indexed = []
    skipped_unapproved = []

    for doc in documents:
        status = doc["approval_status"]
        doc_id = doc["id"]

        if status != "APPROVED":
            skipped_unapproved.append(doc)
            continue

        existing_record = indexed_docs.get(doc_id)
        if (
            not force
            and existing_record
            and existing_record.get("status") == "indexed"
            and existing_record.get("content_sha256") == doc.get("content_sha256")
        ):
            already_indexed.append(doc)
        else:
            to_upload.append(doc)

    return to_upload, already_indexed, skipped_unapproved


async def upload_document_to_assistant(
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    assistant_id: str,
    file_path: Path,
) -> Dict[str, Any]:
    """Upload a document to an assistant via POST /assistants/{assistant_id}/documents."""
    url = f"{base_url.rstrip('/')}/assistants/{assistant_id}/documents"
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "PahaarPulse-Knowledge-Ingest/1.0",
    }

    mime_type, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type or "application/octet-stream"

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": (file_path.name, file_bytes, mime_type)}

    try:
        response = await client.post(url, headers=headers, files=files)
    except httpx.RequestError as e:
        raise DocumentIngestionError(f"HTTP request error during upload of '{file_path.name}': {e}") from e

    if response.status_code >= 400:
        raise DocumentIngestionError(
            f"Backboard upload error (HTTP {response.status_code}): {response.text}"
        )

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise DocumentIngestionError(f"Non-JSON response from Backboard upload: {response.text}") from e

    doc_id = data.get("document_id") or data.get("id")
    if not doc_id:
        raise DocumentIngestionError(f"Backboard upload response missing document ID: {data}")

    return data


async def poll_document_status(
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    document_id: str,
    max_wait_seconds: float = 60.0,
    poll_interval: float = 2.0,
) -> Dict[str, Any]:
    """Poll document indexing status until indexed, error, or timeout."""
    url = f"{base_url.rstrip('/')}/documents/{document_id}/status"
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "PahaarPulse-Knowledge-Ingest/1.0",
    }

    start_time = time.monotonic()
    attempts = 0

    while True:
        attempts += 1
        elapsed = time.monotonic() - start_time
        if elapsed > max_wait_seconds:
            raise DocumentIngestionError(
                f"Indexing timed out after {elapsed:.1f}s for document {document_id}"
            )

        try:
            response = await client.get(url, headers=headers)
        except httpx.RequestError as e:
            raise DocumentIngestionError(f"HTTP error polling document status: {e}") from e

        if response.status_code >= 400:
            raise DocumentIngestionError(
                f"Error response polling document {document_id} (HTTP {response.status_code}): {response.text}"
            )

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise DocumentIngestionError(f"Invalid JSON polling document status: {response.text}") from e

        status = data.get("status", "").lower()
        if status == "indexed":
            return data
        elif status == "error":
            err_msg = data.get("error_message") or data.get("error") or "Unknown indexing failure"
            raise DocumentIngestionError(f"Backboard document indexing failed: {err_msg}")

        # Still pending or processing
        await asyncio.sleep(poll_interval)


async def execute_live_ingestion(
    documents_to_upload: List[Dict[str, Any]],
    kb_dir: Path,
    state_file: Path,
    settings: BackboardSettings,
    http_client: Optional[httpx.AsyncClient] = None,
    poll_timeout: float = 60.0,
    poll_interval: float = 2.0,
) -> Tuple[int, int]:
    """Execute live upload and indexing against Backboard. Returns (success_count, fail_count)."""
    if not settings.is_configured:
        raise MissingCredentialsError(
            "Live ingestion requires BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID."
        )

    state_data = load_ingestion_state(state_file)
    success_count = 0
    fail_count = 0

    client_context = (
        http_client if http_client is not None else httpx.AsyncClient(timeout=settings.timeout_seconds)
    )

    # Use existing client or manage new client lifecycle
    manage_client = http_client is None
    client = client_context if not manage_client else await client_context.__aenter__()

    try:
        for doc in documents_to_upload:
            doc_id = doc["id"]
            filename = doc["filename"]
            file_path = kb_dir / filename
            sha256 = doc["content_sha256"]

            print(f"\n--> Uploading {doc_id} ({filename})...")
            try:
                upload_res = await upload_document_to_assistant(
                    client=client,
                    base_url=settings.base_url,
                    api_key=settings.api_key,
                    assistant_id=settings.assistant_id,
                    file_path=file_path,
                )
                bb_doc_id = upload_res.get("document_id") or upload_res.get("id")
                print(f"    Uploaded successfully. Remote doc ID: {bb_doc_id}")
                print(f"    Polling indexing status (timeout: {poll_timeout}s)...")

                status_res = await poll_document_status(
                    client=client,
                    base_url=settings.base_url,
                    api_key=settings.api_key,
                    document_id=bb_doc_id,
                    max_wait_seconds=poll_timeout,
                    poll_interval=poll_interval,
                )

                chunks = status_res.get("chunks", 0)
                print(f"    [INDEXED] Successfully indexed into {chunks} chunks.")

                # Update state
                state_data["documents"][doc_id] = {
                    "filename": filename,
                    "content_sha256": sha256,
                    "backboard_document_id": bb_doc_id,
                    "status": "indexed",
                    "chunks": chunks,
                    "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                save_ingestion_state(state_file, state_data)
                success_count += 1

            except Exception as e:
                print(f"    [FAILED] {e}")
                state_data["documents"][doc_id] = {
                    "filename": filename,
                    "content_sha256": sha256,
                    "status": "error",
                    "error_message": str(e),
                    "failed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                save_ingestion_state(state_file, state_data)
                fail_count += 1

    finally:
        if manage_client:
            await client.__aexit__(None, None, None)

    return success_count, fail_count


def print_dry_run_summary(
    to_upload: List[Dict[str, Any]],
    already_indexed: List[Dict[str, Any]],
    skipped_unapproved: List[Dict[str, Any]],
    manifest_path: Path,
    kb_dir: Path,
    state_file: Path,
) -> None:
    """Print structured, human-readable dry-run execution plan."""
    print("=" * 78)
    print("PAHAARPULSE - KNOWLEDGE BASE INGESTION PLAN (DRY RUN)")
    print("=" * 78)
    print(f"Manifest Path:   {manifest_path}")
    print(f"Knowledge Base:  {kb_dir}")
    print(f"State File:      {state_file}")
    print("-" * 78)

    print("\n1. APPROVED DOCUMENTS PENDING UPLOAD / INDEXING:")
    if to_upload:
        for doc in to_upload:
            print(f"  [+] {doc['id']:<8} | {doc['filename']:<45} | {doc['title'][:35]}...")
            print(f"      SHA256: {doc['content_sha256'][:16]}... | Size: {doc.get('size_bytes', 0)} bytes")
    else:
        print("  (None -- all approved documents are already indexed and up-to-date)")

    print("\n2. UP-TO-DATE INDEXED DOCUMENTS (SKIP):")
    if already_indexed:
        for doc in already_indexed:
            print(f"  [=] {doc['id']:<8} | {doc['filename']:<45} | Hash matches local state")
    else:
        print("  (None)")

    print("\n3. SKIPPED NON-APPROVED CANDIDATES (GATED):")
    for doc in skipped_unapproved:
        status = doc['approval_status']
        fn = doc.get('filename') or "<no local file>"
        print(f"  [-] {doc['id']:<8} | [{status:<14}] | {fn:<28} | {doc['title'][:30]}")

    print("-" * 78)
    print(f"SUMMARY: {len(to_upload)} pending upload, {len(already_indexed)} up-to-date, {len(skipped_unapproved)} gated/skipped.")
    print("=" * 78)
    print("[DRY RUN COMPLETE] Zero remote network calls were executed.")
    print("To execute live upload, specify '--live' and ensure valid credentials in environment.")
    print("=" * 78)


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="PahaarPulse Knowledge-Base Ingestion Utility for Backboard RAG Assistant."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to knowledge_base_manifest.json",
    )
    parser.add_argument(
        "--kb-dir",
        type=Path,
        default=DEFAULT_KB_DIR,
        help="Directory containing approved Markdown documents",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_FILE,
        help="Path to ingestion_state.json recording indexed hashes",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Strict opt-in required to perform live remote API uploads.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Re-upload approved documents even if hash matches state.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Max polling timeout in seconds per document during live indexing.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds during live status checks.",
    )

    args = parser.parse_args()

    try:
        # 1. Load manifest
        manifest_data = load_manifest(args.manifest)

        # 2. Validate manifest and check file hashes / path safety
        validated_docs = validate_document_manifest(manifest_data, args.kb_dir)

        # 3. Load state and determine execution plan
        state_data = load_ingestion_state(args.state_file)
        to_upload, already_indexed, skipped_unapproved = build_execution_plan(
            documents=validated_docs,
            state_data=state_data,
            force=args.force,
        )

        # 4. Handle Dry Run vs Live
        if not args.live:
            print_dry_run_summary(
                to_upload=to_upload,
                already_indexed=already_indexed,
                skipped_unapproved=skipped_unapproved,
                manifest_path=args.manifest,
                kb_dir=args.kb_dir,
                state_file=args.state_file,
            )
            return 0

        # Live mode requested
        print("=" * 78)
        print("PAHAARPULSE - LIVE KNOWLEDGE BASE INGESTION (GATED)")
        print("=" * 78)
        print("NOTICE: Live document upload and indexing may incur Backboard provider charges.\n")

        settings = BackboardSettings()
        print(f"Target Base URL:     {settings.base_url}")
        print(f"Target Assistant ID: {redact_secret(settings.assistant_id)}")
        print(f"API Key:             {redact_secret(settings.api_key)}")
        print(f"Documents to Upload: {len(to_upload)}")

        if not settings.is_configured:
            print("\n[ERROR] Missing required credentials for live Backboard ingestion.")
            print("Please set BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID in backend/.env or your shell environment.")
            return 1

        if not to_upload:
            print("\nAll approved documents are already indexed and up-to-date. Nothing to upload.")
            return 0

        successes, failures = asyncio.run(
            execute_live_ingestion(
                documents_to_upload=to_upload,
                kb_dir=args.kb_dir,
                state_file=args.state_file,
                settings=settings,
                poll_timeout=args.timeout,
                poll_interval=args.poll_interval,
            )
        )

        print("\n" + "=" * 78)
        print(f"INGESTION COMPLETED: {successes} succeeded, {failures} failed.")
        print("=" * 78)
        return 0 if failures == 0 else 1

    except (ManifestValidationError, PathTraversalError, MissingCredentialsError) as e:
        print(f"\n[VALIDATION ERROR] {e.__class__.__name__}: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e.__class__.__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
