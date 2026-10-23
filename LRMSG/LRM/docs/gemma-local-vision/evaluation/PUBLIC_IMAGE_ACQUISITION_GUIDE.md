# Public Landslide Image Discovery, Licensing & Benchmark Ingestion Guide

## 1. Overview & Ethical Mission

This guide details the automated, reproducible, and license-aware workflow for discovering, evaluating, downloading, and preparing public landslide-related photographs for the **PahaarPulse Scientific Evaluation Benchmark**.

### Non-Negotiable Scientific Integrity Rule
> [!IMPORTANT]
> **Candidate discovery is strictly a data-gathering stage and does NOT constitute scientific validation.**
> Discovered metadata (image titles, search queries, uploader tags, or automated descriptions) are unverified claims and must **never** be used as ground-truth hazard labels or to report model accuracy metrics.
> All benchmark ground truth requires independent dual-expert geotechnical review pursuant to [`GROUND_TRUTH_PROTOCOL.md`](./GROUND_TRUTH_PROTOCOL.md).

---

## 2. System Architecture & Ingestion Stages

The public image acquisition pipeline operates in three distinct, decoupled stages:

```
+-------------------------------------------------------------------------------+
| STAGE 1: METADATA-ONLY DISCOVERY (Dry-Run)                                    |
| - Queries Wikimedia Commons MediaWiki API (action=query&generator=search...)  |
| - Discovers metadata across 7 standard geotechnical hazard categories         |
| - Evaluates license against 4-state taxonomy                                  |
| - Populates docs/gemma-local-vision/evaluation/public_image_candidates.csv    |
| - NO full-resolution image downloads                                          |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| STAGE 2: 4-STATE LICENSING GATE                                               |
| - APPROVED_FOR_REDISTRIBUTION: Permissive CC0, Public Domain, CC-BY, CC-BY-SA |
| - APPROVED_FOR_INTERNAL_EVALUATION: CC-BY-NC, CC-BY-NC-SA (internal test only)|
| - PENDING_REVIEW: Ambiguous, unverified, or custom repository terms          |
| - REJECTED: All Rights Reserved, proprietary, CC-BY-ND, fair-use, non-raster |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| STAGE 3: CONTROLLED DOWNLOAD & INTEGRITY VALIDATION                           |
| - Download restricted strictly to APPROVED_* candidates                       |
| - Magic-byte file signature validation (JPEG, PNG, WebP)                      |
| - Maximum file size enforcement (15 MB default) with atomic temp-file cleanup |
| - Pillow raster decoding & non-zero dimension verification                    |
| - SHA-256 byte digest computation & duplicate suppression                    |
| - Path traversal protection (sanitized candidate IDs)                         |
| - Storage outside production uploads (data/public_candidates/images/)         |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| STAGE 4: BENCHMARK MANIFEST INTEGRATION                                       |
| - Exports to 18-column schema (public_benchmark_draft.csv)                    |
| - Sets adjudication_status='pending', ground truth labels EMPTY               |
| - Enforces DataLeakageError and MissingExpertGroundTruthError guards          |
+-------------------------------------------------------------------------------+
```

---

## 3. Standard Search Categories & Visible Indicators

Discovery searches across 8 standardized geotechnical categories:

| Topic Identifier | Search Query | Target Observable Indicators |
| :--- | :--- | :--- |
| `landslide_scars` | `landslide scar` | Depleted slide zones, scarps, exposed bedrock surfaces |
| `roadside_slope_failures` | `landslide blocked road` | Roadway obstruction, toe slumps, carriageway collapse |
| `tension_cracks` | `tension crack slope` | Crown cracks, ground fissures, extensional opening |
| `rockfall_debris` | `rockfall boulder` | Fallen boulders, scree accumulation, talus cones |
| `mudflow_debris_flow` | `debris flow` | Channelized torrents, boulder slurry deposits, mud levees |
| `slope_displacement` | `rotational slide scarp` | Main scarp detachment, terraced displacement steps |
| `water_seepage_drainage` | `water seepage slope` | Saturated toe, piping, perched spring emergence |
| `non_landslide_controls` | `mountain pass road` | Stable mountain corridors, engineered gabions, negative controls |

---

## 4. Licensing Gates & Permission Statuses

Every discovered image is automatically evaluated and assigned two orthogonal attributes:

### A. License Verification Status
1. **`VERIFIED`**: Recognized standardized open-source or Creative Commons license with documented URL.
2. **`UNVERIFIED`**: Blank, empty, or generic license field.
3. **`AMBIGUOUS`**: Unrecognized custom repository terms (e.g. "No restrictions" from Flickr Commons) requiring manual legal vetting.
4. **`REJECTED`**: Proprietary, All Rights Reserved, or non-derivative license.

### B. Intended-Use Permission Status
1. **`APPROVED_FOR_REDISTRIBUTION`**:
   - Licenses: `CC0 1.0`, `Public domain`, `PD-USGS`, `PD-USGov`, `CC-BY-4.0`, `CC-BY-SA-4.0`, `CC-BY-3.0`, `CC-BY-SA-3.0`, `CC-BY-2.0`, `CC-BY-SA-2.0`.
   - Permitted for both local model training/evaluation and inclusion in open-source redistributable benchmarks with attribution.
2. **`APPROVED_FOR_INTERNAL_EVALUATION`**:
   - Licenses: `CC-BY-NC-4.0`, `CC-BY-NC-SA-4.0`, `CC-BY-NC-3.0`.
   - Permitted for internal research and evaluation only. Prohibited from unencumbered public redistribution under Apache-2.0.
3. **`PENDING_REVIEW`**:
   - Missing or ambiguous terms.
   - **Excluded from automated downloads** until manually reviewed and transitioned to `APPROVED_*`.
4. **`REJECTED`**:
   - Licenses: `All rights reserved`, `Copyrighted`, `Fair use`, `CC-BY-ND-4.0`.
   - Blocked from downloading and ingestion.

### C. Scientific Suitability Status
1. **`CANDIDATE`**: Genuine field photograph depicting geological slopes, roads, rocks, or landslides.
2. **`REQUIRES_QUALITY_REVIEW`**: Questionable resolution (e.g. < 640x480), heavy blur, or distant aerial view requiring review.
3. **`UNSUITABLE`**: Historical book scans, printed text pages, geological maps, diagrams, cross-sections, or non-hazard material.
4. **`AWAITING_EXPERT_ANNOTATION`**: Legally approved and downloaded photograph ready for dual-expert review.

---

## 5. Candidate Manifest Specification (28 Columns)

Saved to: `docs/gemma-local-vision/evaluation/public_image_candidates.csv`

| Column Header | Description | Example |
| :--- | :--- | :--- |
| `candidate_id` | Unique stable candidate identifier | `WMC_97705470` |
| `source_repository` | Originating repository | `Wikimedia Commons` |
| `source_page_url` | Search/category source URL | `https://commons.wikimedia.org/wiki/Special:Search?...` |
| `original_image_page_url` | Original file description page | `https://commons.wikimedia.org/wiki/File:Bloc_Lauzet...` |
| `image_title` | Original file title | `Bloc Lauzet P1010012mod.jpg` |
| `creator_attribution` | Author/artist attribution text | `JYB Devot` |
| `license_identifier` | Cleaned license name | `CC BY-SA 4.0` |
| `license_url` | Canonical license link | `https://creativecommons.org/licenses/by-sa/4.0` |
| `license_verification_status` | Verification category | `VERIFIED` |
| `intended_use_permission_status` | Operational intake gate | `APPROVED_FOR_REDISTRIBUTION` |
| `media_type` | Standard MIME type | `image/jpeg` |
| `dimensions` | Pixel resolution ($W \times H$) | `2560x1650` |
| `approximate_geographic_region` | Documented coordinates or region | `Coordinates: 44.441195, 6.414042` |
| `candidate_subject` | Hazard category query | `rockfall_road_blockage` |
| `retrieval_timestamp` | ISO 8601 UTC timestamp | `2026-10-22T20:41:26Z` |
| `download_status` | State of file download | `downloaded` |
| `image_sha256` | 64-character SHA-256 byte hash | `4bb34360b5ef...` |
| `duplicate_group_id` | Cluster ID if identical to another image | `""` |
| `event_site_group` | Physical site / series cluster identifier | `Lauzet_Ubaye_Rockfall` |
| `event_site_confidence` | Site grouping confidence | `CONFIRMED_SITE` |
| `scientific_suitability_status` | Scientific triage status | `CANDIDATE` |
| `scene_type` | Visual scene categorization | `slope_face` |
| `image_quality_assessment` | Objective quality assessment | `high_resolution` |
| `relevance_to_ground_photo_triage`| Hazard triage relevance | `high` |
| `suitability_exclusion_reason` | Exclusion justification if unsuitable | `""` |
| `review_status` | Human intake review status | `unreviewed` |
| `exclusion_reason` | Diagnostic note if skipped/rejected | `""` |
| `direct_download_url` | Resolvable direct master/derivative URL | `https://upload.wikimedia.org/...` |

---

## 6. How to Run Discovery, Auditing, and Ingestion

### Step 1: Discover Metadata Across Topics (Dry-Run / Metadata-Only)
Discovers candidate images across all 8 hazard topics with search generator pagination:
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM
python backend/scripts/discover_public_landslide_images.py discover --limit 10 --append --delay 0.5
```

### Step 2: Run Independent License Provenance Audit
Performs live MediaWiki API queries for all candidates in the manifest and writes `license_provenance_audit.csv`:
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM
python backend/scripts/discover_public_landslide_images.py audit `
    --manifest docs/gemma-local-vision/evaluation/public_image_candidates.csv `
    --output docs/gemma-local-vision/evaluation/license_provenance_audit.csv
```

### Step 3: Migrate Manifest Schema
Safely migrates older manifest CSVs to the latest 28-column format:
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM
python backend/scripts/discover_public_landslide_images.py migrate --manifest docs/gemma-local-vision/evaluation/public_image_candidates.csv
```

### Step 4: Execute Controlled Image Download
Downloads only candidates with `APPROVED_*` status:
```powershell
Set-Location C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM
python backend/scripts/discover_public_landslide_images.py download `
    --download-dir data/public_candidates/images `
    --max-size-mb 15.0 `
    --export-benchmark docs/gemma-local-vision/evaluation/public_benchmark_draft.csv `
    --split dev
```
Safety Guarantees during Download:
1. **Magic-Byte Gate:** Verifies `\xff\xd8\xff` (JPEG), `\x89PNG` (PNG), or `RIFF...WEBP` (WebP). Rejects renamed or malicious payloads.
2. **File Size Gate:** Streaming download breaks and unlinks temporary files if size exceeds `--max-size-mb` (default 15 MB).
3. **Pillow Raster Verification:** Ensures images decode without error and extracts actual pixel dimensions.
4. **Duplicate Suppression:** Computes SHA-256 byte digest during stream. Identical image hashes are recorded as `duplicate_of_<id>` without duplicating files on disk.
5. **Path Traversal Protection:** Sanitizes candidate IDs to `[A-Za-z0-9_-]` and ensures destination paths remain strictly within `data/public_candidates/images/`.
6. **Isolated Storage:** Files are saved under `data/public_candidates/images/`, which is ignored in `.gitignore` and kept separate from operational `backend/uploads/field_reports`.

---

## 7. Moving Images into the Expert-Annotation Workflow

When candidates are downloaded and exported to `docs/gemma-local-vision/evaluation/public_benchmark_draft.csv`:
1. Ground truth columns (`annotator_1_label`, `annotator_2_label`, `adjudicated_label`) are strictly **empty**.
2. `adjudication_status` is explicitly set to **`pending`**.
3. To qualify images for model evaluation:
   - Provide the images to two independent geotechnical specialists.
   - Instruct annotators to score images according to [`GROUND_TRUTH_PROTOCOL.md`](./GROUND_TRUTH_PROTOCOL.md).
   - Enter their blinded ratings in `annotator_1_label` and `annotator_2_label`.
   - Run `evaluate_vlm.py` to verify inter-annotator agreement ($\kappa \ge 0.70$).
   - For divergent samples, convene an adjudication session with a senior geotechnical engineer to set `adjudicated_label` and `adjudication_status = "adjudicated"`.
4. Only adjudicated samples with verified licenses and dual-expert ground truth may be placed in the frozen `test` split.
