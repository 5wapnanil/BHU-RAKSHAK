# PahaarPulse — Backboard Knowledge Base Ingestion Guide

**Phase:** Phase 2, Milestone 4B: Controlled Knowledge-Base Ingestion  
**Component:** PahaarPulse Landslide Knowledge Assistant  
**Date:** October 23, 2026  
**Status:** IMPLEMENTED & OFFLINE VERIFIED (LIVE CALLS GATED)

---

## 1. Executive Summary & Principles

The PahaarPulse Landslide Knowledge Assistant utilizes Retrieval-Augmented Generation (RAG) to provide scientifically grounded answers regarding slope stability, geotechnical triggers, GIS terrain mapping, satellite remote sensing, and early warning systems.

To guarantee that the assistant only cites authorized, peer-reviewed scientific literature and approved disaster management protocols, knowledge base ingestion is controlled via an explicit, audited ingestion pipeline.

### Core Non-Negotiable Rules

1. **Dry-Run by Default:** Without the explicit `--live` CLI flag, the ingestion script only validates manifests, verifies local file hashes, reports planned actions, and exits with code 0 without creating network sockets or contacting remote APIs.
2. **Manifest Governance:** Every knowledge candidate must be documented in `backend/data/knowledge_base_manifest.json`. Only documents explicitly designated with `approval_status: "APPROVED"` and `approved_for_ingestion: true` are uploaded.
3. **Cryptographic Idempotency:** Every file has its SHA-256 hash computed before ingestion. If the hash matches `backend/data/ingestion_state.json` with status `"indexed"`, re-upload is skipped unless `--force` is requested.
4. **Path Traversal Protection:** All referenced files must resolve strictly within `backend/data/knowledge_base/`. Relative traversals (`../`) or absolute path escapes are rejected immediately.
5. **Zero Fabrication:** External documents without verified local source files (e.g. proposed NDMA guidelines) are tracked as `PENDING_REVIEW` with `approved_for_ingestion: false`. Text is never fabricated.
6. **Isolated Operation:** Ingestion never runs on application server startup and does not modify PostgreSQL database tables or alter emergency response routes.

---

## 2. Manifest Schema & Document Catalog

The authoritative document catalog is maintained in [`backend/data/knowledge_base_manifest.json`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/data/knowledge_base_manifest.json).

### Schema Specification

```json
{
  "manifest_version": "1.0",
  "generated_at": "ISO-8601 Timestamp",
  "description": "PahaarPulse Knowledge-Base Manifest",
  "knowledge_base_directory": "knowledge_base",
  "documents": [
    {
      "id": "DOC-001",
      "filename": "01_why_do_landslides_happen.md",
      "title": "Why Do Landslides Happen? Understanding the Signals Before Failure",
      "slug": "why-do-landslides-happen",
      "summary": "Overview of physical mechanisms, slope equilibrium, and rainfall triggers.",
      "category": "LANDSLIDE SCIENCE",
      "author": "LRM Research Team",
      "published_at": "2026-08-15",
      "source_path": "frontend/src/data/articles.ts",
      "approval_status": "APPROVED",
      "approved_for_ingestion": true,
      "content_sha256": "c874935e569322dbfb7b0d30dc02b9c5afb50fb6eadfd1a19c847d5d0de40138",
      "size_bytes": 2804,
      "format": ".md",
      "mime_type": "text/markdown",
      "provenance": "internal verified",
      "license": "Proprietary / Internal Research & Educational",
      "use_cases": ["Slope stability queries", "Pore-water pressure physics"],
      "domain_tags": ["landslide_science", "geotechnical", "slope_stability"]
    }
  ]
}
```

### Approved Knowledge Corpus (Tier 1)

| Doc ID | Stable Filename | Title | Category | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DOC-001** | `01_why_do_landslides_happen.md` | Why Do Landslides Happen? | LANDSLIDE SCIENCE | `c874935e...0de40138` | **APPROVED** |
| **DOC-002** | `02_how_gis_turns_terrain_data_into_risk_maps.md` | How GIS Turns Terrain Data into Maps | GIS & REMOTE SENSING | `e8f7d969...7598e43` | **APPROVED** |
| **DOC-003** | `03_how_machine_learning_predicts_landslide_risk.md` | How Machine Learning Predicts Risk | ARTIFICIAL INTELLIGENCE | `9cbdf24a...f25401bb` | **APPROVED** |
| **DOC-004** | `04_why_rainfall_and_soil_moisture_matter.md` | Why Rainfall & Soil Moisture Matter | ENVIRONMENTAL MONITORING | `b0d4ee03...8da64819` | **APPROVED** |
| **DOC-005** | `05_watching_landscape_from_space.md` | Watching the Landscape from Space | SATELLITE MONITORING | `86fd86f7...31d753db` | **APPROVED** |
| **DOC-006** | `06_from_risk_maps_to_early_warning.md` | From Risk Maps to Early Warning | EARLY WARNING | `34785ac8...09a04197` | **APPROVED** |

### Gated & Rejected Candidates (Tiers 2 & 3)

- **DOC-007** (`NDMA Guidelines`): `PENDING_REVIEW` (`approved_for_ingestion: false`). External statutory document awaiting official PDF download and legal verification.
- **DOC-008** (`GSI Susceptibility Mapping SOP`): `PENDING_REVIEW` (`approved_for_ingestion: false`). Awaiting government release clearance.
- **DOC-009** (`Community Evacuation Handbook`): `PENDING_REVIEW` (`approved_for_ingestion: false`). Awaiting state disaster authority sign-off.
- **DOC-010** (`sensor_readings.csv`): `REJECTED` (`approved_for_ingestion: false`). Raw high-frequency numeric telemetry unsuitable for narrative text RAG.
- **DOC-011** (`weather_scrape.log`): `REJECTED` (`approved_for_ingestion: false`). Unstructured ephemeral worker logs.

---

## 3. How to Add or Update Knowledge Documents

### Step 1: Author the Markdown Document

1. Create a clean UTF-8 encoded Markdown file under `backend/data/knowledge_base/<filename>.md`.
2. Include YAML frontmatter at the top of the file:
   ```yaml
   ---
   document_id: "DOC-00X"
   title: "Descriptive Document Title"
   slug: "url-friendly-slug"
   category: "PRIMARY CATEGORY"
   author: "Author or Organization"
   published_at: "YYYY-MM-DD"
   source: "Attribution Source"
   license: "Explicit License Type"
   provenance: "internal verified | official public authority"
   approval_status: "APPROVED"
   version: "1.0"
   ---
   ```
3. Use structured Markdown headings (`## H2`, `### H3`) and concise, informative paragraphs for optimal chunking by Backboard's hybrid search engine.

### Step 2: Compute SHA-256 Digest

Run PowerShell or Python to compute the exact hash and file size:

```powershell
python -c "
import hashlib, sys
p = 'backend/data/knowledge_base/<filename>.md'
data = open(p, 'rb').read()
print('SHA256:', hashlib.sha256(data).hexdigest())
print('Bytes:', len(data))
"
```

### Step 3: Update `knowledge_base_manifest.json`

Add the entry to the `documents` array with `approval_status: "APPROVED"` and `approved_for_ingestion: true`. Ensure the SHA-256 hash and size match your file.

### Step 4: Run Dry-Run Validation

```powershell
python backend/scripts/ingest_knowledge_base.py
```

The script will validate the manifest syntax, check that the file exists, verify that the SHA-256 matches, and report the pending document in the execution plan.

---

## 4. Ingestion CLI Commands & Operation

The ingestion tool is located at [`backend/scripts/ingest_knowledge_base.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/scripts/ingest_knowledge_base.py).

### 1. Dry Run (Default / Safe Verification)

```powershell
# Standard dry run
python backend/scripts/ingest_knowledge_base.py

# Custom manifest or knowledge base directory
python backend/scripts/ingest_knowledge_base.py --manifest path/to/manifest.json --kb-dir path/to/kb
```

**Expected Behavior:**
- No environment credentials required.
- Inspects all 11 catalogued documents.
- Verifies SHA-256 hashes of all 6 local Markdown files.
- Prints execution plan.
- Exits with code 0.

### 2. Live Ingestion (Strict Opt-In)

Live upload and polling require the `--live` flag and configured credentials:

```powershell
# Prerequisites in backend/.env:
# BACKBOARD_API_KEY=your_backboard_api_key
# BACKBOARD_ASSISTANT_ID=your_target_assistant_id

python backend/scripts/ingest_knowledge_base.py --live
```

**Live Ingestion Lifecycle:**
1. Verifies manifest integrity and credentials.
2. For each pending approved document:
   - Posts file to `POST https://app.backboard.io/api/assistants/{assistant_id}/documents`.
   - Obtains Backboard `document_id`.
   - Polls `GET https://app.backboard.io/api/documents/{document_id}/status` until `indexed`.
3. Atomically writes local indexing state to `backend/data/ingestion_state.json`.

### 3. Advanced CLI Flags

- `--force`: Re-upload and re-index approved documents even if the SHA-256 hash matches the local state.
- `--timeout 120`: Set custom polling timeout ceiling in seconds (default: 60s).
- `--poll-interval 3.0`: Set custom interval between status checks (default: 2.0s).

---

## 5. Ingestion State & Tracking

Local indexing progress and Backboard remote document IDs are tracked in `backend/data/ingestion_state.json`:

```json
{
  "version": "1.0",
  "documents": {
    "DOC-001": {
      "filename": "01_why_do_landslides_happen.md",
      "content_sha256": "c874935e569322dbfb7b0d30dc02b9c5afb50fb6eadfd1a19c847d5d0de40138",
      "backboard_document_id": "bb-doc-uuid-999",
      "status": "indexed",
      "chunks": 14,
      "indexed_at": "2026-10-23T14:45:00Z"
    }
  }
}
```

The state file is written atomically (via temporary file replacement) to prevent file corruption during unexpected interruptions.

---

## 6. Post-Ingestion Verification

After live ingestion is executed:

1. **Verify State File:** Confirm that all 6 documents are listed with `"status": "indexed"`.
2. **Execute Gated Smoke Test:**
   ```powershell
   python backend/scripts/smoke_test_backboard.py --live
   ```
   Verify that the query response includes `retrieved_files` citing one or more of the ingested Markdown files (e.g., `01_why_do_landslides_happen.md`).
3. **Verify API Endpoint:**
   Submit an authenticated query to `POST /api/assistant/query`:
   ```json
   {
     "query": "What happens when pore-water pressure increases in steep mountain soil?",
     "session_token": "<valid_session_token>"
   }
   ```
   Verify that the assistant's answer reflects knowledge from DOC-001 or DOC-004.

---

## 7. Document Retirement & Update Protocol

### Updating an Ingested Document
1. Edit the Markdown file in `backend/data/knowledge_base/`.
2. Recompute SHA-256 and update `knowledge_base_manifest.json`.
3. Run dry run: verify the modified document appears under `APPROVED DOCUMENTS PENDING UPLOAD`.
4. Run live ingestion: the script uploads the new version and updates `ingestion_state.json`.

### Retiring a Document
1. Change `approval_status` in `knowledge_base_manifest.json` from `APPROVED` to `REJECTED`.
2. Set `approved_for_ingestion: false`.
3. Add a clear reason in `review_notes`.
4. Run live script to delete or unlink the remote document from Backboard if required by provider cleanup protocols.
