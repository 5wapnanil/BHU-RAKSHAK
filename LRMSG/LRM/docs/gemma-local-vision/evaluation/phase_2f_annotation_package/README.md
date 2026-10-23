# PahaarPulse — Human Annotation & Adjudication Package

**Package Version:** v1.0 (Phase 2F)  
**Release Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Subsystem:** Gemma Field-Photo Vision Hazard Screening Benchmark  
**Review Target:** Public Candidate Evaluation Cohort ($N=54$)  

---

## 1. Purpose & Scope

This package contains the operational guidelines, standardized data entry forms, decision protocols, and review checklists for independent dual-expert geotechnical labeling of field photographs.

### 1.1 Core Mission
To establish an uncompromised, scientifically defensible ground-truth reference set for evaluating PahaarPulse's vision models. 

### 1.2 The Golden Rule of Scientific Integrity
**No model predictions, web search titles, or file metadata may be consulted during annotation.** Reviewers evaluate each photograph based strictly on visible optical evidence within the frame.

---

## 2. Package Contents & File Inventory

```
docs/gemma-local-vision/evaluation/phase_2f_annotation_package/
├── README.md               # This document (purpose, architecture, workflow)
├── annotator_guide.md      # Detailed operational guide, decision trees, criteria
├── annotation_form.csv     # Blank, versioned template for individual reviewer
├── adjudication_form.csv   # Structured consensus resolution form
└── review_checklist.md     # Pre-submission verification checklist
```

1. **[`README.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/README.md):** Workflow rules, blind-review separation, and dispute escalation protocols.
2. **[`annotator_guide.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/annotator_guide.md):** The operational specification defining required evidence, insufficient evidence, edge cases, and the 5-class visual-triage taxonomy.
3. **[`annotation_form.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/annotation_form.csv):** Form containing candidate IDs and SHA-256 hashes with blank annotation fields.
4. **[`adjudication_form.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/adjudication_form.csv):** Formal record of disagreements, consensus labels, and escalation tracking.
5. **[`review_checklist.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/review_checklist.md):** Verification checklist ensuring completeness, uncertainty documentation, and schema compliance.

---

## 3. Double-Blind Review Workflow

To prevent anchoring bias and social conformity, the annotation campaign enforces a strict double-blind protocol:

```
                  ┌─────────────────────────────────────────┐
                  │ 54 Candidate Images (data/public_.../)  │
                  └───────────────────┬─────────────────────┘
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
┌───────────────────────────────────┐                   ┌───────────────────────────────────┐
│ Reviewer 1 (Independent)          │                   │ Reviewer 2 (Independent)          │
│ • Completes annotation_form_R1.csv│                   │ • Completes annotation_form_R2.csv│
│ • Blind to Reviewer 2 answers     │                   │ • Blind to Reviewer 1 answers     │
└─────────────────┬─────────────────┘                   └─────────────────┬─────────────────┘
                  │                                                       │
                  └───────────────────────────┬───────────────────────────┘
                                              ▼
                              ┌───────────────────────────────┐
                              │ Automated Disagreement Check  │
                              │ (Cohen's Kappa & Gwet's AC1)  │
                              └───────────────┬───────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
       [ Agreement (R1 == R2) ]                            [ Disagreement (R1 != R2) ]
                    │                                                   │
                    ▼                                                   ▼
       ┌─────────────────────────┐                         ┌─────────────────────────┐
       │ Consensus Label Adopted │                         │ Senior Adjudication     │
       │ (Documented in Audit)   │                         │ (adjudication_form.csv) │
       └─────────────────────────┘                         └─────────────────────────┘
```

### 3.1 Blind Isolation Rules
1. **No Shared Worksheets:** Reviewer 1 and Reviewer 2 receive separate copies of `annotation_form.csv` (named `annotation_form_R1.csv` and `annotation_form_R2.csv`).
2. **No Interim Discussion:** Reviewers must not communicate regarding individual candidate images until both forms are fully completed and committed to version control.
3. **No Model Access:** Reviewers are prohibited from accessing Gemma VLM analysis endpoints or viewing model prediction outputs during the review period.

---

## 4. Adjudication & Disagreement Resolution

When Reviewer 1 and Reviewer 2 assign different hazard triage classes or disagree on primary failure mechanisms:
1. **Preservation of Original Records:** Neither reviewer's original annotation is altered or deleted.
2. **Formal Disagreement Logging:** The conflicting records are merged into [`adjudication_form.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/adjudication_form.csv), capturing `annotator_1_label`, `annotator_2_label`, and `disagreement_type`.
3. **Senior Adjudicator Review:** An independent third geotechnical specialist inspects the image and both sets of notes, determining the `consensus_label` and documenting the `adjudication_rationale`.
4. **Escalation Protocol:** If an image depicts an ambiguous or severely occluded feature where neither consensus nor definitive geomorphic interpretation can be reached, the image is marked `escalation_required=yes` and classified as `indeterminate` or `excluded`.

---

## 5. Reviewer Qualification Requirements

To ensure scientific defensibility, human annotators must possess documented domain qualifications:
- **Mandatory Background:** Degree in Geotechnical Engineering, Engineering Geology, Civil Engineering (with slope mechanics specialization), or Earth Sciences with field mapping experience.
- **Protocol Training:** Reviewers must complete a formal walkthrough of [`annotator_guide.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2f_annotation_package/annotator_guide.md) and demonstrate agreement on 5 calibration training images prior to reviewing the candidate cohort.
- **Reviewer Identifier Format:** Identifiers must follow standard anonymized institutional codes (e.g., `EXPERT_GEOTECH_01`, `EXPERT_GEOTECH_02`). Generic labels or AI model strings are strictly rejected by backend validators.
