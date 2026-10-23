# PahaarPulse — Phase 2D: Scientific Geotechnical Annotation Protocol

**Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Evaluation Subsystem:** Gemma Vision Field-Photo Ground-Truth Benchmark Pipeline  
**Document Status:** Complete & Version-Controlled (v1.0)  

---

## Executive Summary

This protocol establishes the scientific, visual, and operational rules for creating expert ground-truth annotations for field photographs analyzed by PahaarPulse's vision models. 

A central tenet of geotechnical engineering is that **a single photograph provides optical surface evidence, not a subsurface geotechnical model**. A photograph alone cannot establish:
- Subsurface slip-surface depth or geometry without geotechnical borings or geophysical surveys.
- Movement velocity or displacement history without temporal survey points, LiDAR, or inclinometers.
- Immediate trigger causality (e.g., pore-water pressure spikes vs. toe undercutting) without hydrological data.
- Absolute factor of safety ($FS$) or time-to-failure.

Therefore, this protocol enforces strict epistemic separation between **directly observable optical evidence**, **reviewer inferences**, and **independently confirmed geotechnical facts**. It also strictly prohibits the fabrication of labels, auto-labeling via AI models, and treating non-observable factors as negative findings.

---

## 1. Epistemic Separation of Knowledge Layers

Every annotation must maintain clear boundaries across four levels of understanding:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Level 1: Directly Observable Visual Evidence                           │
│ (Scarps, rockfall clasts, asphalt cracks, muddy lobes, standing water) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Level 2: Reviewer Geomorphic Inference                                 │
│ (Likely translational slide, candidate rockfall chute, stable cut)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Level 3: Independently Confirmed Geotechnical Facts                    │
│ (Field inspection report, road closure log, inclinometer confirmation)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Level 4: Indeterminate / Non-Observable Information                    │
│ (Blind slope toes, fog occlusion, hidden water tables, scale absence)  │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Directly Observable Visual Evidence:**  
   Features plainly visible to an optical sensor: color discontinuity, exposed saprolite, tension crack lineations, displaced rock fragments, damaged guardrails, or unobstructed pavement.
2. **Reviewer Geomorphic Inference:**  
   The expert’s qualitative assessment of hazard potential (`low`, `moderate`, `high`, `critical`) based on visible geometry, slope angle, proximity to infrastructure, and recent activity indicators.
3. **Independently Confirmed Geotechnical Facts:**  
   External validation (e.g. Geological Survey of India reports, municipal road maintenance logs, or GPS georeferencing) confirming that an event occurred at that coordinate and time.
4. **Indeterminate / Non-Observable Information:**  
   Features that cannot be established from the photograph. Crucially, **the absence of visible cracks does NOT equal proof of stability** if the slope crown is occluded by vegetation, fog, or out of frame. Such conditions must be flagged as `uncertain` or `indeterminate`.

---

## 2. Controlled Observable Indicators Taxonomy

Annotations must select from the standardized indicator taxonomy (`CONTROLLED_OBSERVABLE_INDICATORS`) in `backend/app/services/vlm_evaluation.py`. Multiple indicators must be delimited by semicolons (`;`).

### 2.1 Slope Failure & Scarp Evidence
- `fresh_scarp`: High-angle, unweathered break in slope exposing raw soil or freshly fractured bedrock. Lacks lichens or pioneer herbaceous cover.
- `vegetated_relict_scarp`: Arcuate or steep slope break showing established vegetation, weathered rock surfaces, or soil creep hummocks indicating historical, non-active failure.
- `displaced_soil`: Colluvial or landslide soil debris deposited downslope from its original source area.
- `displaced_rock`: Detached bedrock blocks, boulders, or shattered scree located away from in-situ strata.

### 2.2 Rockfall & Slope Collapse
- `rockfall_debris`: Accumulation of angular rock clasts, talus deposits, or impact craters on roads, ditches, or toe terraces.
- `ground_deformation`: Visible bulging, stepped terraces, hummocky topography, or leaning trees (pistol-butt trees) indicating active slope movement.
- `tension_cracks`: En-echelon, transverse, or marginal fissures in soil or bedrock, typically located near the crown, flanks, or crest of a slope.

### 2.3 Debris Flows & Drainage
- `debris_flow_deposit`: Poorly sorted, matrix-supported sediment lobe containing mud, gravel, cobbles, and organic debris deposited in an alpine torrent or alluvial fan.
- `channel_obstruction`: Debris, sediment, or fallen timber actively blocking a culvert, roadside drainage ditch, or mountain stream.
- `water_seepage`: Visible groundwater discharge, spring emergence, damp soil patches on slope faces, or unmanaged surface runoff eroding a slope cut.

### 2.4 Infrastructure & Roadway Damage
- `road_damage_slope_movement`: Cracking, subsidence, shoulder drop-off, guardrail displacement, or asphalt distortion directly contiguous with an adjacent slope instability.
- `roadway_clearing_operation`: Heavy machinery (graders, excavators, dump trucks) actively removing landslide deposits or blasted rockfall debris from transportation corridors.

### 2.5 Negative Controls (Stable Ground)
- `stable_slope`: Slopes showing continuous undisturbed vegetation, mature tree growth without curvature, planar/uniform geometry, and stable engineered retaining walls.
- `negative_control`: Verified non-hazard scenes (e.g., intact mountain passes, well-drained highway corridors, flat plateau terrain) providing essential balance to prevent false positives.

### 2.6 Data Quality & Degradation
- `occluded_or_degraded`: Image obscured by fog, rainfall, lens flares, motion blur, extreme distance, or night conditions.
- `insufficient_evidence`: Scene lacks sufficient context, depth reference, or scale to establish slope geometry or hazard indicators reliably.

---

## 3. Controlled Annotation Schema

Annotations must be recorded in versioned files (e.g. `docs/gemma-local-vision/evaluation/phase_2d_annotations_template.csv`) following this 11-column specification:

| Field Name | Type | Allowed Values / Format | Description |
| :--- | :--- | :--- | :--- |
| `candidate_id` | String | `WMC_[0-9]+` (matches manifest) | Unique candidate identifier from discovery manifest. |
| `image_sha256` | String | 64-character lowercase hexadecimal | Exact cryptographic hash of image bytes on disk. |
| `annotator_id` | String | `EXPERT_[A-Z0-9_-]+` | Anonymized identifier of qualified human reviewer. |
| `annotation_version` | String | `v[0-9]+\.[0-9]+` (e.g. `v1.0`) | Immutable version identifier for this annotation pass. |
| `observable_indicators` | String | Semicolon-delimited controlled indicators | Semicolon-separated list from Section 2 (or empty if pending). |
| `image_quality` | Enum | `high_resolution`, `adequate`, `low_resolution`, `occluded_or_degraded` | Visual quality assessment for model consumption. |
| `reviewer_label` | Enum | `none`, `low`, `moderate`, `medium`, `high`, `critical`, `indeterminate` | Categorical geotechnical hazard triage label. |
| `confidence` | Enum | `certain`, `probable`, `tentative`, `indeterminate` | Reviewer subjective certainty based on optical evidence. |
| `evidence_notes` | String | Freeform text | Specific geomorphic observations justifying the label. |
| `review_status` | Enum | `pending_review`, `draft`, `completed`, `adjudicated`, `rejected` | Workflow lifecycle state of this record. |
| `reviewed_at` | String | ISO-8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`) | Exact date and time annotation was finalized. |

### 3.1 Strict State Transition Rules
- If `review_status == "pending_review"`: `reviewer_label` MUST be empty or `"indeterminate"`, `annotator_id` must be empty, and `reviewed_at` must be empty.
- If `review_status == "completed"`: `annotator_id`, `reviewer_label`, `confidence`, and `reviewed_at` MUST be populated.
- If `review_status == "adjudicated"`: `reviewer_label` MUST be populated with the consensus label (cannot be `"pending"`), and `evidence_notes` must record the adjudication rationale.
- **Prohibition of AI Annotators:** Any `annotator_id` matching `gemma*`, `gemini*`, `ollama*`, `gpt*`, `claude*`, `ai_*`, `model_*`, or `bot_*` is immediately rejected by [`AIAnnotatorProhibitedError`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/vlm_evaluation.py).

---

## 4. Multi-Reviewer Adjudication Protocol

To guarantee scientific reproducibility and minimize single-reviewer bias, ground-truth labels for PahaarPulse evaluation must follow a dual-independent review protocol:

```
                        [Candidate Image]
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
       [Reviewer A (Blind)]            [Reviewer B (Blind)]
                │                               │
                └───────────────┬───────────────┘
                                ▼
                   [Automated Agreement Check]
                                │
         ┌──────────────────────┴──────────────────────┐
         ▼                                             ▼
 [Full Agreement]                             [Discordance / Gap]
         │                                             │
         │                                             ▼
         │                                  [Lead Geotechnical Adjudicator]
         │                                             │
         └──────────────────────┬──────────────────────┘
                                ▼
              [Final Consensus Adjudicated Label]
```

### 4.1 Independent Blind Review
- **Reviewer Qualifications:** Reviewers must hold a degree in Civil/Geotechnical Engineering, Engineering Geology, Geomorphology, or have documented landslide inventory mapping training.
- **Independence:** Reviewer A and Reviewer B annotate the candidate set without seeing each other's labels, notes, or model predictions.
- **Prohibition on Model Output Exposure:** Reviewers must NEVER be shown Gemma or Gemini predictions prior to completing their independent annotations.

### 4.2 Inter-Rater Reliability Assessment
Prior to adjudication, inter-rater reliability must be quantified using Cohen's Kappa ($\kappa$) for categorical ratings:

$$\kappa = \frac{P_o - P_e}{1 - P_e}$$

where $P_o$ is observed relative agreement and $P_e$ is hypothetical chance agreement.
- $\kappa \ge 0.75$: Strong agreement; proceeding directly to consensus sign-off.
- $0.40 \le \kappa < 0.75$: Moderate agreement; all discordant pairs require formal adjudication meeting.
- $\kappa < 0.40$: Inadequate reliability; protocol definitions and image clarity must be re-evaluated before benchmarking.

### 4.3 Adjudication Mechanism
For cases where Reviewer A and Reviewer B disagree:
1. A senior Geotechnical Adjudicator reviews the image, Reviewer A notes, and Reviewer B notes.
2. If optical evidence supports a clear geomorphic conclusion, the adjudicator issues the final label with documented reasoning in `evidence_notes`.
3. If optical evidence is genuinely ambiguous (e.g. cannot tell if road collapse is from landslide or poor subgrade compaction), the final label is conservatively adjudicated as `indeterminate`.
4. The adjudicated record is assigned `review_status = "adjudicated"`.

---

## 5. Data Separation & Versioning Architecture

To protect production workflows and evaluation benchmarks from accidental corruption:

1. **Separation from Discovery Manifests:**  
   [`public_image_candidates.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/public_image_candidates.csv) tracks acquisition, licensing, and file download state. It is never edited during annotation.
2. **Separation from Draft Benchmarks:**  
   [`public_benchmark_draft.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/public_benchmark_draft.csv) preserves the unlabelled draft format with empty ground-truth fields until consensus adjudication is officially merged.
3. **Dedicated Versioned Annotation Files:**  
   Human annotations are stored in dedicated versioned files (e.g. `phase_2d_annotations_template.csv`, `phase_2d_annotations_v1.0.csv`).
4. **Automated Schema Validation:**  
   All annotation CSVs must pass [`AnnotationValidator.load_and_validate_annotations_csv()`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/vlm_evaluation.py) before being merged into the evaluation harness.
