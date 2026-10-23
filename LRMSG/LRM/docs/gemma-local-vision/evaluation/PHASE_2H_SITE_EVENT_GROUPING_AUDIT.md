# PahaarPulse — Phase 2H: Site & Event Grouping Audit

**Document Version:** v1.0  
**Audit Completion Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Lead Authority:** Senior Computer-Vision Engineer, Geotechnical Data-Quality Researcher, ML Evaluation Specialist, and Backend Safety Engineer  
**Status:** Audit Complete & Verified  

---

## 1. Executive Rationale & Evaluation Leakage Vulnerability

A fundamental flaw in naive computer-vision evaluations is **random image-level train/test splitting**. When multiple photographs are captured during the same landslide event, on the same highway cut slope, or by the same photographer within minutes of each other, they share:
- Identical lithological textures and rock weathering patterns.
- Identical roadway pavement markings, guardrails, and background vegetation.
- Identical ambient lighting, camera sensors, and focal lengths.

If image $A$ is placed in the training/fine-tuning split and companion image $B$ is placed in the test/evaluation split, a Vision-Language Model can achieve artificially inflated accuracy scores by memorizing site-specific visual idiosyncrasies rather than learning generalizable geotechnical hazard indicators.

This audit evaluates the physical independence of all candidate images across the collection and establishes strict site/event grouping boundaries to guarantee zero-leakage evaluation splitting.

---

## 2. Grouping Taxonomy & Epistemic Confidence Levels

Every candidate record is evaluated and categorized into one of three standardized confidence states:

```
Grouping State              Definition & Evidence Criteria
─────────────────────────────────────────────────────────────────────────────────────────────
CONFIRMED_SITE_EVENT        High certainty. Explicit matching GPS coordinates (within ≤ 500 m),
                            identical named disaster event with matching timestamp, or documented
                            photographic sequence captured by the same operator during a single shoot.
─────────────────────────────────────────────────────────────────────────────────────────────
PROBABLE_SITE_EVENT         Moderate certainty. Same highway corridor, valley section, or district
                            within ≤ 10 km, sharing geomorphic features or photographic themes where
                            spatial independence cannot be scientifically guaranteed.
─────────────────────────────────────────────────────────────────────────────────────────────
UNKNOWN_SITE_EVENT          Low certainty. Isolated photograph lacking precise geocoding or location
                            specificity. IMPORTANT: UNKNOWN status DOES NOT imply independence!
─────────────────────────────────────────────────────────────────────────────────────────────
```

> [!CRITICAL]
> **The Independence Fallacy ("Unknown $\ne$ Independent"):**  
> Under no circumstances may an image marked `UNKNOWN_SITE_EVENT` be assumed to be physically independent of another image merely because their titles, filenames, or URLs differ. In the absence of positive proof of geographic separation, unknown images must be treated with caution during benchmark partitioning.

---

## 3. Confirmed Multi-Record Site/Event Clusters ($N=41$ Candidates)

The audit identified **16 confirmed multi-record clusters** encompassing 41 candidate records (36 downloaded on disk):

### 3.1 Cluster Catalog

| Cluster Identifier | Records | Disk Files | Location & Setting | Grouping Evidence & Leakage Risk |
| :--- | :---: | :---: | :--- | :--- |
| **`ODOT_Helicopter_Rockfall_Mesh_Series`** | 10 | 10 | Oregon Highway Cut Slope (US 30 / OR 22) | 10 consecutive photos of a single helicopter netting installation by Oregon DOT. Extreme visual correlation. |
| **`Oregon_Route_22_Rockfall`** | 2 | 2 | Oregon Route 22 Milepost 63 | 2 photos depicting the exact same fallen boulder and asphalt impact divot. |
| **`Himachal_Rohtang_Pass_Clearing`** | 2 | 2 | Rohtang Pass, Himachal Pradesh (GPS: 32.57, 77.05) | 2 photos taken seconds apart showing rock clearance operations across the highway surface. |
| **`Himachal_Mandi_Kullu_Highway_370_371`** | 2 | 2 | Delhi-Manali NH-03 Sector A (GPS: 31.68, 77.08) | 2 cut-slope photos separated by 11 meters along the highway bend. |
| **`Himachal_Mandi_Kullu_Highway_558_559`** | 2 | 2 | Delhi-Manali NH-03 Sector B (GPS: 31.84, 77.17) | 2 cut-slope photos separated by 80 meters along the highway corridor. |
| **`Taiwan_Caoling_1999_Landslide_Scar`** | 2 | 2 | Caoling, Yunlin County, Taiwan (GPS: 23.59, 120.62) | 2 photos of the 1999 Chi-Chi earthquake mega-landslide scarp. Identical geological structure. |
| **`Georgia_Varaziskhevi_Landslide_2025`** | 2 | 2 | Varaziskhevi Valley, Georgia (GPS: 41.70, 44.76) | 2 photos taken on 2025-03-20 showing the active valley failure scarp. |
| **`USFS_Bolam_Creek_Lava_Fire`** | 2 | 2 | Bolam Creek, Mt. Shasta, California | 2 photos taken 2 minutes apart by USFS during post-fire debris flow. |
| **`NPS_Halemaumau_Trail_Rockfall`** | 2 | 2 | Halemaʻumaʻu Trail, Kilauea, Hawaii | 2 photos of fresh rockfall boulders across the tourist trail. |
| **`Colorado_Cumberland_Pass`** | 2 | 2 | Cumberland Pass, Gunnison County, CO (GPS: 38.69, -106.48) | 2 photos by John Sowell of high-altitude unpaved road cut. |
| **`Colorado_Carnero_Pass`** | 2 | 2 | Carnero Pass, Saguache County, CO (GPS: 38.00, -106.43) | 2 photos by John Sowell of mountain road cut slope. |
| **`Norway_Asker_Semsvannet`** | 2 | 2 | Semsvannet Ravine, Asker, Norway | 2 photos of torrent outflow ravine by Bjoertvedt. |
| **`NASA_North_India_2013_Preflood_Postflood`** | 2 | 2 | Uttarakhand Himalayan Basin (Satellite) | Before/after satellite pair of 2013 Kedarnath disaster. Unsuitable for ground triage. |
| **`North_Sikkim_Lingzya_Series`** | 2 | 2 | Lingzya, North Sikkim | 2 photos by Balakrishnan Valappil of vegetation/landscape in North Sikkim. |
| **`IAF_Sikkim_2011_Earthquake_Survey`** | 2 | 0 | Sikkim Himalayan Valleys (Aerial) | 2 helicopter aerial damage survey photos post-2011 earthquake. Excluded from download. |
| **`Internet_Archive_Historical_Book_Scans`** | 3 | 0 | Historical printed scans (1898–1911) | 3 scanned book pages from Internet Archive. Excluded from download. |

**Total In Multi-Record Clusters:** 41 candidate records (36 downloaded images on disk).

---

## 4. Single-Site Confirmed & Probable Clusters ($N=76$ Candidates)

The remaining 76 candidate records were classified as follows:
- **`CONFIRMED_SITE_EVENT` (Single-Member, $N=25$ records):** Individual photographs with validated, high-precision GPS coordinates verified in metadata (e.g., `WMC_14428956` in Conwy Wales, `WMC_40222037` in Uttarakhand, `WMC_97705470` in Lauzet Ubaye France).
- **`PROBABLE_SITE_EVENT` ($N=14$ records):** Photographs with specific named geographic localities (valleys, passes, or named highways) but without coordinate pinpoints (e.g., `Kinnaur_Nigulsari_Active_Slide`, `Tharali_Chamoli_Debris_Slide`, `Zanskar_Kargyak_Culvert`).
- **`UNKNOWN_SITE_EVENT` ($N=37$ records):** Records with insufficient geographic or circumstantial evidence to localize. Each is assigned a unique tracking ID (`UNKNOWN_SITE_EVENT_<candidate_id>`) to prevent accidental pooling.

---

## 5. Grouping Manifest Reference

The full mapping of every candidate ID to its group identifier, member count, and justification is version-controlled in:  
[`PHASE_2H_GROUPING_MANIFEST.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/PHASE_2H_GROUPING_MANIFEST.csv)

### 5.1 Evaluation Split Invariant
All candidate images sharing the same `site_event_group_id` **MUST** be allocated as an indivisible atomic block into either the development split or the held-out test split. Under no circumstances may a multi-member cluster be split across train/dev and test.
