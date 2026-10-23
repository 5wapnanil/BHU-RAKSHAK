# PahaarPulse — Reviewer Recruitment Brief

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Target Audience:** Prospective Geotechnical & Engineering Geology Reviewers  

---

## 1. Project Mission & Scientific Background

PahaarPulse is an open-science early-warning and landslide risk screening system designed to enhance transportation safety along vulnerable mountain highway corridors, with a primary focus on the Indian Himalayan Region (IHR).

As part of the evaluation of computer vision systems for emergency slope monitoring, we are establishing an authoritative, publication-grade human ground-truth benchmark. This benchmark measures the ability of vision systems to:
1. Detect acute mass wasting failures (rockfall rubble, debris flows, translational slide scarps) obstructing roadways.
2. Identify early precursor instability signatures (asphalt tension cracking, shoulder subsidence, wall bulging) before catastrophic loss of roadway occurs.
3. Differentiate intact engineering mitigations (retaining walls, pinned rockfall netting, clear drainage culverts) from failing slopes to prevent false-alarm cascades.
4. Express appropriate epistemic modesty when atmospheric conditions (fog, shadow, distance) limit visual confidence.

To ensure scientific defensibility, all evaluation imagery must be independently evaluated by qualified human geotechnical and geological experts under strict double-blinding.

---

## 2. Scope of Image Triage & Review Tasks

Reviewers will evaluate high-resolution ground-level photographs taken from mountain road corridors. For each image, the reviewer executes a structured 4-zone visual inspection:
- **Zone 1: Roadway Surface & Shoulders:** Road blockage, fresh boulder accumulation, sediment mud slurry, pavement cracks.
- **Zone 2: Cut Slope & Hillside Face:** Exposed shear scarps, detachment faces, tilted vegetation, uncontrolled seepage.
- **Zone 3: Engineered Infrastructure:** Gravity/gabion retaining walls, pinned wire mesh drapes, catch fences, roadside drainage culverts and ditches.
- **Zone 4: Atmospheric & Optical Context:** Distance to slope, lighting contrast, fog/rain spray occlusion, motion blur.

For each photograph, reviewers will record:
1. **Primary Category:** Exactly one of 6 standardized geomorphic categories:
   - `ACUTE_SLOPE_FAILURE_OR_DEBRIS`
   - `PRECURSOR_INSTABILITY_INDICATOR`
   - `INTACT_ENGINEERING_CONTROL` (Negative Control)
   - `CONTEXTUAL_TERRAIN_LANDSCAPE` (Negative Control)
   - `UNCERTAIN_INSUFFICIENT_CONTEXT` (Valid epistemic label)
   - `UNUSABLE_OUT_OF_SCOPE`
2. **Confidence Level:** `HIGH`, `MEDIUM`, or `LOW`.
3. **Observable Indicators:** Semicolon-delimited visible features (e.g., `boulder_debris; blocked_lane; scarp`).
4. **Quality Limitations:** `NONE`, `BLURRED`, `DISTANT`, `LOW_CONTRAST`, or `OCCLUDED`.
5. **Geomorphic Rationale:** A concise 1–3 sentence narrative explaining the physical justification for the classification.
6. **Adjudication Flag:** `YES` or `NO` if the case is borderline or difficult.

---

## 3. Expected Qualifications & Domain Expertise

We seek reviewers with formal training and experience in:
- **Civil Engineering / Geotechnical Engineering** (B.Sc., B.Tech, M.Sc., M.Tech, Ph.D.).
- **Engineering Geology / Earth Sciences / Geomorphology**.
- **Practical Field Experience:** Familiarity with slope stability assessment, highway cut-slope inspections, rockfall mitigation installation, or landslide hazard mapping.

*Formal qualification tiers (Tier 1 Senior Expert, Tier 2 Field Reviewer, Tier 3 Post-Graduate Researcher) are detailed in [`qualification_decision_guide.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/qualification_decision_guide.md).*

---

## 4. Expected Review Workload & Commitment

The evaluation is structured into two sequential stages:

| Stage | Cohort Size | Estimated Reviewer Time Commitment | Notes |
| :--- | :---: | :---: | :--- |
| **Stage 1: Calibration Pilot** | 10 images | **15 – 30 minutes** (annotation)<br>+ **30 minutes** (calibration debrief) | Evaluates taxonomy clarity and workflow. Discordant cases are reviewed to calibrate edge cases. |
| **Stage 2: Full Benchmark Cohort** | 102 images | **2.5 – 4.0 hours total** (can be completed across multiple self-paced sessions) | Full independent annotation of the cleared dataset. |

*Exact terms of engagement, research co-authorship / acknowledgment, or compensation/honorarium are to be confirmed directly by the Project Owner prior to formal assignment.*

---

## 5. Reviewer Protections & Ethical Standards

- **Blinded Evaluation:** Reviewers evaluate images without seeing model predictions, online search tags, or companion reviews.
- **Privacy & Anonymity:** Reviewers are assigned pseudonyms (`REV_A1`, `REV_B2`). Personal identity documents and contact details are stored offline and never committed to the public code repository.
- **Epistemic Honesty Valued:** Acknowledging uncertainty (`UNCERTAIN_INSUFFICIENT_CONTEXT`) is considered a high-value scientific label, not an error.

---

## 6. How to Express Interest

Interested experts should submit:
1. A brief curriculum vitae or professional profile highlighting slope stability, civil/geotechnical engineering, or geomorphology experience.
2. The completed [`reviewer_screening_questionnaire.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/reviewer_screening_questionnaire.md).

Submissions should be delivered directly to the Project Owner via secure institutional communication.
