# PahaarPulse — Phase 2I: Expert Annotation Protocol

**Protocol Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Authority:** Geotechnical Data-Quality Specialist & Evaluation Working Group  

---

## 1. Scope & Scientific Objectives

This protocol governs the human geotechnical annotation of ground-level field photographs for the PahaarPulse Vision-Language Model (VLM) hazard screening evaluation.

The goal is to produce an authoritative, leakage-resistant benchmark that measures the model's ability to:
1. Detect acute, road-blocking or slope-deforming mass wasting events.
2. Recognize subtle early-warning precursor indicators (tension cracks, head scarps, subsidence).
3. Differentiate intact engineering slope mitigations (retaining walls, drainage ditches, rockfall netting) from active slope hazards to prevent false-alarm cascades.
4. Express appropriate epistemic modesty when visual context is occluded, distant, or ambiguous.

---

## 2. Epistemic Guardrails: What a Single 2D Photograph Can and Cannot Establish

Annotators must adhere to the three evidentiary levels defined in the Phase 2E protocol:

```
Evidentiary Tier                Definition & Capabilities
─────────────────────────────────────────────────────────────────────────────────────────────
Level 1: Directly Observable    Visible surface features directly captured in the optical 2D raster:
Optical Evidence                exposed soil scarps, rock rubble on road surface, tension cracks in
                                asphalt, concrete retaining walls, functional drainage culverts,
                                wire mesh pinning, heavy rainfall, or dense vegetation.
─────────────────────────────────────────────────────────────────────────────────────────────
Level 2: Expert Geomorphic      Inferences regarding mass-wasting mechanisms derived from Level 1:
Inference                       debris flow runout vs. planar rockfall, tension crack extension along
                                slip surface, culvert sediment choking vs. clear drainage.
─────────────────────────────────────────────────────────────────────────────────────────────
Level 3: Confirmed Geotechnical Subsurface realities: pore water pressure, internal shear planes,
Ground Reality                  soil cohesion, and historical slip depth. CANNOT be established
                                from a single surface photograph.
─────────────────────────────────────────────────────────────────────────────────────────────
```

> [!CAUTION]
> **The Negative Control Fallacy:**  
> A photograph showing an intact retaining wall or a clear road surface establishes only that **no active structural collapse is visible in that camera frame**. It does **not** prove that the slope is geotechnical risk-free, nor does it guarantee slope stability under future extreme precipitation.

---

## 3. Primary Observation Category Taxonomy

Every image must be classified into exactly **one** of the following six primary observation categories:

### Category 1: `ACUTE_SLOPE_FAILURE_OR_DEBRIS`
- **Definition:** The photograph contains definitive visible evidence of an active, ongoing, or recently occurred mass wasting failure.
- **Observable Indicators:**
  - Fresh, unvegetated slip surface, scarp, or shear face.
  - Debris flow runout, mudflow deposits, or saturated sediment deposition.
  - Rockfall boulder accumulation on roadway, ditch, or downslope shoulder.
  - Partial or complete road blockage, guardrail destruction, or structural impact.
- **Examples in Dataset:** Rock clearing on Rohtang Pass highway (`ANN_024`, `ANN_025`), landslide scarps in Chamoli/Tharali (`ANN_040`, `ANN_087`), active slide along Kinnaur corridor (`ANN_084`).

### Category 2: `PRECURSOR_INSTABILITY_INDICATOR`
- **Definition:** The slope or roadway has not experienced complete catastrophic collapse, but exhibits observable physical manifestations of incipient or accelerating deformation.
- **Observable Indicators:**
  - En-echelon, arcuate, or longitudinal tension cracks in asphalt pavement or unpaved shoulder.
  - Fresh minor crown scarps or terracing above road cut slopes.
  - Road-edge subsidence, shoulder sagging, or outward guardrail tilt.
  - Bulging, outward tilting, or structural fracturing of retaining walls without total collapse.
  - Uncontrolled water seepage discharging directly from cut-slope face.
- **Examples in Dataset:** Pavement tension cracks on mountain highway (`ANN_009`), roadside cracking in Conwy (`ANN_008`).

### Category 3: `INTACT_ENGINEERING_CONTROL` (Negative Control)
- **Definition:** The photograph prominently depicts man-made geotechnical engineering infrastructure installed to stabilize the slope or manage runoff, with no visible signs of structural failure.
- **Observable Indicators:**
  - Concrete, masonry, or gabion gravity retaining walls supporting roadway cut slopes.
  - Pinned wire mesh, rockfall catch fences, or drapery netting anchored to rock faces.
  - Concrete-lined roadside drainage ditches, box culverts, or runoff channels directing water safely.
  - Horizontal drains or weep holes actively draining slope faces without surface scouring.
- **Examples in Dataset:** Pinned rockfall netting installations on highway slopes (`ANN_049`–`ANN_058`), culverts and ditches in Zanskar and UK mountain tracks (`ANN_046`, `ANN_048`).

### Category 4: `CONTEXTUAL_TERRAIN_LANDSCAPE`
- **Definition:** High-altitude, mountain pass, or valley landscape imagery providing geological and regional context, but lacking specific slope instability features, road failure, or prominent engineered mitigation.
- **Observable Indicators:**
  - Stable natural mountain slopes with undisturbed forest canopy or alpine meadow vegetation.
  - Mountain road corridors with stable cut slopes and no visible debris or cracking.
  - Panoramic vista of mountain passes (e.g., Cumberland Pass, Carnero Pass, Eğribel Pass).
- **Examples in Dataset:** Mountain passes in Colorado and Alps (`ANN_037`, `ANN_039`, `ANN_042`).

### Category 5: `UNCERTAIN_INSUFFICIENT_CONTEXT`
- **Definition:** Visual context is inadequate to determine slope condition, hazard presence, or infrastructure integrity with scientific confidence.
- **Observable Indicators:**
  - Distant panoramic perspective where slope face or road surface cannot be resolved.
  - Severe environmental occlusion (dense fog, heavy monsoonal rain spray, nighttime shadow).
  - Oblique camera angle where slope crown, toe, or pavement edge is completely out of frame.
  - Ambiguous debris that cannot be distinguished from routine roadside construction or unpaved road gravel.

### Category 6: `UNUSABLE_OUT_OF_SCOPE`
- **Definition:** Photograph does not represent an outdoor geological or ground-level roadside scene, or exhibits fatal raster defects.
- **Observable Indicators:**
  - Non-geotechnical subject matter (e.g., interior structures, vehicles, biological specimens).
  - Severe raster corruptions, extreme compression artifacts, or extreme motion blur.
  - Historical scans, book diagrams, or non-photographic graphics.

---

## 4. Required Field Specifications

For every evaluated photograph, annotators must record:

| Field Name | Allowed Values | Description |
| :--- | :--- | :--- |
| `annotation_id` | `ANN_001` to `ANN_102` | Controlled opaque image reference. |
| `reviewer_id` | Pseudonymous string (e.g., `REV_A1`, `REV_B2`) | Unique identifier for the human evaluator. |
| `review_timestamp` | ISO 8601 UTC timestamp | Exact completion timestamp (`YYYY-MM-DDTHH:MM:SSZ`). |
| `primary_category` | Exactly one of Categories 1–6 | The authoritative primary classification. |
| `confidence_level` | `HIGH`, `MEDIUM`, `LOW` | Subjective certainty in primary category assignment. |
| `observable_indicators` | Semicolon-delimited strings | Specific optical features seen (e.g., `boulder_debris; blocked_lane; scarp`). |
| `image_quality_limitations`| `NONE`, `BLURRED`, `DISTANT`, `LOW_CONTRAST`, `OCCLUDED` | Quality impediments affecting visual inspection. |
| `geomorphic_rationale` | Concise narrative (1–3 sentences) | Geotechnical explanation supporting the chosen category. |
| `requires_adjudication` | `YES` or `NO` | Flagged if the annotator considers the case ambiguous or borderline. |
| `review_status` | `COMPLETED` | Updated from `PENDING` upon form submission. |
| `protocol_version` | `v1.0` | Invariant protocol version tracker. |

---

## 5. Ambiguity & Borderline Case Decision Rules

1. **Active Failure vs. Early Precursor:** If displaced material has physically detached and accumulated across the road surface or shoulder, classify as `ACUTE_SLOPE_FAILURE_OR_DEBRIS`. If cracks are opening without major mass displacement, classify as `PRECURSOR_INSTABILITY_INDICATOR`.
2. **Damaged Retaining Wall:** If an engineered retaining wall shows bulging, cracking, or partial displacement, classify as `PRECURSOR_INSTABILITY_INDICATOR`. If the wall has suffered total blowout and structural collapse, classify as `ACUTE_SLOPE_FAILURE_OR_DEBRIS`.
3. **Engineered Netting with Trapped Rocks:** Pinned or draped wire mesh holding minor gravel/cobbles is designed to do so and remains functional; classify as `INTACT_ENGINEERING_CONTROL`. If the netting is ruptured, overtopped, or actively failing, classify as `ACUTE_SLOPE_FAILURE_OR_DEBRIS`.
4. **Resolution Deficits:** If you cannot discern whether material on a road is rockfall debris or gravel surfacing due to low contrast or distance, do **not** guess. Classify as `UNCERTAIN_INSUFFICIENT_CONTEXT` and flag `requires_adjudication = YES`.
