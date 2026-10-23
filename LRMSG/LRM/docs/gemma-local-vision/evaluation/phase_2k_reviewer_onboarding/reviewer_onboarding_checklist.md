# PahaarPulse — Reviewer Onboarding Gatekeeper Checklist

**Checklist Version:** v1.0  
**Effective Date:** 2026-10-23  
**Reviewer Identifier (Placeholder):** `[ENTER_REVIEWER_PSEUDONYM_E_G_REV_A1]`  
**Verification Authority (Placeholder):** `[ENTER_VERIFYING_OFFICER_NAME_OR_TITLE]`  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  

---

## 1. Overview & Gatekeeping Function

This checklist serves as an operational gate. No human reviewer may receive blinded evaluation packages or submit annotations until every requirement below is verified, affirmed, and signed off by the Evaluation Working Group Lead.

> [!CAUTION]
> **Placeholder Notice:**  
> This document is an unpopulated operational checklist template. Checkboxes must only be marked upon genuine receipt and verification of real credentials and affirmations.

---

## Part A: Credential & Competency Verification

- [ ] **A1. Academic Credential Verification:** Verified degree certificates (B.Sc., M.Sc., Ph.D., B.Tech, M.Tech) in Civil Engineering, Geology, Geotechnical Engineering, or related geosciences.
- [ ] **A2. Experience Verification:** Verified $\ge 2$ years practical/research experience in geotechnical slope inspection, landslide reconnaissance, or mountain corridor infrastructure monitoring.
- [ ] **A3. Qualification Tier Assignment:** Classified into Tier 1 (Senior Expert), Tier 2 (Field Reviewer), or Tier 3 (Post-Graduate Researcher).
- [ ] **A4. Administrative Registry Logging:** Recorded real name, institutional affiliation, CV audit reference, and contact details in offline administrative registry.
- [ ] **A5. Pseudonym Assignment:** Issued controlled alphanumeric reviewer identifier (e.g., `REV_A1`, `REV_B2`).

---

## Part B: Hardware & Inspection Environment

- [ ] **B1. Display Resolution:** Confirmed primary evaluation monitor has a native resolution of $\ge 1920 \times 1080\text{ px}$.
- [ ] **B2. Color & Contrast Calibration:** Display is calibrated with neutral color balance and adequate contrast to resolve subtle shadowing in rock fractures.
- [ ] **B3. Software Inspection Tooling:** Reviewer has uncompressed image viewing software capable of $100\%$ native pixel rendering without bicubic softening or lossy smoothing.

---

## Part C: Protocol & Taxonomy Mastery

- [ ] **C1. Protocol Review:** Reviewer has read [`annotation_protocol.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2i_annotation_package/annotation_protocol.md) (Version `v1.0`).
- [ ] **C2. Taxonomy Comprehension:** Demonstrated understanding of the 6 canonical categories:
  - `ACUTE_SLOPE_FAILURE_OR_DEBRIS`
  - `PRECURSOR_INSTABILITY_INDICATOR`
  - `INTACT_ENGINEERING_CONTROL`
  - `CONTEXTUAL_TERRAIN_LANDSCAPE`
  - `UNCERTAIN_INSUFFICIENT_CONTEXT`
  - `UNUSABLE_OUT_OF_SCOPE`
- [ ] **C3. Evidentiary Guardrails:** Familiar with Level 1 (optical surface), Level 2 (geomorphic inference), and Level 3 (subsurface ground truth limitations).
- [ ] **C4. Uncertainty Protocol:** Acknowledged that ambiguous, distant, or occluded imagery must be labeled `UNCERTAIN_INSUFFICIENT_CONTEXT` rather than guessed.

---

## Part D: Confidentiality, Blinding & Ethical Affirmations

- [ ] **D1. Strict Reviewer Independence:** Reviewer affirmed in writing that they will conduct evaluations in isolation and will not communicate with companion reviewers.
- [ ] **D2. External Search Ban:** Reviewer affirmed that they will not use reverse image search engines, metadata extractors, or web queries to find original image sources.
- [ ] **D3. Model Contamination Ban:** Reviewer affirmed they have had zero exposure to Gemma VLM zero-shot predictions or historical evaluation outputs.
- [ ] **D4. Conflict of Interest Disclosure:** Reviewer reported whether they have prior familiarity or proprietary involvement with any site or image in the evaluation set.

---

## Part E: Submission Validation & Package Custody

- [ ] **E1. Schema Compliance Awareness:** Familiar with required CSV column structure and format of `annotation_form.csv`.
- [ ] **E2. Mechanical Validator Training:** Briefed on the automated submission validator [`validate_human_annotations.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/scripts/validate_human_annotations.py) and required ISO 8601 timestamps.
- [ ] **E3. Blinded Package Receipt:** Received blinded distribution bundle with zero metadata leakage (no search queries, no GPS, no model labels).
- [ ] **E4. Assignment Registry Logged:** Formally recorded in [`reviewer_assignment_template.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/reviewer_assignment_template.csv).

---

## Part F: Operational Sign-off & Gate Approval

```
Reviewer Pseudonym:        [ENTER_PSEUDONYM]
Assigned Evaluation Batch: [ENTER_BATCH_E_G_PHASE_2J_PILOT]
Assigned Protocol Version: v1.0
Verification Date:         [YYYY-MM-DD]
Verifying Officer:         [ENTER_NAME_AND_TITLE]
Verification Status:       [PENDING / APPROVED / REJECTED]
Signature (Placeholder):   __________________________________
```
