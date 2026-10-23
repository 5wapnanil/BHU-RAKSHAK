# PahaarPulse — Reviewer Qualification Decision Guide

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Applicability:** Human Evaluation Coordinator & Working Group Lead  
**Authority:** Evaluation Working Group  

---

## 1. Purpose & Human Gatekeeper Responsibility

This guide provides an objective rubric for evaluating prospective human reviewer applications. It maps candidate documentary evidence to the project's Tier 1, 2, and 3 qualification standards.

> [!CAUTION]
> **No Automated or Fictional Approvals:**  
> Reviewers must **never** be automatically approved or synthesized by software scripts. A human coordinator must inspect real academic documents, verify professional experience, check screening questionnaire answers, and sign off on qualification logs before image packages are distributed.

---

## 2. Evidence Requirements & Verification Checklist

For each candidate, the human coordinator must inspect:
1. **Academic Proof:** Verified copy of degree certificate or official academic transcript.
2. **Professional Experience:** Curriculum vitae detailing slope stability, civil/geotechnical engineering, or geomorphology projects.
3. **Screening Questionnaire:** Verification of answers in [`reviewer_screening_questionnaire.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/reviewer_screening_questionnaire.md).
   - *Mandatory Pass on Question 10:* Must select "photograph shows only optical surface features... cannot confirm subsurface pore pressure without instrumentation."
   - *Mandatory Pass on Question 11:* Must select "I will select UNCERTAIN_INSUFFICIENT_CONTEXT and flag it for adjudication rather than guessing."
   - *Mandatory Pass on Questions 13 & 14:* Must affirm independence and the reverse-image search ban.

---

## 3. Tier Classification Decision Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: SENIOR GEOTECHNICAL EXPERT (Adjudication Lead or Senior Reviewer)                   │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ Required Academic Degree:   Ph.D. or M.Sc. / M.Tech in Geotechnical Engineering,           │
│                             Engineering Geology, Geological Sciences, or Natural Hazards.   │
│ Minimum Experience:         ≥ 5 years post-graduate professional engineering practice or    │
│                             academic research in rock/soil slope stability or hazard mapping│
│ Required Field Experience:  Direct experience inspecting or designing mountain highway      │
│                             retaining structures, rockfall netting, or slope stabilization. │
│ Eligible Project Roles:     • Senior Geotechnical Adjudicator                               │
│                             • Primary Reviewer 1 or Reviewer 2                              │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: FIELD GEOTECHNICAL REVIEWER (Primary Reviewer 1 or Reviewer 2)                      │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ Required Academic Degree:   B.Sc. / B.Tech in Civil Engineering, Geology, or Earth Sciences.│
│ Minimum Experience:         ≥ 2 years professional experience in slope inspection, cut-slope│
│                             stabilization, retaining wall assessment, or geohazard surveys. │
│ Required Field Experience:  Direct participation in field slope surveys or road inspections.│
│ Eligible Project Roles:     • Primary Reviewer 1 or Reviewer 2                              │
│                             (Not eligible for solo Senior Adjudicator role)                 │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 3: POST-GRADUATE GEOMORPHOLOGY RESEARCHER (Primary Reviewer 1 or Reviewer 2)           │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ Required Academic Status:   Enrolled Ph.D. candidate or advanced Master's researcher in     │
│                             Geomorphology, Engineering Geology, or Physical Geography.      │
│ Minimum Experience:         Completion of graduate coursework in rock mechanics, slope      │
│                             stability, and field photogrammetry / optical reconnaissance.   │
│ Eligible Project Roles:     • Primary Reviewer 1 or Reviewer 2                              │
│                             (Not eligible for solo Senior Adjudicator role)                 │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Disqualification & Rejection Criteria

A candidate must be **disqualified** if any of the following apply:
1. **Academic Mismatch:** Candidate lacks a relevant degree in Civil Engineering, Geology, Geotechnical Engineering, or Earth Sciences, with no compensating domain experience.
2. **Epistemic Incompatibility:** Candidate asserts that single surface photographs can prove absolute slope stability, or indicates an unwillingness to use the `UNCERTAIN_INSUFFICIENT_CONTEXT` label.
3. **Refusal of Blinding Affirmation:** Candidate refuses to affirm independence or declines to observe the reverse-image search ban.
4. **Hardware Inadequacy:** Candidate lacks access to a display of $\ge 1920 \times 1080\text{ px}$ resolution or uncompressed image viewing software.
5. **Significant Conflict of Interest:** Candidate has proprietary ownership or legal liability tied to a major commercial corridor represented in the benchmark.

---

## 5. Audit Logging Procedure

Upon reaching a qualification decision:
1. Assign the candidate a unique opaque pseudonym (e.g., `REV_A1`, `REV_B2`, `ADJ_LEAD`).
2. Log the candidate's real identity, CV reference, and degree verification in the **offline administrative registry**.
3. Record the non-sensitive audit entry in [`PHASE_2M_RECRUITMENT_TRACKER_TEMPLATE.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/PHASE_2M_RECRUITMENT_TRACKER_TEMPLATE.csv) and [`reviewer_qualification_log_template.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/reviewer_qualification_log_template.csv).
4. Store verified copies of application documents in the offline secure archive.
