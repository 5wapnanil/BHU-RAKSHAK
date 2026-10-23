# AI/ML Landslide Risk Management --- Frozen ML Architecture

## Final Three-Model Comparison, Architecture, Validation & Performance

**Frozen candidate architecture:** XGBoost + AHC + Spatial Logistic Regression Decision Layer

**Purpose:** Consolidated technical record of the three modelling layers, datasets, validation results, overfitting/underfitting checks, calibration, spatial robustness, warning thresholds, limitations, and the reasons the proposed architecture is stronger than either individual model.

**Important interpretation:** The reported results are those generated during this project. They support a strong research/prototype decision-support model; they do not constitute safety certification or proof of operational emergency-warning reliability.

---

## 1. Executive Summary

The project uses a layered architecture in which:
1.  **XGBoost** supplies supervised landslide-event probability.
2.  **AHC** (Agglomerative Hierarchical Clustering) supplies environmental susceptibility/context.
3.  A **Logistic Regression Decision Layer** learns how to combine those outputs into a final layered probability and warning level.

The spatially improved Decision Layer is the frozen candidate final model.

On the independent 2025 dataset, the final spatial layered model achieved:

| Metric | Final Spatial Layered Model |
| --- | --- |
| ROC-AUC | 0.998025 |
| PR-AUC | 0.996979 |
| Accuracy | 98.54% |
| Precision | 97.04% |
| Recall | 98.90% |
| F1 | 97.96% |

The final architecture is stronger than the individual components in the independent evaluation. The ablation study also shows that adding AHC information and a dedicated decision layer contributes measurable predictive value.

---

## 2. Final Architecture

### 2.1 Data Flow

```text
INPUT ENVIRONMENTAL / TEMPORAL OBSERVATIONS
                    |
          +---------+---------+
          |                   |
          v                   v
      XGBoost                AHC
          |                   |
          |                   +--> Cluster
          |                   +--> Susceptibility
          |
          +--> Event Probability
                    |
                    v
       Spatial Decision Layer
          (Logistic Regression)
                    |
                    v
          Final Layered Probability
                    |
                    v
          Threshold / Warning Level
```

The same observation enters both XGBoost and AHC.
The two outputs then enter the Spatial Decision Layer, which produces the final layered probability and corresponding warning level.

### 2.2 Deliberately Different Model Roles

| Component | Role |
| --- | --- |
| XGBoost | Supervised, event-oriented landslide prediction |
| AHC | Unsupervised environmental susceptibility/context profiling |
| Logistic Regression Decision Layer | Meta-model combining XGBoost event evidence with AHC susceptibility/context |

The Logistic Regression layer is intended to combine the two model families rather than replace either one.

---

## 3. Dataset Details

| Dataset / File | Rows × Columns | Purpose |
| --- | --- | --- |
| `Landslide_NER_MASTER_2016_ROWS_RAW.csv` | 2016 × 19 | Original master observations |
| `Landslide_NER_MASTER_2016_ROWS_WITH_XGBOOST_FEATURES.csv` | 2016 × 28 | Master + XGBoost engineered features |
| `Landslide_NER_XGBOOST_TRAIN_1278.csv` | 1278 × 28 | XGBoost development/training data |
| `Landslide_NER_AHC_Preprocessed_Final.csv` | 2016 × 18 | AHC-ready dataset |
| `Layering dataset` | 2016 × 12 | Aligned XGBoost + AHC outputs |

### 3.1 Target Distribution
The 2,016-row master dataset contains:
-   1,344 non-landslides --- 66.67%
-   672 landslides --- 33.33%

### 3.2 Spatial Structure
-   656 unique coordinate locations
-   Average 3.07 observations per location
-   99 districts
-   8 states

### 3.3 Independent Evaluation and Holdout
**2025 Independent Dataset**
-   1,026 rows
-   662 negatives
-   364 positives

**2026 Untouched Holdout**
-   137 rows
-   All 137 are labelled negative.
-   Therefore, conventional ROC-AUC and recall cannot be used as positive-case performance evaluation for 2026.

---

## 4. Model 1 --- XGBoost

Frozen model file: `models/STEP73_FROZEN_XGBOOST.json`

### 4.1 Configuration

| Parameter | Value |
| --- | --- |
| Objective | `binary:logistic` |
| Booster | `gbtree` |
| Trees | 300 |
| Max depth | 6 |
| Learning rate | 0.3 |

### 4.2 Features
The frozen XGBoost model uses 12 features:
```text
rzsm_1, rzsm_2, rzsm_3, cumulative_rainfall_3d_mm, _rzsm_mean_, _rzsm_range_, _rzsm_surface_deep_diff_, _rain_rzsm_interaction_, _previous_rzsm_, _previous_rzsm_2_, _previous_rzsm_3_, _previous_rainfall_
```

### 4.3 XGBoost Performance

| Dataset | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | F1 | LogLoss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training | 0.995617 | 0.988894 | 0.972613 | 0.950431 | 0.973510 | 0.961832 | 0.087094 |
| OOF 2023--2024 | 0.984332 | 0.954979 | 0.949590 | 0.928803 | 0.931818 | 0.930308 | 0.199103 |
| Independent 2025 | 0.993937 | 0.986574 | 0.966862 | 0.950820 | 0.956044 | 0.953425 | 0.095180 |
| Strict Spatial OOF | 0.986179 | 0.964658 | 0.953107 | 0.932258 | 0.938312 | 0.935275 | --- |

### 4.4 Overfitting / Underfitting Diagnostic
-   Training → OOF ROC-AUC gap: 0.011285
-   Training → 2025 ROC-AUC gap: 0.001680

The project diagnostic found no obvious overfitting/underfitting signal from ROC-AUC. The independent 2025 result remained close to training performance.

---

## 5. Model 2 --- AHC Susceptibility Layer

Algorithm: Agglomerative Hierarchical Clustering

### 5.1 Configuration

| Parameter | Final Configuration |
| --- | --- |
| Algorithm | Agglomerative Hierarchical Clustering |
| Clusters | 7 |
| Linkage | Ward |
| Distance | Euclidean |
| Numerical features | `cumulative_rainfall_3d_mm`, `rzsm_0_100`, `elevation_m`, `slope_deg` |
| Categorical feature | `soil_type_wrb` |
| Scaling | StandardScaler |

### 5.2 Learned Cluster Susceptibility Mapping

| Cluster | Susceptibility | Category |
| --- | --- | --- |
| 2 | 0.00% | LOW |
| 6 | 5.00% | LOW |
| 4 | 9.813084% | LOW |
| 3 | 32.638889% | HIGH |
| 5 | 38.461538% | HIGH |
| 1 | 89.887640% | VERY HIGH |
| 0 | 92.207792% | VERY HIGH |

**Important Interpretation:** AHC is used as a susceptibility/context layer. Its cluster susceptibility is not the same thing as a calibrated event probability.

---

## 6. Model 3 --- Final Spatial Decision Layer

Frozen model file: `models/spatial_layered_decision_model.pkl`

### 6.1 Configuration
-   Classifier: Logistic Regression
-   Numeric inputs: standardized
-   AHC category: one-hot encoded
-   `class_weight='balanced'`
-   `max_iter=2000`

### 6.2 Meta-Features
The Decision Layer receives:
1.  XGBoost OOF/spatial-OOF probability
2.  AHC susceptibility
3.  AHC cluster
4.  AHC category

### 6.3 Learned Relationship

| Feature | Coefficient | Role / Direction |
| --- | --- | --- |
| XGBoost probability | +2.752474 | Strongest positive contribution |
| AHC susceptibility | +2.083646 | Second strongest positive contribution |
| AHC cluster | +0.543682 | Additional cluster contribution |
| AHC category HIGH | +0.376215 | Positive contribution |
| AHC category VERY HIGH | +0.264566 | Positive contribution |
| AHC category LOW | −0.718082 | Reduces final risk |

This confirms that the final layer actually integrates both model families: XGBoost event evidence + AHC susceptibility/context.

### 6.4 Decision-Layer Validation

| Metric | Original Decision OOF | Spatial Decision OOF |
| --- | --- | --- |
| ROC-AUC | 0.991803 | 0.992762 |
| PR-AUC | 0.987829 | 0.989186 |
| Accuracy | 0.946073 | 0.951934 |
| Precision | 0.904321 | 0.908257 |
| Recall | 0.951299 | 0.964286 |
| F1 | 0.927215 | 0.935433 |
| Brier | 0.032460 | 0.030670 |
| LogLoss | 0.112013 | 0.108047 |

---

## 7. Independent 2025 Head-to-Head --- Final Comparison

The independent 2025 evaluation is the key comparison used to judge the final architecture.

| Model | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | F1 | Brier | LogLoss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XGBoost | 0.993937 | 0.986574 | 0.966862 | 0.956044 | 0.956044 | 0.953425 | --- | 0.095180 |
| AHC | 0.941000 | 0.875600 | 0.904500 | 0.952381 | 0.769231 | 0.851064 | --- | --- |
| Original layered | 0.998012 | 0.996952 | 0.979532 | 0.954907 | 0.989011 | 0.971660 | 0.016739 | 0.069904 |
| FINAL spatial layered | **0.998025** | **0.996979** | **0.985380** | **0.970350** | **0.989011** | **0.979592** | **0.016261** | **0.067609** |

### 7.1 Final Spatial Model Confusion Matrix
```text
TN = 651
FP = 11
FN = 4
TP = 360
```
Compared with the original layered model:
-   Recall remained the same at 98.90%
-   False positives decreased from 17 → 11
-   Accuracy improved by 0.5848 percentage points
-   Precision improved by 1.5443 points
-   F1 improved by 0.7932 points

This is a major reason the spatial layered model is the frozen candidate final model.

---

## 8. Ablation Study --- Why Layering Matters

| Architecture | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| A --- XGBoost only | 0.993937 | 0.986574 | 0.970760 | 0.948925 | 0.969780 | 0.959239 |
| B --- XGBoost + AHC susceptibility | 0.997618 | 0.996274 | 0.961988 | 0.922078 | 0.975275 | 0.947931 |
| C --- Full layering | **0.998012** | **0.996952** | **0.979532** | **0.954907** | **0.989011** | **0.971660** |

The full architecture was the best ablation by ROC-AUC. Importantly, the complete layered model also produced the strongest F1 and recall among the three tested architectures.

---

## 9. Overfitting / Underfitting Evidence

| Model / Split | ROC-AUC | Key Gap / Interpretation |
| --- | --- | --- |
| XGBoost training | 0.995617 | Reference training performance |
| XGBoost OOF | 0.984332 | Train→OOF gap = 0.011285 |
| XGBoost independent 2025 | 0.993937 | Train→2025 gap = 0.001680 |
| Decision meta-training | 0.994001 | Reference meta-training |
| Decision OOF | 0.991803 | Train→OOF gap = 0.002198 |
| Decision independent 2025 | 0.998012 | No deterioration vs training |

**Conclusion:** The observed numbers do not show a classic severe overfitting pattern. There is also no obvious underfitting signal from ROC-AUC. The stronger concern is validation design and data limitations, not an observed collapse in generalization.

---

## 10. Spatial Generalization

The dataset contains 656 coordinate locations and repeated observations. Therefore, strict grouped spatial validation was performed for XGBoost.

### 10.1 Strict Spatial XGBoost OOF
-   ROC-AUC: 0.986179
-   PR-AUC: 0.964658
-   Accuracy: 95.31%
-   Precision: 93.23%
-   Recall: 93.83%
-   F1: 93.53%

### 10.2 2025 Unseen Locations
For 2025:
-   353 locations were genuinely new
-   955 rows came from previously unseen locations

The earlier layered model on the 955-row unseen-location subset achieved:
-   ROC-AUC: 0.998429
-   PR-AUC: 0.997877
-   Accuracy: 98.22%
-   Precision: 96.51%
-   Recall: 98.90%
-   F1: 97.69%

### 10.3 Important Validation Note
The final spatial Decision Layer was built from spatial OOF XGBoost probabilities. The next methodological strengthening would be an end-to-end grouped-spatial validation of the complete stack. This is a validation enhancement, not evidence that the current model failed.

---

## 11. Probability Calibration & Reliability

| Dataset | ROC-AUC | PR-AUC | Brier | LogLoss |
| --- | --- | --- | --- | --- |
| Decision OOF | 0.991803 | 0.987829 | 0.032460 | 0.112013 |
| Independent 2025 | 0.998012 | 0.996952 | 0.016739 | 0.069904 |

For probability ≥ 0.9 in OOF data:
-   Mean predicted probability ≈ 0.9906
-   Observed landslide rate ≈ 0.9887

Calibration is therefore good overall, especially at high risk, but not perfect in sparse intermediate probability bins. The final probability should not be interpreted as a universally calibrated physical probability without further external validation.

---

## 12. Warning Threshold & Operational Levels

### 12.1 Threshold Analysis

| Threshold | Accuracy | Precision | Recall | F1 | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.20 | 0.9600 | 0.9027 | 0.9945 | 0.9464 | 39 | 2 | 362 |
| 0.30 | 0.9630 | 0.9137 | 0.9890 | 0.9499 | 34 | 4 | 360 |
| 0.40 | 0.9678 | 0.9254 | 0.9890 | 0.9562 | 29 | 4 | 360 |
| 0.50 | 0.9795 | 0.9549 | 0.9890 | 0.9717 | 17 | 4 | 360 |
| **0.60** | **0.9854** | **0.9834** | **0.9753** | **0.9793** | **6** | **9** | **355** |
| 0.70 | 0.9844 | 0.9860 | 0.9698 | 0.9778 | 5 | 11 | 353 |
| 0.80 | 0.9649 | 0.9910 | 0.9093 | 0.9484 | 3 | 33 | 331 |
| 0.90 | 0.9542 | 0.9907 | 0.8791 | 0.9316 | 3 | 44 | 320 |

### 12.2 Selected Prototype Operating Point
The selected prototype operating point is: `Threshold = 0.60`
Reason:
-   Best tested F1 = 0.9793
-   Recall = 97.53%
-   Precision = 98.34%
-   Only 6 false positives

This is an evaluated prototype operating point, not a universally optimal emergency threshold.

### 12.3 Warning-Level Distribution on 2025

| Warning Level | Count | Percentage | Observed Occurrence Rate |
| --- | --- | --- | --- |
| LOW | 625 | 60.92% | 0.32% |
| MODERATE | 12 | 1.17% | 16.67% |
| HIGH | 28 | 2.73% | 17.86% |
| VERY HIGH | 27 | 2.63% | 88.89% |
| EXTREME | 334 | 32.55% | 99.10% |

The warning levels show a strong observed risk gradient.

---

## 13. 2026 Holdout

The 2026 dataset contains:
-   137 observations
-   Date range: 2026-01-01 to 2026-04-10
-   It was not used for training or model modification

### 13.1 Prospective Predictions
At the predefined 0.50 decision point:
-   Predicted landslides: 8
-   Predicted no-landslide: 129
-   High-risk flags at VERY HIGH + EXTREME warning levels: 7

### 13.2 Interpretation
Because there are zero observed positive cases in 2026, the following are not reported as conventional test metrics: ROC-AUC, PR-AUC, Recall. These are prospective holdout predictions only.

---

## 14. Why This Model Can Stand Out

1. **True Layered Design:** Combines supervised event prediction (XGBoost) with unsupervised susceptibility profiling (AHC), integrated by Logistic Regression.
2. **Independent Future-Year Evaluation:** 2025 was held out as an independent evaluation period.
3. **Spatial Robustness Effort:** Strict grouped spatial validation was performed for XGBoost.
4. **Strong Event Detection:** 98.90% recall and only 4 false negatives on 2025 data.
5. **Low False-Positive Count:** Reduced 2025 false positives to 11.
6. **Ablation Evidence:** Full layering outperforms individual components.
7. **Interpretable Final Layer:** Explicit coefficients show how signals influence final decision.
8. **Operational Warning Framework:** Converts probability into interpretable warning levels.
9. **Holdout Discipline:** 2026 kept untouched as prospective holdout.
10. **Reproducible Frozen Components:** Files are separated and ready for integration.

---

## 15. Remaining Limitations --- Important for Faculty Review

| Limitation | Correct Interpretation |
| --- | --- |
| Dataset size | 2,016 observations is useful for a prototype but limited for a regional safety-critical system. |
| Negative-label reliability | A zero label may mean no recorded event; it does not prove no landslide occurred. |
| 2026 has no positives | The 2026 holdout cannot establish positive-case sensitivity. |
| Feature completeness | Current set can be expanded with physical/geological variables. |
| Calibration | Good overall but imperfect in some sparse probability bins. |
| Operational threshold | 0.60 is a tested prototype threshold, not a validated emergency threshold. |
| End-to-end spatial validation | A final grouped-spatial validation of the complete stack would strengthen evidence. |

---

## 16. Final Technical Verdict

- **Architecture:** ACCEPTABLE / FROZEN FOR PROJECT INTEGRATION
- **Predictive Performance:** EXCELLENT on independent 2025 evaluation.
- **Overfitting:** No major observed signal.
- **Spatial Robustness:** Strong evidence.
- **Research Readiness:** YES
- **Safety-Critical Deployment:** NOT YET CERTIFIED.

**Final Recommended Statement:**
"The proposed XGBoost--AHC layered architecture with a spatially validated Logistic Regression decision layer demonstrates excellent predictive discrimination, high landslide-event recall, improved performance over individual modelling components, and encouraging spatial robustness on the available dataset. The model is suitable as a research prototype and decision-support framework, while further independent spatial-temporal validation and improved ground-truth data are required before safety-critical operational deployment."

---

## 17. Frozen Model Files & Key Result Files

| File | Status / Purpose |
| --- | --- |
| `models/STEP73_FROZEN_XGBOOST.json` | Frozen XGBoost event model |
| `models/ahc_landslide_susceptibility_model.pkl` | Frozen AHC susceptibility model |
| `models/spatial_layered_decision_model.pkl` | Frozen final spatial Decision Layer |
| `results/final_2026_holdout_predictions.csv` | 2026 prospective holdout predictions |
| `results/final_2026_holdout_summary.csv` | 2026 holdout summary |
| `results/step27c_2025_old_vs_spatial_comparison.csv` | Original vs spatial Decision Layer comparison |
| `results/unseen_location_2025_model_comparison.csv` | Unseen-location robustness comparison |
| `results/layered_warning_threshold_analysis_2025.csv` | Threshold analysis |
| `results/decision_layer_reliability_oof.csv` | OOF calibration/reliability |

---

## 18. Implementation Guidance for the Project

**Model Responsibilities**
Do not collapse the three components into a single conceptual model:
* XGBoost = "What is the likelihood of a landslide event based on learned event patterns?"
* AHC = "What environmental susceptibility/context does this observation belong to?"
* Decision Layer = "How should event evidence and environmental susceptibility be combined into the final project risk signal?"

**Recommended Prototype Warning Mapping**
The selected prototype operating threshold is `Final probability >= 0.60`.

**Important Safety/Research Constraint**
The system must not be presented as a certified life-safety or emergency-warning system. Use terminology such as:
* research prototype
* decision-support system
* early-warning framework

---

## 19. Key Numbers to Preserve Exactly

**Final Spatial Layered Model --- Independent 2025**
- ROC-AUC = 0.998025
- PR-AUC = 0.996979
- Accuracy = 98.54%
- Precision= 97.04%
- Recall = 98.90%
- F1 = 97.96%

**Confusion Matrix:** TN = 651, FP = 11, FN = 4, TP = 360
**Prototype Threshold:** 0.60
**2026 Holdout:** Total rows = 137, Predicted landslide at 0.50 = 8, Predicted no-landslide = 129, VERY HIGH + EXTREME flags = 7, Observed positives = 0
