# PahaarPulse — Phase 2I: Reviewer & Adjudicator Quality Checklist

**Checklist Version:** v1.0  
**Effective Date:** 2026-10-23  
**Applicability:** Human Geotechnical Annotators & Adjudication Lead  

---

## Part A: Human Annotator Pre-Review Checklist

Before evaluating any field photographs, each reviewer must verify and affirm:

- [ ] **Display Calibration:** Monitor resolution is $\ge 1920 \times 1080\text{ px}$ with calibrated contrast and color profile.
- [ ] **Native Resolution Viewing:** Image viewing software is configured to allow $100\%$ native raster inspection without lossy resampling.
- [ ] **Package Integrity:** All 102 images (`ANN_001` to `ANN_102`) open cleanly without raster corruption or decoding failure.
- [ ] **Evidentiary Understanding:** Familiar with the distinction between Level 1 (optical evidence), Level 2 (geomorphic inference), and Level 3 (subsurface ground reality).
- [ ] **Category Mastery:** Confident in the boundaries of the 6 primary observation categories defined in [`annotation_protocol.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2i_annotation_package/annotation_protocol.md).
- [ ] **Independence Commitment:** Affirmed that no communication, file sharing, or discussion will take place with the companion reviewer during the review process.
- [ ] **Zero Outside Search:** Affirmed that no reverse image searching, title lookups, or metadata queries will be conducted.

---

## Part B: Image Evaluation Workflow Checklist (Per Image)

For each photograph evaluated:

- [ ] **Step 1: Pavement & Shoulder Check:** Inspected road surface for rock boulders, soil deposition, erosion washouts, and pavement cracking.
- [ ] **Step 2: Slope & Crown Check:** Inspected cut-slope face and crest for exposed scarps, tension cracks, tilted trees, and seepage.
- [ ] **Step 3: Infrastructure Check:** Inspected retaining walls, culvert barrels, drainage channels, and pinned netting for structural integrity.
- [ ] **Step 4: Quality & Atmosphere Check:** Evaluated visibility, fog, rain spray, distance, and shadow occlusion.
- [ ] **Step 5: Category Selection:** Selected exactly one category from the 6 standardized options.
- [ ] **Step 6: Confidence Rating:** Assigned `HIGH`, `MEDIUM`, or `LOW`.
- [ ] **Step 7: Evidence Enumeration:** Recorded observable indicators separated by semicolons.
- [ ] **Step 8: Rationale:** Provided a 1–3 sentence geotechnical explanation.
- [ ] **Step 9: Adjudication Flag:** If borderline or uncertain, flagged `requires_adjudication = YES`.

---

## Part C: Pre-Submission Verification Checklist

Before submitting `annotation_form.csv`:

- [ ] **Zero Missing Values:** Exactly 102 rows are completed with non-empty categories, confidences, and rationales.
- [ ] **Reviewer Identity:** Valid `reviewer_id` present across all 102 rows.
- [ ] **Timestamps Validated:** All `review_timestamp` entries follow ISO 8601 UTC format.
- [ ] **Valid Categories Only:** No non-standard category names, typos, or custom classifications.
- [ ] **No Overwritten Templates:** The original blinded template was preserved; annotations saved in reviewer's personal working copy.
- [ ] **Change Log Verification:** If any modifications were made post-completion, recorded in `annotation_change_log.csv`.

---

## Part D: Senior Geotechnical Adjudicator Checklist

Upon receiving submissions from Reviewer 1 and Reviewer 2:

- [ ] **Independent Completion Check:** Verified that both Reviewer 1 and Reviewer 2 completed all 102 images independently.
- [ ] **Automated Disagreement Detection:** Ran automated diff between Reviewer 1 and Reviewer 2 primary categories.
- [ ] **Inter-Rater Reliability Calculation:**
  - Computed raw percent agreement $P_o$.
  - Computed Cohen's Kappa $\kappa$ across binary hazard presence (`ACUTE_SLOPE_FAILURE_OR_DEBRIS` + `PRECURSOR_INSTABILITY_INDICATOR` vs. others).
  - Confirmed whether $\kappa \ge 0.70$ evaluation threshold is achieved.
- [ ] **Disagreement Adjudication:**
  - Inspected all cases with category mismatch.
  - Re-examined full image at 100% native resolution.
  - Assigned final authoritative `adjudicated_category` and wrote detailed `adjudication_rationale`.
- [ ] **Uncertain Case Adjudication:** Inspected all cases where either reviewer flagged `requires_adjudication = YES` or `UNCERTAIN_INSUFFICIENT_CONTEXT`.
- [ ] **Consensus Classification:** Categorized each resolution as `AGREED_CONSENSUS`, `ADJUDICATED_RESOLVED`, or `FLAGGED_DISPUTED_INSUFFICIENT_CONTEXT`.
- [ ] **Immutable Benchmark Lock:** Committed final consensus into version-controlled benchmark manifest and locked against future modification.
