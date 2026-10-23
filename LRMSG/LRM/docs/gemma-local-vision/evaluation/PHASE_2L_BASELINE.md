# PahaarPulse — Phase 2L: Baseline Verification & Operational Safeguards

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Repository:** `C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM`  
**Operational Status:** BASELINE VERIFIED (Starting Phase 2L Synthetic Workflow Dry Run)

---

## 1. Verified Starting Baseline State

Prior to executing the synthetic dry run, an independent audit of the active repository was conducted:

### 1.1 Dataset & Review Package Inventories
- **Candidate Index (`candidate_index.csv`):** Exactly 102 verified, image-backed candidate records (`ANN_001` through `ANN_102`).
- **Phase 2J Pilot Dataset (`PHASE_2J_PILOT_SELECTION.csv`):** Exactly 10 candidate rows (`PILOT_01` to `PILOT_10`), representing 10 distinct site/event groups and 10 unique SHA-256 hashes.
- **Genuine Annotation Form (`annotation_form.csv`):** Exactly 102 rows; 100% have `review_status = PENDING` with empty reviewer fields.
- **Genuine Adjudication Form (`adjudication_form.csv`):** Exactly 102 rows; 100% have `consensus_status = PENDING` with empty adjudication fields.
- **Pilot Selection Manifest Status:** Exactly 10 rows; 100% have `review_status = PENDING` with empty reviewer fields.
- **Reviewer Recruitment Status:** `AWAITING_REVIEWER_RECRUITMENT` (0 human reviewers recruited, 0 completed reviews, 0 adjudications).

### 1.2 Test Suite State
- **Backend Tests:** Exactly **255 / 255 tests passed** in 1.644s with exit code 0.

### 1.3 Database & System Configuration
- **Active Provider:** `GEMMA_PROVIDER=google` (unchanged).
- **Active Model:** `GEMMA_MODEL=gemini-3.5-flash` (unchanged).
- **Production Uploads:** `backend/uploads/` verified clean with **0** leaked WMC candidate images.
- **PostgreSQL Database Tables (10 tables verified):**
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

## 2. Strict Synthetic-Fixture Isolation Rules

To protect the integrity of the benchmark and prevent data pollution:
1. All generated data must reside exclusively under `backend/tests/fixtures/phase_2l/` or temporary test directories.
2. Identifiers must be explicitly prefixed with `TEST_` (e.g., `TEST_REVIEWER_A`, `TEST_REVIEWER_B`, `TEST_ADJUDICATOR`, `TEST_RUN_001`).
3. Synthetic test records must **never** be written to genuine packages (`phase_2i_annotation_package/`, `PHASE_2J_PILOT_SELECTION.csv`, `phase_2k_reviewer_onboarding/`, or production tables).
4. No synthetic metric will ever be reported as genuine inter-rater reliability.
5. Benchmark inference remains strictly **BLOCKED**.
