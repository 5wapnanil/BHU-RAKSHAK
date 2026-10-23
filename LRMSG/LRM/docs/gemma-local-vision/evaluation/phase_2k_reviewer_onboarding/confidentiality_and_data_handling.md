# PahaarPulse — Confidentiality, Blinding & Data Handling Protocol

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Applicability:** All Onboarded Human Annotators, Adjudicators & Working Group Personnel  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  

---

## 1. Ethical Foundations & Scientific Integrity

The PahaarPulse ground-level image evaluation benchmark establishes life-critical screening baselines for early mountain highway landslide hazards. To guarantee scientific defensibility and publication-grade integrity, all human evaluations must adhere to strict confidentiality, blinding, and data handling protocols.

---

## 2. Reviewer Blinding & Isolation Protocol

### 2.1 Double-Blinded Evaluation Architecture
Reviewers evaluate images under strict double-blinding:
1. **Blind to Model Predictions:** Reviewers must never have access to Gemma VLM outputs, prompt transcripts, confidence scores, or historical evaluation metrics.
2. **Blind to Source Context:** Reviewers receive only opaque identifiers (`ANN_001` through `ANN_102`) and raw optical image files. All Wikimedia Commons titles, URLs, geocoding coordinates, uploader comments, and search keywords are withheld.
3. **Blind to Companion Reviewers:** Reviewer 1 (`REV_A1`) and Reviewer 2 (`REV_B2`) evaluate identical batches independently. Neither reviewer knows the identity of their companion or sees their annotations until formal adjudication.

### 2.2 Strict Prohibition of External Web Queries
- **Reverse Image Search Prohibition:** Annotators are legally and ethically bound not to execute reverse image searches (e.g., Google Lens, TinEye, Bing Visual Search) or search image hashes.
- **Geographic Hunting Prohibition:** Annotators must not search regional maps, news reports, or social media to discover where or when an incident occurred.
- **Evidentiary Primacy:** All classifications must derive exclusively from Level 1 directly observable optical features within the supplied photograph.

---

## 3. Conflict of Interest & Prior Familiarity Disclosure

If a human reviewer has personal, professional, or academic familiarity with a specific image or geographic site:
1. **Immediate Disclosure:** The reviewer must record the `annotation_id` and declare their prior knowledge in [`pilot_issue_log_template.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/pilot_issue_log_template.csv) under `issue_type = CONFLICT_OF_INTEREST_OR_PRIOR_FAMILIARITY`.
2. **Evaluation Impact Assessment:** The Evaluation Working Group assesses whether the familiarity compromises blinding. If prior knowledge reveals the subsurface outcome (Level 3 ground truth) that cannot be seen optically, an alternate blinded reviewer is assigned to that item.

---

## 4. Handling Optical Uncertainty & Missing Context

Reviewers must not speculate or attempt to extrapolate beyond what the camera captured:
- **Optical Obstructions:** Heavy fog, rain spray, night shadows, or motion blur that prevent resolving cut slopes or road shoulders must be recorded as `UNCERTAIN_INSUFFICIENT_CONTEXT` with appropriate limitation flags (`BLURRED`, `DISTANT`, `LOW_CONTRAST`, or `OCCLUDED`).
- **Missing Perspective:** If a road blockage is suspected but the camera angle cuts off the roadway entirely, reviewers must flag `requires_adjudication = YES` and explain the geometric limitation in `geomorphic_rationale`.

---

## 5. Auditability, Corrections & Change Tracking

Any modification to annotations, assignments, or protocol guidelines must follow an auditable chain of custody:
1. **Immutable Original Submissions:** Once submitted and validated, a reviewer's CSV file is hashed (SHA-256) and archived in a read-only directory. It is never edited in place.
2. **Change Log Requirement:** Any post-submission correction requested by a reviewer before adjudication must be logged in [`annotation_change_log.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2i_annotation_package/annotation_change_log.csv) with timestamp, previous value, new value, and technical justification.
3. **Adjudication Transparency:** When disagreements are adjudicated, the Adjudication Lead records the specific rationale resolving the dispute. Both reviewers' original opinions are preserved in the consensus manifest.

---

## 6. Protection of Source Attribution & Licensing Provenance

While reviewers receive blinded packages to prevent cognitive bias, the project strictly respects open-access copyright and provenance:
1. **Separation of Attributions:** Authoritative creator names, licenses (e.g., CC BY 2.0, CC BY-SA 4.0, Public Domain), and source URLs are permanently maintained in [`candidate_index.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2i_annotation_package/candidate_index.csv) and [`license_provenance_audit.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/license_provenance_audit.csv).
2. **Attribution Restoration:** When the final benchmark is published, full creator attributions and license notices will be restored in the public benchmark release, fulfilling all legal requirements without compromising internal evaluation blinding.
