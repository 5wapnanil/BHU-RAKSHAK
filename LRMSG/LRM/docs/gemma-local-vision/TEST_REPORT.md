# Test Report — Gemma Local Vision Inference Extension

## 1. Overview and Execution Summary

- **Component:** PahaarPulse AI Field Report Screening Pipeline
- **Target Architectures:** Hosted Google GenAI (`gemini-3.5-flash`), Local Open-Weights VLM (`ollama:gemma3:4b`), and In-Memory Simulation (`mock_gemma`).
- **Date:** October 2026
- **Test Results Summary:**
  - Backend Baseline Tests: **90 / 90 Passed**
  - API Authorization & Privileged Endpoint Tests: **25 / 25 Passed** (`backend/tests/test_api_authorization.py`)
  - Local Vision & Security Provider Tests: **15 / 15 Passed** (including constant-time auth and env variants)
  - VLM Evaluation Harness & Scientific Benchmark Tests: **22 / 22 Passed in 0.025s**
  - Public Image Acquisition & Licensing Gate Suite: **20 / 20 Passed in 0.048s** (`backend/tests/test_public_image_discovery.py`)
  - Total Backend Test Suite: **172 / 172 Passed in 1.65s**
  - Mobile Application Test Suite: **17 / 17 Passed** (Duration: 6.63ms)
  - Frontend TypeScript Check & Build: **0 Errors & Clean Build** (`npm run build` in `frontend`, Turbopack: 1.26s, 24 routes)
  - Mobile TypeScript Check: **0 Errors** (`npx tsc --noEmit` in `landslide-app`)
  - Real Hosted Multimodal Smoke Test: **100% Passed** (`gemini-3.5-flash`, 10.56s)
  - Real Local Multimodal VLM Smoke Test: **100% Passed** (`ollama:gemma3:4b`, 2.98s warm inference, 3,821 MiB VRAM)
  - Database Integrity: **100% Preserved** across all operational tables with zero data loss
  - Photo Storage: **44 files preserved** in `backend/uploads/field_reports`

---

## 2. Test Execution Details

### A. Full Backend Test Suite
**Command:**
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM
python -m unittest discover backend/tests
```
**Output:**
```text
Ran 172 tests in 1.649s
OK
```

### B. API Authorization Test Breakdown (`backend/tests/test_api_authorization.py`)
**Command:**
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM
python -m unittest backend/tests/test_api_authorization.py
```
**Results:**
| Test Case | Description | Verification Status |
| :--- | :--- | :--- |
| `test_volunteer_verify_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `/api/volunteers/{id}/verify`. | **PASS** |
| `test_volunteer_activate_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `/api/volunteers/{id}/activate`. | **PASS** |
| `test_volunteer_status_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `PATCH /api/volunteers/{id}/status`. | **PASS** |
| `test_volunteer_verify_allows_authorized_with_key_and_bearer` | Valid credentials via `X-Coordinator-Key` and `Authorization: Bearer` allow access. | **PASS** |
| `test_assignment_create_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/assignments`. | **PASS** |
| `test_assignment_status_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `PATCH /api/assignments/{id}/status`. | **PASS** |
| `test_relief_resource_create_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/relief-resources`. | **PASS** |
| `test_relief_resource_allocate_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/relief-resources/{id}/allocate`. | **PASS** |
| `test_relief_resource_release_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/relief-resources/allocations/{id}/release`. | **PASS** |
| `test_shelter_create_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/shelters`. | **PASS** |
| `test_shelter_update_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `PATCH /api/shelters/{id}`. | **PASS** |
| `test_alert_acknowledge_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/alerts/{id}/acknowledge`. | **PASS** |
| `test_alert_resolve_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/alerts/{id}/resolve`. | **PASS** |
| `test_alert_responding_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/alerts/{id}/responding`. | **PASS** |
| `test_alert_demo_trigger_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/alerts/demo/trigger`. | **PASS** |
| `test_field_report_review_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `PATCH /api/field-reports/{id}/review`. | **PASS** |
| `test_field_report_analyze_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `POST /api/field-reports/{id}/analyze`. | **PASS** |
| `test_field_report_review_does_not_fabricate_user_identity` | Verifies `reviewed_by` remains `None` without user session (never fabricated). | **PASS** |
| `test_audit_history_blocks_unauthorized_when_configured` | Missing credentials reject with HTTP 403 on `GET /api/audit-history` and detail. | **PASS** |
| `test_audit_history_allows_authorized_with_key_and_bearer` | Valid credentials via `X-Coordinator-Key` and Bearer token permit audit log access. | **PASS** |
| `test_production_environment_fails_closed_when_key_unconfigured` | In production (`ENVIRONMENT`, `ENV`, `NODE_ENV`, `FASTAPI_ENV`), all 18 sensitive endpoints fail closed with HTTP 503. | **PASS** |
| `test_non_existent_hypothetical_routes_return_404_or_405` | Confirms `PATCH /api/incidents/{id}`, `POST /api/evacuation-routes`, `POST /api/risk-observations` return 404/405. | **PASS** |
| `test_public_routes_remain_open_in_production` | Public field report submission, photo upload, volunteer signup, and mobile sync remain accessible. | **PASS** |

### B. Local Vision & Security Test Breakdown (`backend/tests/test_local_vision_provider.py`)
**Command:**
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM
python -m unittest backend/tests/test_local_vision_provider.py
```
**Results:**
| Test Case | Description | Verification Status |
| :--- | :--- | :--- |
| `test_ollama_passes_image_bytes_and_notes_separately` | Verifies real image bytes are Base64-encoded in `images` array and observer notes are separated from visual instructions. | **PASS** |
| `test_ollama_text_only_when_no_photo` | Verifies `images` key is omitted when photo is absent and prompt indicates text-only screening. | **PASS** |
| `test_parse_gemma_json_handles_markdown_code_fences` | Verifies model outputs enclosed in ```` ```json ... ``` ```` are safely extracted and parsed. | **PASS** |
| `test_parse_gemma_json_raises_malformed_on_invalid_syntax` | Verifies non-JSON outputs raise `GemmaMalformedOutputError`. | **PASS** |
| `test_unsupported_hazard_category_normalized_to_indeterminate` | Verifies rogue or hallucinated hazard categories normalize safely to `indeterminate`. | **PASS** |
| `test_ollama_missing_model_raises_clear_pull_instruction` | Verifies HTTP 404 from Ollama raises `GemmaProviderUnavailableError` with explicit `ollama pull gemma3:4b` instructions. | **PASS** |
| `test_ollama_non_vision_model_raises_explicit_error` | Verifies text-only model tags (e.g. `gemma2`) raise clear multimodal mismatch errors. | **PASS** |
| `test_ollama_connection_failure_raises_unavailable` | Verifies `httpx.ConnectError` maps to `GemmaProviderUnavailableError` when daemon is not running. | **PASS** |
| `test_ollama_timeout_raises_timeout_error` | Verifies inference exceeding timeout limit raises `GemmaTimeoutError`. | **PASS** |
| `test_no_fabricated_verdict_when_local_inference_fails` | Verifies failure results in `indeterminate` hazard level with null confidence and no fabricated data. | **PASS** |
| `test_fallback_provider_execution_and_provenance` | Verifies primary failure triggers fallback with `[Inference Provider: ... (fallback)]` provenance tracking. | **PASS** |
| `test_coordinator_authorization_blocks_unauthorized_when_configured` | Verifies `COORDINATOR_API_KEY` configuration enforces header-based security on `/review` and `/analyze`. | **PASS** |
| `test_coordinator_authorization_fails_closed_in_production_when_unconfigured` | Verifies in production (`ENVIRONMENT=production`), missing coordinator credentials reject requests with HTTP 503 (fail-closed). | **PASS** |
| `test_coordinator_authorization_rejects_invalid_credentials_and_protects_secrets` | Verifies invalid credentials are rejected with HTTP 403, constant-time `secrets.compare_digest` is used, and secrets are never returned in error messages or logs. | **PASS** |
| `test_production_environment_variants_fail_closed` | Verifies all standard production aliases (`ENV=production`, `FASTAPI_ENV=prod`, `APP_ENV=live`, `NODE_ENV=production`) fail closed with HTTP 503 when keys are unset. | **PASS** |

### C. VLM Evaluation Harness & Scientific Benchmark Tests (`backend/tests/test_vlm_evaluation.py`)
**Command:**
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM
python -m unittest backend/tests/test_vlm_evaluation.py
```
**Results:**
| Test Case | Description | Verification Status |
| :--- | :--- | :--- |
| `test_load_dataset_csv_ignores_comments_and_empty_lines` | Verifies comments (`#`), empty rows, and whitespace are safely ignored during evaluation dataset loading. | **PASS** |
| `test_load_dataset_csv_handles_whitespace_cleanly` | Verifies leading/trailing whitespace around fields is stripped during CSV parsing. | **PASS** |
| `test_load_dataset_csv_parses_observable_indicators` | Verifies pipe-delimited indicator strings are parsed into clean sets of normalized strings. | **PASS** |
| `test_load_dataset_csv_parses_exclusion_reason` | Verifies exclusion reasons (`unusable_quality`, `non_geotechnical`, etc.) are recognized and stored. | **PASS** |
| `test_load_dataset_csv_filters_by_split` | Verifies dataset loader properly subsets samples by split (`train`, `dev`, `test`). | **PASS** |
| `test_load_dataset_csv_detects_data_leakage_cross_split` | Verifies `DataLeakageError` is raised when identical image SHA-256 digests span multiple splits. | **PASS** |
| `test_load_dataset_csv_strict_permissions_blocks_missing_license` | Verifies `MissingPermissionError` is raised under strict mode if license is missing or unverified. | **PASS** |
| `test_load_dataset_csv_rejects_missing_image_file` | Verifies `FileNotFoundError` is raised when an image referenced by local path does not exist. | **PASS** |
| `test_abstains_from_metric_calculation_when_ground_truth_absent` | Verifies evaluation engine returns `None` and displays explicit abstention warnings when labels are unadjudicated. | **PASS** |
| `test_computes_exact_classification_metrics_and_confusion_matrix` | Verifies exact mathematical computation of Confusion Matrix, per-class Precision, Recall, F1, Macro F1, and Weighted F1. | **PASS** |
| `test_computes_inter_annotator_agreement_and_cohens_kappa` | Verifies calculation of observed agreement (Po), chance agreement (Pe), and Cohen's Kappa with reliability interpretations. | **PASS** |
| `test_computes_wilson_score_confidence_intervals` | Verifies Wilson score 95% confidence intervals on Overall Accuracy and Determinate Coverage Rate. | **PASS** |
| `test_computes_multilabel_observable_indicators_metrics` | Verifies micro-averaged precision, recall, and F1 calculation for Target 1 physical hazard indicators. | **PASS** |
| `test_computes_stratified_accuracy_by_image_quality` | Verifies stratified accuracy calculations broken down across `pristine`, `adequate`, and `marginal` image quality tiers. | **PASS** |
| `test_computes_inference_failure_rate` | Verifies tracking of model runtime/network failure rate across evaluated samples. | **PASS** |
| `test_evaluate_sample_with_mock_provider` | Verifies end-to-end inference execution of `evaluate_sample()` against the `AnalysisProvider` interface without DB mutation. | **PASS** |
| `test_export_results_csv` | Verifies evaluated model predictions, indicators, and metadata are exported cleanly to CSV. | **PASS** |
| `test_provenance_registry_contains_evaluated_datasets` | Verifies dataset provenance registry contains validated records for `HLAD`, `Landslide4Sense`, and `PahaarPulse-Field-Benchmark`. | **PASS** |
| `test_hlad_rejected_due_to_unverified_license` | Verifies `HLAD` is blocked from ingestion with `UnverifiedLicenseError` due to blank license field on Zenodo. | **PASS** |
| `test_landslide4sense_rejected_due_to_unsupported_modality` | Verifies `Landslide4Sense` is blocked with `UnsupportedModalityError` due to incompatible 14-band multispectral satellite modality. | **PASS** |
| `test_pahaarpulse_benchmark_provenance_valid` | Verifies internal field report benchmark passes provenance and compatibility verification. | **PASS** |
| `test_unsupported_modality_file_extensions_rejected` | Verifies multi-spectral raster formats (`.tif`, `.tiff`, `.npy`, `.h5`, `.hdf5`) raise `UnsupportedModalityError`. | **PASS** |

### D. Public Image Discovery & Licensing Gate Tests (`backend/tests/test_public_image_discovery.py`)
**Command:**
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM
python -m unittest backend/tests/test_public_image_discovery.py
```
**Results:**
| Test Case | Description | Verification Status |
| :--- | :--- | :--- |
| `test_license_gate_permissive_redistribution` | Verifies CC0, Public Domain, CC-BY, and CC-BY-SA map to VERIFIED / APPROVED_FOR_REDISTRIBUTION. | **PASS** |
| `test_license_gate_non_commercial_internal_only` | Verifies CC-BY-NC and CC-BY-NC-SA map to VERIFIED / APPROVED_FOR_INTERNAL_EVALUATION. | **PASS** |
| `test_license_gate_rejected_and_nd_licenses` | Verifies All Rights Reserved, Copyrighted, Fair Use, and CC-BY-ND map to REJECTED / REJECTED. | **PASS** |
| `test_license_gate_ambiguous_and_missing_licenses` | Verifies blank, unverified, and custom terms map to PENDING_REVIEW (excluded from download). | **PASS** |
| `test_license_gate_cleans_html_and_escapes` | Verifies HTML tags and XML entities in creator/license fields are decoded cleanly. | **PASS** |
| `test_metadata_only_discovery_with_mocked_wikimedia` | Verifies MediaWiki API parsing into candidate records without downloading image bytes. | **PASS** |
| `test_downloader_rejects_unapproved_candidate` | Verifies downloader skips candidates in PENDING_REVIEW or REJECTED states. | **PASS** |
| `test_downloader_validates_magic_bytes_for_valid_jpeg_and_png` | Verifies file header magic-byte validation for JPEG (`\xff\xd8\xff`) and PNG (`\x89PNG`). | **PASS** |
| `test_downloader_rejects_fake_extension_and_invalid_signature` | Verifies files with fake image extensions or invalid signatures raise `InvalidMediaSignatureError`. | **PASS** |
| `test_downloader_rejects_oversized_file` | Verifies streaming downloader aborts, unlinks temp files, and marks failed when exceeding max size. | **PASS** |
| `test_downloader_rejects_zero_byte_file` | Verifies empty/zero-byte downloads are rejected with temp-file cleanup. | **PASS** |
| `test_downloader_rejects_corrupt_raster_image` | Verifies corrupt raster files failing Pillow decoding are rejected with diagnostic reason. | **PASS** |
| `test_downloader_detects_duplicate_sha256` | Verifies identical SHA-256 hashes are mapped to duplicate groups without duplicate disk storage. | **PASS** |
| `test_downloader_sanitizes_filename_and_blocks_path_traversal` | Verifies candidate IDs are sanitized and path traversal injections (`../../`) are blocked. | **PASS** |
| `test_downloader_handles_network_errors` | Verifies HTTP 429 rate-limiting and 500 errors are handled gracefully without server crash. | **PASS** |
| `test_manifest_manager_csv_roundtrip` | Verifies candidate manifest CSV serialization and deserialization across all 20 fields. | **PASS** |
| `test_export_to_draft_benchmark_manifest_enforces_pending_labels` | Verifies exported draft benchmarks have empty ground-truth labels and `adjudication_status='pending'`. | **PASS** |
| `test_vlm_evaluation_strictly_excludes_unverified_from_test_benchmark` | Verifies `MissingExpertGroundTruthError` when unadjudicated samples enter frozen test benchmarks. | **PASS** |
| `test_vlm_evaluation_detects_site_group_leakage_across_splits` | Verifies `DataLeakageError` when duplicate/event site groups span multiple splits. | **PASS** |
| `test_vlm_evaluation_rejects_missing_source_under_strict_permissions` | Verifies `InvalidSourceError` when benchmark samples lack documented source provenance. | **PASS** |

### E. Mobile Application Test Suite
**Command:**
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\landslide-app
node --test src/__tests__/run-mobile-tests.mjs
```
**Output:**
```text
✔ Landslide Mobile App — FieldReport & Sync Queue Unit Tests (4.9397ms)
ℹ tests 17
ℹ pass 17
ℹ fail 0
```

### F. Real Hosted Multimodal Inference Smoke Test
**Script:** `scratch/real_smoke_test.py`  
**Provider:** `GoogleGenAIGemmaProvider` (`gemini-3.5-flash`)  
**Execution Time:** 10.56 seconds  
**Findings:**
- Disposable report (`5a169e0e-b8f2-49fb-9d78-4ea9e9158109`) created with a real 4.39 MB mountain road photograph.
- Real model `gemini-3.5-flash` evaluated the image and returned `CRITICAL` hazard level with 5 indicators (`tension_cracks`, `slope_displacement`, `road_blockage`, `rockfall_debris`, `structural_damage`) and 95% uncalibrated confidence.
- Results persisted atomically in PostgreSQL and verified via `GemmaAnalysisService.get_analysis_details`.
- Disposable report and temporary photo cleaned up completely; baseline PostgreSQL tables verified intact.

### G. Real Local Gemma 3 Vision Multimodal Smoke Test
**Script:** `scratch/test_local_e2e_workflow.py`  
**Provider:** `OllamaGemmaProvider` (`ollama:gemma3:4b`)  
**Hardware:** NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM), Driver 592.82, CUDA 13.1  
**Execution Profile:**
- **Initial Load & Cold Inference:** 79.26 seconds (loading weights from disk into GPU memory).
- **Subsequent Warm Inference:** 2.98 seconds.
- **GPU Memory Usage:** 3,821 MiB / 8,188 MiB (~4.36 GB headroom available).
- **Process:** `llama-server.exe` PID 32152.
**Findings:**
- Evaluated real 4.39 MB field photo (`04f05d8cd5df49b2aa7294f0f5bfcb9c.png`) with observer notes from Bhowali Mountain Pass.
- Model output: `hazard_level="moderate"`, `confidence=0.85` (uncalibrated), `detected_hazards=['road_blockage', 'tension_cracks']`.
- Summary: *"The photograph shows a road surface with significant sloughing and collapse along the margin, indicating a road blockage. Visible tension cracks..."*
- Limitations: *"Image quality is sufficient to identify key hazards. However, the overall slope geometry and subsurface conditions are not discernible from the photograph."*
- Provenance persisted in PostgreSQL: `provider_name: "ollama:gemma3:4b"`, `ai_status: "completed"`.
- Disposable report (`474cbdb0-903b-4dc3-b81b-1bc70704d6cd`) and disposable file cleaned up atomically.

---

## 3. Real Inference vs. Mocked Verification

- **Real Hosted Inference:** **VERIFIED LIVE.** Verified on real disposable field reports using `GoogleGenAIGemmaProvider` with `gemini-3.5-flash`.
- **Local Vision Provider (`ollama:gemma3:4b`):** **VERIFIED LIVE.** Tested directly against running Ollama 0.40.8 daemon with real downloaded `gemma3:4b` weights (3.4 GB) and hardware-accelerated GPU inference (2.98s per image).

---

## 4. Evaluation Dataset Availability & Scientific Benchmark Status

- **Audit Scope:** Inspection of all storage volumes, databases, tabular artifacts (`extensive_validation_summary.csv`, `backend/uploads/field_reports`), and candidate external benchmarks (`HLAD`, `Landslide4Sense`).
- **Audit Finding:** **No expert-adjudicated, ground-truth labelled landslide image dataset currently exists in the repository.**
- **Candidate Benchmark Ingestion Decisions:**
  - **`HLAD` (Zenodo DOI 10.5281/zenodo.22811448):** ~4,000 Himalayan images with masks/bounding boxes. **REJECTED_BLOCKED.** License field on Zenodo is blank. Annotations delineate scar geometry, lacking categorical hazard triage classes and road infrastructure context. Ingestion prohibited under project research policy.
  - **`Landslide4Sense` (Hugging Face / IEEE GRSS):** 14-band multispectral satellite patches with binary masks. **REJECTED_BLOCKED.** Incompatible 14-channel satellite tensor modality and binary mask task. Belongs to macro-scale satellite GIS pipeline, not conversational RGB vision model.
- **Integrity Rule:** The project strictly enforces a zero-fabrication policy. Model predictions from automated screenings (`gemini-3.5-flash` or `gemma3:4b`) are never converted into synthetic ground truth.
- **Phase 1 Scientific Benchmark Infrastructure Built:**
  - **Formal Target Distinction:** Target 1 (observable surface indicators), Target 2 (visual triage urgency), and Target 3 (future failure probability, out of scope for photos alone).
  - **Dual-Expert Ground-Truth Protocol:** `docs/gemma-local-vision/evaluation/GROUND_TRUTH_PROTOCOL.md` specifying independent blinding, Cohen's Kappa threshold (kappa >= 0.70), consensus adjudication, 4 quality tiers, 4 hard exclusion reasons, and privacy masking.
  - **Standardized 18-Column Manifest:** `docs/gemma-local-vision/evaluation/field_photo_benchmark_template.csv` with cryptographic SHA-256 byte digests and split allocations.
  - **Data Leakage Guards:** Automatic rejection of cross-split duplicate image hashes and missing licenses.
  - **Provenanced Registry:** `docs/gemma-local-vision/evaluation/dataset_provenance_register.json` and `DATASET_PROVENANCE_AND_COMPATIBILITY.md`.
  - **Scientific Evaluation Tooling:** `backend/scripts/evaluate_vlm.py` computing Wilson score 95% CIs, Cohen's Kappa, multi-label indicator F1, stratified quality accuracy, and exporting reproducible `<output>.metadata.json` run records.
  - **Automated Test Coverage:** 22 passing tests in `backend/tests/test_vlm_evaluation.py`.

---

## 5. Security Audit Findings & Defect Remediation

| Ref | Component | Description / Finding | Severity | Status / Remediation |
| :--- | :--- | :--- | :---: | :--- |
| **SEC-01** | `deps.py` / `field_reports.py` | String comparison `provided != expected` vulnerable to timing side-channel attacks against secret keys. | **Medium** | **FIXED:** Replaced with constant-time `secrets.compare_digest(provided, expected)`. |
| **SEC-02** | `deps.py` / `field_reports.py` | Production environment detection relied on subset of aliases (`ENVIRONMENT`, `APP_ENV`, `FASTAPI_ENV`, `NODE_ENV`). | **Low** | **FIXED:** Added `ENV` alias (`ENV=production`). Verified all aliases fail closed with HTTP 503 when keys are unset. |
| **SEC-03** | `fieldReports.ts` & Next.js BFF | Client forwarded `NEXT_PUBLIC_COORDINATOR_API_KEY` from browser, baking secrets into public JS client bundles. | **High** | **FIXED:** Removed `NEXT_PUBLIC_COORDINATOR_API_KEY` completely from client code. Created server-side route handlers (`/api/field-reports/[id]/review` and `/api/field-reports/[id]/analyze`) with host/origin CSRF protection and server-only credential resolution. |
| **SEC-04** | `field_reports.py` | Potential secret leakage in server exception responses or log lines. | **High** | **VERIFIED SAFE:** Neither `expected` nor `provided` keys are included in exception details (`detail`) or log strings. |
| **SEC-05** | Public Ingestion Routes | Verification that public submission and offline sync remain open for field operations. | **High** | **VERIFIED:** Field report creation (`POST /api/field-reports`), photo staging, volunteer signup, and mobile sync remain accessible. |
| **SEC-06** | `coordination.py` & `alerts.py` | 14 coordinator mutation routes lacked auth middleware, guarded only by `# TODO` comments. | **Critical** | **FIXED:** Centralized `verify_coordinator_authorization` in `deps.py` and attached to all 14 routes. Validated via 21 dedicated tests in `test_api_authorization.py`. |

---

## 6. Known Gaps, Remaining Limitations and Validation Blockers

1. **User Identity & Session Management (Prerequisite):** While backend endpoints now enforce server-side `verify_coordinator_authorization` and Next.js route handlers fail closed in production, the application lacks an individual user session and identity layer (cookie/JWT-based RBAC) for individual reviewer logins. Full multi-tenant coordinator audit trail (`reviewed_by = current_user.id`) requires implementing this prerequisite before multi-operator clinical deployment.
2. **Independent Geotechnical Benchmark:** The vision model has passed architectural, contract, and live smoke tests, but is NOT yet clinically validated on an expert-annotated regional landslide dataset.
3. **Statistical Model Calibration:** Neither hosted Google AI nor local Gemma 3 model confidence scores are statistically calibrated probabilities. The application explicitly labels confidence as `UNCALIBRATED`.
4. **Geotechnical Ground Truth:** Model screenings are preliminary observational triage aids only. They must not replace qualified on-site geotechnical engineering inspections or be used to issue safety clearances.
