# PahaarPulse — Reviewer Qualification Criteria & Domain Competencies

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Applicability:** Human Geotechnical Annotators & Adjudication Personnel  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  

---

## 1. Domain Expertise Rationale

Evaluating ground-level photographs of mountainous highway corridors for slope instability requires specialized scientific expertise. Unlike general object detection (e.g., vehicles, pedestrians), geomorphic hazard screening demands deep understanding of:
1. **Kinematics of Mass Wasting:** Discerning whether displaced rock debris originated from a planar slide, wedge failure, toppling event, or debris flow runout.
2. **Precursor Instability Signatures:** Recognizing subtle surface deformations (hairline tension cracks in asphalt, en-echelon shearing, shoulder subsidence, wall bulging) before catastrophic road loss occurs.
3. **Engineered Control Assessment:** Distinguishing functioning structural mitigations (gabion/masonry retaining walls, pinned rockfall drapery, concrete catch fences, culverts) from failing or overtopped infrastructure.
4. **Epistemic Limitations of 2D Vision:** Understanding what can and cannot be established from optical surface imagery, strictly avoiding the "negative control fallacy" (an intact wall in camera frame does not prove infinite slope stability).

---

## 2. Reviewer Qualification Tiers

Prospective human reviewers must meet the credential and experience standards of at least one of the following three tiers:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Tier 1: Senior Geotechnical / Geological Expert (Adjudication & Review)       │
│ • Education: Ph.D. or M.Sc. / M.Tech in Geotechnical Engineering, Engineering │
│   Geology, Geological Sciences, or Natural Hazard Management.                 │
│ • Experience: ≥ 5 years professional engineering practice or academic research│
│   in rock/soil slope stability, landslide hazard mapping, or mountain highway │
│   transportation corridor geotechnical monitoring.                            │
│ • Role: Authoritative adjudication of reviewer disagreements; protocol lead.   │
├───────────────────────────────────────────────────────────────────────────────┤
│ Tier 2: Field Geotechnical Reviewer (Independent Reviewer 1 or 2)             │
│ • Education: B.Sc. / B.Tech in Civil Engineering, Geology, or Earth Sciences. │
│ • Experience: ≥ 2 years practical experience in highway cut-slope inspection, │
│   rockfall mitigation installation, retaining wall inspection, or geohazard   │
│   reconnaissance surveys.                                                     │
│ • Role: Independent primary annotation of blinded image batches.              │
├───────────────────────────────────────────────────────────────────────────────┤
│ Tier 3: Post-Graduate Geomorphology Researcher (Independent Reviewer 1 or 2)  │
│ • Education: Advanced Master's or enrolled Ph.D. candidate in Geomorphology,  │
│   Engineering Geology, or Physical Geography.                                 │
│ • Experience: Formal graduate coursework in rock mechanics, slope stability   │
│   analysis, and field photogrammetry / optical reconnaissance.                 │
│ • Role: Independent primary annotation of blinded image batches.              │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mandatory Competency Assessment

Prior to authorization and assignment of blinded image batches, each candidate reviewer must demonstrate competence in four essential domains:

### 3.1 Competency 1: Mass Wasting Mechanism Differentiation
- **Requirement:** Ability to correctly apply Varnes / Cruden & Varnes / Hungr mass-wasting taxonomy to optical surface features.
- **Verification:** Correctly distinguish:
  - *Rockfall / Topple:* Detached rock blocks on pavement originating from vertical or near-vertical cut slopes.
  - *Debris Flow / Mudflow:* High-velocity, saturated slurry of sediment, rocks, and organic material channeled down ravines.
  - *Translational / Rotational Slide:* Shear displacement along identifiable planar or concave failure surfaces.

### 3.2 Competency 2: Incipient Precursor Hazard Recognition
- **Requirement:** Ability to detect sub-failure deformation without confusing it with routine pavement aging or construction joints.
- **Verification:** Differentiate:
  - *Active Geomorphic Tension Cracking:* Arcuate, crescentic, or en-echelon fractures parallel to slope crest or road shoulder, indicating active slip surface propagation.
  - *Non-Hazard Asphalt Defects:* Pavement thermal fatigue, longitudinal shrinkage cracking, or utility trench repaving joints.

### 3.3 Competency 3: Engineered Mitigation Structural Health Inspection
- **Requirement:** Ability to assess engineered slope protection assets and recognize functional vs. distressed states.
- **Verification:** Identify:
  - *Functioning Engineered Controls:* Intact gravity/gabion retaining walls, clear drainage ditches/culverts, pinned wire mesh securely retaining cobbles.
  - *Distressed / Failed Controls:* Outward wall rotation/bulging, blocked culvert barrels discharging water onto road fills, ruptured wire drapery with overtopped rock debris.

### 3.4 Competency 4: Epistemic Honesty & Uncertainty Handling
- **Requirement:** Complete alignment with the Phase 2E/2I evidentiary tier framework.
- **Verification:** Annotator must affirm that:
  - Single 2D optical images cannot determine subsurface pore pressures or deep shear plane cohesion.
  - If focal length, distance, lighting, fog, or shadow prevent reliable observation of slope features, the correct label is `UNCERTAIN_INSUFFICIENT_CONTEXT` rather than an ungrounded guess.

---

## 4. Qualification Verification & Audit Trail Procedure

1. **Document Submission:** Candidate submits verified copies of academic degrees, professional licenses (e.g., PE, CEng, P.Geo, or equivalent), and a curriculum vitae detailing slope stability experience.
2. **Administrative Intake:** Reviewer identity and credentials are logged into an offline administrative registry by the Evaluation Working Group Lead.
3. **Pseudonymization:** Reviewer is assigned an immutable opaque identifier (`REV_A1`, `REV_B2`, etc.). Real personal data is never committed to code repositories, benchmark manifests, or model prompts.
4. **Competency Affirmation:** Reviewer reads the Phase 2I annotation protocol and completes the onboarding checklist affirmation.
5. **Machine-Readable Audit Entry:** The verification is recorded in [`reviewer_qualification_log_template.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/reviewer_qualification_log_template.csv) prior to batch assignment.
