# PahaarPulse — Phase 2E: Scientific Evaluation Protocol & Manifest Specification

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Subsystem:** Gemma Local & Cloud Vision Hazard Screening Pipeline  
**Classification:** Geotechnical ML Scientific Protocol & Evaluation Contract  

---

## 1. Executive Summary & Evaluation Contract

This protocol formalizes the scientific, statistical, operational, and software contract for benchmarking vision-language models (VLMs)—specifically Gemma 2/3 vision workflows—within the PahaarPulse Landslide Risk Management platform.

### 1.1 Objective & Intended Operational Use
The primary function of the Gemma vision pipeline in PahaarPulse is **rapid initial triage and visual hazard screening** of citizen and volunteer field-report photographs from the Indian Himalayan Region (IHR). Its operational scope is strictly delimited:
- **Intended Purpose:** To assist human emergency coordinators and geotechnical dispatch teams by prioritizing incoming ground reports according to visible qualitative geomorphic distress indicators, flagging potential life-safety emergencies, and identifying uncompromised evacuation routes.
- **Explicit Non-Objectives:** The model is **not** a geotechnical slope stability solver, is **not** a substitute for subsurface geophysical exploration (e.g., standard penetration tests, core drilling, electrical resistivity), and does **not** calculate physical factors of safety ($FS$) or time-to-failure.

### 1.2 The Evaluation Contract
To maintain scientific defensibility and prevent data snooping, model evaluation adheres to five immutable principles:
1. **Zero Metric Fabrication:** Model performance metrics (Accuracy, Precision, Recall, Macro-F1, Wilson CIs) are strictly withheld until independent double-expert ground-truth labels and consensus adjudications are finalized.
2. **Immutable Run Manifests:** Every evaluation execution is bound to a cryptographic SHA-256 digest of the dataset manifest, model identifier, frozen prompt version, and deterministic inference parameters (`temperature=0.0`).
3. **Absolute Prediction-Annotation Separation:** Model inference outputs are logged to separate prediction artifacts. Predictions are strictly prohibited from mutating or writing into human annotator columns (`annotator_1_label`, `annotator_2_label`, `adjudicated_label`).
4. **Site & Event Cluster Isolation:** Photographs originating from the same physical slope, landslide scar, or extreme weather event (e.g., Kedarnath 2013, Chamoli 2021) are grouped into atomic clusters (`duplicate_group_id`) and assigned entirely to a single evaluation split to prevent spatial and temporal data leakage.
5. **Safety-First Error Accounting:** In disaster risk screening, a false negative on an active critical slope carries catastrophic life-safety consequences. The protocol requires dedicated safety-critical under-call tracking alongside standard symmetrical classification metrics.

---

## 2. Image-Level Tasks & Controlled Taxonomy

The Gemma field-photo vision model executes two distinct evaluation tasks on each input RGB photograph:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Input RGB Photograph (Resolution >= 400x400 px, Ground Field Capture)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
          ┌─────────────────────────┴─────────────────────────┐
          ▼                                                   ▼
┌───────────────────────────────────┐       ┌───────────────────────────────────┐
│ Task 1: Observable Indicators     │       │ Task 2: Geotechnical Triage Class │
│ (Multi-Label Visual Extraction)   │       │ (Single 5-Class Categorical)      │
│ • fresh_scarp                     │       │ • low                             │
│ • tension_cracks                  │       │ • moderate                        │
│ • displaced_rock / soil           │       │ • high                            │
│ • channel_obstruction             │       │ • critical                        │
│ • road_damage_slope_movement      │       │ • indeterminate (Abstention)      │
│ • stable_slope                    │       └───────────────────────────────────┘
└───────────────────────────────────┘
```

### 2.1 Task 1: Visible Geomorphic Indicators (Multi-Label)
Extraction of visible physical surface manifestations. Evaluated against expert annotations as a multi-label classification task using precision, recall, and micro/macro F1-scores.

Standard indicators from `CONTROLLED_OBSERVABLE_INDICATORS`:
- `fresh_scarp`: Exposed, unweathered shear plane or detachment headwall lacking vegetation.
- `vegetated_relict_scarp`: Old, weathered rupture surface covered by secondary growth.
- `displaced_soil`: Colluvium or soil mass moved from original position.
- `displaced_rock`: Detached bedrock blocks, boulders, or scree.
- `rockfall_debris`: Clasts deposited on road, ditch, or catchment area.
- `tension_cracks`: Extensional fissures near slope crown, crest, or flanks.
- `ground_deformation`: Terracettes, bulging toe, hummocky surface, tilted trees.
- `debris_flow_deposit`: Poorly sorted, matrix-supported sediment lobe.
- `channel_obstruction`: Blockage of drainage culvert, gully, or stream channel.
- `road_damage_slope_movement`: Asphalt cracking, subsidence, or guardrail deformation directly associated with slope instability.
- `water_seepage`: Active groundwater discharge, spring emergence, or saturated soil patch.
- `stable_slope`: Intact slope with uniform vegetation and no distress indicators.
- `negative_control`: Non-hazard image (e.g., standard infrastructure, flat valley, sunny day).

### 2.2 Task 2: Geotechnical Hazard Severity Triage (Single-Label Categorical)
Assessment of current qualitative slope hazard severity into exactly one of five mutually exclusive classes:
- **`low`**: Stable natural slopes or well-engineered cuts showing mature vegetation, functional drainage, and no signs of extensional cracking, toe bulging, or active raveling.
- **`moderate`**: Slopes with superficial erosion, weathered relict scarps, or minor rockfall where drainage is partially impaired but structural infrastructure is not immediately threatened.
- **`high`**: Actively creeping slopes, open tension cracks, significant debris flow accumulation near roads, or ongoing raveling threatening transportation corridors or settlements.
- **`critical`**: Imminent or freshly triggered catastrophic mass movements, broad headwall collapse across active roads, blocked major waterways creating landslide-dam outburst flood (LDOF) hazards, or destruction of occupied structures.
- **`indeterminate`**: Explicit model or annotator abstention triggered when visual evidence is insufficient to evaluate hazard (e.g., thick fog, severe motion blur, extreme close-up of mud without surrounding slope context, or uninterpretable camera angle).

---

## 3. Epistemic Separation & Scientific Honesty

A fundamental failure mode in computer-vision hazard assessment is confusing what is visible in a 2D optical raster with what exists in 3D subsurface geotechnical space.

| Knowledge Tier | Description | Source of Evidence | Model Capability |
| :--- | :--- | :--- | :--- |
| **Level 1: Optical Surface Evidence** | Color differences, exposed saprolite, fresh rock fracture, asphalt tears, mud lobes | Direct pixel intensities from camera sensor | **High** (Pattern recognition, edge detection) |
| **Level 2: Geomorphic Reviewer Inference** | Qualitative likelihood of kinematic failure, candidate slip mechanism | Geotechnical interpretation based on geomorphology | **Moderate** (Visual reasoning under prompt constraints) |
| **Level 3: Confirmed Geotechnical Ground Truth** | Subsurface failure depth, water table elevation, slip velocity, pore pressure | Borehole logs, inclinometers, piezometers, municipal logs | **Zero** (Cannot be seen in a photograph) |
| **Level 4: Indeterminate / Non-Observable** | Blind slope crests, dense canopy obscuring cracks, night capture | Lack of sensor observation | **Must Abstain** (`indeterminate`) |

### 3.1 The "Negative Evidence" Fallacy
In slope stability assessment, **absence of visible cracks in a photograph does NOT prove slope stability**. A slope may have zero surface tension cracks while being minutes away from failure due to elevated basal pore-water pressure from heavy monsoon precipitation. 

The evaluation protocol explicitly penalizes models that equate lack of visible distress in degraded or occluded photographs with `low` hazard. Such images must be routed to `indeterminate`.

---

## 4. Candidate Inclusion & Exclusion Criteria

To ensure the benchmark reflects real-world Himalayan field conditions without introducing legal or methodological liabilities, all candidate photographs must satisfy strict eligibility criteria:

### 4.1 Mandatory Inclusion Criteria
1. **Modality:** Optical RGB field photographs captured from ground, vehicle, or low-altitude perspective.
2. **Resolution & Integrity:** Minimum raster resolution of $\ge 400 \times 400\text{ px}$. File format must be JPEG, PNG, or WebP. Must pass PIL/Pillow raster decode integrity verification without truncation.
3. **Legal Provenance:** Documented Creative Commons license (CC0, CC-BY, CC-BY-SA, CC-BY-NC) or confirmed public domain government release (USGS, NASA, GSI public reports). Blank or ambiguous licenses are rejected.
4. **Himalayan Geomorphic Relevance:** Realistic mountainous terrain, cut slopes, highway passes, or river valley settings representative of high-relief orogenesis.
5. **Contextual Interpretability:** The image must capture sufficient geomorphic context (slope face, road interface, or valley floor) to allow geotechnical review.

### 4.2 Explicit Exclusion Criteria
1. **Remote Sensing Tensors:** Multispectral satellite bands (e.g., Sentinel-2 14-band patches, Landslide4Sense `.tif`, `.npy`, `.h5` files) are strictly excluded from the VLM field-photo benchmark.
2. **Pure Scar Masks & Bounding Boxes:** Datasets annotated solely with binary segmentation masks or bounding boxes (e.g., HLAD Zenodo) without categorical hazard severity are excluded.
3. **Severe Raster Degradation:** Extreme camera motion blur, complete nighttime blackouts, or corrupted JPEG bitstreams where no landforms can be discerned.
4. **Microscopic / Extreme Close-Ups:** Photographs showing only a single hand holding a soil clod or pebble without slope context.

---

## 5. Site & Event Cluster Isolation (Data Leakage Prevention)

A major risk in field-photo benchmarking is **spatial and temporal autocorrelation leakage**. Photographers and field survey teams frequently capture 5 to 15 images of the same landslide from slightly different vantage points or at 30-second intervals.

### 5.1 The Clustering Rule
If multiple images depict the same physical slope or event, allocating one image to the training/prompting split and another to the test split produces massive synthetic over-performance.

```
WRONG (LEAKAGE):
  Image A (Kedarnath Road km 42, 10:14 AM) ───► Split: TRAIN
  Image B (Kedarnath Road km 42, 10:15 AM) ───► Split: TEST  ❌ [Severe Data Leakage]

CORRECT (ISOLATION):
  Site Cluster: SERIES_KEDARNATH_KM42 (Images A, B, C, D) ───► Split: TEST (All-in-one) ✅
```

### 5.2 Implementation in PahaarPulse
- Every candidate image is tagged with a `duplicate_group_id` representing its spatial/event cluster.
- The evaluation harness executes `VLMEvaluationHarness.validate_split_integrity(samples)`. If any `duplicate_group_id` or SHA-256 hash appears across multiple splits (e.g., `train` and `test`), the runner immediately halts and raises `DataLeakageError`.

---

## 6. Model Execution & Inference Parameter Freezing

To guarantee exact reproducibility across evaluation runs, inference parameters must be strictly frozen:

```json
{
  "provider": "google",
  "model_id": "gemini-3.5-flash",
  "protocol_version": "Phase-2E-v1.0",
  "prompt_version": "v2.1",
  "inference_parameters": {
    "temperature": 0.0,
    "top_p": 1.0,
    "timeout_seconds": 30.0,
    "max_retries": 2
  }
}
```

### 6.1 Temperature Freezing ($T=0.0$)
Stochastic decoding ($T > 0$) introduces run-to-run variance, making scientific comparisons invalid. Evaluation inference runs exclusively with `temperature=0.0` (greedy argmax decoding).

### 6.2 Prompt Versioning & System Freezing
The prompt must be locked to a version-controlled template string. Any change to system instructions, few-shot exemplars, or JSON output formatting constitutes a new `prompt_version` and requires a new run manifest.

### 6.3 Handling of Inference Failures
Model inference over network endpoints can fail. The evaluation harness enforces deterministic mapping for all failure modes:

| Failure Mode | Provider Exception | Execution Status | Evaluation Handling |
| :--- | :--- | :--- | :--- |
| **Malformed Non-JSON Output** | `GemmaMalformedOutputError` | `malformed_output` | Logged as inference failure; mapped to `predicted_hazard="indeterminate"` |
| **Rate Limit (HTTP 429)** | `GemmaRateLimitError` | `rate_limit` | Logged as failure; logged for retry or backoff |
| **Inference Timeout (> 30s)** | `GemmaTimeoutError` | `timeout` | Logged as failure; mapped to `predicted_hazard="indeterminate"` |
| **Provider 503 / Network Error** | `GemmaTemporaryUnavailableError` | `provider_error` | Logged as provider failure; mapped to `predicted_hazard="indeterminate"` |
| **Explicit Model Abstention** | Output `hazard_level="indeterminate"` | `abstention_indeterminate` | Valid inference; counted towards Determinate Coverage metric |
| **Successful Deterministic Output** | Output `hazard_level in VALID_HAZARD_CLASSES` | `success` | Valid inference; counted towards Accuracy and F1 metrics |

---

## 7. Performance Metrics Specification

Evaluation scorecards are computed across ground-truth adjudicated samples using mathematically rigorous formulas.

### 7.1 Confusion Matrix Structure
A $5 \times 5$ contingency table $C_{i,j}$ where row $i$ represents ground-truth class and column $j$ represents model prediction:

$$\mathcal{C} = \{c_1: \text{low}, c_2: \text{moderate}, c_3: \text{high}, c_4: \text{critical}, c_5: \text{indeterminate}\}$$

### 7.2 Precision, Recall, and F1-Score
For class $c \in \mathcal{C}$:
$$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c} = \frac{C_{c,c}}{\sum_{k} C_{k,c}}$$
$$\text{Recall}_c = \frac{TP_c}{TP_c + FN_c} = \frac{C_{c,c}}{\sum_{k} C_{c,k}}$$
$$F1_c = \frac{2 \cdot \text{Precision}_c \cdot \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$

$$\text{Macro-F1} = \frac{1}{|\mathcal{C}_{\text{active}}|} \sum_{c \in \mathcal{C}_{\text{active}}} F1_c$$
$$\text{Weighted-F1} = \frac{1}{N} \sum_{c \in \mathcal{C}} \text{Support}_c \cdot F1_c$$

### 7.3 Wilson Score 95% Confidence Intervals
Standard normal approximation intervals ($\hat{p} \pm 1.96 \sqrt{\hat{p}(1-\hat{p})/n}$) fail dramatically on small datasets ($N \le 100$) and boundary conditions ($\hat{p}=0$ or $\hat{p}=1$). The evaluation harness requires asymmetric Wilson score intervals:

$$w = \frac{1}{1 + \frac{z^2}{n}} \left( \hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}} \right)$$

Where $z = 1.959964$ for 95% two-sided confidence.

### 7.4 Safety-Critical Under-Call Analysis (Severe False Negatives)
In an operational landslide warning system, false alarms (predicting `high` for a `low` slope) cause inconvenience, but **false negatives (predicting `low` or `moderate` for a `critical` or `high` slope) cause loss of human life**.

The evaluation protocol defines the **Safety-Critical Under-Call Metric**:
$$\mathcal{S}_{\text{under-call}} = \{s \in \mathcal{D}_{\text{labeled}} \mid \text{True}(s) \in \{\text{high}, \text{critical}\} \land \text{Pred}(s) \in \{\text{low}, \text{moderate}\}\}$$
$$\text{Safety Under-Call Rate} = \frac{|\mathcal{S}_{\text{under-call}}|}{\sum_{s} \mathbb{I}(\text{True}(s) \in \{\text{high}, \text{critical}\})}$$

Any model deployment pipeline must enforce a hard threshold: $\text{Safety Under-Call Rate} \le 5.0\%$.

### 7.5 Determinate Coverage Rate
Measures the proportion of field reports on which the model makes an actionable categorical prediction vs. abstaining:
$$\text{Coverage Rate} = \frac{N_{\text{determinate}}}{N_{\text{total}}} = \frac{\sum_{s} \mathbb{I}(\text{Pred}(s) \neq \text{'indeterminate'})}{N}$$

---

## 8. Sample Size Adequacy & Statistical Power Analysis

A widespread misconception in applied machine learning is that a benchmark of $N=50$ or $N=100$ is sufficient to "certify" an AI model. A formal power analysis demonstrates the limitations:

### 8.1 Precision of Proportions
To estimate a classifier's overall accuracy with a margin of error $E = \pm 5\%$ at 95% confidence ($\alpha = 0.05$):
$$N = \frac{z^2 \cdot p(1-p)}{E^2} = \frac{1.96^2 \cdot 0.5 \cdot 0.5}{0.05^2} \approx 384.16 \approx 385 \text{ samples}$$

### 8.2 Margin of Error on Candidate Dataset ($N=54$)
With the current candidate collection ($N=54$), if the model achieves an observed accuracy of 80% ($\hat{p}=0.80$):
$$\text{Wilson 95\% CI for } \hat{p}=0.80, N=54: [67.4\%, 88.5\%]$$
The resulting margin of error is **$\pm 10.5\%$**. 

### 8.3 Per-Class Support and Degrees of Freedom
When $N=54$ is distributed across 5 categorical classes (`low`, `moderate`, `high`, `critical`, `indeterminate`), a uniform distribution yields approximately 10 to 11 samples per class. However, landslide occurrences in real collections are heavily skewed toward high/critical events. If the `critical` class contains only 6 samples:
- Correctly predicting 5 out of 6 yields $\hat{p} = 83.3\%$.
- The 95% Wilson CI for $5/6$ is $[43.6\%, 97.0\%]$—a confidence interval spread of **53.4 percentage points**.

### 8.4 Methodological Conclusion & Benchmark Phasing
1. **Current Ingested Candidates ($N=54$):** Sufficient only for **Pilot Protocol Verification**, pipeline smoke testing, and regression verification of evaluation tooling. It is **statistically underpowered** to support generalizable accuracy claims.
2. **Phase 3 Expansion Target ($N \ge 350$):** Full scientific benchmarking requires expanding the curated benchmark to at least 350-400 adjudicated samples across the 5 classes, ensuring a minimum of $N \ge 40$ per class.

---

## 9. Evaluation Readiness Criteria & Verdict

| Readiness Gate | Requirement | Current Status | Verification Evidence |
| :--- | :--- | :---: | :--- |
| **G1: Infrastructure & Tests** | Backend evaluation harness, manifest tooling, and split leakage guards passing | **PASS** | 206/206 unit tests passing (`test_evaluation_protocol.py` + full test suite) |
| **G2: Image Raster Integrity** | 100% ingested images valid, decodable, $\ge 400\text{ px}$ | **PASS** | 54/54 candidate images verified on disk (174.39 MB) |
| **G3: License Provenance** | Zero unverified/blank licenses in benchmark | **PASS** | 57 approved open licenses; 6 commercial pending excluded from benchmark |
| **G4: Operational Safety** | Zero DB mutations, zero credential leaks, provider intact | **PASS** | DB counts verified intact; `GEMMA_PROVIDER=google` intact |
| **G5: Ground-Truth Adjudication** | Dual-expert geotechnical annotations completed & adjudicated | **BLOCKED** | Live ground-truth annotations are pending review (`phase_2d_annotations_template.csv`) |

### Final Recommendation
- **Evaluation Tooling & Protocol Readiness:** **APPROVED / READY**. The evaluation architecture, runner, metrics calculator, and test harness are fully operational.
- **Model Evaluation Benchmark Execution:** **FORMALLY BLOCKED** pending completion of independent dual-expert geotechnical annotation and adjudication. No model accuracy figures may be published until expert labels are finalized.
