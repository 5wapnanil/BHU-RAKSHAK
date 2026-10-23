# PahaarPulse — Phase 2F: Dataset Expansion Plan & Sourcing Specification

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Strategic Goal:** Evidence-Driven Expansion of the Field-Photo Evaluation Benchmark  
**Baseline Dataset:** 54 Public Candidate Images (174.39 MB)  
**Expansion Phasing:** Phase 3 Execution Plan (No automated downloads in Phase 2F)  

---

## 1. Executive Summary & Expansion Strategy

The Phase 2F Dataset Coverage Audit demonstrated that while the current 54 candidate images successfully validated the ingestion pipeline, data schema, and manifest hashing infrastructure, the dataset is **statistically and geographically underpowered** for operational certification in the Indian Himalayan Region (IHR).

### 1.1 The Three Core Deficits
1. **Severe Geographic Deficit:** Only 2 of 54 images (3.7%) represent the Indian Himalayas (both from a single site in Himachal Pradesh). 96.3% originate from foreign mountain ranges (Alps, Rockies, Caucasus, Taiwan, Baltics).
2. **Perspective Confounding in Negative Controls:** 100% of the 10 negative controls are panoramic mountain pass vistas (`landscape_pass`), while 85% of hazard images are mid-range slope cuts (`slope_face`) or ground-level scenes (`ground_level_roadside`). This introduces a dangerous shortcut learning vulnerability.
3. **Severe Shortage of Precursor Indicators:** Tension cracks appear in only 2 candidates, and roadside culvert drainage blockages appear in only 1 candidate, skewing the benchmark heavily toward post-disaster debris lobes rather than early-warning distress features.

### 1.2 Core Principle of Expansion
**Expansion must be driven by independent site diversity, geomorphic balance, and strict legal provenance—not by raw image volume.** Adding 100 near-identical photographs from the same rockfall scar produces the illusion of a large dataset while providing zero statistical power.

---

## 2. Targeted Acquisition Priorities

```
┌────────────────────────────────────────────────────────────────────────┐
│ Current Cohort (N=54): Global Pilot Dataset                            │
│ • 3.7% Indian Himalayas                                                │
│ • 100% Panoramic Controls                                              │
│ • 2 Tension Crack Images                                               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ Phase 3 Expansion Drive
┌────────────────────────────────────────────────────────────────────────┐
│ Target Cohort (N=250–350 Independent Samples):                         │
│                                                                        │
│ 1. Indian Himalayan Corridors (>= 40% of cohort)                       │
│    • Uttarakhand (Rishikesh-Badrinath NH-58, Mandakini Valley NH-107)  │
│    • Himachal Pradesh (Manali-Leh NH-3, Hindustan-Tibet NH-5)          │
│    • Sikkim & North Bengal (Sevoke-Gangtok NH-10)                      │
│                                                                        │
│ 2. True Negative Roadside Controls (>= 20% of cohort)                  │
│    • Engineered slopes with intact wire mesh, shotcrete, soil nails    │
│    • Undamaged retaining walls and gabion baskets                      │
│    • Paved mountain highways with clear, functioning drainage ditches  │
│                                                                        │
│ 3. Precursor & Early-Warning Distress (>= 20% of cohort)              │
│    • Crown tension cracks, asphalt step-subsidence                     │
│    • Active water seepage patches on cut slope faces                   │
│    • Culvert and ditch blockages causing ponding                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Gap Specifications

### 3.1 Priority 1: Indian Himalayan Region (IHR) Field Photos
- **Target Count:** +100 to +120 new candidates.
- **Geographic Focus:**
  - **Uttarakhand:** Chamoli, Rudraprayag, Uttarkashi, Pithoragarh, Tehri Garhwal highway segments.
  - **Himachal Pradesh:** Kullu, Mandi, Kinnaur, Shimla, Kangra valley corridors.
  - **Sikkim & West Bengal:** Teesta River gorge, Gangtok highway corridor.
- **Geological Diversity Requirements:**
  - Highly weathered, fractured Precambrian metamorphics (phyllites, schists, quartzites).
  - Tectonically sheared Main Central Thrust (MCT) and Main Boundary Thrust (MBT) zones.
  - Colluvial overburden slopes prone to rainfall-induced slumping.

### 3.2 Priority 2: Matched Roadside Negative Controls
- **Target Count:** +40 to +50 new candidates.
- **Scene Type Mandate:** Must be strictly `ground_level_roadside` or `slope_face` (matching the perspective of hazard reports).
- **Required Visual Features:**
  - Stable, engineered mountain highway cut slopes with mature vegetation or structural facing.
  - Paved asphalt in pristine condition with visible road markings and clear ditches.
  - Dry or well-drained retaining structures showing zero bulging, cracking, or settlement.
- **Purpose:** Eliminates the panoramic shortcut confound, forcing models to evaluate slope distress rather than horizon composition.

### 3.3 Priority 3: Precursor Indicators & Infrastructure Damage
- **Target Count:** +40 to +50 new candidates.
- **Specific Visual Features:**
  - `tension_cracks`: En-echelon fractures on soil cuts, arcuate pavement cracks on road shoulders.
  - `water_seepage`: Visible spring emergence, wet saprolite patches, unmanaged runoff eroding slope toes.
  - `road_damage_slope_movement`: Asphalt shear steps, tilted crash barriers, bulging retaining masonry.
  - `channel_obstruction`: Silted culvert inlets, debris-dammed roadside ditches.

---

## 4. Sourcing Strategy & Provenance Standards

Candidate images will be discovered across three vetted scientific channels:

### 4.1 Approved Public Channels
1. **Government Open Data & Disaster Survey Archives:**
   - Geological Survey of India (GSI) public landslide documentation and open disaster assessment reports.
   - National Disaster Management Authority (NDMA) public domain field survey imagery.
   - United States Geological Survey (USGS) Landslide Hazards Program public domain repository.
2. **Open-Access Scientific Literature (CC-BY 4.0):**
   - Articles in open-access journals (*Landslides*, *Natural Hazards and Earth System Sciences*, *Engineering Geology*, *Geomatics, Natural Hazards and Risk*) published under Creative Commons Attribution licenses.
   - Extraction of field photograph figures with complete DOI and author attribution.
3. **Wikimedia Commons (Targeted Sourcing):**
   - Verified open categories: `Landslides in India`, `Roads in Uttarakhand`, `Roads in Himachal Pradesh`, `Landslide damage to roads`.
   - Automated query scripts executing `discover_public_landslide_images.py` with bounding box and category filters.

### 4.2 Legal Provenance & Licensing Mandate
Every newly proposed candidate must pass the Phase 2B provenance audit before ingestion:
- **Approved Licenses:** CC0, Public Domain (US Gov / State Gov with open terms), CC-BY (all versions), CC-BY-SA (all versions), CC-BY-NC (for research benchmarks).
- **Prohibited:** Blank licenses, all-rights-reserved commercial photography, stock photo watermarks, and unverified terms.
- **Attribution Evidence:** Author name, source URL, license identifier, and license URL must be recorded in `license_provenance_audit.csv`.

---

## 5. Statistical Power & Sample Size Justification

### 5.1 Misconception of the "Universal 384"
Phase 2E demonstrated that estimating a single binomial proportion with margin of error $E = \pm 5\%$ at 95% confidence requires $N \approx 384$. However, applying this number universally to a 5-class clustered benchmark is statistically invalid because:
1. **Categorical Triage is Multinomial, Not Binomial:** A 5-class problem distributes support across 5 bins.
2. **Unequal Class Prevalence:** Landslide occurrences in real datasets are naturally skewed; `critical` and `high` events occur less frequently than `moderate` or `low` in general screening, but more frequently in emergency dispatch.
3. **Intra-Cluster Correlation ($DEFF$):** Multiple photos from the same event or valley exhibit clustering. If photos from the same event have intraclass correlation $\rho$, the effective sample size is:
   $$N_{\text{eff}} = \frac{N}{1 + (m - 1)\rho}$$
   Where $m$ is the average cluster size and $DEFF = 1 + (m-1)\rho > 1.0$.

### 5.2 Methodologically Justified Sample Target
For the PahaarPulse Phase 3 benchmark:
- **Minimum Independent Sites ($M$):** At least **180 to 220 unique geographic sites/events**.
- **Average Photos per Site ($m$):** $\le 1.8$ (strictly avoiding large clusters; max 3 photos per site).
- **Target Benchmark Size ($N$):** **$N = 300 \text{ to } 350 \text{ images}$**.
- **Per-Class Support Requirement:**
  - `low`: $\ge 60$ samples (including $\ge 40$ matched roadside controls)
  - `moderate`: $\ge 60$ samples
  - `high`: $\ge 60$ samples
  - `critical`: $\ge 50$ samples
  - `indeterminate`: $\ge 40$ samples (calibrated abstention test suite)
- **Resulting Precision:** At $N=300$, overall accuracy margin of error is $\pm 5.6\%$ at 95% confidence, and per-class recall for a class with $N_c = 60$ achieves a 95% Wilson CI margin of error of $\pm 11.5\%$. This represents the scientifically defensible threshold for operational safety validation.

---

## 6. Ingestion Guardrails & Execution Protocol

During this Phase 2F milestone, **no automated downloading or dataset expansion is executed**. Ingestion of new candidates will take place in Phase 3 under the following strict execution protocol:

1. **Staged Candidate Register:** New candidate URLs and metadata must first be written to a staging manifest (`phase_3_candidates_staging.csv`).
2. **Pre-Download License Audit:** Candidate licenses must be verified by automated audit scripts before initiating HTTP download requests.
3. **Hash Deduplication:** Candidate SHA-256 hashes must be verified against the existing 54 hashes to guarantee zero duplicates.
4. **Raster Decode Gate:** Newly downloaded images must pass PIL raster integrity checks and meet the elevated resolution threshold ($\ge 800 \times 800\text{ px}$).
5. **Split Assignment Guard:** New candidates must be assigned to evaluation splits based on cluster IDs to prevent cross-split data leakage.
