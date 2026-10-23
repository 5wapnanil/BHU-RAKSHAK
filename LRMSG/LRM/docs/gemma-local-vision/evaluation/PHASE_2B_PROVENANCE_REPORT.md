# PahaarPulse — Phase 2B: Dataset Expansion & License Provenance Audit Report

**Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Repository Working Directory:** `C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM`  
**Evaluation Subsystem:** Gemma Vision Field-Photo Ground-Truth Benchmark Pipeline  
**Document Status:** Complete & Evidence-Based  

---

## Executive Summary

Phase 2B expands the PahaarPulse candidate field-photograph collection from an initial 9 candidates to **63 candidate records** across eight core geotechnical hazard categories, while establishing an independent, reproducible license and scientific suitability provenance audit.

This expansion was executed entirely under strict scientific integrity and production safety constraints:
1. **Zero Ground-Truth Fabrication:** All ground-truth hazard labels (`annotator_1_label`, `annotator_2_label`, `adjudicated_label`) remain strictly empty with `adjudication_status = "pending"`. Image titles, search keywords, and repository tags are recorded solely as observational metadata hints and are never treated as ground truth.
2. **Metadata-Only Default Discovery:** Automated discovery queries were restricted strictly to metadata ingestion. Zero unapproved images were downloaded.
3. **Safety Limit Preservation:** The 15 MB file size limit was strictly preserved without exception.
4. **Independent Provenance Audit:** Every candidate was verified against original MediaWiki APIs, generating `docs/gemma-local-vision/evaluation/license_provenance_audit.csv`.
5. **Physical Event/Site Grouping:** 28 distinct site and series clusters were identified to prevent split leakage across training, development, and evaluation sets.
6. **Production Configuration & Database Invariance:** `GEMMA_PROVIDER=google` and `GEMMA_MODEL=gemini-3.5-flash` were preserved, and all 15 PostgreSQL operational tables remain intact with zero mutation.

---

## 1. Candidate Acquisition & Audit Summary

| Metric | Phase 2A Baseline | Phase 2B Result | Net Change | Verification Source |
| :--- | :--- | :--- | :--- | :--- |
| **Total Candidates Discovered** | 9 | **63** | +54 | `public_image_candidates.csv` |
| **Audited Provenance Records** | 0 | **63** | +63 | `license_provenance_audit.csv` |
| **Verified Open Licenses** | 7 | **57** | +50 | Official MediaWiki API & LicenseGate |
| **Pending Review Licenses** | 2 | **6** | +4 | Flickr Commons "No restrictions" / Custom |
| **Rejected Licenses** | 0 | **0** | 0 | Prohibited / Non-Derivative Gates |
| **Source Unavailable Records** | 0 | **0** | 0 | Live HTTP MediaWiki API Queries |
| **Downloaded Verified Images** | 6 | **6** | 0 (Preserved) | `data/public_candidates/images/` |
| **Skipped (Pending Review)** | 2 | **2** | 0 (Preserved) | Blocked by `IntendedUseStatus` Gate |
| **Failed Downloads (Size Limit)** | 1 | **1** | 0 (Preserved) | Blocked by 15 MB Safety Gate |
| **Not Downloaded (Metadata-Only)** | 0 | **54** | +54 | Intentional Discovery Gate |
| **Distinct Event / Site Groups** | 0 | **28** | +28 | GPS Coordinates & Known Named Sites |
| **Backend Test Suite Pass Rate** | 172 / 172 | **182 / 182** | +10 tests | `unittest discover backend/tests` |

---

## 2. Independent License Provenance Audit

All 63 candidates were audited by querying the official Wikimedia Commons MediaWiki API (`action=query`, `prop=imageinfo`, `iiprop=url|size|mime|extmetadata|sha1`). The audited evidence is recorded in `docs/gemma-local-vision/evaluation/license_provenance_audit.csv`.

### License Distribution Across All Candidates

```
  CC BY-SA 4.0:             20 candidates (31.7%)  [VERIFIED - Redistribution Permitted]
  Public Domain:            11 candidates (17.5%)  [VERIFIED - Redistribution Permitted]
  CC BY-SA 2.0:              8 candidates (12.7%)  [VERIFIED - Redistribution Permitted]
  CC BY-SA 3.0:              7 candidates (11.1%)  [VERIFIED - Redistribution Permitted]
  CC BY 2.0:                 7 candidates (11.1%)  [VERIFIED - Redistribution Permitted]
  No restrictions (Flickr):  4 candidates  (6.3%)  [PENDING_REVIEW - Requires Legal Review]
  CC BY 4.0:                 3 candidates  (4.8%)  [VERIFIED - Redistribution Permitted]
  Attribution (Custom):      2 candidates  (3.2%)  [PENDING_REVIEW - Requires Legal Review]
  CC BY-SA 3.0 de:           1 candidate   (1.6%)  [VERIFIED - Redistribution Permitted]
```

### Breakdown by License Version

| Version | Count | Intended Use Status | Redistribution Eligibility |
| :--- | :--- | :--- | :--- |
| **Version 4.0** (CC BY 4.0, CC BY-SA 4.0) | 23 | `APPROVED_FOR_REDISTRIBUTION` | Permitted with Attribution & Share-Alike |
| **Version 3.0** (CC BY-SA 3.0, CC BY-SA 3.0 de) | 8 | `APPROVED_FOR_REDISTRIBUTION` | Permitted with Attribution & Share-Alike |
| **Version 2.0** (CC BY 2.0, CC BY-SA 2.0) | 15 | `APPROVED_FOR_REDISTRIBUTION` | Permitted with Attribution & Share-Alike |
| **Public Domain / Custom / Flickr** | 17 | 11 Verified PD, 6 Pending Review | 11 Permitted; 6 Excluded from Ingestion |

---

## 3. Investigation of Edge Cases

### 3.1 The Two Pending Flickr Commons Candidates (`WMC_43209273` & `WMC_43642493`)

* **Source Pages:**
  * `WMC_43209273`: `https://commons.wikimedia.org/wiki/File:Annual_report_(1910)_(14777201184).jpg`
  * `WMC_43642493`: `https://commons.wikimedia.org/wiki/File:Forest_physiography;_physiography_of_the_United_States_and_principles_of_soils_in_relation_to_forestry_(1911)_(14590490147).jpg`
* **Original Attribution:** New York State Museum / Internet Archive Book Images Flickr stream.
* **Asserted License:** "No restrictions" (`https://www.flickr.com/commons/usage/`).
* **Legal Finding:**
  The "No known copyright restrictions" statement used by Flickr's *The Commons* project is a cultural institution notice, not a legally binding standard open copyright license deed (such as CC0 or CC-BY). While the original underlying US books (published in 1910 and 1911) are in the US public domain, institutions occasionally claim sui generis reproduction or database rights in overseas jurisdictions. Under PahaarPulse's strict licensing gate, these candidates remain classified as `PENDING_REVIEW` and must **not** be downloaded automatically.
* **Scientific Suitability Finding:**
  Both files are high-resolution scans of printed book pages containing text and historical engraved plates rather than operational RGB field triage photographs. They have been categorized as `UNSUITABLE` (`scene_type = "historical_book_scan"`, `relevance = "irrelevant"`). Consequently, even if legally cleared, they will not enter the active evaluation split.

### 3.2 The Oversized Candidate (`WMC_82792389`)

* **Source Page:** `https://commons.wikimedia.org/wiki/File:Bergtocht_van_S-charl_naar_Alp_Sesvenna._10-09-2019._(d.j.b)_25.jpg`
* **Creator / License:** Dominicus Johannes Bergsma / CC BY-SA 4.0.
* **File Metrics:** Original master resolution: 5184x3456 pixels. Original file size: 19,256,893 bytes (~18.36 MiB).
* **Safety Gate Verification:**
  During Phase 2A, the stream downloader hit the 15 MB limit (`DEFAULT_MAX_FILE_SIZE_BYTES = 15,728,640 bytes`), immediately severed the HTTP stream, atomically removed the partial temporary file from disk, and recorded status `failed` with reason `file_size_exceeded_15736832_bytes`.
* **Policy Compliance:**
  In accordance with Phase 2B constraints, the 15 MB safety limit was **not** increased. The safety limit protects field and server runtimes from denial-of-service and memory exhaustion.
* **Derivative Availability:**
  Wikimedia Commons officially provides an on-demand scaled 1920px derivative (`width: 1920`, `file_size: ~1.5 MB`) under the identical CC BY-SA 4.0 license deed. If needed for ground-truth benchmarking in future phases, this derivative can be downloaded safely within the 15 MB ceiling.

---

## 4. Scientific Suitability Assessment

Candidate photographs were assessed independently of copyright licensing to ensure that only genuine, informative field photographs reach expert geotechnical adjudication.

### Suitability Status Distribution

```
  CANDIDATE (Geological Field Photographs):        57 candidates (90.5%)
  UNSUITABLE (Book Scans, Maps, Diagrams):          4 candidates  (6.3%)
  REQUIRES_QUALITY_REVIEW (Low-Res / Aerial View):  2 candidates  (3.2%)
  AWAITING_EXPERT_ANNOTATION (Adjudication Ready):   0 candidates  (0.0%)
```

### Scene Type Breakdown

1. **`slope_face` (39 records):** Direct exposures of rock slopes, talus cones, failure crowns, and erosional gullies.
2. **`ground_level_roadside` (9 records):** Roadways impacted or obstructed by rockfall, rotational toe bulges, or torrent overflow.
3. **`landscape_pass` (10 records):** Stable mountainous passes and engineered highway corridors serving as non-landslide negative control scenes.
4. **`historical_book_scan` (4 records):** 20th-century book page scans from archival streams; excluded from field triage.
5. **`aerial_or_distant` (1 record):** Oblique regional perspectives requiring manual resolution verification.

---

## 5. Physical Event and Site Grouping

To prevent data leakage across train, dev, and test evaluation splits, photographs were grouped using GPS coordinates, physical site names, and documented photographic series.

* **Distinct Identified Physical Event / Site Groups:** **28 groups**
* **Confirmed Site Records:** **28 candidates**
  * Clustered via GPS coordinates within a ~1.1 km radius (e.g., `GPS_44.44_6.41`, `GPS_32.57_77.05`, `GPS_38.69_-106.48`) or confirmed named sites (`Lauzet_Ubaye_Rockfall`, `Sirac_Ecrins_Torrent`, `Nida_Parnidis_Dune`, `Vitkaiciai_Lithuania_Outcrop`, `Sesvenna_Alps_Torrent`).
* **Tentative Series Clusters:** **5 candidates**
  * Photostream series grouped by common series stem (e.g., `Series_asker_semsvann_gupuelva_tveite`).
* **Unknown / Independent Site Records:** **30 candidates**
  * Explicitly assigned `event_site_group = "UNKNOWN_EVENT_OR_SITE"` with `event_site_confidence = "UNKNOWN"`.
  * **Leakage Guard Guarantee:** The evaluation harness recognizes `UNKNOWN_EVENT_OR_SITE` as distinct independent events, preventing false positive leakage errors while strictly barring any confirmed group from spanning multiple splits.

---

## 6. Attribution Obligations

Under Creative Commons BY and BY-SA licenses (versions 2.0, 2.5, 3.0, and 4.0), any public distribution or presentation of benchmark images must include creator attribution and license notices. Key creator attributions documented in `license_provenance_audit.csv`:

* **`WMC_97705470`:** *"Bloc Lauzet P1010012mod.jpg"* © JYB Devot, licensed under CC BY-SA 4.0.
* **`WMC_122140394`:** *"Passerelle en partie détruite sur le torrent du Sirac"* © Pline, licensed under CC BY-SA 4.0.
* **`WMC_61515158`:** *"Nida wydma Parnidis 04.jpg"* © Andrzej Otrębski, licensed under CC BY-SA 4.0.
* **`WMC_8877448`:** *"Vitkaičių Atodanga"* © Andrjusgeo at lt.wikipedia, licensed under CC BY-SA 3.0.
* **`WMC_14428956`:** *"Tension cracks"* © Jonathan Wilkins, licensed under CC BY-SA 2.0 (via Geograph).
* **`WMC_13491080`:** *"Erosion patterns"* © Rudi Winter, licensed under CC BY-SA 2.0 (via Geograph).

---

## 7. Exact Commands to Reproduce Phase 2B

All operations are fully deterministic and reproducible using the CLI in `backend/scripts/discover_public_landslide_images.py`:

```powershell
# 1. Navigate to backend/website root
Set-Location "C:\Users\Swapnanil\Desktop\app2\LRMSG\LRM"

# 2. Run metadata-only discovery across the 8 standard geotechnical topics
python backend/scripts/discover_public_landslide_images.py discover --limit 10 --append --delay 0.5

# 3. Perform independent license and provenance audit against original MediaWiki APIs
python backend/scripts/discover_public_landslide_images.py audit --manifest docs/gemma-local-vision/evaluation/public_image_candidates.csv --output docs/gemma-local-vision/evaluation/license_provenance_audit.csv

# 4. Migrate or verify candidate manifest schema
python backend/scripts/discover_public_landslide_images.py migrate --manifest docs/gemma-local-vision/evaluation/public_image_candidates.csv

# 5. Export downloaded and verified images to the draft benchmark format
python -c "from backend.app.services.public_image_acquisition import PublicImageManifestManager; c = PublicImageManifestManager.read_candidates_csv('docs/gemma-local-vision/evaluation/public_image_candidates.csv'); PublicImageManifestManager.export_to_draft_benchmark_manifest(c, 'docs/gemma-local-vision/evaluation/public_benchmark_draft.csv')"

# 6. Run full unit and regression test suite
python -m unittest backend.tests.test_public_image_discovery
python -m unittest discover backend/tests
```

---

## 8. Remaining Scientific Validation Requirements

Before any benchmark results or accuracy claims can be published:
1. **Physical Site Ground-Truth Adjudication:**
   In accordance with `GROUND_TRUTH_PROTOCOL.md`, all candidate field images must undergo independent dual-expert geotechnical review (minimum M.Sc./B.Tech. in Geotechnical Engineering or Geology).
2. **Inter-Annotator Reliability:**
   Dual annotations must achieve a Cohen's Kappa $\ge 0.70$ before a dataset partition can be frozen for model accuracy validation.
3. **Controlled Image Ingestion:**
   Only candidates with `VERIFIED` license status and `CANDIDATE` suitability should be downloaded into the controlled research directory.
4. **Himalayan Domain Alignment:**
   Ensure adequate representation of Himalayan lithologies (phyllites, schists, weathered quartzites) and monsoon-driven saturation indicators.
