# PahaarPulse — Geotechnical Field-Photo Annotator Guide

**Document Version:** v1.0 (Phase 2F)  
**Effective Date:** 2026-10-23  
**Target Audience:** Qualified Geotechnical Reviewers & Engineering Geologists  
**System Context:** PahaarPulse AI/ML Field-Photo Rapid Triage Screening  

---

## 1. Scientific Foundations & Epistemic Boundaries

### 1.1 The Golden Geotechnical Truth
**A 2D photograph captures optical surface reflections at a single instant in time; it does not capture subsurface geotechnical state.**

A field photograph cannot establish:
1. **Factor of Safety ($FS$):** Cannot calculate shear strength, internal friction angle ($\phi$), cohesion ($c$), or pore-water pressure ($u$) without laboratory testing and piezometric instrumentation.
2. **Subsurface Slip Geometry:** Cannot determine whether a failure is shallow surficial sloughing ($< 1\text{ m}$) or deep-seated rotational shearing ($> 10\text{ m}$) without borehole core logs or electrical resistivity tomography.
3. **Temporal Kinematics:** A single still frame cannot determine whether displacement occurred 10 minutes ago, 24 hours ago, or during the previous monsoon season without temporal baseline surveying.
4. **Negative Stability Proof:** **Absence of visible cracking does NOT prove slope stability.** Slopes with occluded crests, dense jungle canopy, or high phreatic surfaces can fail abruptly without visible optical warnings.

### 1.2 Epistemic Separation of Knowledge Layers

Every annotation must maintain strict boundaries across four levels:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Level 1: Directly Observable Visual Evidence                           │
│ (Bare soil scar, rockfall clasts on asphalt, arcuate ground fissure)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Level 2: Reviewer Geomorphic Inference                                 │
│ (Translational rockslide chute, active colluvial creep, stable cut)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Level 3: Independently Confirmed Geotechnical Facts                    │
│ (Borehole log, GSI landslide atlas entry, Border Roads clearance log)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Level 4: Indeterminate / Non-Observable Information                    │
│ (Fog-occluded slope crown, night capture, subsurface water table)      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Controlled Observable Indicators Taxonomy

Select all applicable indicators visible in the image. Multiple indicators must be delimited with semicolons (`;`). Do not guess features that are out of frame or occluded.

| Indicator Code | Geological / Geomorphic Definition | Visible Verification Criteria |
| :--- | :--- | :--- |
| `fresh_scarp` | Active rupture surface or detachment headwall | Unweathered soil/bedrock, sharp crest edge, lack of lichens or vegetation |
| `vegetated_relict_scarp` | Historical, dormant slip surface | Arcuate or steep slope break covered by established grass, shrubs, or weathered rock patina |
| `displaced_soil` | Colluvial or landslide soil mass | Unconsolidated soil accumulation downslope from its original source bed |
| `displaced_rock` | Detached bedrock blocks or boulders | Fragmented boulders, scree, or clasts dislodged from in-situ strata |
| `rockfall_debris` | Talus or fallen rock accumulation | Angular rock clasts scattered across roads, shoulders, ditches, or catchment terraces |
| `tension_cracks` | Extensional ground fissures | Linear, transverse, or en-echelon open cracks near slope crest, flanks, or pavement |
| `ground_deformation` | Slope creep or internal shearing | Terracettes, bulging toe, hummocky topography, tilted trees (pistol-butt curvature) |
| `debris_flow_deposit` | Saturated sediment slurry accumulation | Poorly sorted matrix-supported sediment lobe containing mud, gravel, and organic debris |
| `channel_obstruction` | Culvert or gully drainage blockage | Mud, boulders, or timber debris actively damming or choking a stream, culvert, or roadside ditch |
| `road_damage_slope_movement`| Structural deformation of transportation corridor | Asphalt cracking, shoulder drop-off, buckled pavement, or tilted guardrail caused by slope displacement |
| `water_seepage` | Active groundwater emergence | Wet soil patch on slope face, spring discharge, or unmanaged runoff eroding slope toe |
| `stable_slope` | Intact natural slope or engineered cut | Uniform vegetation cover, functional drainage, well-maintained retaining structures, zero cracking |
| `negative_control` | Non-hazard environmental setting | Open flat valley, highway corridor, distant mountain vista with no active slope movement |
| `occluded_or_degraded` | Impaired optical visibility | Dense fog, heavy rain blur, lens flare, nighttime capture, or resolution preventing interpretation |
| `insufficient_evidence` | Indeterminate framing | Extreme close-up of mud/rock with zero slope context, or uninterpretable camera angle |

---

## 3. Operational Hazard Triage Severity Classes

The five-class taxonomy (`low`, `moderate`, `high`, `critical`, `indeterminate`) represents an **operational visual-triage target** designed for emergency dispatch prioritization. It does not represent a calibrated physical factor of safety.

---

### Class 1: `low` (Nominally Stable / Negligible Visual Hazard)

#### Required Evidence (Must satisfy ALL):
1. Slope appears structurally intact with uniform vegetation cover, planar rock cuts with stable dip angles, or engineered stabilization (retaining walls, shotcrete, wire mesh).
2. Roadway, shoulder, and ditch are completely clear of rockfall, colluvium, or ponded water.
3. No visible tension cracks, scarps, bulging, or leaning trees.

#### Insufficient Evidence:
- Clear pavement alone is **insufficient** if the cut slope above is heavily fractured, overhangs the road, or shows fresh rock raveling.
- Dense tree cover alone is **insufficient** if trees exhibit distinct pistol-butt curvature indicating active soil creep.

#### When to Use `indeterminate` Instead:
- If the crown of a steep cut slope is obscured by fog, clouds, or out of frame, do **not** assume `low` hazard. Mark `indeterminate`.

---

### Class 2: `moderate` (Superficial Instability / Low Immediate Impact)

#### Required Evidence (Any of the following):
1. Minor, localized rockfall clasts confined entirely to the roadside ditch or catchment area without blocking traffic lanes.
2. Shallow, superficial rill erosion or small slumps on cut slopes where drainage is partially impaired but structural road base is intact.
3. Vegetated relict scarps showing no signs of recent reactivation.
4. Minor water seepage without piping or sediment mobilization.

#### Insufficient Evidence:
- Boulders encroaching onto the active driving lane exceed `moderate` and must be escalated to `high`.
- Open tension cracks on the road surface exceed `moderate` and must be escalated to `high`.

---

### Class 3: `high` (Active Slope Failure Threatening Infrastructure)

#### Required Evidence (Any of the following):
1. Fresh, active tension cracks visible near slope crest, flanks, or across road pavement.
2. Ongoing rock raveling or recurring boulder falls actively encroaching on traffic lanes.
3. Bulging retaining walls, deformed guardrails, or asphalt step-subsidence indicating ongoing slope shear.
4. Channelized debris flow deposit that has reached a road culvert or bridge abutment.
5. Saturated colluvial slide mass partially blocking transport lanes.

#### Expert Escalation Rule:
- If tension cracks on asphalt show open apertures $> 5\text{ cm}$ or vertical step offsets $> 10\text{ cm}$, flag for urgent geotechnical inspection.

---

### Class 4: `critical` (Imminent Catastrophic Failure or Active Disaster)

#### Required Evidence (Any of the following):
1. Massive slope rupture actively blocking an entire highway or transportation lifeline.
2. Major debris flow in progress or fresh deposits having inundated occupied structures, vehicles, or settlements.
3. Landslide dam actively blocking a river or major stream, creating an imminent Landslide Dam Outburst Flood (LDOF) threat.
4. Complete structural collapse of highway embankment, bridge abutment, or major retaining structure.
5. Large-scale translational or rotational headwall failure with ongoing active detachment.

#### Life-Safety Mandate:
- When marking `critical`, specify in `evidence_notes` whether the road is completely severed and whether structural lifelines are compromised.

---

### Class 5: `indeterminate` (Abstention / Insufficient Optical Evidence)

#### Appropriate Use (Mandatory in these conditions):
1. **Atmospheric Occlusion:** Dense monsoon fog, torrential downpour, cloud cover, or darkness obscuring $> 40\%$ of the relevant slope.
2. **Extreme Framing Limitations:** Macro close-up of a crack, rock, or mud clod with zero perspective of the surrounding slope, road, or valley.
3. **Severe Raster Degradation:** Severe camera shake, compression artifacts, or pixelation preventing geomorphic feature identification.
4. **Conflicting Optical Cues:** Ambiguous features where an expert cannot determine whether an exposed surface is a fresh failure scarp or natural rock outcrop.

---

## 4. Edge Cases & Difficult Scenarios

### 4.1 Fresh Road Cuts vs. Fresh Failure Scarps
- **Challenge:** Machine-excavated road cuts expose raw, unweathered rock and soil resembling fresh landslide headwalls.
- **Decision Rule:** Inspect for drill-hole half-casts, planar benching, wire netting, or uniform vertical faces. Excavated benches are `moderate` or `low` unless accompanied by extensional cracking, rock raveling, or toe debris accumulation.

### 4.2 Ancient Relict Features vs. Active Failures
- **Challenge:** Himalayan valleys contain massive relict landslide amphitheaters from the early Holocene.
- **Decision Rule:** Inspect for established forest, soil formation, or weathered rock patina. If the feature is ancient and currently stable with no fresh toe raveling, classify as `low` or `moderate` (with `vegetated_relict_scarp`), **not** `critical`.

### 4.3 Atypical Lithologies (e.g., Coastal Sand Dunes)
- **Challenge:** Candidate `WMC_61515158` depicts coastal sand dune cliff slumping in Lithuania.
- **Decision Rule:** While sand slip is technically mass wasting, PahaarPulse targets mountainous rock and soil slope hazard triage. Such atypical non-mountainous samples must be flagged in `evidence_notes` as `atypical_lithology`.

---

## 5. Unresolved Scientific Questions & Taxonomy Ambiguities

Reviewers should note that the following ambiguities remain active research topics in the geotechnical vision community:

1. **Velocity / Rate of Movement:** Visual evidence cannot definitively distinguish between slow creeping soil shear ($< 1\text{ mm/day}$) and fast-moving transitional slides without temporal multi-frame sequences.
2. **Hydraulic Trigger State:** An identical-looking slope may have vastly different stability on dry sunny days versus during prolonged monsoon saturation. The protocol evaluates current visual distress, not weather-conditioned probability.
3. **Scale Ambiguity:** Photographs lacking human, vehicle, or infrastructural scale objects can deceive reviewers regarding the volume of displaced material.

Document any such ambiguities in the `evidence_notes` column rather than forcing an artificial certainty.
