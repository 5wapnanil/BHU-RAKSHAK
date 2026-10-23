# PahaarPulse — Phase 2K: Reviewer Onboarding Packet

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Authority:** Geotechnical Data-Quality Specialist & Evaluation Working Group  
**Status:** ONBOARDING PACKAGE READY (Reviewer Recruitment Pending; Benchmark Inference Strictly Blocked)

---

## 1. Purpose & Scope

This packet contains the formal operational, ethical, and technical documentation required to recruit, verify, onboard, and manage qualified human geotechnical reviewers for the PahaarPulse visual landslide screening evaluation.

It operationalizes the 10-image Phase 2J pilot evaluation and establishes the governance controls needed before any ground-level field imagery can be distributed to human annotators.

> [!IMPORTANT]
> **Operational Status Affirmation:**  
> - Human Reviewers Recruited: **0** (zero).  
> - Human Reviews Completed: **0** (zero).  
> - Expert Adjudications Performed: **0** (zero).  
> - Fictional / Synthetic Records: **0** (strictly prohibited).  
> - Benchmark Model Inference: **STRICTLY BLOCKED** until dual-blind annotations and expert adjudications are finalized.

---

## 2. Directory Contents

| Filename | Description |
| :--- | :--- |
| [`reviewer_qualification_criteria.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/reviewer_qualification_criteria.md) | Exhaustive domain competency criteria across Tier 1 (Senior Expert), Tier 2 (Field Reviewer), and Tier 3 (Post-Graduate Researcher). |
| [`reviewer_onboarding_checklist.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/reviewer_onboarding_checklist.md) | Step-by-step gatekeeper checklist tracking qualification verification, calibration, and assignment. |
| [`confidentiality_and_data_handling.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/confidentiality_and_data_handling.md) | Binding protocol for data blinding, conflict-of-interest disclosure, reverse-image search ban, and license attribution protection. |
| [`pilot_execution_protocol.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/pilot_execution_protocol.md) | Strict operational rules governing the execution of the 10-image Phase 2J calibration pilot. |
| [`reviewer_assignment_template.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/reviewer_assignment_template.csv) | Machine-readable assignment log linking pseudonymous reviewers to batches and protocol versions (unpopulated template). |
| [`reviewer_qualification_log_template.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/reviewer_qualification_log_template.csv) | Machine-readable audit register documenting verified degrees, credentials, and verifier sign-offs (unpopulated template). |
| [`pilot_issue_log_template.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/pilot_issue_log_template.csv) | Standardized defect and ambiguity logging template for recording taxonomy uncertainties during the pilot (unpopulated template). |

---

## 3. Human Reviewer Core Responsibilities

1. **Independent Evaluation:** Complete annotations in isolation without conferring with companion reviewers.
2. **Standardized Taxonomy Application:** Apply the 6 canonical categories defined in [`annotation_protocol.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2i_annotation_package/annotation_protocol.md).
3. **Epistemic Honesty:** Explicitly assign `UNCERTAIN_INSUFFICIENT_CONTEXT` when 2D raster resolution or occlusion obscures slope features; never guess.
4. **Blinded Compliance:** Never attempt reverse image searches or examine file metadata to deduce geographic locations or model predictions.
5. **Issue Logging:** Document boundary ambiguities or raster defects in `pilot_issue_log_template.csv` to inform protocol amendments.
