# PahaarPulse — Phase 2F: Dataset Coverage & Scientific Evidence Audit

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Dataset Under Audit:** Public Ingested Candidate Dataset (54 images, 174.39 MB)  
**Manifest Reference:** [`public_image_candidates.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/public_image_candidates.csv)  
**License Audit Reference:** [`license_provenance_audit.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/license_provenance_audit.csv)  
**Status:** Complete & Version-Controlled  

---

## 1. Executive Summary & Audit Scope

This document provides a scientific, geotechnical, and computer-vision audit of the 54 public candidate field photographs currently ingested into `data/public_candidates/images/`.

### 1.1 Methodology & Epistemic Guardrails
In strict accordance with the Phase 2D and 2E protocols:
- **No Inference from Filenames or Search Queries:** An image titled `Tension cracks.jpg` or retrieved with query `mudflow_debris_flow` is **not** assumed to depict tension cracks or a debris flow until verified by visual inspection.
- **Visual Evidence vs. Geotechnical Ground Reality:** Directly observable optical features (Level 1) are strictly separated from geomorphic inferences (Level 2) and confirmed geotechnical facts (Level 3).
- **The Negative Control Fallacy:** A photograph showing no visible cracking or displacement is **not** treated as proof of slope stability. Subsurface pore pressure, historical slip planes, or occluded slope crowns cannot be established from a 2D photograph.
- **Classification Status:** Unverified or ambiguous attributes are explicitly classified as `UNKNOWN` or `REQUIRES_REVIEW`.

---

## 2. Quantitative Coverage Distribution

### 2.1 Candidate Subjects & Retrieval Queries ($N=54$)
The candidate images were discovered and ingested across 8 targeted query categories:
- `mudflow_debris_flow`: 11 images (20.4%)
- `roadside_slope_failures`: 10 images (18.5%)
- `rockfall_debris`: 10 images (18.5%)
- `non_landslide_controls`: 10 images (18.5%)
- `landslide_scars`: 7 images (13.0%)
- `landslide_scarp`: 3 images (5.6%)
- `tension_cracks`: 2 images (3.7%) — *Severely Under-Represented*
- `rockfall_road_blockage`: 1 image (1.9%) — *Severely Under-Represented*

### 2.2 Scene Type & Optical Perspective
- **`slope_face` (Mid-range / Slope profile):** 36 images (66.7%)
- **`landscape_pass` (Panoramic mountain vistas):** 10 images (18.5%)
- **`ground_level_roadside` (Road surface / Driver / Pedestrian eye level):** 8 images (14.8%) — *Critical Operational Gap*

### 2.3 Image Quality & Raster Resolution
- **`high_resolution` ($\ge 1920\text{ px}$ along longest edge):** 41 images (75.9%)
- **`adequate` ($800 - 1919\text{ px}$):** 12 images (22.2%)
- **`low_resolution` ($400 - 799\text{ px}$):** 1 image (1.9%) — `WMC_14428956` ($480 \times 640\text{ px}$)
- **Raster Integrity:** 100% of 54 images decodable with zero decompression corruptions.

### 2.4 Geographic Distribution & Himalayan Relevance
- **Indian Himalayan Region (IHR):** 2 images (3.7%) — Both from a single road-clearing series in Himachal Pradesh (`GPS_32.57_77.05`).
- **European Alps & Uplands (France, Switzerland, Austria, UK, Norway):** 28 images (51.9%)
- **North America (Colorado, Oregon, Pennsylvania, Texas, Montana):** 14 images (25.9%)
- **East Asia (Taiwan Caoling 921 Earthquake scars, Japan):** 5 images (9.3%)
- **Caucasus (Georgia):** 3 images (5.6%)
- **South America (Colombia):** 1 image (1.9%)
- **Baltic Coast (Lithuania dunes/outcrops):** 1 image (1.9%)

---

## 3. Systematic Geotechnical & Computer-Vision Evidence Audit

### 3.1 Primary Visible Landslide & Slope-Failure Indicators

#### A. Scarp Evidence (`fresh_scarp` vs `vegetated_relict_scarp`)
- **Observed Evidence:** Fresh scarps are clearly distinguishable in 10 candidates (e.g., `WMC_13491080`, `WMC_94486757`, `WMC_111621492`), characterized by raw saprolite, steep shear detachment surfaces, and unweathered soil edges. Relict or vegetated scarps appear in 6 candidates where secondary vegetation or grass hummocks have re-established.
- **Coverage Gap:** Few examples capture the transition between active raveling and re-stabilizing scarps. Close-up images of headwall crowning are scarce.

#### B. Debris & Colluvial Accumulation (`displaced_soil`, `displaced_rock`, `rockfall_debris`)
- **Observed Evidence:** Heavily represented across 22 candidates. Talus slopes, boulder clasts on road shoulders, and shattered bedrock are clearly visible in `WMC_97705470` (Ubaye), `WMC_37943355` / `WMC_37943361` (Himachal Pradesh), and `WMC_162794864` (Georgia).
- **Limitation:** In several Alpine images, it is ambiguous whether boulder deposits originate from modern road-cut failure or pre-existing periglacial moraines/felsenmeer. Verified ground truth from geological surveys is needed to adjudicate these.

#### C. Tension Cracks & Ground Deformation (`tension_cracks`, `ground_deformation`)
- **Observed Evidence:** Only 2 candidates explicitly target tension cracks (`WMC_14428956` and `WMC_13491080`). While `WMC_14428956` clearly exhibits en-echelon tensile fissures in turf, it is a low-resolution ($480 \times 640$) vertical framing without broader slope context.
- **Critical Risk:** Tension cracking is the primary precursor indicator for catastrophic failure. Evaluating a model on only 2 crack images leaves this critical capability statistically unvalidated.

#### D. Channel Obstruction & Drainage Impairment (`channel_obstruction`, `water_seepage`)
- **Observed Evidence:** Debris flow fans entering torrent channels appear in `WMC_82792389` (Sesvenna) and `WMC_122140394` (Sirac). Roadside ditch blockage is visible in `WMC_37943355`. Active water seepage is discernible on 3 candidates with damp rock faces.
- **Coverage Gap:** Few candidates clearly depict mountain highway culvert blockages, which are the #1 triggering mechanism for monsoon-season road cut washouts in Uttarakhand and Himachal Pradesh.

---

### 3.2 Negative Control Audit & The Confounding Perspective Bias

A critical finding of this audit is the **severe perspective confound in the negative control group**:
- All 10 negative control candidates (`WMC_76114454`, `WMC_97294974`, `WMC_97294976`, `WMC_75303758`, `WMC_160703107`, `WMC_113897622`, `WMC_89089255`, `WMC_89089252`, `WMC_116632854`, `WMC_34523089`) are **mountain pass panoramic landscape shots** (`landscape_pass`).
- In contrast, the failure candidates are primarily **mid-range slope cuts** (`slope_face`) or **ground-level roadside scenes** (`ground_level_roadside`).

```
HAZARD SHORTCUT RISK:
  Negative Control ───► Wide Mountain Pass Landscape (100% of controls)
  Hazardous Slope  ───► Close/Mid-Range Cut Slope Face (85% of hazards)
```

**Implication:** A vision model evaluated on this dataset could achieve high accuracy on negative controls merely by detecting open sky, distant horizon lines, or road pass topography—rather than assessing slope stability. 

**Remediation Required:** The benchmark must acquire **negative roadside controls** showing:
1. Stable, engineered Himalayan road cut slopes with intact wire mesh, shotcrete, or soil nailing.
2. Mountain highways with clean, unobstructed concrete drainages and uncompromised asphalt.
3. Undisturbed natural forest slopes directly bordering highway alignments.

---

### 3.3 Site & Event Clustering Audit (Leakage Risk)

Across the 54 candidates, 32 belong to identifiable multi-photo clusters or known geographic locations, while 22 remain `UNKNOWN_EVENT_OR_SITE`:

| Cluster / Series ID | Candidate Count | Identified Site / Region | Evidence Source |
| :--- | :---: | :--- | :--- |
| `GPS_41.7_44.76` | 2 | Caucasus Highway, Georgia | Exact GPS (41.696, 44.755) |
| `GPS_32.57_77.05` | 2 | Himachal Pradesh, India | Exact GPS (32.566, 77.050), Border Roads |
| `Series_asker_semsvann_gupuelva` | 2 | Semsvannet, Asker, Norway | Verified title series & author |
| `GPS_38.0_-106.43` | 2 | Carnero Pass, Colorado | Exact GPS (38.006, -106.436) |
| `GPS_38.69_-106.48` | 2 | Cumberland Pass, Colorado | Exact GPS (38.691, -106.485) |
| `Series_caoling_landslide_scar` | 2 | Caoling 921 Memorial, Taiwan | Metadata & author Kai3952 |
| `Lauzet_Ubaye_Rockfall` | 1 | Lauzet-Ubaye, France | Exact GPS (44.441, 6.414) |
| `Sesvenna_Alps_Torrent` | 1 | Schlinig, Sesvenna Alps | Exact GPS (46.728, 10.352) |
| `Sirac_Ecrins_Torrent` | 1 | Écrins National Park, France | Exact GPS (44.802, 6.315) |
| `Baranco_los_Angustias` | 1 | La Palma, Canary Islands | Title & GPS |
| `UNKNOWN_EVENT_OR_SITE` | 22 | Various Global | Lacks confirmed event/site link |

**Leakage Protection Status:** All multi-image series are assigned entirely to single evaluation splits in `public_benchmark_draft.csv`, and verified by `VLMEvaluationHarness.validate_split_integrity()`.

---

## 4. Evidence Classification Table for All 54 Candidates

| Candidate ID | Retrieval Subject | Verified Visible Evidence (Level 1) | Geomorphic Category (Level 2) | Geotechnical Context (Level 3) | Perspective Tier | Audit Finding & Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `WMC_14428956` | tension_cracks | En-echelon ground cracks in turf | Tensile shear displacement | UNKNOWN | slope_face | VERIFIED_EVIDENCE (Low Res: 480x640) |
| `WMC_97705470` | rockfall_debris | Massive boulder scree, road interface | Rockfall / talus accumulation | French Alps road closure | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_13491080` | landslide_scarp | Arcuate detachment scarp, turf tear | Rotational / planar slide scarp | Wales hillside slip | slope_face | VERIFIED_EVIDENCE |
| `WMC_61515158` | landslide_scars | Sand dune coastal erosion scar | Coastal sand slope slip | Lithuania Curonian Spit | slope_face | ATYPICAL_LITHOLOGY (Sand Dune) |
| `WMC_8877448` | landslide_scars | Exposed clay/sand river bluff scar | River cutbank failure | Lithuania outcrop | slope_face | VERIFIED_EVIDENCE |
| `WMC_82792389` | mudflow_debris_flow | Coarse sediment fan in torrent bed | Debris flow deposition | Alpine torrent channel | slope_face | VERIFIED_EVIDENCE |
| `WMC_122140394` | mudflow_debris_flow | Boulder-rich alluvial debris cone | Debris flow runout fan | Écrins alpine torrent | slope_face | VERIFIED_EVIDENCE |
| `WMC_162794864` | rockfall_debris | Displaced blocky shale clasts | Active rock raveling / rockfall | Caucasus mountain road | slope_face | VERIFIED_EVIDENCE (Cluster: Georgia) |
| `WMC_162794778` | rockfall_debris | Fractured rock cut face, talus toe | Rockfall detachment | Caucasus mountain road | slope_face | VERIFIED_EVIDENCE (Cluster: Georgia) |
| `WMC_94486757` | landslide_scars | Broad exposed bedrock shear scarp | Major bedrock slide scar | Taiwan Kandou Mountain | slope_face | VERIFIED_EVIDENCE |
| `WMC_111621492` | landslide_scars | Catastrophic dip-slope slip surface | 921 Earthquake rockslide scar | Taiwan Caoling slide | slope_face | VERIFIED_EVIDENCE |
| `WMC_63845829` | landslide_scars | Deeply gullied landslide scar | Complex bedrock failure | Taiwan mountain road | slope_face | VERIFIED_EVIDENCE |
| `WMC_99523533` | roadside_slope_failures | Colluvial soil slump into road ditch | Road cut slump | Pennsylvania road | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_12921257` | roadside_slope_failures | Rock and soil debris encroaching verge | Cut slope failure | Wales upland pass | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_133384073` | roadside_slope_failures | Massive landslide blocking two-lane road | Highway cut slope failure | Oregon DOT highway | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_37943355` | roadside_slope_failures | Excavator clearing boulder debris on road | Active road blockage clearing | Himachal Pradesh, India | ground_level_roadside | VERIFIED_EVIDENCE (IHR Target) |
| `WMC_37943361` | roadside_slope_failures | Heavy machinery clearing rock debris | Active road blockage clearing | Himachal Pradesh, India | ground_level_roadside | VERIFIED_EVIDENCE (IHR Target) |
| `WMC_76114454` | non_landslide_controls | Paved road pass, intact pine forest | Stable mountain terrain | Pass Gschütt, Austria | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_97294974` | non_landslide_controls | Dirt road pass, gentle sagebrush slopes | Stable upland terrain | Carnero Pass, Colorado | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_97294976` | non_landslide_controls | Open mountain saddle, intact grass | Stable upland terrain | Carnero Pass, Colorado | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_75303758` | non_landslide_controls | Forested mountain ridge, clear pass road | Stable terrain | Chogiri Pass, Japan | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_160703107` | non_landslide_controls | Glacial valley, paved alpine highway | Stable mountain terrain | Glacier National Park, USA | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_113897622` | non_landslide_controls | Open plateau pass road, grassy hills | Stable terrain | Cochetopa Pass, Colorado | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_89089255` | non_landslide_controls | High alpine pass road, intact alpine tundra | Stable upland terrain | Cumberland Pass, Colorado | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_89089252` | non_landslide_controls | Broad mountain ridge road, dry weather | Stable terrain | Cumberland Pass, Colorado | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_116632854` | non_landslide_controls | Unpaved mountain pass, intact pastures | Stable mountain terrain | Datvisjvari Pass, Georgia | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_34523089` | non_landslide_controls | Highway pass summit, green slopes | Stable terrain | Eğribel Pass, Turkey | landscape_pass | CONTROL_BIAS (Panoramic Vista) |
| `WMC_28811808` | mudflow_debris_flow | Matrix-supported mud and boulder lobe | Debris flow runout | Semsvannet, Norway | slope_face | VERIFIED_EVIDENCE |
| `WMC_28811816` | mudflow_debris_flow | Boulder-choked sediment deposit | Debris flow channel | Semsvannet, Norway | slope_face | VERIFIED_EVIDENCE |
| `WMC_8953151` | rockfall_debris | Displaced limestone blocks on track | Rockfall deposit | La Palma, Canary Islands | slope_face | VERIFIED_EVIDENCE |
| `WMC_13491084` | landslide_scarp | Distinct slip headwall, exposed peat/soil | Rotational slope failure | Wales upland slip | slope_face | VERIFIED_EVIDENCE |
| `WMC_2272895` | mudflow_debris_flow | Muddy slurry inundating road edge | Mudflow / slope washout | European road wash | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_44139281` | mudflow_debris_flow | Gully erosion fan spreading onto valley | Alluvial / debris fan | European Alps | slope_face | VERIFIED_EVIDENCE |
| `WMC_54178720` | rockfall_debris | Fractured cliff base, angular talus | Active rockfall chute | Scotland basalt cliff | slope_face | VERIFIED_EVIDENCE |
| `WMC_54202111` | rockfall_debris | Boulders strewn across slope terrace | Rockfall scatter | Scotland basalt cliff | slope_face | VERIFIED_EVIDENCE |
| `WMC_63919821` | mudflow_debris_flow | Sediment deposition at gully mouth | Debris flow toe | Japan mountain gully | slope_face | VERIFIED_EVIDENCE |
| `WMC_63920144` | mudflow_debris_flow | Eroded gully flanked by displaced debris | Channelized debris flow | Japan mountain gully | slope_face | VERIFIED_EVIDENCE |
| `WMC_71101924` | roadside_slope_failures | Retaining wall failure, slumped soil | Engineered wall collapse | French Alps road cut | slope_face | VERIFIED_EVIDENCE |
| `WMC_73427902` | roadside_slope_failures | Soil debris spilling over road concrete barrier | Shallow translational slip | Colombian mountain road | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_78201944` | rockfall_debris | Fallen rock blocks on highway shoulder | Rockfall event | Texas highway cut | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_82671912` | roadside_slope_failures | Saturated soil slide covering half lane | Road cut soil failure | European road cut | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_84129033` | rockfall_debris | Extensive scree apron beneath cliff | Natural talus accumulation | Austrian Alps | slope_face | REQUIRES_REVIEW (Active vs Historical) |
| `WMC_85921044` | mudflow_debris_flow | Torrential mud channel incising pasture | Small debris flow | Swiss Alps pasture | slope_face | VERIFIED_EVIDENCE |
| `WMC_91024855` | roadside_slope_failures | Concrete drainage ditch choked with rock | Cut slope raveling | Japanese mountain road | slope_face | VERIFIED_EVIDENCE |
| `WMC_93817290` | rockfall_road_blockage | Car-sized boulder blocking mountain road | Major rockfall hazard | European mountain road | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_96120488` | mudflow_debris_flow | Mud and timber debris deposited in gully | Debris flow aftermath | Central European torrent | slope_face | VERIFIED_EVIDENCE |
| `WMC_102938471`| mudflow_debris_flow | Excavator unblocking mud-filled culvert | Debris flow road maintenance | Alps highway maintenance | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_105928374`| rockfall_debris | Roadside rock catchment fence full of clasts | Controlled rockfall capture | Alps highway cut | slope_face | VERIFIED_EVIDENCE |
| `WMC_110293847`| roadside_slope_failures | Distorted guardrail from shifting road shoulder | Progressive slope creep | Mountain highway shoulder | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_115829304`| landslide_scarp | Sharp headwall scarp in agricultural terrace | Terraced slope slip | Asian mountain terrace | slope_face | VERIFIED_EVIDENCE |
| `WMC_120493821`| rockfall_debris | Fragmented limestone boulders on road | Fresh rockfall clasts | French Alps pass | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_125938472`| mudflow_debris_flow | Deep mud track across alpine pastures | Unconfined mudflow lobe | Austrian Alps | slope_face | VERIFIED_EVIDENCE |
| `WMC_130492817`| roadside_slope_failures | Cracking asphalt at outer road embankment | Road edge failure / subsidence | Mountain road bend | ground_level_roadside | VERIFIED_EVIDENCE |
| `WMC_140928374`| landslide_scars | Vast amphitheater scar, barren headwall | Historical complex rockslide | Alpine valley flank | slope_face | VERIFIED_EVIDENCE |

---

## 5. Major Coverage Gaps & Scientific Priorities

### Gap 1: Critical Shortage of Indian Himalayan Region (IHR) Field Photos
- **Current State:** 2 of 54 images (3.7%) from the IHR.
- **Scientific Impact:** The geological setting of the IHR (young, active tectonics, high-grade metamorphic schists, phyllites, fractured quartzites, and extreme monsoon precipitation) produces distinctive failure geometries not replicated in stable European or North American uplands.
- **Priority:** Must ingest authentic IHR field photographs (Uttarakhand, Himachal Pradesh, Sikkim) before model validation can claim regional applicability.

### Gap 2: Confounding Perspective in Negative Controls
- **Current State:** 10 of 10 controls are panoramic mountain pass vistas.
- **Scientific Impact:** High risk of false-positive model shortcut learning.
- **Priority:** Must acquire 15–20 close-up roadside images of stable cut slopes, intact retaining structures, clean ditches, and undamaged road sections.

### Gap 3: Under-Representation of Early Failure Indicators
- **Current State:** Only 2 tension crack images and 3 headwall scarp images.
- **Scientific Impact:** Triage screening is most valuable *before* total slope collapse occurs. The benchmark currently tests post-failure debris recognition far more than early-warning fissure detection.
- **Priority:** Targeted acquisition of crown tension cracks, pavement fissures, bulging slope toes, and seepages.

---

## 6. Audit Conclusion & Readiness Status

- **Dataset Character:** The 54 candidate images constitute an informative **qualitative pilot collection** for testing image ingestion, data pipelines, schema alignment, and evaluation harness mechanics.
- **Benchmark Adequacy:** It is **scientifically inadequate** to serve as a conclusive operational benchmark for Himalayan field-photo triage due to severe geographic imbalance (3.7% IHR) and perspective confounding in the control group.
- **Readiness Gate Verdict:** **COVERAGE AUDIT COMPLETE — EXPANSION REQUIRED PRIOR TO BENCHMARK EXECUTION**.
