# PahaarPulse — Phase 2G: Controlled Dataset Acquisition & Provenance Validation Report

**Document Version:** v1.0  
**Audit Completion Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Lead Authority:** Senior Computer-Vision Engineer, Geotechnical Data-Quality Researcher, ML Evaluation Specialist, and Backend Safety Engineer  
**Status:** Complete, Verified & Archived  

---

## 1. Executive Summary & Baseline Reconciliation

Phase 2G successfully executed an evidence-based, protocol-governed acquisition workflow to systematically address the geographic, morphological, and negative-control deficiencies identified in the Phase 2F evaluation audit.

### 1.1 Baseline Invariant Verification
Prior to making any file modifications or executing discovery workflows, the existing environment was audited and verified:
- **Active AI Configuration:** Verified in `backend/.env` without credential leakage:
  - `GEMMA_PROVIDER = google`
  - `GEMMA_MODEL = gemini-3.5-flash`
  - Zero modifications to active inference providers or model definitions.
- **Production PostgreSQL Database:** Verified against the baseline table counts across all 10 application tables with zero records added, deleted, or migrated:
  - `alembic_version`: 1
  - `alerts`: 6
  - `assignments`: 6
  - `audit_history`: 177
  - `emergency_requests`: 89
  - `field_reports`: 3 (verified consistent with previous baseline audits)
  - `relief_resources`: 15
  - `shelters`: 11
  - `users`: 2
  - `volunteer_profiles`: 1
- **Baseline Candidate Image Archive:** Ingested images in `data/public_candidates/images/` remain strictly immutable:
  - Total files: 54 images
  - Total size: 174.39 MB
  - MD5/SHA-256 integrity: 100% preserved; no files modified or overwritten.
- **Baseline Manifests:** `public_image_candidates.csv` (63 records) and `public_benchmark_draft.csv` (54 records) preserved without modification.

---

## 2. Phase 2G Acquisition Outcomes & Summary Statistics

All Phase 2G candidate discovery, licensing audits, and downloaded rasters were isolated into dedicated, version-controlled artifacts:
- **Phase 2G Candidate Manifest:** [`phase_2g_candidates.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2g_candidates.csv) (60 candidate rows, 28 columns)
- **Phase 2G License Provenance Audit:** [`phase_2g_license_audit.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2g_license_audit.csv) (60 audit rows, 18 columns)
- **Phase 2G Isolated Image Batch:** `data/public_candidates/batch_2g/` (53 verified rasters, 155.08 MB)

### 2.1 Quantitative Breakdown

| Stage / Metric | Count / Value | Details |
| :--- | :--- | :--- |
| **Total Candidates Discovered** | **60 records** | Discovered via rate-limited MediaWiki Search API queries |
| **Permissive Open Licenses** | **56 records (93.3%)** | CC BY (16), CC BY-SA (30), Public domain (10) |
| **Quarantined / Pending Review Licenses** | **4 records (6.7%)** | 2 GODL-India, 2 Flickr Commons "No known restrictions" |
| **Rejected Licenses (ND / NC)** | **0 records (0.0%)** | Zero prohibited licenses ingested |
| **Scientific Suitability — CANDIDATE** | **55 records (91.7%)** | Geological field photos & roadside infrastructure controls |
| **Scientific Suitability — REQUIRES_REVIEW** | **2 records (3.3%)** | Low-resolution / distant aerial scenes |
| **Scientific Suitability — UNSUITABLE** | **3 records (5.0%)** | Historical printed book scans (1898–1911) & line drawings |
| **Newly Downloaded & Verified Images** | **53 images** | Isolated in `data/public_candidates/batch_2g/` |
| **Downloaded Batch Storage Size** | **155.08 MB** | All individual files $\le 15.0\text{ MB}$ safety ceiling |
| **Raster Integrity Pass Rate** | **100% (53 / 53)** | Validated via Pillow `img.verify()` and dimensions decode |
| **Minimum Raster Dimension** | **427 px** | Meets minimum $\ge 400\text{ px}$ threshold (longest side up to 6000 px) |
| **Exact Hash Duplicates Skipped** | **0** | No SHA-256 collisions within the batch |
| **Suspected Perceptual Near-Duplicates** | **0** | All pairwise dHash Hamming distances $> 10 / 64$ bits |

---

## 3. Independent Source License Provenance Audit

All 60 records in `phase_2g_candidates.csv` were independently re-audited against the live upstream Wikimedia Commons API (`action=query&prop=imageinfo&iiprop=url|size|mime|extmetadata|sha1`).

### 3.1 Distribution of Verified Licenses ($N=60$)

| License Short Name | Version | Records | Redistribution Permitted? | Attribution & Re-Use Requirements |
| :--- | :---: | :---: | :---: | :--- |
| **CC BY-SA 4.0** | 4.0 | 18 | Yes | Author credit, license link, share-alike |
| **CC BY 2.0** | 2.0 | 12 | Yes | Author credit, license link |
| **Public domain** | PD | 10 | Yes (USGS, NPS, USFS, expired copyright) | No copyright restrictions |
| **CC BY-SA 2.0** | 2.0 | 9 | Yes | Author credit, license link, share-alike |
| **CC BY 4.0** | 4.0 | 4 | Yes | Author credit, license link |
| **CC BY-SA 3.0** | 3.0 | 3 | Yes | Author credit, license link, share-alike |
| **GODL-India** | Custom | 2 | Pending Legal Review | Government Open Data License (India); attribution required |
| **No restrictions** | Custom | 2 | Pending Legal Review | Flickr Commons / Internet Archive historical scans (1898, 1901) |
| **Total** | — | **60** | **56 Approved / 4 Quarantined** | Strict enforcement of redistribution policy |

### 3.2 Audit Safeguard: Quarantined Candidates
The 4 candidates marked `PENDING_REVIEW` (`WMC_71769303`, `WMC_71769307`, `WMC_43470710`, `WMC_43428262`) were automatically quarantined by the downloader's license gate:
- Neither downloaded nor stored on disk in `data/public_candidates/batch_2g/`.
- Preserved in `phase_2g_candidates.csv` with status `download_status = SKIPPED_UNAPPROVED` and `intended_use_permission_status = PENDING_REVIEW`.
- Demonstrates zero-leakage automated enforcement of the redistribution policy.

---

## 4. Coverage Transformation: Before Phase 2G vs After Phase 2G

The systematic query plan directly addressed the critical deficiencies cataloged in the Phase 2F coverage audit:

### 4.1 Priority A: Indian Himalayan Region (IHR) Representation
- **Baseline (Phase 2F):** Only 2 images (3.7%) from the IHR, both from a single post-landslide rock clearing operation in Himachal Pradesh.
- **Phase 2G Additions:** **29 candidate records (48.3% of new candidates)** representing distinct Himalayan highway corridors and geomorphic settings:
  - **Uttarakhand (10 candidates):** Landslide scarps, slope debris, and road clearance along Chamoli, Tharali, Lansdowne, and Nainital historic/modern corridors.
  - **Himachal Pradesh (10 candidates):** Active rockslides, mudslides, and road-blocking debris along Kinnaur (Nigulsari active slide), Kullu-Manali, and Spiti valley corridors.
  - **Sikkim (7 candidates):** Teesta basin roadside washouts and steep slope failures.
  - **Jammu & Kashmir / Ladakh (2 candidates):** High-altitude road cutting, rockfall, and culvert construction in Zanskar (Kargyak) and J&K passes.
- **Geotechnical Impact:** Drastically reduces geographic bias; model evaluation can now specifically test tropical/monsoonal weathering and fractured Himalayan schist/phyllite regimes.

### 4.2 Priority B: Matched Roadside Engineering Negative Controls
- **Baseline (Phase 2F):** 10 images (18.5%), consisting almost entirely of panoramic alpine mountain passes without man-made slope stabilization.
- **Phase 2G Additions:** **26 candidate records (43.3% of new candidates)** of ground-level engineered infrastructure:
  - **Engineered Retaining Walls (6 candidates):** Intact concrete, dry stone, and masonry gravity retaining walls supporting mountain roads.
  - **Roadside Drainage Controls & Culverts (10 candidates):** Concrete drainage channels, unblocked culverts, corrugated metal pipes, and roadside ditches directing storm runoff safely.
  - **Rockfall Mitigation Infrastructure (10 candidates):** Anchored steel rockfall netting, wire mesh pinning, and debris catch fences along steep cut slopes.
- **Geotechnical Impact:** Enables defensible false-positive evaluation. The system can measure whether the VLM mistakenly classifies intact engineering structures as slope failures.

### 4.3 Priority C: Early-Warning Precursor Indicators
- **Baseline (Phase 2F):** Only 2 images (3.7%) showing tension cracks.
- **Phase 2G Additions:** **5 candidate records (8.3% of new candidates)** depicting early tension cracks in soil/asphalt, road subsidence, and scarp initiation prior to complete slope collapse.
- **Geotechnical Impact:** Establishes initial evaluation capacity for early-warning screening, where intervention is most cost-effective and life-saving.

### 4.4 Synthesis: Dataset Distribution Shift

```
Coverage Dimension           Baseline (Phase 2F)    Phase 2G Additions    Combined Collection
─────────────────────────────────────────────────────────────────────────────────────────────
Total Candidate Records              63                     60                    123
Images Ingested on Disk              54 (174.4 MB)          53 (155.1 MB)         107 (329.5 MB)
IHR (Himalayas) Candidates            2 (3.7%)              29 (48.3%)             31 (25.2%)
Engineering Negative Controls        10 (18.5%)             26 (43.3%)             36 (29.3%)
Precursor Indicators (Cracks)         2 (3.7%)               5 (8.3%)               7 (5.7%)
Verified Open CC/PD Licenses         54 (100% of DL)        53 (100% of DL)       107 (100% of DL)
Physical Storage Isolation     data/public_candidates/   data/public_candidates/   Strictly Separated
                                     images/                  batch_2g/
```

---

## 5. Security & Ingestion Pipeline Enhancements

To guarantee bulletproof isolation and safety, four architectural enhancements were implemented and verified in `backend/app/services/public_image_acquisition.py`:

1. **SSRF and Network Target Validation (`validate_safe_url`):**
   - Strictly enforces `http` or `https` schemes.
   - Blocks loopback addresses (`localhost`, `127.0.0.1`, `0.0.0.0`), cloud metadata endpoints (`169.254.169.254`), private RFC1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and internal DNS suffixes (`.internal`, `.local`).
2. **Production Storage Protection (`_validate_isolated_download_dir`):**
   - Evaluates target download directory paths and raises `PublicAcquisitionError` if any attempt is made to write into production upload paths (`uploads`, `backend_uploads`).
3. **Strict Non-Overwrite Protection (`download_candidate`):**
   - Checks if the destination file already exists on disk.
   - If present, verifies existing file SHA-256 without re-downloading or clobbering, ensuring complete immutability for existing assets.
4. **Targeted Unit Test Expansion:**
   - 5 comprehensive security tests added to `backend/tests/test_public_image_discovery.py`:
     - `test_validate_safe_url_accepts_valid_http_and_https`
     - `test_validate_safe_url_blocks_unsafe_schemes`
     - `test_validate_safe_url_blocks_ssrf_and_private_ips`
     - `test_validate_isolated_download_dir_blocks_production_uploads`
     - `test_download_candidate_strict_non_overwrite_preservation`
   - Test suite expanded from 212 to 217 unit tests; all 217 tests passing with zero regressions in 3.1s.

---

## 6. Formal Benchmark Entry Gate & Evaluation Status

In strict accordance with the Phase 2E Evaluation Protocol and Phase 2F Entry Gates:
- **Benchmark Evaluation Status:** **FORMALLY BLOCKED**
- **Adjudication Requirement:** All 53 images in `batch_2g` remain strictly un-evaluated. They have **NOT** been assigned ground-truth labels.
- **Entry Gate Criteria:**
  - [x] Controlled acquisition complete and physically isolated in `batch_2g/`.
  - [x] 100% raster integrity and magic byte verification confirmed.
  - [x] Independent source API license audit complete (56 verified, 4 quarantined).
  - [x] Perceptual dHash near-duplicate audit complete (0 intra-batch duplicates).
  - [ ] Independent dual-expert geotechnical annotation (Pending Phase 3).
  - [ ] Inter-annotator agreement verification ($\kappa \ge 0.70$) (Pending Phase 3).
  - [ ] Formal consensus adjudication and test/dev frozen split partitioning (Pending Phase 3).

No accuracy claims, benchmark scoring, or model training may proceed until the human annotation gates are fully executed.
