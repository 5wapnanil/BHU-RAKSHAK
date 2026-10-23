# PahaarPulse — Gemma Local Vision Inference Technical Specification
## Architecture, Open-Weight Model Selection, Implementation Record, and Verification

---

## 1. Executive Summary

This document specifies the design, implementation, and verification of the **Local Vision Inference Enhancement** for the PahaarPulse Landslide Risk Management System.

PahaarPulse utilizes an AI-assisted observational screening pipeline to triage ground field reports submitted by mobile and web clients in mountainous regions. Previously dependent solely on cloud-hosted Google GenAI endpoints, the system has been extended with an on-premises open-weight Vision-Language Model (VLM) provider powered by **Google Gemma 3 4B (`gemma3:4b`)** via the Ollama runtime.

This enhancement achieves:
1. **Zero Cloud Dependence:** Complete offline operation during severe weather, landslides, or communication blackouts.
2. **Unified Architecture:** Strict reuse of the existing `AnalysisProvider` interface, Pydantic schemas (`GemmaHazardOutput`), background orchestration (`GemmaAnalysisService`), and PostgreSQL storage.
3. **Evidence-Grounded Geotechnical Screening:** Prompt guardrails that separate direct physical photograph evidence from subjective observer notes, prohibit false "safe" clearances, and handle ambiguous views with `indeterminate` ratings.
4. **Resilience & Provenance:** Structured error handling for local VLM states (missing daemon, unpulled model, concurrency saturation, timeouts) with transparent model provenance tracking.
5. **Administrative Security:** Coordinator-only authorization guard enforcing credential checks on review and manual analysis endpoints.

---

## 2. System Architecture & Component Interaction

```
                        +---------------------------------------------+
                        |   Field Report Sources (Web / Mobile App)   |
                        +---------------------------------------------+
                                               |
                                               v
                              +----------------------------------+
                              |    FastAPI REST Endpoints        |
                              |  /api/field-reports [POST / GET] |
                              |  /api/field-reports/{id}/analyze |
                              +----------------------------------+
                                               |
                                               v
                                +------------------------------+
                                |     GemmaAnalysisService     |
                                |  (Orchestration & Atomicity) |
                                +------------------------------+
                                               |
                                +--------------+---------------+
                                |                              |
                                v                              v
                     +----------------------+       +----------------------+
                     | GoogleGenAIGemma     |       |  OllamaGemmaProvider |
                     | Provider (Hosted)    |       |  (Local Vision VLM)  |
                     | - gemini-3.5-flash   |       |  - gemma3:4b         |
                     +----------------------+       +----------------------+
                                |                              |
                                +--------------+---------------+
                                               |
                                               v
                              +----------------------------------+
                              |    Pydantic Schema Validation    |
                              |       (GemmaHazardOutput)        |
                              +----------------------------------+
                                               |
                                               v
                              +----------------------------------+
                              | PostgreSQL Atomic Persistence    |
                              | (field_reports database table)   |
                              +----------------------------------+
```

### Component Roles:
- **`GemmaAnalysisService`:** Orchestrates report processing, prevents duplicate in-flight jobs, loads images from `LocalStorageAdapter`, invokes the active provider, and atomically updates the database.
- **`GoogleGenAIGemmaProvider`:** Hosted adapter using Google's GenAI SDK (`google-genai`) with `gemini-3.5-flash`.
- **`OllamaGemmaProvider`:** Local VLM adapter sending HTTP POST requests to `http://localhost:11434/api/generate` with Base64-encoded image payloads and JSON formatting.
- **`FallbackGemmaProvider`:** Explicit failover wrapper executing the primary provider and gracefully falling back to the secondary provider if configured.
- **`MockGemmaProvider`:** In-memory deterministic heuristic provider for continuous integration and unit testing.

---

## 3. Selected Local Vision Model & Licensing

### Primary Model: Google Gemma 3 4B (`gemma3:4b`)
- **Publisher:** Google DeepMind
- **Model Tag:** `gemma3:4b` (Ollama), `google/gemma-3-4b-it` (Hugging Face)
- **Architecture:** Multimodal Auto-regressive Decoder with native SigLIP vision encoder and 128k context window.
- **Quantized Storage Footprint (Q4_K_M):** ~3.1 GB disk storage.
- **VRAM Requirements:** ~3.8 GB to 4.2 GB VRAM for 2048-token context.
- **Hardware Headroom:** On an NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM), Gemma 3 4B operates fully within GPU memory with ~4 GB VRAM remaining.
- **License:** Gemma Terms of Use (permissive open-weights license permitting commercial deployment under Google's Responsible Use Guidelines).

---

## 4. Evidence-Grounded Geotechnical Screening Rules

The `SYSTEM_PROMPT` enforces strict geotechnical screening boundaries:
1. **Separation of Evidence:** Differentiate directly visible features in the photograph from assertions in observer notes. Only include indicators in `detected_hazards` that are visibly supported by the image.
2. **Conservative Triage & Indeterminate State:** If image quality, lighting, perspective, distance, or vegetation obscures the slope, classify `hazard_level` as `indeterminate`. Never default an uncertain report to `low`.
3. **No Safety Clearances:** Never state or imply that a slope or location is safe, stable, or cleared for occupancy. This analysis is strictly preliminary triage.
4. **Uncalibrated Confidence:** Model-reported confidence is an observational clarity index (0.0 to 1.0), NOT an actuarial or statistically calibrated probability.

---

## 5. Configuration Reference

| Environment Variable | Default | Description |
| :--- | :--- | :--- |
| `GEMMA_PROVIDER` | `google` | Active provider: `google`, `ollama`, or `mock`. |
| `GEMINI_API_KEY` | *None* | Hosted Google AI Studio API key. |
| `GEMMA_MODEL` | `gemini-3.5-flash` | Hosted vision model tag. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama daemon base URL. |
| `OLLAMA_MODEL` | `gemma3:4b` | Local vision model identifier. |
| `OLLAMA_TIMEOUT` | `60.0` | Timeout in seconds for local VLM inference. |
| `GEMMA_ENABLE_FALLBACK`| `false` | Enable explicit secondary failover. |
| `GEMMA_FALLBACK_PROVIDER` | `ollama` | Fallback provider target. |
| `COORDINATOR_API_KEY` | *None* | Shared secret for review/analyze endpoints. |

---

## 6. Verification and Test Results

### Automated Test Runs
1. **Backend Full Test Suite:** **172 / 172 Passed in 1.65s** (`python -m unittest discover backend/tests`)
2. **Public Image Acquisition & Licensing Gate Suite:** **20 / 20 Passed in 0.048s** (`backend/tests/test_public_image_discovery.py`)
3. **API Authorization & Privileged Endpoint Security Suite:** **25 / 25 Passed in 0.45s** (`backend/tests/test_api_authorization.py`)
4. **Local Vision & Security Provider Tests:** **15 / 15 Passed** (`backend/tests/test_local_vision_provider.py`)
5. **VLM Evaluation Harness & Scientific Benchmark Suite:** **22 / 22 Passed in 0.025s** (`backend/tests/test_vlm_evaluation.py`)
6. **Mobile App Suite:** **17 / 17 Passed in 7.03ms** (`node --test src/__tests__/run-mobile-tests.mjs`)
7. **Frontend Typecheck & Production Build:** **0 Errors & Clean Build** (`npm run build` in `frontend`)
8. **Mobile Typecheck:** **0 Errors** (`npx tsc --noEmit` in `landslide-app`)
9. **Real Multimodal Hosted Smoke Test:** **100% Passed** with `gemini-3.5-flash` (10.56s)
10. **Real Multimodal Local VLM Smoke Test:** **100% Passed** with `ollama:gemma3:4b` (2.98s warm inference on NVIDIA RTX 4060 GPU, 3,821 MiB VRAM)
11. **Database Preservation:** **100% Preserved** across all 11 public tables with zero data loss.

---

## 7. Security Audit & Hardening Findings

| Ref | Risk Area | Audit Finding & Impact | Severity | Remediation Applied |
| :--- | :--- | :--- | :---: | :--- |
| **SEC-01** | Timing Attack | Standard string equality (`provided != expected`) susceptible to side-channel key extraction. | **Medium** | Replaced with constant-time `secrets.compare_digest(provided, expected)`. |
| **SEC-02** | Environment Aliasing | Docker/K8s standard `ENV=production` was not checked alongside `ENVIRONMENT`. | **Low** | Added `os.environ.get("ENV")`. Verified all aliases fail closed with HTTP 503 when keys are unset. |
| **SEC-03** | Browser Secret Exposure | `NEXT_PUBLIC_COORDINATOR_API_KEY` was exposed to client-side bundles and forwarded from browsers. | **High** | **REMEDIATED:** Completely removed `NEXT_PUBLIC_COORDINATOR_API_KEY` from client code. Routed reviews and re-analysis through server-side Next.js route handlers (`/api/field-reports/[id]/review` and `/api/field-reports/[id]/analyze`) with origin/CSRF validation, server-only secret resolution, and fail-closed authentication. |
| **SEC-04** | Secret Masking | Potential credential leakage in server logs or HTTP error details. | **High** | Verified safe: neither expected nor provided keys appear in error responses or logs. |
| **SEC-05** | Public Route Protection | Unauthenticated routes must remain accessible for field reporters. | **High** | Verified: public report creation (`POST /api/field-reports`), photo staging (`POST /api/field-reports/upload-photo`), volunteer self-signup, and mobile sync (`/api/sync/upload`) remain open. |
| **SEC-06** | Unprotected Coordination & Audit Routes | 14 coordinator mutation endpoints and 2 audit read endpoints (`GET /api/audit-history`, `GET /api/audit-history/{id}`) were previously unprotected or lacked authorization. | **Critical** | **REMEDIATED:** Centralized `verify_coordinator_authorization` in `deps.py` and enforced on all 16 mutation routes plus 2 audit read endpoints. Tested across 25 denial, constant-time, and fail-closed scenarios. |
| **SEC-07** | Proxy Confused-Deputy & Origin Validation | Next.js server proxies risked being exploited as confused deputies by anonymous callers to execute privileged actions. | **High** | **REMEDIATED:** Added Origin, Host, and Fetch-Metadata validation to both Next.js route handlers. In production, proxies fail closed (HTTP 401) unless explicit coordinator credentials are supplied by the caller, preventing anonymous proxy misuse. |

---

## 8. Scientific Validation Phase 1: Defensible Field-Photo Benchmark & Evaluation Pipeline

### A. Target Task Triad and Geotechnical Boundaries
The scientific validation pipeline establishes formal boundaries between three distinct geotechnical assessment targets:
1. **Target 1: Observable Surface Hazard Indicators (In-Scope, Multi-Label Classification):** Direct visual identification of physical phenomena visible on the surface. Evaluated across 8 standardized indicators: `tension_cracks`, `slope_displacement`, `road_blockage`, `rockfall_debris`, `structural_damage`, `toe_erosion`, `mudflow`, and `water_seepage`.
2. **Target 2: Visual Triage Urgency (In-Scope, Categorical Classification):** Operational triage priority for emergency dispatch and engineer inspection (`low`, `moderate`, `high`, `critical`, `indeterminate`). Governed by conservative geotechnical defaults where obscured slopes default to `indeterminate`.
3. **Target 3: Future Slope Failure Probability (Explicitly Out of Scope for Field Photos):** Quantitative actuarial probability of future slope failure (Pf). Physically impossible to compute from single RGB field photographs alone because it requires subsurface geotechnical boreholes, slope angle/DEM, material shear strength, groundwater pore pressure, and real-time precipitation thresholds. Model confidence scores reflect visual interpretation clarity (0.0 to 1.0) and are explicitly labeled as **uncalibrated**.

### B. Dual-Expert Ground-Truth Annotation Protocol
Documented in `docs/gemma-local-vision/evaluation/GROUND_TRUTH_PROTOCOL.md`:
- **Independent Blinding:** Annotators independently assign labels without seeing model predictions or co-annotator scores.
- **Inter-Annotator Reliability Threshold:** Cohen's Kappa (kappa >= 0.70) required to qualify benchmarks for model evaluation.
- **Consensus Adjudication:** Discrepancies between Annotator 1 and Annotator 2 must be formally resolved by a senior geotechnical engineer, recording `adjudication_status` (`unanimous`, `adjudicated`, `pending`).
- **Quality Stratification:** Samples categorized into 4 tiers: `pristine`, `adequate`, `marginal`, `unusable`.
- **Exclusion Rules:** 4 hard exclusion criteria: `unusable_quality`, `non_geotechnical`, `duplicate_event`, `missing_permission`.
- **Privacy & Safety Safeguards:** Strict masking of faces, license plates, private property, and exclusion of casualties or sensitive disaster imagery.

### C. Standardized 18-Column Benchmark Manifest & Leakage Guards
Implemented in `docs/gemma-local-vision/evaluation/field_photo_benchmark_template.csv`:
- **18 Required Columns:** `image_id`, `image_sha256`, `image_path_or_controlled_reference`, `source`, `license_or_permission_reference`, `capture_date`, `region`, `image_quality`, `observable_indicators`, `annotator_1_id`, `annotator_1_label`, `annotator_2_id`, `annotator_2_label`, `adjudicated_label`, `adjudication_status`, `exclusion_reason`, `split`, `notes`.
- **Cryptographic Image Hashing:** SHA-256 byte digest recorded for every image to guarantee reproducibility and prevent tampering.
- **Data Leakage Guards:** Automatic rejection (`DataLeakageError`) if identical or duplicate SHA-256 digests appear across train, dev, and test splits.
- **Strict Permission Checks:** Automatic rejection (`MissingPermissionError`) when `--strict-permissions` is enabled and licenses/permissions are missing or unverified.

### D. Candidate Benchmark Dataset Compatibility & Provenance Register
External candidate datasets were audited against licensing, modality, and annotation compatibility (`docs/gemma-local-vision/evaluation/DATASET_PROVENANCE_AND_COMPATIBILITY.md` and `dataset_provenance_register.json`):

| Dataset ID | Source & Citation | Modality & Resolution | Annotation Format | License Status | Decision & Suitability Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **HLAD** | Zenodo `10.5281/zenodo.22811448` (~4,000 images) | Optical / UAV RGB photos; Himalayan terrain | Bounding boxes & pixel masks (spatial extents) | **BLANK / UNVERIFIED** on Zenodo | **REJECTED_BLOCKED:** Legal distribution license missing on Zenodo; spatial masks cannot be silently coerced into categorical hazard triage levels. |
| **Landslide4Sense** | Hugging Face / IEEE GRSS Data Fusion | 14-band multispectral satellite rasters ($128 \times 128$) | Binary segmentation masks (0/1 background/scar) | Academic / Non-Commercial | **REJECTED_BLOCKED:** Incompatible remote-sensing raster modality; binary segmentation is an orthogonal task to VLM ground-photo triage. |
| **PahaarPulse-Field-Benchmark** | Internal operational repository | Ground-level oblique RGB field photos (`.jpg`, `.png`) | 5-level categorical hazard severity + 8 indicators | Apache-2.0 / Internal System | **CANDIDATE_PENDING_ADJUDICATION:** Fully compatible schema; blocked on collecting permission-cleared field photos and independent geotechnical expert adjudication. |

### E. Scientific Evaluation Metrics & Reproducible Tooling
Implemented in `backend/app/services/vlm_evaluation.py` and CLI runner `backend/scripts/evaluate_vlm.py`:
- **Wilson Score 95% Confidence Intervals:** Computed for Overall Accuracy and Determinate Coverage Rate.
- **Inter-Annotator Agreement Statistics:** Cohen's Kappa, Observed Agreement (Po), and Chance Agreement (Pe).
- **Multi-Label Indicator Performance:** Precision, Recall, and F1 across Target 1 surface features.
- **Image Quality Stratification:** Breakdown of accuracy across `pristine`, `adequate`, and `marginal` tiers.
- **Coverage & Failure Accounting:** Explicit tracking of Determinate Coverage Rate, Excluded Samples, and Model Inference Failures.
- **Abstention Guarantee:** Harness withholds metric calculations and outputs clear warnings when ground-truth labels are absent.
- **Run Metadata Artifact:** Exports `<output>.metadata.json` capturing timestamp, manifest SHA-256, evaluated split, and full metric summary for scientific reproducibility.

---

## 9. Status Verification Matrix

| Capability / Requirement | Implemented | Automated Tested | Real Model Tested | Security Verified | PDF Verified |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Hosted Google GenAI Vision (`gemini-3.5-flash`) | YES | YES | YES (Live E2E) | YES | YES |
| Local Ollama Vision Provider (`gemma3:4b`) | YES | YES (Contract) | YES (Live E2E: 2.98s, 3.8GB VRAM) | YES | YES |
| Evidence-Grounded Triage Prompt Rules | YES | YES | YES (Live E2E) | YES | YES |
| Provider Fallback & Provenance Tracking | YES | YES | YES (Unit/Integ) | YES | YES |
| Production Fail-Closed Coordinator Guard (18 Endpoints) | YES | YES (25 Tests) | YES (All Mutation Routes + Audit) | YES (Fail-Closed) | YES |
| Server-Only BFF Proxy (Zero Client Secrets) | YES | YES (Next.js Build) | YES (SSR / CSRF Protected) | YES (Origin Enforced) | YES |
| VLM Evaluation Harness & Provenance Guard | YES | YES (22 Tests) | YES (CLI Runner Tested) | YES (Data Isolated) | YES |
| Phase 1 Field-Photo Benchmark Protocol & Template | YES | YES (22 Tests) | YES (Harness Validated) | YES (SHA-256 Hashed) | YES |
| Phase 2A Public Image Discovery & Licensing Gates | YES | YES (20 Tests) | YES (6 Downloaded & Verified) | YES (Magic-Byte / Path Traversal) | YES |

---

## 10. Operational Guide & Remaining Production Blockers

### Operational Commands
- Ollama daemon startup: `& "C:\Users\Swapnanil\AppData\Local\Programs\Ollama\ollama.exe" serve`
- Run evaluation: `python backend/scripts/evaluate_vlm.py --dataset-id pahaarpulse-field-benchmark --dataset docs/gemma-local-vision/evaluation/evaluation_dataset_template.csv --provider ollama`
- Provider selection: `GEMMA_PROVIDER=google` (active hosted default); toggle to `GEMMA_PROVIDER=ollama` for zero-cloud local operation.

### Remaining Production Blockers
1. **User Identity & Session Management (Prerequisite):** While API routes now strictly enforce `verify_coordinator_authorization` and Next.js proxies fail closed in production, the frontend currently lacks an individual user session and identity layer (cookie/JWT-based RBAC) for reviewer logins. Individual reviewer attribution (`reviewed_by = current_user.id`) requires implementing this prerequisite before multi-operator clinical deployment.
2. **Expert Adjudicated Validation Dataset:** Formal clinical/geotechnical field deployment requires independent validation against at least 100+ expert-annotated photographs from Himalayan terrains.
3. **Statistical Model Calibration:** Model-reported confidence is uncalibrated. Temperature scaling or isotonic regression on expert validation data is required before confidence can be treated as an actuarial probability.
4. **Site Geotechnical Verification:** AI screening outputs must always remain preliminary triage aids and never supersede on-site engineering inspection.
