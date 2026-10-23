# PahaarPulse — Phase 2F: Benchmark Entry Gates & Operational Readiness Standards

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Subsystem:** Gemma Field-Photo Vision Hazard Screening Benchmark  
**Purpose:** Formal Readiness Criteria Governing Benchmark Inference Execution  

---

## 1. Executive Summary & Gate Architecture

To prevent premature claims of machine learning accuracy, publication of fabricated scorecards, and deployment of unvalidated computer-vision models, PahaarPulse enforces **eleven mandatory Benchmark Entry Gates**.

### 1.1 The Golden Rule of Benchmark Execution
**Real model benchmark inference on the candidate dataset remains strictly BLOCKED until all eleven gates achieve a status of PASS.** Under no circumstances may model predictions be evaluated against pending, unreviewed, or partially adjudicated candidate images.

```
┌────────────────────────────────────────────────────────────────────────┐
│ ELEVEN BENCHMARK ENTRY GATES                                           │
│                                                                        │
│  [G01] Dataset Integrity & Provenance              ──► [ PASS ]        │
│  [G02] Human Annotation Completeness               ──► [ BLOCKED ]     │
│  [G03] Reviewer Qualification & Blind Separation   ──► [ BLOCKED ]     │
│  [G04] Inter-Annotator Agreement & Adjudication    ──► [ BLOCKED ]     │
│  [G05] Class Balance & Matched Negative Controls   ──► [ BLOCKED ]     │
│  [G06] Geographic & Independent-Site Coverage      ──► [ BLOCKED ]     │
│  [G07] Cross-Split Leakage Prevention              ──► [ PASS ]        │
│  [G08] Frozen Test-Set Immutability                ──► [ PASS ]        │
│  [G09] Reproducible Model & Prompt Parameters      ──► [ PASS ]        │
│  [G10] Failure Handling & Abstention Mapping       ──► [ PASS ]        │
│  [G11] Scientific Metrics & Safety-Critical Rules  ──► [ PASS ]        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │ OVERALL BENCHMARK VERDICT: FORMALLY BLOCKED             │
       │ (Tooling ready; awaiting independent human annotations) │
       └─────────────────────────────────────────────────────────┘
```

---

## 2. Gate-by-Gate Specification

---

### Gate 1: Dataset Integrity & Cryptographic Provenance
- **Objective:** Ensure all images are authentic, decodable, and legally cleared for benchmark evaluation.
- **Criteria:**
  - **PASS:** 100% of candidate images exist on disk, pass Pillow bitmap decode verification without truncation, meet minimum resolution ($\ge 400 \times 400\text{ px}$ for pilot, $\ge 800 \times 800\text{ px}$ for expanded set), and have documented open licenses in `license_provenance_audit.csv`.
  - **BLOCKED:** Missing raster files, unverified licenses, or unresolved copyright status.
  - **FAIL:** Corrupted rasters, blank/unverified licenses, or scraping of private/copyrighted data.
- **Current Status:** **PASS** (54/54 candidate images decodable, 174.39 MB, all licenses verified).

---

### Gate 2: Human Annotation Completeness
- **Objective:** Guarantee that all benchmark samples possess verified ground-truth labels before evaluation.
- **Criteria:**
  - **PASS:** 100% of samples in the evaluation benchmark possess completed, non-empty `adjudicated_label` and `observable_indicators` entries. No sample in the evaluation split has `adjudication_status="pending"` or `"pending_review"`.
  - **BLOCKED:** Benchmark contains candidate rows with pending, draft, or incomplete human reviews.
  - **FAIL:** Evaluation metrics calculated over empty or synthetic ground truth.
- **Current Status:** **BLOCKED** (All 54 public candidates are pending human review in `public_benchmark_draft.csv` and `phase_2d_annotations_template.csv`).

---

### Gate 3: Reviewer Qualification & Double-Blind Separation
- **Objective:** Prevent bias, anchoring, and non-expert noise in ground-truth generation.
- **Criteria:**
  - **PASS:** Two independent geotechnical specialists with verified credentials conduct blind reviews using separate form copies. Reviewer IDs follow anonymized institutional formatting (`EXPERT_GEOTECH_01`). Neither reviewer sees the other's responses. Zero AI model interaction during review.
  - **BLOCKED:** Reviewers unassigned, single-annotator workflow, or review forms accessible to both reviewers prior to completion.
  - **FAIL:** AI models used to auto-generate labels, or non-geotechnical annotators labeling slope features.
- **Current Status:** **BLOCKED** (Annotation package finalized; human reviewer recruitment and execution pending).

---

### Gate 4: Inter-Annotator Agreement & Disagreement Resolution
- **Objective:** Validate ground-truth label reliability across independent reviewers before accepting labels.
- **Criteria:**
  - **Statistical Agreement Requirement:**
    - Standard Cohen's Kappa ($\kappa$) is heavily distorted by class imbalance (the **Feinstein & Cicchetti Paradox**, where high observed agreement produces paradoxically low $\kappa$ due to asymmetrical marginal distributions).
    - Therefore, PahaarPulse mandates a **Tripartite Agreement Assessment**:
      1. Observed Percentage Agreement ($P_o$): $P_o \ge 75.0\%$
      2. Cohen's Kappa ($\kappa$): $\kappa \ge 0.60$ (Moderate to High agreement)
      3. Gwet's $AC_1$ Index: $AC_1 \ge 0.70$ (Resistant to marginal prevalence imbalance)
  - **Adjudication Requirement:** 100% of material disagreements must be formally resolved by a third Senior Adjudicator with written rationale in `adjudication_form.csv`. Original reviewer entries must remain preserved.
  - **PASS:** Tripartite agreement criteria satisfied and all disagreements resolved.
  - **BLOCKED:** Disagreement analysis pending or unresolved conflicts remain.
  - **FAIL:** Forcing consensus by coin-toss, majority vote without expert rationale, or discarding minority reviews without record.
- **Current Status:** **BLOCKED** (Awaiting completion of dual independent reviews).

---

### Gate 5: Class Coverage & Matched Roadside Negative Controls
- **Objective:** Prevent shortcut learning and guarantee statistically meaningful support across all 5 hazard classes.
- **Criteria:**
  - **PASS:** Benchmark contains $\ge 40$ verified samples in each of the four determinate classes (`low`, `moderate`, `high`, `critical`), plus a calibrated abstention suite ($\ge 30$ samples of `indeterminate`). Negative controls (`low`) must include at least 25 ground-level roadside cut slopes and retaining structures, eliminating the mountain pass vista bias.
  - **BLOCKED:** Classes with $< 10$ samples, or negative controls composed exclusively of panoramic landscapes.
  - **FAIL:** Imbalanced evaluation where zero negative controls exist or where entire classes are absent.
- **Current Status:** **BLOCKED** (Current 54 candidates have severe class imbalance: 2 tension cracks, and 100% of negative controls are panoramic passes).

---

### Gate 6: Geographic & Independent-Site Coverage
- **Objective:** Ensure the benchmark accurately reflects Indian Himalayan Region (IHR) conditions.
- **Criteria:**
  - **PASS:** At least $40\%$ of the benchmark samples originate from verified IHR corridors (Uttarakhand, Himachal Pradesh, Sikkim). The benchmark spans at least 150 independent geographic sites/events ($M \ge 150$).
  - **BLOCKED:** $< 20\%$ IHR representation, or $> 50\%$ of candidates concentrated in foreign non-tectonic mountain ranges.
  - **FAIL:** Single-event benchmark (e.g., all photos from one slope or one rainfall storm).
- **Current Status:** **BLOCKED** (Currently only 2 of 54 candidates [3.7%] are from the IHR).

---

### Gate 7: Cross-Split Site & Event Leakage Prevention
- **Objective:** Eliminate spatial and temporal autocorrelation between training/prompting and test splits.
- **Criteria:**
  - **PASS:** All candidate images are assigned a `duplicate_group_id`. `VLMEvaluationHarness.validate_split_integrity()` verifies that zero duplicate hashes or site groups span multiple splits.
  - **BLOCKED:** Unmapped duplicate relationships or ambiguous site groups.
  - **FAIL:** Identical slope photographed from different angles appearing in both train/prompt and test splits.
- **Current Status:** **PASS** (Split isolation enforced and regression-tested via `test_cross_split_site_group_leakage_detection`).

---

### Gate 8: Frozen Test-Set Immutability & Manifest Hashing
- **Objective:** Prevent post-hoc dataset manipulation, test-set pruning, or cherry-picking.
- **Criteria:**
  - **PASS:** Dataset manifest is cryptographically frozen with SHA-256 digest recorded in `EvaluationRunManifest`. `EvaluationResultLogger.verify_manifest_integrity()` runs prior to any inference and halts with `ManifestHashMismatchError` if the manifest is altered.
  - **BLOCKED:** Benchmark manifest unhashed or mutable.
  - **FAIL:** Modifying test dataset composition after seeing model predictions.
- **Current Status:** **PASS** (Infrastructure fully implemented and tested in `test_manifest_tamper_detection_raises_mismatch_error`).

---

### Gate 9: Reproducible Model & Inference Parameter Freezing
- **Objective:** Guarantee deterministic, repeatable evaluation executions.
- **Criteria:**
  - **PASS:** Model parameters locked to `temperature=0.0`, `top_p=1.0`, `timeout_seconds=30.0`. Prompt template locked to a version-controlled string (`prompt_version="v2.1"`). Zero live prompt tuning during benchmark runs.
  - **BLOCKED:** Unfrozen temperature ($T > 0$) or unversioned prompts.
  - **FAIL:** Manually tweaking prompts on test samples to inflate accuracy.
- **Current Status:** **PASS** (Frozen parameters embedded in `EvaluationRunManifest` and runner).

---

### Gate 10: Robust Failure Handling & Abstention Mapping
- **Objective:** Prevent unhandled API crashes and reward appropriate model abstention.
- **Criteria:**
  - **PASS:** Deterministic mapping implemented in `EvaluationResultLogger`:
    - `GemmaMalformedOutputError` $\rightarrow$ `execution_status="malformed_output"`, `predicted_hazard="indeterminate"`
    - `GemmaTimeoutError` $\rightarrow$ `execution_status="timeout"`, `predicted_hazard="indeterminate"`
    - `GemmaRateLimitError` $\rightarrow$ `execution_status="rate_limit"`, logged for backoff
    - Model abstention (`hazard_level="indeterminate"`) correctly tracked in Determinate Coverage Rate.
  - **BLOCKED:** Unhandled exceptions causing pipeline crashes or silent dropouts.
  - **FAIL:** Treating inference failures as `low` hazard or deleting failed predictions from scorecards.
- **Current Status:** **PASS** (Implemented and tested in `test_execution_statuses_handling`).

---

### Gate 11: Scientific Metrics & Safety-Critical Rules
- **Objective:** Report mathematically sound metrics with confidence intervals and life-safety false-negative tracking.
- **Criteria:**
  - **PASS:** Metrics include Macro-F1, Weighted-F1, Confusion Matrix, asymmetric Wilson score 95% CIs on accuracy and coverage, and dedicated Safety-Critical Under-Call Rate. Deployment pipelines require:
    $$\text{Safety-Critical Under-Call Rate} \le 5.0\%$$
    Zero metrics fabricated when ground truth is absent.
  - **BLOCKED:** Metrics calculated without confidence intervals or missing safety under-call analysis.
  - **FAIL:** Suppressing false negatives or reporting overall accuracy on severely imbalanced test sets without per-class breakdowns.
- **Current Status:** **PASS** (Implemented and tested in `test_safety_critical_under_call_metrics`).

---

## 3. Operational Gate Status Matrix

| Gate | Category | Requirement | Current Status | Blocker Description |
| :---: | :--- | :--- | :---: | :--- |
| **G01** | Dataset Integrity | Decodable rasters, open licenses | **PASS** | 54/54 verified, 174.39 MB |
| **G02** | Annotation Completeness | 100% expert ground truth | **BLOCKED** | All 54 candidates pending human review |
| **G03** | Reviewer Qualification | Independent dual geotechnical review | **BLOCKED** | Qualified human reviewers not yet engaged |
| **G04** | Inter-Annotator Agreement | Tripartite agreement ($P_o \ge 75\%$, $\kappa \ge 0.60$, $AC_1 \ge 0.70$) | **BLOCKED** | Awaiting dual independent submissions |
| **G05** | Class Balance & Controls | $\ge 40$ per class, matched roadside controls | **BLOCKED** | Confounded controls, tension crack shortage |
| **G06** | Geographic Coverage | $\ge 40\%$ IHR, $\ge 150$ independent sites | **BLOCKED** | Currently 3.7% IHR representation |
| **G07** | Leakage Prevention | Atomic site/event cluster splits | **PASS** | `validate_split_integrity()` passing |
| **G08** | Manifest Immutability | Frozen SHA-256 manifest hash | **PASS** | `EvaluationRunManifest` implemented |
| **G09** | Model Parameters | $T=0.0$, timeout 30s, locked prompt | **PASS** | Freezing enforced in logger |
| **G10** | Failure Handling | Deterministic status mapping | **PASS** | All execution statuses mapped & tested |
| **G11** | Metrics & Safety | Wilson CIs, under-call rate $\le 5\%$ | **PASS** | Metrics engine implemented & tested |

---

## 4. Final Verdict & Formal Recommendation

- **Infrastructure & Software Gates (G01, G07, G08, G09, G10, G11):** **ALL PASS (6/6).** The backend evaluation harness, manifest security, failure handlers, and statistical metrics engines are production-ready.
- **Scientific Data & Human Review Gates (G02, G03, G04, G05, G06):** **ALL BLOCKED (5/5).** The candidate dataset lacks human ground-truth labels, possesses severe geographic deficits (3.7% IHR), and requires dataset expansion and dual-expert adjudication.
- **Final Determination:** **BENCHMARK EXECUTION FORMALLY BLOCKED.**  
  No model accuracy scores, capability percentages, or deployment clearances may be issued until the five scientific data gates achieve PASS status through Phase 3 dataset expansion and independent geotechnical adjudication.
