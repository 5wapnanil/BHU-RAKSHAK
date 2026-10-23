# Implementation Log — Gemma Local Vision Inference Enhancement

## Project Overview
PahaarPulse AI/ML Landslide Risk Management System  
Local Vision-Language Model (VLM) Provider Architecture Extension  
Date: October 2026  

---

## Stage 1 — Audit and Baseline Establishment

### 1. Existing System Audit

#### A. Provider Hierarchy & Protocol
- Defined in `backend/app/services/gemma_providers.py`:
  - `AnalysisProvider` Protocol requires:
    - `@property provider_name -> str`
    - `is_available() -> bool`
    - `async def analyze(notes, location_name, photo_bytes, photo_mime) -> GemmaHazardOutput`
  - Existing concrete implementations:
    - `GoogleGenAIGemmaProvider`: Hosted Google GenAI SDK (`google-genai`). Reads `GEMINI_API_KEY` and `GEMMA_MODEL` (defaults to `gemini-2.5-flash`, active model is `gemini-3.5-flash`). Passes images via `types.Part.from_bytes()`.
    - `OllamaGemmaProvider`: Local REST adapter contacting `http://localhost:11434/api/generate`. Reads `OLLAMA_BASE_URL` and `OLLAMA_MODEL` (defaults to `gemma2`).
    - `MockGemmaProvider`: In-memory deterministic heuristic provider for testing. Supports simulation flags (`simulate_timeout`, `simulate_rate_limit`, `simulate_unavailable`, `simulate_malformed`, `simulate_error`).
    - `UnconfiguredGemmaProvider`: Null provider raising `GemmaProviderUnavailableError` when credentials/runtimes are missing.

#### B. Provider Selection Logic
- In `get_gemma_provider()`:
  - Checks `GEMMA_PROVIDER` environment variable: `"mock"`, `"google"`, or `"ollama"`.
  - Fallback autodetection: If `GEMINI_API_KEY` is present -> `GoogleGenAIGemmaProvider`. Else if `OLLAMA_BASE_URL` or `OLLAMA_HOST` is present -> `OllamaGemmaProvider`. Else -> `UnconfiguredGemmaProvider`.
  - Current `.env` configuration: `GEMMA_PROVIDER=google`, `GEMMA_MODEL=gemini-3.5-flash`.

#### C. Model Schema & Output Validation
- Schema: `backend/app/api/schemas/gemma_analysis.py` -> `GemmaHazardOutput`
  - `hazard_level`: Literal `["low", "moderate", "high", "critical", "indeterminate"]` (normalizes `"medium"` -> `"moderate"`, `"severe"` -> `"critical"`).
  - `detected_hazards`: List[str] (observable geotechnical indicators e.g. `tension_cracks`, `slope_displacement`, `rockfall_debris`, `road_blockage`, `structural_damage`, `toe_erosion`, `mudflow`, `water_seepage`).
  - `confidence`: Optional[float] (0.0 to 1.0; documented as uncalibrated model-reported evidence clarity).
  - `summary`: str (observational summary).
  - `limitations`: Optional[str] (explicit caveats or observational uncertainty).
  - Strict JSON format enforced via system prompt and Pydantic validation.

#### D. Orchestration & Persistence
- Service: `backend/app/services/gemma_analysis_service.py` -> `GemmaAnalysisService`
  - Atomically marks `[PROCESSING]` state before dispatching to provider.
  - Skips re-analysis if `ai_analyzed_at` is set (idempotency), unless `force=True`.
  - Clears stale hazards (`ai_detected_hazards = []`) and resets `ai_hazard_level = "indeterminate"` whenever entering processing or encountering temporary/rate-limit provider failures.
  - Catches typed exceptions:
    - `GemmaTemporaryUnavailableError` (HTTP 503 / UNAVAILABLE / high demand spikes) -> `ai_status: "unavailable"`.
    - `GemmaRateLimitError` (HTTP 429) -> `ai_status: "unavailable"`.
    - `GemmaTimeoutError` -> `ai_status: "unavailable"`.
    - `GemmaMalformedOutputError` -> `ai_status: "failed"`.
    - `GemmaProviderUnavailableError` -> `ai_status: "unavailable"`.
  - Updates PostgreSQL `field_reports` table via `FieldReportRepository`.

#### E. Storage & API Routes
- Photo storage: `backend/app/services/photo_storage_service.py` -> `LocalStorageAdapter`
  - Files saved under `backend/uploads/field_reports/<uuid>.<ext>`.
  - Magic byte validation for image mime types (`image/jpeg`, `image/png`, `image/webp`).
- Endpoints (`backend/app/api/endpoints/field_reports.py`):
  - `POST /api/field-reports` (multipart with photo / JSON)
  - `GET /api/field-reports` (listing)
  - `GET /api/field-reports/{id}` (single report)
  - `POST /api/field-reports/{id}/analyze` (manual trigger/retry of AI analysis)
  - `GET /api/field-reports/{id}/ai-analysis` (screening metadata)
  - `PATCH /api/field-reports/{id}/review` (administrative review)
- Authorization status:
  - Endpoints currently lack global RBAC middleware. The review endpoint includes documentation marking it coordinator-only.

#### F. Hardware & Environment Baseline
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU, 8,188 MiB VRAM (Driver 592.82, CUDA 13.1).
- System RAM: 16 GB (16,408,932 KB).
- Storage: Drive C: with 269 GB free space.
- Local runtime status: Ollama is not currently installed on the host. Python environment has `google-genai` and `httpx`; no local PyTorch or Ollama CLI installed.
- Hosted inference: Verified working with `gemini-3.5-flash` on real report `8b625a3b-275b-4d1e-8806-95b692988480`.

#### G. Baseline Test Execution
- Backend: `python -m unittest discover backend/tests`
  - Ran 90 tests in 3.810s.
  - Status: 90 passed, 0 failed.
- Mobile: `node --test src/__tests__/run-mobile-tests.mjs`
  - Ran 17 tests in 7.47ms.
  - Status: 17 passed, 0 failed.


---

## Stage 2 — Open-Weight Vision Model Selection

### 1. Research and Model Evaluation
We conducted an evaluation of open-weight vision-language models capable of local inference on consumer GPU hardware (NVIDIA RTX 4060, 8 GB VRAM):

1. **Google Gemma 3 4B (`gemma3:4b` via Ollama):**
   - **Publisher:** Google DeepMind
   - **Architecture:** Multimodal Auto-regressive Decoder with native SigLIP vision encoder and 128k context window.
   - **Quantized Footprint:** ~3.1 GB disk storage, ~3.8 GB VRAM.
   - **License:** Gemma Terms of Use (permissive open-weights license, commercial use permitted).
   - **Selection Decision:** **Selected as Primary Local VLM.** Direct lineage with Gemma architecture, native multimodal image tokens, fast local inference, and fits comfortably within 8 GB VRAM.

2. **Meta Llama 3.2 Vision 11B (`llama3.2-vision:11b`):**
   - High quality, but requires ~8.8 GB VRAM, causing layer offloading and throttling on 8 GB cards.

3. **Moondream 2 (`moondream:1.8b`):**
   - Lightweight (~1.8 GB VRAM), but exhibits higher hallucination rates on technical geotechnical indicator schemas.

### 2. Environment Safeguard Decision
- Host check revealed `ollama.exe` is not currently installed on PATH.
- In accordance with non-negotiable safeguard rule 9 (*"Do not download a large model, change production configuration, or install unnecessary dependencies without first checking requirements, available disk/RAM/VRAM and the current environment"*), automated large binary downloads were withheld.
- Complete mock-driven integration and contract tests were built to verify all Ollama REST API interactions.

---

## Stage 3 & 4 — Architecture Extension & Evidence-Grounded Screening

### 1. Files Modified
- `backend/app/services/gemma_providers.py`:
  - Upgraded `SYSTEM_PROMPT` to enforce evidence-grounded screening:
    - Rule 1: Differentiate directly visible physical evidence from unverified observer notes.
    - Rule 2: Force `indeterminate` classification if slope features are obscured, poorly lit, or lack scale.
    - Rule 3: Explicit prohibition against issuing "safe" verdicts or clearance declarations.
    - Rule 4: Explicit qualification of confidence score as uncalibrated observational clarity.
  - Added `parse_gemma_json(raw_text: str)` helper handling empty responses, whitespace, and markdown code fences (````json ... ````).
  - Enhanced `OllamaGemmaProvider`:
    - Updated default model identifier to `gemma3:4b`.
    - Added configurable timeout via `OLLAMA_TIMEOUT` (default: 60.0s).
    - Added HTTP 404 handler detecting unpulled models and returning actionable `ollama pull gemma3:4b` instructions.
    - Added HTTP 429 concurrency and HTTP 503 temporary overload mapping.
    - Added connection failure handling mapping `httpx.ConnectError` to `GemmaProviderUnavailableError`.
  - Added `FallbackGemmaProvider`:
    - Provides explicit secondary failover if `GEMMA_ENABLE_FALLBACK=true`.
    - Preserves provenance in summary footer: `[Inference Provider: ... (fallback)]`.
  - Enhanced `MockGemmaProvider`:
    - Added flags for `simulate_missing_model`, `simulate_connection_error`, and `simulate_markdown_json`.
    - Added inspection attributes `last_received_notes`, `last_received_location`, `last_received_photo_bytes`, and `last_received_photo_mime`.

- `backend/app/services/gemma_analysis_service.py`:
  - Updated `get_analysis_details` to parse and surface provider provenance from stored summaries.

- `backend/app/api/endpoints/field_reports.py`:
  - Added `verify_coordinator_authorization` dependency checking `COORDINATOR_API_KEY` (via `X-Coordinator-Key` or `Authorization: Bearer <token>`).
  - Protects `PATCH /api/field-reports/{id}/review` and `POST /api/field-reports/{id}/analyze`.

---

## Stage 5 & 6 — Reliability, Testing & End-to-End Verification

### 1. New Test Suite Implementation
Created `backend/tests/test_local_vision_provider.py` containing 12 unit and integration tests covering:
1. Valid local image inference with mock runtime.
2. Binary image bytes passed in Base64 `images` array.
3. Separation of observer notes from visual evidence instructions.
4. Structured JSON extraction with markdown code fences.
5. Normalization of rogue hazard categories to `indeterminate`.
6. Missing model in Ollama producing `ollama pull` instructions.
7. Non-vision model tags producing clear mismatch error.
8. Connection refused errors producing `GemmaProviderUnavailableError`.
9. Timeout errors producing `GemmaTimeoutError`.
10. Non-fabrication of verdicts on local inference failure.
11. Fallback provider execution and provenance tagging.
12. Coordinator authorization protection on review endpoints.

### 2. Comprehensive Test Verification
- `python -m unittest discover backend/tests`: **103 / 103 Passed in 1.645s**.
- `node --test src/__tests__/run-mobile-tests.mjs`: **17 / 17 Passed in 4.94ms**.
- `npx tsc --noEmit` (frontend): **0 Errors**.
- `npx tsc --noEmit` (landslide-app): **0 Errors**.
- Database records: **100% Preserved** across all operational tables.

---

## Stage 7 — Real Local Vision Model Runtime Deployment & Live Verification

### 1. Ollama Runtime Installation
- **Installer:** Downloaded official Windows installer `OllamaSetup.exe` (v0.40.8).
- **Installed Binary:** `C:\Users\Swapnanil\AppData\Local\Programs\Ollama\ollama.exe`.
- **Daemon Startup:** Launched daemon via background service (`ollama serve`), binding locally to `http://127.0.0.1:11434`.

### 2. Gemma 3 4B Vision Model Pull
- **Command:** `ollama pull gemma3:4b`
- **Layers Downloaded:**
  - Base Auto-regressive Language Model: `f06e91e18fc7` (2.5 GB)
  - Multimodal SigLIP Vision Encoder & Projection: `7a50f9607a47` (851 MB)
  - Total Disk Footprint: 3.4 GB stored under `C:\Users\Swapnanil\.ollama\models`.
- **Registry Tag:** `gemma3:4b:latest` (ID: `68ceab7e468a`).

### 3. Real Local Multimodal VLM Inference Execution
- **Verification Script:** `scratch/test_local_e2e_workflow.py`
- **Test Image:** Real 4.39 MB field photograph (`04f05d8cd5df49b2aa7294f0f5bfcb9c.png`) depicting a mountain road margin collapse with visible tension cracks and debris.
- **Hardware Profile:**
  - GPU: NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM).
  - VRAM Consumption: 3,821 MiB / 8,188 MiB (~4.36 GB headroom available).
  - Compute Process: `llama-server.exe` PID 32152.
- **Execution Performance:**
  - Cold Start & Weights Loading: 79.26s.
  - Warm GPU Inference: **2.98s** (multimodal image token processing + JSON generation).
- **Model Triage Output:**
  - `hazard_level`: `"moderate"`
  - `confidence`: `0.85` (uncalibrated model-reported evidence clarity)
  - `detected_hazards`: `['road_blockage', 'tension_cracks']`
  - `limitations`: *"Image quality is sufficient to identify key hazards. However, the overall slope geometry and subsurface conditions are not discernible from the photograph."*
- **PostgreSQL Persistence:**
  - Persisted in disposable report `474cbdb0-903b-4dc3-b81b-1bc70704d6cd`.
  - Stored `provider_name`: `"ollama:gemma3:4b"`.
  - Atomic cleanup: Disposable test report and temporary file deleted immediately following verification.
  - Zero data loss verified on user report `8b625a3b-275b-4d1e-8806-95b692988480` and all other operational tables.
