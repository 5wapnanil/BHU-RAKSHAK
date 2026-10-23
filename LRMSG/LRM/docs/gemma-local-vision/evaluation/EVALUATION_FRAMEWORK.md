# PahaarPulse — VLM Geotechnical Evaluation Framework

## 1. Executive Grounding & Repository Audit Findings

### 1.1 Dataset Availability Audit
A systematic audit of the PahaarPulse codebase and storage volumes was conducted:
- **Tabular/Geospatial Datasets:** The repository contains regional meteorological and geotechnical tabular datasets (`extensive_validation_summary.csv` containing rainfall and root-zone soil moisture features evaluated against XGBoost and AHC models).
- **Field Photographs:** The directory `backend/uploads/field_reports` contains raw photographs uploaded via field reporting workflows.
- **Ground Truth Determination:** **No expert-reviewed, geotechnically labelled ground-truth photograph dataset currently exists in the repository.** The single operational database record contains an automated hosted model prediction (`ai_hazard_level = critical`, `ai_confidence = 0.95`) with human review status `pending`.

### 1.2 Scientific Integrity Rule
In accordance with professional engineering ethics and safety standards:
- **Model predictions and synthetic examples must NEVER be treated as ground truth.**
- **No statistical accuracy, sensitivity, or specificity claims are made without an independently adjudicated, expert-labelled dataset.**
- This framework provides the formal evaluation protocol, dataset schema, and reproducible evaluation pipeline to benchmark models once an adjudicated dataset is collected.

---

## 2. Standardized Hazard Classification Taxonomy

Ground-truth adjudication and model predictions are mapped to a 5-tier classification:

| Hazard Class | Geotechnical Definition | Visible Physical Evidence |
| :--- | :--- | :--- |
| **`low`** | Stable slope with negligible probability of immediate failure. | Intact slope vegetation, stable road shoulders, minor surface wash or shallow rills without displacement, dry surface. |
| **`moderate`** | Incipient instability or minor localized slope movement. | Minor sloughing, localized debris on road margin, tension cracks $<1$ cm width without vertical offset, minor water seeps. |
| **`high`** | Active, progressing slope instability presenting significant hazard. | Tension cracks $>1$ cm width, observable head scarp formation, partial road collapse, active rockfall accumulation, bulging toe. |
| **`critical`** | Catastrophic failure or imminent collapse threatening life or infrastructure. | Major rotational or translational slide, complete roadway breach, large debris flow blocking route, destroyed retaining structures. |
| **`indeterminate`** | Insufficient or compromised visual evidence to make a determination. | Obscured view, heavy vegetation blocking slope, distant perspective lacking scale, glare, motion blur, night/low-light condition. |

### Geotechnical Indicator Taxonomy
Reviewers and models identify standardized discrete physical indicators:
- `tension_cracks`: Longitudinal or transverse fissures in pavement or soil.
- `slope_displacement`: Downward or outward translation of soil/rock mass.
- `road_blockage`: Debris, boulders, or collapsed road surface obstructing traffic.
- `rockfall_debris`: Detached stones, boulders, or scree accumulated below a rockface.
- `structural_damage`: Compromised retaining walls, culverts, gabions, or guardrails.
- `toe_erosion`: Undercutting of slope base by drainage or stream flow.
- `mudflow`: Saturated, viscous slurry of fine-grained soil and rock.
- `water_seepage`: Visible active groundwater discharge or saturated piping on face.

---

## 3. Ground-Truth Adjudication Protocol

To prevent subjective bias and ensure clinical-grade reliability:

1. **Independent Dual Review:** Each photograph must be evaluated independently by two qualified engineering geologists or geotechnical engineers without access to model outputs.
2. **Consensus Requirement:** If both experts agree on the hazard class and key physical indicators, the label is marked `adjudicated`.
3. **Third-Party Adjudication:** If the independent reviewers disagree, a senior geotechnical adjudicator reviews the photograph and field notes to establish the final consensus label.
4. **Data Isolation:** Evaluation datasets must be maintained in a dedicated directory outside the operational database and production upload directories.
5. **Data Privacy & Governance:** Local field photographs may depict private property, identifying features, or disaster victims. Photographs must not be transmitted to external cloud providers without explicit authorization.

---

## 4. Evaluation Metrics & Handling of Indeterminate Outputs

### 4.1 Confusion Matrix
For classes $\mathcal{C} = \{\text{low}, \text{moderate}, \text{high}, \text{critical}, \text{indeterminate}\}$:
$$C_{i,j} = \text{Count of images with true class } i \text{ predicted as class } j$$

### 4.2 Per-Class Performance Metrics
For each class $c \in \mathcal{C}$:
$$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}$$
$$\text{Recall}_c = \frac{TP_c}{TP_c + FN_c}$$
$$\text{F1-Score}_c = 2 \cdot \frac{\text{Precision}_c \cdot \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$

### 4.3 Macro and Weighted Averages
$$\text{Macro F1} = \frac{1}{|\mathcal{C}|} \sum_{c \in \mathcal{C}} \text{F1-Score}_c$$
$$\text{Weighted F1} = \frac{1}{\sum_{c} N_c} \sum_{c \in \mathcal{C}} N_c \cdot \text{F1-Score}_c$$

### 4.4 Explicit Handling of `indeterminate` Predictions
In preliminary geotechnical screening, returning `indeterminate` on low-quality or ambiguous images is safe behavior (conservative triage), whereas guessing `low` on an obscured hazard is dangerous.
The evaluation harness computes two views:
1. **Full 5-Class Evaluation:** Treats `indeterminate` as an explicit class measuring triage conservatism.
2. **Coverage & Determinate Performance:**
   $$\text{Coverage Rate} = \frac{N_{\text{determinate predictions}}}{N_{\text{total images}}}$$
   Determinate Precision/Recall/F1 are calculated specifically across the subset of images where the model provided a decisive hazard classification.

---

## 5. Candidate Dataset Compatibility & Ingestion Barriers

Candidate external datasets evaluated for PahaarPulse VLM benchmarking must satisfy license legality, optical field modality, and categorical geotechnical triage compatibility:

### 5.1 HLAD (Himalayan Landslide Detection Dataset)
- **Source:** Zenodo DOI [10.5281/zenodo.22811448](https://doi.org/10.5281/zenodo.22811448) (~4,000 images).
- **License Status:** **UNVERIFIED (Blank License Field on Zenodo)**.
- **Modality & Schema:** High-resolution optical/drone orthophotos annotated with spatial bounding boxes and scar segmentation masks.
- **Suitability Assessment:** **Incompatible & Blocked.**
  1. *License Enforcement:* Per project research policy, datasets with blank license fields must not be downloaded, ingested, or redistributed.
  2. *Schema Mismatch:* Bounding boxes delineate scar geometry but do not indicate geotechnical hazard severity triage (`low`/`moderate`/`high`/`critical`) or road infrastructure impact.
  3. *Perspective Mismatch:* Overhead drone orthophotos lack observer eye-level perspective of road cracks, retaining walls, and toe erosion.

### 5.2 Landslide4Sense
- **Source:** IEEE GRSS Data Fusion / Landslide4Sense Challenge.
- **License Status:** Academic competition use only.
- **Modality & Schema:** 14-band multispectral satellite imagery (Sentinel-2, ALOS DEM, topographic slope) with pixel-level binary segmentation masks (0/1).
- **Suitability Assessment:** **Incompatible & Blocked.**
  1. *Modality Incompatibility:* 14-channel satellite raster tensors ($128 \times 128$) cannot be ingested by conversational RGB Vision-Language Models (Gemma 3 4B) without custom spectral adapters.
  2. *Task Incompatibility:* Pixel-level binary segmentation is an orthogonal computer vision task to geotechnical severity triage.
  3. *Architectural Decoupling:* Satellite remote-sensing belongs to macro-scale GIS hazard pipelines (e.g., PostGIS, satellite indexing), completely decoupled from micro-scale field report screening.

### 5.3 Automated Rejection Barriers
The evaluation engine (`backend/app/services/vlm_evaluation.py`) actively enforces:
- `UnsupportedModalityError`: Rejects non-RGB raster formats (`.tif`, `.tiff`, `.npy`, `.h5`, `.hdf5`, `.nc`).
- `MismatchedAnnotationSchemaError`: Rejects binary masks (`0`/`1`) and spatial bounding box columns (`mask_path`, `bbox_coords`).
- `UnverifiedLicenseError`: Blocks ingestion of datasets with unverified/blank licenses (`license_verified: false`).

