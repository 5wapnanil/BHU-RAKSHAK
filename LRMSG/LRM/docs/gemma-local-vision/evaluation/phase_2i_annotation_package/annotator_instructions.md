# PahaarPulse — Phase 2I: Human Annotator Instructions

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Target Audience:** Independent Geotechnical Reviewers (Reviewer 1 and Reviewer 2)  

---

## 1. Introduction & Ethical Responsibilities

Thank you for participating in the scientific evaluation of PahaarPulse's field-hazard screening system.

Your annotations provide the foundational ground truth against which AI vision models will be evaluated for early landslide hazard detection in mountain highway corridors (particularly the Indian Himalayan Region).

### 1.1 Critical Ethical Principles
- **Strict Independence:** You must complete your annotations independently. Do not consult, discuss, or share your annotations with any other reviewer until formal adjudication begins.
- **Epistemic Honesty:** Do not guess. If an image is ambiguous, blurry, or lacks sufficient geological context, record `UNCERTAIN_INSUFFICIENT_CONTEXT`. Acknowledging uncertainty is a scientifically valuable label.
- **No Search Engine Lookups:** Do not attempt to search for the original image online using reverse image search or image titles. Your evaluation must be based exclusively on the visual evidence contained within the provided photograph.

---

## 2. Step-by-Step Annotation Procedure

### Step 1: Open the Image
- Locate the image file corresponding to your assigned `annotation_id` (e.g., `ANN_001.jpg` through `ANN_102.jpg`).
- Open the raster file in an uncompressed image viewer at 100% native resolution.

### Step 2: Perform 4-Zone Visual Inspection
Examine the photograph systematically across four spatial zones:
1. **Zone 1: Roadway Surface & Shoulders**
   - Is the driving lane clear, partially obstructed, or completely severed?
   - Are there fresh rock boulders, mud accumulation, or soil debris on the pavement?
   - Are there visible cracks (longitudinal, transverse, or crescent) in the asphalt?
2. **Zone 2: Cut Slope & Hillside Face**
   - Is there an exposed, unvegetated soil scar or rock shear surface?
   - Are trees or utility poles tilted, bent, or uprooted?
   - Can you identify an active head scarp or lateral shear margin?
3. **Zone 3: Engineered Infrastructure**
   - Are retaining walls visible? Are they vertical and intact, or bulging, cracked, or overturned?
   - Are roadside drainage ditches and culvert inlets clear, silted up, or destroyed?
   - Is rockfall drape netting installed? Is it holding loose rock safely or ruptured?
4. **Zone 4: Atmospheric & Image Quality Context**
   - Is the image sharp and clear?
   - Are parts of the scene occluded by dense fog, heavy rainfall spray, or dark shadows?
   - Is the slope too far away to resolve individual boulders or fractures?

### Step 3: Select Primary Category
Based on your 4-zone inspection, select exactly **one** primary category:
- `ACUTE_SLOPE_FAILURE_OR_DEBRIS`: Mass displacement, rockfall on road, debris runout, or active washout.
- `PRECURSOR_INSTABILITY_INDICATOR`: Sub-failure deformation, asphalt tension cracks, scarp formation, road-edge subsidence.
- `INTACT_ENGINEERING_CONTROL`: Functioning retaining wall, clean culvert/ditch, pinned rockfall mesh.
- `CONTEXTUAL_TERRAIN_LANDSCAPE`: Panoramic pass, stable mountain terrain, highway with no visible failure or prominent mitigation.
- `UNCERTAIN_INSUFFICIENT_CONTEXT`: Severe blur, distant vista, or ambiguous features where certainty cannot be reached.
- `UNUSABLE_OUT_OF_SCOPE`: Non-geotechnical subject, interior scene, corrupted image.

### Step 4: Record Confidence & Observable Indicators
- **Confidence:** Assign `HIGH`, `MEDIUM`, or `LOW`.
- **Observable Indicators:** List specific optical features separated by semicolons (e.g., `boulder_debris; blocked_lane; scarp; damaged_guardrail`).
- **Quality Limitations:** Record `NONE`, `BLURRED`, `DISTANT`, `LOW_CONTRAST`, or `OCCLUDED`.

### Step 5: Write Geomorphic Rationale
Write a concise, 1–3 sentence rationale explaining the physical justification for your decision.  
*Example:* "Active rockfall event with three angular gneissic boulders (>1 m diameter) obstructing the northbound highway lane. Fresh rock detachment scarp visible on the cut slope directly above."

### Step 6: Flag for Adjudication
If you find the image borderline or difficult to categorize, set `requires_adjudication = YES`.

---

## 3. Decision Matrix & Common Edge Cases

| Visual Scenario | Correct Category | Common Mistake to Avoid |
| :--- | :--- | :--- |
| **Loose gravel along unpaved mountain road shoulder** | `CONTEXTUAL_TERRAIN_LANDSCAPE` | Do NOT mistake routine unpaved road aggregate for landslide debris. |
| **Roadside ditch directing flowing storm water safely** | `INTACT_ENGINEERING_CONTROL` | Do NOT mistake flowing drainage water for a mudflow or flood disaster. |
| **Paved road with 2 cm wide crescent cracks near slope edge** | `PRECURSOR_INSTABILITY_INDICATOR` | Do NOT wait for full road collapse to record hazard indicators. |
| **Wire mesh on cut slope holding cobbles in place** | `INTACT_ENGINEERING_CONTROL` | Trapped rocks indicate the netting is functioning as designed. |
| **Massive landslide scar covered in thick secondary vegetation** | `CONTEXTUAL_TERRAIN_LANDSCAPE` or `ACUTE_SLOPE_FAILURE_OR_DEBRIS` (depending on reactivation) | If fully revegetated with no fresh movement, it is a historical dormant landform. |
| **Heavy monsoonal fog obscuring entire mountain slope** | `UNCERTAIN_INSUFFICIENT_CONTEXT` | Do NOT assume hazard presence when the slope is invisible. |

---

## 4. Submitting Your Annotations

1. Ensure all 102 rows in your copy of `annotation_form.csv` are populated.
2. Confirm your `reviewer_id` and ISO 8601 timestamps are present on all completed rows.
3. Save the CSV file with UTF-8 encoding.
4. Deliver the completed file directly to the Geotechnical Adjudication Lead.
