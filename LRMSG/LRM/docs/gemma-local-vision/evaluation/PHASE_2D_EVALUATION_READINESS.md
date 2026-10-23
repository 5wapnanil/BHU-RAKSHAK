# PahaarPulse — Phase 2D: Leakage-Free Evaluation Readiness Audit

**Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Evaluation Subsystem:** Gemma Vision Field-Photo Ground-Truth Benchmark Pipeline  
**Document Status:** Complete & Evaluated  

---

## Executive Summary & Readiness Verdict

**Current Evaluation Readiness Status:** **BLOCKED (PENDING EXPERT GROUND-TRUTH ANNOTATION)**

While all technical prerequisites for dataset ingestion, raster validation, deduplication, and split-leakage prevention have successfully passed, **PahaarPulse cannot and must not compute or publish VLM accuracy metrics at this time**.

This blocked status is a deliberate, scientifically honest finding based on two non-negotiable facts:
1. **Zero Ground-Truth Labels Exist:** All 54 ingested candidate images remain unadjudicated (`adjudication_status = "pending"`). The PahaarPulse evaluation harness strictly abstains from metric calculation when ground truth is absent.
2. **Sample Size & Statistical Power Limitations:** A total of 54 candidate images distributed across 5 hazard classes yields an average of only 10.8 samples per class. Partitioning this into train/dev/test subsets would produce test sets of only 10–15 images, where a single classification error alters reported accuracy by 7–10%, yielding Wilson 95% confidence intervals broader than $\pm 25\%$.

---

## 1. Candidate Dataset Structure & Physical Site Grouping

### 1.1 Ingested Dataset Summary
- **Validated Images on Disk:** 54 images stored in [`data/public_candidates/images/`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/data/public_candidates/images/).
- **Decodability & Raster Integrity:** 100% (54 / 54) verified via Pillow.
- **Resolution Compliance:** 100% $\ge 400 \times 400\text{ px}$ (range: $480\text{ px}$ to $7,360\text{ px}$).
- **Total Storage Volume:** 174.39 MB.
- **Deduplication:** 0 identical SHA-256 hash duplicates.

### 1.2 Event and Site Grouping Audit
To prevent spatial data leakage—where multiple photographs of the same physical landslide or roadway collapse appear across different splits (e.g., train and test)—all candidate images have been mapped to physical site clusters:

```
[54 Ingested Images]
       │
       ├─── 10 Grouped Site Clusters (16 images)
       │    ├── 5 Multi-Image Clusters (10 images, 2 each)
       │    │   ├── GPS_41.7_44.76 (Varaziskhevi valley, Georgia)
       │    │   ├── GPS_32.57_77.05 (Himachal Pradesh road clearing, India)
       │    │   ├── Series_asker_semsvann_gupuelva_tveite (Asker rockfall, Norway)
       │    │   ├── GPS_38.0_-106.43 (Carnero Pass controls, Colorado, USA)
       │    │   └── GPS_38.69_-106.48 (Cumberland Pass controls, Colorado, USA)
       │    └── 5 Single-Image Named Site Clusters (6 images)
       │        ├── Lauzet_Ubaye_Rockfall (France)
       │        ├── Nida_Parnidis_Dune (Lithuania)
       │        ├── Vitkaiciai_Lithuania_Outcrop (Lithuania)
       │        ├── Sesvenna_Alps_Torrent (Switzerland)
       │        └── Sirac_Ecrins_Torrent (France)
       │
       ├─── 16 Single-Image GPS Georeferenced Sites (16 images)
       │
       └─── 22 Ungrouped Independent Field Photographs (22 images)
```

### 1.3 Confirmed vs. Tentative Grouping Confidence
- **`CONFIRMED_SITE` (24 images):** Explicit GPS coordinates or direct physical field site documentation proving identical geographic origin.
- **`TENTATIVE_GEOGRAPHIC_CLUSTER` (4 images):** Series title or named watercourse indicating adjacent geomorphic features (e.g. `Series_asker_semsvann`, `Series_caoling`, `Series_baranco_los_angustias`, `Series_e_ribel_pass`).
- **`UNKNOWN_EVENT_OR_SITE` (26 images):** Independent field photographs without shared metadata, titles, or coordinates.

**Conservative Grouping Rule:**  
In accordance with [`vlm_evaluation.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/vlm_evaluation.py#L335-L372), both `CONFIRMED_SITE` and `TENTATIVE_GEOGRAPHIC_CLUSTER` groups are treated as indivisible units: **all photos belonging to a cluster must reside strictly within the same evaluation split**. Only `UNKNOWN_EVENT_OR_SITE` records may be assigned independently.

---

## 2. Split Strategy & Data Leakage Assessment

### 2.1 The Split Leakage Guard
The automated guard [`VLMEvaluationHarness.validate_split_integrity()`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/vlm_evaluation.py#L335-L372) enforces two layers of defense:
1. **Hash Leakage Check:** Checks pairwise intersections of image SHA-256 digests across `train`, `dev`, and `test`. Raises [`DataLeakageError`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/vlm_evaluation.py#L66-L69) if any hash appears in more than one split.
2. **Cluster Group Leakage Check:** Checks pairwise intersections of `duplicate_group_id` / `event_site_group` across splits. If images from `GPS_32.57_77.05` or `Series_asker_semsvann` are split across train and test, [`DataLeakageError`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/vlm_evaluation.py#L66-L69) aborts evaluation immediately.

### 2.2 Theoretical Split Allocation (When Annotated)
When dual-expert adjudication is complete, the 54 images can be partitioned conservatively as follows without violating cluster indivisibility:

| Proposed Split | Assigned Site Clusters / Samples | Target Image Count | Purpose |
| :--- | :--- | :--- | :--- |
| **Train (Few-Shot / Calibration)** | 14 independent sites + `Series_asker_semsvann` (2) + `GPS_38.0_-106.43` (2) | ~26 images | Prompt engineering, in-context examples, few-shot calibration |
| **Dev (Hyperparameter Tuning)** | 7 independent sites + `GPS_32.57_77.05` (2) + `GPS_38.69_-106.48` (2) | ~14 images | Threshold tuning, temperature search, prompt refinement |
| **Test (Frozen Evaluation)** | 7 independent sites + `GPS_41.7_44.76` (2) + single-site torrents (5) | ~14 images | Held-out, untouched final performance assessment |

### 2.3 Sample Size & Statistical Power Limitations
Partitioning 54 images across 3 splits produces a test set of only 14 images:
- **Binomial Standard Error:** For $N=14$ and an observed accuracy of 80% (11/14), the Wilson 95% Confidence Interval is **[54.8%, 93.0%]**—a margin of error of $\pm 19\%$.
- **Class Imbalance:** With 7 hazard topics, several classes would have only 1–2 test instances, rendering class-specific precision and recall statistically meaningless.
- **Scientific Decision:** While a preliminary dev/test split can be maintained for regression validation, **formal scientific benchmark claims require expanding the candidate collection to at least 150–200 verified field photographs** prior to frozen test reporting.

---

## 3. Evaluation Metrics Specification

Once independent expert ground-truth annotations are merged, the evaluation harness will compute the following metrics defined in [`EvaluationMetrics`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/vlm_evaluation.py#L186-L212):

### 3.1 Primary Classification Metrics
1. **Determinate Accuracy ($Acc_{\text{det}}$):**  
   Accuracy computed strictly over samples where the model produces a determinate prediction (`low`, `moderate`, `high`, `critical`), excluding `indeterminate` outputs.
2. **Coverage Rate ($Cov$):**  
   The proportion of samples where the model commits to a determinate hazard classification:
   $$Cov = \frac{N_{\text{determinate}}}{N_{\text{total}}}$$
3. **Macro-Averaged F1 ($F1_{\text{macro}}$):**  
   Unweighted mean of class-specific F1 scores across all hazard classes:
   $$F1_{\text{macro}} = \frac{1}{|C|} \sum_{c \in C} F1_c$$
4. **Wilson 95% Confidence Intervals:**  
   Asymmetric binomial score intervals computed for accuracy and coverage via [`compute_wilson_ci()`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/vlm_evaluation.py#L230-L246), avoiding normal-approximation failures on small sample sizes.

### 3.2 Safety-Critical False-Negative Error Analysis
In disaster-management systems, **false negatives (predicting `none` or `low` when actual hazard is `high` or `critical`) are catastrophic errors**, while false positives (cautionary evacuations) represent operational costs.

The evaluation scorecard must explicitly track:
- **Critical Under-Prediction Rate:** Count of `critical` actual hazards predicted as `low` or `none`.
- **Confusion Matrix:** Full $5 \times 5$ contingency table mapping actual vs. predicted classes.
- **Stratification by Image Quality:** Accuracy breakdown across `high_resolution`, `adequate`, and `low_resolution` subsets to verify performance robustness under degraded field optics.

---

## 4. Evaluation Readiness Checklist

| Readiness Gate | Criteria | Current Status | Evidence / Notes |
| :--- | :--- | :--- | :--- |
| **G1: Image Integrity** | 100% of images decodable, $\ge 400\text{ px}$, valid hashes | **PASS** | 54/54 verified via Pillow & SHA-256 |
| **G2: Storage Segregation** | Candidate images stored outside production upload directories | **PASS** | Stored in `data/public_candidates/images/` |
| **G3: License Provenance** | 100% of candidate images have documented open licenses | **PASS** | 54/54 under CC BY, CC BY-SA, or Public Domain |
| **G4: Data Leakage Protection**| Automated split-integrity guard prevents cluster leakage | **PASS** | Verified by 10 targeted tests in `test_annotation_protocol.py` |
| **G5: Ground-Truth Adjudication**| Independent dual-expert annotations completed & consensus signed | **BLOCKED** | All 54 records currently `pending_review` with empty labels |
| **G6: Sample Size Adequacy** | Sufficient sample size ($N \ge 100$) for statistical power | **BLOCKED** | Current pool ($N=54$) too small for formal held-out splits |

### Final Conclusion
PahaarPulse is technically prepared for expert review. The ingestion, validation, cluster tracking, and evaluation infrastructure are 100% green and regression-free. However, **evaluation execution is correctly gated and blocked** until qualified geotechnical reviewers complete the independent annotation protocol established in Phase 2D.
