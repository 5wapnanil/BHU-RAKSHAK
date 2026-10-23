# PahaarPulse — Phase 2H: Dataset Reconciliation Report

**Document Version:** v1.0  
**Audit Completion Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Lead Authority:** Senior Computer-Vision Engineer, Geotechnical Data-Quality Researcher, ML Evaluation Specialist, and Backend Safety Engineer  
**Status:** Audit Complete & Verified  

---

## 1. Executive Summary & Audit Scope

Phase 2H performs a rigorous, read-only scientific data-quality audit and cross-batch reconciliation across the baseline public image collection (Phase 2A–2F) and the newly acquired Phase 2G collection. 

The audit establishes exact counts, resolves cross-manifest relationships, audits physical disk presence, identifies bit-for-bit and perceptual duplicates, establishes site/event clustering boundaries, and evaluates human-annotation readiness without modifying production databases, altering operational configurations, or executing premature model evaluations.

### 1.1 Non-Negotiable Safeguards Compliance
- **Database Non-Destructiveness:** Production PostgreSQL tables (`lrm_db`) were audited using read-only SQL queries. All 10 tables have **zero** modifications, truncations, or migrations.
- **Production Storage Isolation:** Zero candidate files exist in `backend/uploads/` or any production upload path.
- **Provider & Model Invariance:** `backend/.env` preserves `GEMMA_PROVIDER=google` and `GEMMA_MODEL=gemini-3.5-flash` with zero configuration changes or credential exposure.
- **Evaluation Gate:** Real benchmark inference and model training remain strictly **BLOCKED**.

---

## 2. Verified Baseline & Manifest Reconciliation Table

### 2.1 Artifact Reconciliation Summary

| Artifact Under Audit | Repository Path | Recorded Count | Actual Count | Discrepancy | Root Cause & Scientific Action |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Baseline Candidate Manifest** | `docs/.../public_image_candidates.csv` | 63 | 63 | 0 | None. Verified baseline manifest intact. |
| **Baseline Disk Rasters** | `data/public_candidates/images/` | 54 | 54 (174.39 MB) | 0 | None. 54 images verified, 100% raster integrity. |
| **Baseline License Audit** | `docs/.../license_provenance_audit.csv` | 63 | 63 | 0 | None. Upstream API audit records intact. |
| **Draft Benchmark Manifest** | `docs/.../public_benchmark_draft.csv` | 54 | 54 | 0 | None. All 54 point to baseline images; all labels empty (`pending`). |
| **Phase 2G Candidate Manifest** | `docs/.../phase_2g_candidates.csv` | 60 | 60 | 0 | None. Bounded acquisition manifest intact. |
| **Phase 2G Disk Rasters** | `data/public_candidates/batch_2g/` | 53 | 53 (155.08 MB) | 0 | None. 53 images verified, 100% raster integrity. |
| **Phase 2G License Audit** | `docs/.../phase_2g_license_audit.csv` | 60 | 60 | 0 | None. Upstream API audit records intact. |
| **Combined Image Files on Disk** | `images/` + `batch_2g/` | 107 | 107 (329.47 MB) | 0 | 54 baseline files + 53 batch_2g files. |
| **Unique Physical Images on Disk** | Cross-directory SHA-256 | 107 (assumed) | **103** | **-4** | **Reconciliation finding:** Exactly 4 candidate files exist in both directories (`WMC_14428956`, `WMC_21449778`, `WMC_37943355`, `WMC_37943361`). Bit-for-bit identical hashes. |
| **Unique Candidate Records** | Manifest union | 123 (63 + 60) | **117** | **-6** | **Reconciliation finding:** 6 candidate IDs appear in both baseline and Phase 2G manifests due to query overlap. |
| **Records Without Downloaded Images** | Gated candidates | 16 (9 + 7) | **14** | **-2** | 2 of the non-downloaded unsuitable records (`WMC_43428262`, `WMC_43470710`) appear in both manifests. |
| **Orphan Files on Disk** | Unreferenced rasters | 0 | 0 | 0 | Verified: 100% of files on disk match a manifest record. |

---

## 3. Detailed Cross-Batch Reconciliation Analysis

### 3.1 Overlapping Candidate Records ($N=6$)
Six candidate records appear in both [`public_image_candidates.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/public_image_candidates.csv) and [`phase_2g_candidates.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2g_candidates.csv):

1. **`WMC_14428956` ("Tension cracks - geograph.org.uk - 1705880.jpg"):**
   - **Baseline:** Retrieved under query `tension_cracks` on 2026-10-22. Stored in `images/WMC_14428956.jpg` (92,494 bytes).
   - **Phase 2G:** Retrieved under query `tension_crack_slope` on 2026-10-23. Preserved in `batch_2g/WMC_14428956.jpg` (92,494 bytes).
   - **Integrity:** SHA-256 `0901468aa2f1554f5e2056fadaec8c05a6561642dde3807e1676743146b6e95e` (Bit-for-bit identical).
   - **Resolution in Phase 2H:** Grouped as single candidate under `GPS_53.34_-3.88` (Conwy, Wales).
2. **`WMC_21449778` ("Häven Kuhstall Dachstuhl.JPG"):**
   - **Baseline & Phase 2G:** Discovered via keyword matching on Wikimedia Commons. Stored in both directories (3,532,697 bytes, SHA-256 `d4a57cdfb5c9...`).
   - **Critical Audit Finding:** The image depicts an interior timber barn roof truss in Häven, Germany. Irrelevant to geotechnical slope failure triage.
   - **Resolution in Phase 2H:** Reclassified from `CANDIDATE` to `UNSUITABLE` (`EXCLUDED_UNSUITABLE`). Quarantined from annotation packages.
3. **`WMC_37943355` ("Clearing rocks after a landslide (3803032169).jpg"):**
   - **Baseline & Phase 2G:** Roadside rock clearing along Rohtang Pass, Himachal Pradesh (GPS: 32.566501, 77.050459). Stored in both directories (3,389,813 bytes, SHA-256 `c96913f44f74...`).
   - **Resolution in Phase 2H:** Reconciled as confirmed site cluster `Himachal_Rohtang_Pass_Clearing` with partner image `WMC_37943361`.
4. **`WMC_37943361` ("Clearing rocks after a landslide (3803035281).jpg"):**
   - **Baseline & Phase 2G:** Companion photograph to `WMC_37943355` taken seconds apart at GPS: 32.566503, 77.050465. Stored in both directories (3,575,463 bytes, SHA-256 `973f32c7b0de...`).
   - **Resolution in Phase 2H:** Reconciled as confirmed site cluster `Himachal_Rohtang_Pass_Clearing`.
5. **`WMC_43428262` ("Breeder and sportsman (1898) (20222428449).jpg"):**
   - **Baseline & Phase 2G:** Scanned page from an 1898 sporting magazine via Internet Archive Book Images. Excluded from download by both batches (`UNSUITABLE`, `PENDING_REVIEW`).
6. **`WMC_43470710` ("The Antarctic manual for the use of the expedition of 1901 (1901) (20748294826).jpg"):**
   - **Baseline & Phase 2G:** Scanned page from a 1901 expedition manual. Excluded from download by both batches (`UNSUITABLE`, `PENDING_REVIEW`).

---

## 4. Audit of Non-Downloaded Candidate Records ($N=14$)

Of the 117 unique candidates, exactly 14 records have no downloaded image on disk. The audit verified that all 14 exclusions were legitimate and enforced by pipeline gates:

| Candidate ID | License Status | Suitability Status | Gate Exclusion Reason | Title Summary |
| :--- | :--- | :--- | :--- | :--- |
| `WMC_107274804` | `PENDING_REVIEW` | `REQUIRES_QUALITY_REVIEW` | `aerial_perspective_requires_ground_triage_review` | Atami debris flow aerial survey |
| `WMC_15496737` | `LICENSE_VERIFIED` | `UNSUITABLE` | `satellite_remote_sensing_annotated_imagery` | NASA EO-1 Taiwan satellite map |
| `WMC_155551470` | `LICENSE_VERIFIED` | `REQUIRES_QUALITY_REVIEW` | `dimensions_below_400px` | Franklin D. Roosevelt Lake (low-res) |
| `WMC_43209273` | `PENDING_REVIEW` | `UNSUITABLE` | `historical_printed_document_scan` | Annual report 1910 book scan |
| `WMC_43428262` | `PENDING_REVIEW` | `UNSUITABLE` | `historical_printed_document_scan` | Breeder and sportsman 1898 scan |
| `WMC_43470710` | `PENDING_REVIEW` | `UNSUITABLE` | `historical_printed_document_scan` | Antarctic manual 1901 scan |
| `WMC_43642493` | `PENDING_REVIEW` | `UNSUITABLE` | `historical_printed_document_scan` | Forest physiography 1911 scan |
| `WMC_47592210` | `PENDING_REVIEW` | `CANDIDATE` | `unrecognized_custom_license_requires_legal_review` | Diokno Highway Landslide 2016 (Flickr Attribution) |
| `WMC_58853336` | `LICENSE_VERIFIED` | `UNSUITABLE` | `historical_printed_document_scan` | Historical line drawing scan |
| `WMC_6452102` | `LICENSE_VERIFIED` | `UNSUITABLE` | `extraterrestrial_planetary_satellite_imagery` | NASA Mars gully satellite imagery |
| `WMC_71769303` | `PENDING_REVIEW` | `CANDIDATE` | `unrecognized_custom_license_requires_legal_review` | Sikkim earthquake aerial survey (GODL-India) |
| `WMC_71769307` | `PENDING_REVIEW` | `CANDIDATE` | `unrecognized_custom_license_requires_legal_review` | Sikkim earthquake aerial survey (GODL-India) |
| `WMC_82170773` | `LICENSE_VERIFIED` | `REQUIRES_QUALITY_REVIEW` | `dimensions_below_400px` | Green-Harris retaining wall (low-res) |
| `WMC_95706077` | `LICENSE_VERIFIED` | `REQUIRES_QUALITY_REVIEW` | `dimensions_below_400px` | Collapsed bridge ($225 \times 300\text{ px}$) |

**Conclusion:** Zero files were lost or corrupted due to network failures or unhandled exceptions. All non-downloaded records were deliberately gated due to sub-400px resolution, non-ground optical perspective, historical printed scans, or unverified license terms.

---

## 5. Master Reconciliation Manifest

The complete, unified reconciliation of all 117 records is published in:  
[`PHASE_2H_RECONCILIATION_MANIFEST.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/PHASE_2H_RECONCILIATION_MANIFEST.csv)

### 5.1 Reconciliation Schema (20 Columns)
1. `candidate_id`: Canonical WMC identifier.
2. `batch_origin`: Manifest membership (`baseline_only`, `phase_2g_only`, `both_batches`).
3. `image_filename`: Physical file name on disk.
4. `baseline_path`: Path in `data/public_candidates/images/`.
5. `phase_2g_path`: Path in `data/public_candidates/batch_2g/`.
6. `on_disk_status`: Presence status (`DOWNLOADED_BASELINE`, `DOWNLOADED_BATCH_2G`, `DOWNLOADED_BOTH`, `NOT_DOWNLOADED`).
7. `image_sha256`: Cryptographic SHA-256 digest.
8. `dimensions`: Verified raster dimensions ($W \times H$).
9. `file_size_bytes`: File size on disk.
10. `license_identifier`: License deed string.
11. `license_audit_status`: Standardized license status (`LICENSE_VERIFIED`, `PENDING_REVIEW`, `REJECTED`, `SOURCE_UNVERIFIED`).
12. `intended_use_permission_status`: Pipeline permission status.
13. `scientific_suitability_status`: Evaluated suitability (`CANDIDATE`, `REQUIRES_QUALITY_REVIEW`, `UNSUITABLE`).
14. `candidate_subject`: Discovery query category.
15. `scene_type`: Geomorphic perspective.
16. `approximate_geographic_region`: Geocoded or categorized region.
17. `site_event_group_id`: Stable site/event cluster identifier.
18. `site_event_group_confidence`: Grouping confidence (`CONFIRMED_SITE_EVENT`, `PROBABLE_SITE_EVENT`, `UNKNOWN_SITE_EVENT`).
19. `annotation_readiness`: Annotation status (`CLEARED_FOR_ANNOTATION`, `QUARANTINED_UNRESOLVED_LICENSE`, `EXCLUDED_UNSUITABLE`, `EXCLUDED_NOT_DOWNLOADED`, `EXCLUDED_QUALITY_REVIEW`).
20. `reconciliation_notes`: Specific audit observations and cross-batch notes.

---

## 6. Scientific Integrity Summary

1. **Directly Verified Facts:**
   - 107 image files exist on disk across `data/public_candidates/images/` (54) and `data/public_candidates/batch_2g/` (53).
   - 103 unique physical images exist, with 4 exact duplicate files between directories.
   - 117 unique candidate records exist across both manifests, with 6 overlapping records.
   - 100% of the 103 downloaded images pass Pillow decode verification.
   - 0 orphan files exist on disk.
2. **Actionable Audit Correction:**
   - `WMC_21449778` reclassified from `CANDIDATE` to `UNSUITABLE` due to non-geotechnical subject matter (barn timber roof truss).
3. **Blockers & Next Steps:**
   - Benchmark inference remains **BLOCKED**.
   - Cleared candidates ($N=102$) require dual-expert geotechnical review and consensus adjudication before inclusion in evaluation splits.
