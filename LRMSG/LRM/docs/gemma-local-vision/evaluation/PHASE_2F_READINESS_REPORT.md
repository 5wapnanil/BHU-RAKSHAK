# PahaarPulse — Phase 2F: Annotation Preparation & Dataset Expansion Readiness Report

**Document Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Milestone:** Phase 2F — Annotation Preparation & Dataset Expansion Readiness  
**Evaluation Subsystem:** Gemma Field-Photo Vision Hazard Screening Benchmark  
**Overall Readiness Verdict:** **PREPARATION COMPLETE — BENCHMARK INFERENCE FORMALLY BLOCKED** pending human ground-truth annotation and Phase 3 expansion.  

---

## 1. Baseline Verification & Non-Destructive Invariance

All baseline claims from Phase 2E were independently inspected and re-verified against the live codebase and PostgreSQL database.

| Verified Dimension | Expected State (Phase 2E) | Observed State (Phase 2F) | Status & Evidence |
| :--- | :--- | :--- | :---: |
| **Active Provider** | `GEMMA_PROVIDER=google` | `GEMMA_PROVIDER=google` | **[VERIFIED]** in `backend/.env` |
| **Active Model** | `GEMMA_MODEL=gemini-3.5-flash` | `GEMMA_MODEL=gemini-3.5-flash` | **[VERIFIED]** in `backend/.env` |
| **Credential Safety** | No hardcoded secrets | Zero API keys or secrets printed or exposed | **[VERIFIED]** Zero leaks |
| **Candidate Rasters** | 54 images, ~174.39 MB | 54 images, 174.39 MB on disk | **[VERIFIED]** in `data/public_candidates/images/` |
| **Raster Integrity** | 100% decodable, $\ge 400\text{ px}$ | 54/54 passed PIL decode; min $480 \times 410\text{ px}$ | **[VERIFIED]** via Pillow test script |
| **Candidate Manifest** | 63 records | 63 records (54 downloaded, 9 skipped) | **[VERIFIED]** in `public_image_candidates.csv` |
| **Provenance Audit** | 63 records | 63 records (57 verified, 6 pending review) | **[VERIFIED]** in `license_provenance_audit.csv` |
| **Draft Benchmark** | 54 rows, unlabeled | 54 rows, 0 labeled, `status="pending"` | **[VERIFIED]** in `public_benchmark_draft.csv` |
| **Annotation Template**| 54 rows, unreviewed | 54 rows, 0 labeled, `status="pending_review"` | **[VERIFIED]** in `phase_2d_annotations_template.csv` |
| **Test Suite Baseline** | 206 / 206 tests passing | 212 / 212 tests passing (+6 targeted tests) | **[VERIFIED]** Python `unittest discover` |

### PostgreSQL Database Invariance Check **[VERIFIED]**
Live database counts were queried from the active PostgreSQL instance:
```
alembic_version:    1
alerts:             6
assignments:        6
audit_history:      177
emergency_requests: 89
field_reports:      3
relief_resources:   15
shelters:           11
users:              2
volunteer_profiles: 1
```
All 10 tables match the verified baseline with zero additions, modifications, or deletions.

---

## 2. Dataset Coverage Audit Findings

Full audit documented in [`PHASE_2F_DATASET_COVERAGE_AUDIT.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/PHASE_2F_DATASET_COVERAGE_AUDIT.md).

### 2.1 Verified Evidence Dimensions
1. **Critical Himalayan Deficit:** **[VERIFIED]** Only 2 of 54 candidate images (3.7%) are from the Indian Himalayan Region (Himachal Pradesh: `GPS_32.57_77.05`), and both belong to the exact same road-clearing series. 96.3% of candidates originate from non-Himalayan geological contexts (Alps, Rockies, Caucasus, Taiwan, Baltics).
2. **Confounding Perspective Bias in Negative Controls:** **[VERIFIED]** 100% of the 10 negative control candidates (`non_landslide_controls`) are panoramic mountain pass vistas (`landscape_pass`). In contrast, 85% of failure candidates are close/mid-range cut slopes (`slope_face`) or roadside scenes (`ground_level_roadside`). This introduces a severe risk of false-positive shortcut learning.
3. **Severe Precursor Indicator Shortage:** **[VERIFIED]** Tension cracks appear in only 2 candidates (3.7%), and road culvert blockage appears in only 1 candidate (1.9%). The pilot dataset over-indexes on post-disaster debris lobes (20.4%) and rockfall scree (18.5%).
4. **Scene Framing Gap:** **[VERIFIED]** Only 8 candidates (14.8%) represent ground-level driver/pedestrian road perspectives (`ground_level_roadside`), despite this being the primary operational modality for citizen field reports.
5. **Site Cluster Concentration:** **[VERIFIED]** 32 of 54 candidates belong to multi-photo clusters or known GPS coordinates, while 22 remain `UNKNOWN_EVENT_OR_SITE`. All multi-photo clusters are isolated into single splits to prevent data leakage.

---

## 3. Human Annotation Package Finalization

Created a clean, dedicated, version-controlled package in [`docs/gemma-local-vision/evaluation/phase_2f_annotation_package/`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/):

| File Name | Purpose & Contents | Verification Status |
| :--- | :--- | :---: |
| [`README.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/README.md) | Package architecture, workflow rules, reviewer qualification standards, and blind-isolation protocol. | **[VERIFIED]** |
| [`annotator_guide.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/annotator_guide.md) | Operational guidelines, required/insufficient evidence per class, handling of `indeterminate`, and epistemic separation. | **[VERIFIED]** |
| [`annotation_form.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/annotation_form.csv) | Form containing exactly 54 candidate IDs and matching SHA-256 hashes with unpopulated reviewer fields (`review_status="pending_review"`). | **[VERIFIED]** |
| [`adjudication_form.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/adjudication_form.csv) | Consensus resolution form preserving original dual reviewer annotations, disagreement typology, and escalation tracking. | **[VERIFIED]** |
| [`review_checklist.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/review_checklist.md) | Pre-submission and adjudication checklist verifying completeness, hash integrity, and controlled vocabulary compliance. | **[VERIFIED]** |

Zero fake reviewer identities, synthetic ground-truth values, or pre-filled labels were created.

---

## 4. Dataset Expansion Plan Priorities

Full expansion plan documented in [`PHASE_2F_DATASET_EXPANSION_PLAN.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/PHASE_2F_DATASET_EXPANSION_PLAN.md).

### 4.1 Expansion Targets for Phase 3
- **Priority 1: Indian Himalayan Highway Corridors (+100 to +120 candidates):** Focus on Uttarakhand (NH-58, NH-107), Himachal Pradesh (NH-3, NH-5), and Sikkim (NH-10). Target: $\ge 40\%$ of total benchmark.
- **Priority 2: Matched Roadside Negative Controls (+40 to +50 candidates):** Stable, engineered road cuts with shotcrete, wire mesh, intact gabions, and clear drainage ditches from ground-level driver perspective (`ground_level_roadside`). Target: $\ge 20\%$ of total benchmark.
- **Priority 3: Precursor Indicators (+40 to +50 candidates):** Open tension cracks on crests/asphalt, active spring seepage patches on cut slopes, and silted culverts.
- **Statistical Benchmark Size Target:** $N = 300 \text{ to } 350$ images across $\ge 180$ independent site clusters, ensuring $\ge 40$ verified samples per class. Margin of error: $\pm 5.6\%$ at 95% confidence.

---

## 5. Benchmark Entry Gates Evaluation

Full criteria documented in [`PHASE_2F_BENCHMARK_ENTRY_GATES.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/PHASE_2F_BENCHMARK_ENTRY_GATES.md).

| Gate | Requirement | Status | Evidence & Blocking Factor |
| :---: | :--- | :---: | :--- |
| **G01** | Dataset Integrity & Decodable Rasters | **PASS** | **[VERIFIED]** 54/54 images decodable, 174.39 MB, open licenses |
| **G02** | 100% Completed Human Ground Truth | **BLOCKED** | **[PENDING INDEPENDENT REVIEW]** 54 rows pending review |
| **G03** | Qualified Reviewers & Double-Blind Protocol | **BLOCKED** | **[PENDING INDEPENDENT REVIEW]** Human experts not yet engaged |
| **G04** | Inter-Annotator Agreement ($P_o \ge 75\%$, $\kappa \ge 0.60$, $AC_1 \ge 0.70$) | **BLOCKED** | **[PENDING INDEPENDENT REVIEW]** Dual submissions pending |
| **G05** | Class Balance & Matched Roadside Controls | **BLOCKED** | **[VERIFIED GAP]** Perspective confound in controls, tension crack deficit |
| **G06** | Geographic Coverage ($\ge 40\%$ IHR, $\ge 150$ sites) | **BLOCKED** | **[VERIFIED GAP]** Only 3.7% IHR representation currently |
| **G07** | Cross-Split Site & Event Leakage Prevention | **PASS** | **[VERIFIED]** Split isolation enforced and tested |
| **G08** | Frozen Test-Set Immutability (SHA-256) | **PASS** | **[VERIFIED]** `EvaluationRunManifest` tamper detection active |
| **G09** | Reproducible Parameters ($T=0.0$, timeout 30s) | **PASS** | **[VERIFIED]** Parameter freezing enforced in harness |
| **G10** | Deterministic Failure & Abstention Mapping | **PASS** | **[VERIFIED]** Status mapping implemented and tested |
| **G11** | Scientific Metrics & Safety Under-Call Rules | **PASS** | **[VERIFIED]** Metrics engine and Wilson CIs tested |

### Overall Verdict
- **Software & Tooling Infrastructure:** **PASS (6/6)**
- **Scientific Data & Human Ground Truth:** **BLOCKED (5/5)**
- **Determination:** **MODEL BENCHMARK INFERENCE IS FORMALLY BLOCKED.**

---

## 6. Unresolved Scientific Questions & Methodological Caveats

1. **Velocity and Kinematic Ambiguity:** **[INFERRED]** A single 2D photograph cannot establish whether displacement is slow creep ($< 1\text{ mm/day}$) or active rapid shear without multi-temporal baseline surveys.
2. **Hydraulic Trigger State:** **[INFERRED]** Visual distress is evaluated at the instant of capture. An identical-looking slope has vastly different stability on a dry day versus under intense monsoon pore-water pressure.
3. **The Feinstein & Cicchetti Kappa Paradox:** **[VERIFIED]** When hazard classes have heavily skewed base rates (e.g., severe mass movements represent $< 10\%$ of general roadside imagery), standard Cohen's kappa yields paradoxically low values despite high observed percentage agreement. Therefore, Gwet's $AC_1$ and observed percentage agreement must accompany kappa.
4. **Fiducial Scale Absence:** **[INFERRED]** Photographs lacking human, vehicle, or infrastructural scale objects introduce uncertainty regarding the physical volume of displaced colluvium.

---

## 7. Verification Test Suite Execution

### 7.1 Targeted Annotation Package Tests
Command executed:
```powershell
Set-Location "C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM"; python -m unittest backend.tests.test_annotation_package
```
Output:
```
......
----------------------------------------------------------------------
Ran 6 tests in 0.008s
OK
```
All 6 tests passed:
- `test_package_files_exist_and_documented`
- `test_annotation_form_schema_and_candidate_mapping`
- `test_adjudication_form_schema_preserves_dual_reviews`
- `test_independent_reviewer_records_remain_separate`
- `test_indeterminate_distinct_from_negative_controls`
- `test_expansion_candidates_cannot_silently_enter_locked_benchmark`

### 7.2 Full Backend Regression Test Suite
Command executed:
```powershell
Set-Location "C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM"; python -m unittest discover backend/tests
```
Output:
```
----------------------------------------------------------------------
Ran 212 tests in 4.083s
OK
```
**212 / 212 tests passed** (100% green; up from 206 baseline with +6 targeted regression tests).

---

## 8. Concrete Human-Review Requirements & Next Steps

### 8.1 Human Review Campaign Execution (Phase 3A)
1. **Recruitment:** Engage two independent qualified geotechnical specialists or engineering geologists.
2. **Reviewer Isolation:** Issue `annotation_form_R1.csv` and `annotation_form_R2.csv` for independent completion without communication or access to model outputs.
3. **Automated Inter-Annotator Agreement:** Execute agreement scripts computing observed agreement, Cohen's kappa, and Gwet's $AC_1$.
4. **Senior Adjudication:** Senior adjudicator resolves all material disagreements in `adjudication_form.csv`.

### 8.2 Staged Dataset Expansion (Phase 3B)
1. Execute gap-driven acquisition targeting 100+ Indian Himalayan road corridor images and 40+ matched roadside negative controls.
2. Verify all new candidates through the license provenance audit prior to downloading.
3. Re-verify the benchmark entry gates once dual ground truth and IHR representation reach the required thresholds.
