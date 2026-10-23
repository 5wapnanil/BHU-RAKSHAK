# PahaarPulse — Phase 2M: Baseline Verification & Operational Audit

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Repository:** `C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM`  
**Operational Status:** BASELINE AUDITED & VERIFIED (Starting Phase 2M Recruitment & Pilot Launch Readiness)

---

## 1. Verified Baseline Inventory & Audit State

Prior to preparing recruitment materials or introducing launch readiness controls, an exhaustive audit was performed against the live repository state.

### 1.1 Dataset & Image Collection Metrics
- **Candidate Index (`candidate_index.csv`):** Exactly **102 unique image-backed candidate records** (`ANN_001` through `ANN_102`).
  - *Eligibility Criteria:* Ground-level or roadside camera perspective, high-resolution optical raster ($\ge 400\text{ px}$ per dimension), verified open-access licensing (CC BY 2.0, CC BY-SA 2.0/3.0/4.0, Public Domain), absence of non-geological subjects, and deduplicated across batches.
- **Exclusion Register (`exclusion_register.csv`):** Exactly **15 documented exclusions** (14 undownloaded/invalid plus 1 non-geotechnical barn roof truss `WMC_21449778`).
- **Physical Images on Disk:** 54 baseline files (`data/public_candidates/images/`) and 53 Phase 2G files (`data/public_candidates/batch_2g/`), accounting for 103 unique SHA-256 hashes across 107 files on disk (with 4 cross-batch duplicates cleanly deduplicated in `candidate_index.csv`).
- **Phase 2J Pilot Dataset (`PHASE_2J_PILOT_SELECTION.csv`):** Exactly **10 candidate rows** (`PILOT_01` to `PILOT_10`).
  - All 10 active image paths exist on disk.
  - All 10 images match their expected SHA-256 digests.
  - 10 distinct site/event cluster groups (zero multi-image co-dependence within the pilot).
  - All 10 rows have `review_status = PENDING` and empty review conclusion fields.
- **Genuine Annotation Form (`annotation_form.csv`):** Exactly **102 rows**; 100% have `review_status = PENDING` and empty review conclusion fields.
- **Genuine Adjudication Form (`adjudication_form.csv`):** Exactly **102 rows**; 100% have `consensus_status = PENDING` and empty adjudication fields.

### 1.2 Reviewer Recruitment & Onboarding Baseline
- **Recruitment Status:** `AWAITING_REVIEWER_RECRUITMENT`
- **Recruited Reviewers:** **0** (zero real humans recruited).
- **Completed Reviews:** **0** (zero completed reviews).
- **Completed Adjudications:** **0** (zero adjudications).
- **Qualification Criteria:** Tiers 1–3 established in [`reviewer_qualification_criteria.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/reviewer_qualification_criteria.md).

### 1.3 Validation Engine & Workflow Orchestrator Capabilities
- **Validator Tooling ([`validate_human_annotations.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/scripts/validate_human_annotations.py)):**
  - Supported modes: `pilot-selection` (18 columns, all PENDING), `independent-annotation` (12 blinded columns, PENDING or COMPLETED), `adjudication` (13 columns, dual-source inputs required), and `auto`.
  - Default execution: read-only dry-run (`dry_run = True`).
- **Workflow Orchestrator ([`orchestrate_annotation_workflow.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/scripts/orchestrate_annotation_workflow.py)):**
  - Compares two independent reviewer CSVs.
  - Enforces distinct physical files and distinct reviewer IDs (`reviewer_1_id != reviewer_2_id`).
  - Diffs categories, calculates synthetic agreement metrics (labeled `SYNTHETIC_TEST_METRIC — NOT SCIENTIFIC EVIDENCE`), and drafts `adjudication_form_draft.csv`.
  - Overwrite protection enforced by default.

### 1.4 Test Suite Verification
- **Full Backend Test Suite:** Exactly **266 / 266 tests passed** in 1.645s with exit code 0 (`python -m unittest discover backend/tests`).

### 1.5 Database & System Configuration
- **Active Provider:** `GEMMA_PROVIDER=google` in `backend/.env`.
- **Active Model:** `GEMMA_MODEL=gemini-3.5-flash` in `backend/.env`.
- **Production Uploads:** `backend/uploads/` verified clean with **0** leaked WMC candidate images.
- **Production PostgreSQL Database Table Counts (10 tables verified):**
  - `alembic_version`: 1
  - `alerts`: 6
  - `assignments`: 6
  - `audit_history`: 177
  - `emergency_requests`: 89
  - `field_reports`: 3
  - `relief_resources`: 15
  - `shelters`: 11
  - `users`: 2
  - `volunteer_profiles`: 1

---

## 2. Baseline Reconciliation & Discrepancy Findings

| Verification Target | Expected State (from Phase 2L) | Observed Live State | Discrepancy / Action |
| :--- | :--- | :--- | :--- |
| Candidate Image Manifest | 102 rows in `candidate_index.csv` | 102 rows | Confirmed matching. |
| Pilot Selection Manifest | 10 rows, all PENDING | 10 rows, all PENDING | Confirmed matching. |
| Genuine Annotation Package | 102 rows in `annotation_form.csv`, all PENDING | 102 rows, all PENDING | Confirmed matching. Zero synthetic rows. |
| Genuine Adjudication Form | 102 rows in `adjudication_form.csv`, all PENDING | 102 rows, all PENDING | Confirmed matching. Zero synthetic rows. |
| Backend Test Count | 266 tests passing | 266 tests passing | Confirmed matching. |
| Production DB Tables | 10 tables, exact counts | 10 tables, exact counts | Confirmed matching. Zero mutations. |
| Provider & Model Config | `google` / `gemini-3.5-flash` | `google` / `gemini-3.5-flash` | Confirmed matching. |
| Application Uploads | 0 WMC files in `backend/uploads/` | 0 WMC files | Confirmed matching. |

**Conclusion:** The repository is in an exact, unmutated baseline state. No unexplained count differences or schema regressions exist.
