# PahaarPulse — Reviewer Capacity & Workload Planning Guide

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Applicability:** Human Evaluation Coordinator & Project Owner  

---

## 1. Capacity Planning Rationale

A successful, publication-grade evaluation requires realistic capacity planning. Expert geotechnical engineers and academic geomorphologists maintain heavy professional workloads. Estimating review times accurately, budgeting for adjudicator bandwidth, and maintaining a backup reviewer bench are critical to preventing project stalls.

> [!IMPORTANT]
> **No Presumed Availability:**  
> This guide is a planning template. It does **not** assume any individual is currently available or willing to participate. All commitments must be formally confirmed via the screening questionnaire and invitation responses.

---

## 2. Reviewer Workload Model

Based on structured 4-zone inspection (road surface, cut slope, infrastructure, atmospheric limitations) and required geomorphic rationales:

| Evaluation Phase | Total Images | Images per Reviewer | Est. Time per Image | Total Active Time | Recommended Turnaround Window |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Phase 1: Calibration Pilot** | 10 | 10 | 2 – 3 minutes | **20 – 30 minutes** | 5 business days from dispatch |
| **Calibration Debrief** | — | — | Joint discussion | **30 – 45 minutes** | 3 business days post-validation |
| **Phase 2: Full Benchmark Cohort** | 102 | 102 | 1.5 – 2.5 minutes | **2.5 – 4.0 hours** | 15 business days from dispatch |

*Note: For the full 102-image cohort, reviewers should be encouraged to complete the work in 2 or 3 separate sessions (e.g., 30–40 images per session) to prevent visual fatigue and maintain inspection rigor.*

---

## 3. Senior Adjudicator Bandwidth Model

The Senior Geotechnical Adjudicator (`ADJ_LEAD`) evaluates cases where Reviewer 1 and Reviewer 2 disagree, or where either reviewer flagged `requires_adjudication = YES`:

| Evaluation Phase | Est. Disagreement / Escalation Rate | Est. Items for Adjudication | Est. Time per Adjudication | Total Adjudicator Commitment |
| :--- | :---: | :---: | :---: | :---: |
| **Pilot Batch ($N=10$)** | 20% – 30% | 2 – 3 images | 5 – 8 minutes (in-depth inspection) | **15 – 25 minutes** |
| **Full Cohort ($N=102$)** | 15% – 25% | 15 – 25 images | 5 – 8 minutes | **1.5 – 3.0 hours** |

---

## 4. Operational Timeline & Turnaround Schedule

```
Target Milestone                 Duration         Responsible Party
─────────────────────────────────────────────────────────────────────────
1. Candidate Outreach            7–10 days        Project Owner
2. Screening & Qualification     2–3 days         Evaluation Coordinator
3. Pilot Dispatch & Review       5 days           Reviewer 1 & Reviewer 2
4. Pilot Validation & Diffing    1 day (automated)Evaluation Coordinator
5. Pilot Adjudication & Debrief  3 days           Adjudicator & Reviewers
6. Full Cohort Dispatch          15 days          Reviewer 1 & Reviewer 2
7. Full Cohort Adjudication      5 days           Senior Adjudicator
8. Final Benchmark Consensus     2 days           Working Group Lead
─────────────────────────────────────────────────────────────────────────
```

---

## 5. Contingency Protocols: Dropouts, Delays & Conflicts of Interest

### 5.1 Reviewer Delays & Abandonment
- **Check-in Milestone:** If a reviewer has not confirmed receipt or submitted within 3 business days of the deadline, a gentle reminder is sent.
- **Replacement Trigger:** If a reviewer withdraws or fails to respond within 5 business days past the deadline, their incomplete assignment is marked `WITHDRAWN` and the backup candidate (`REV_C3`) is onboarded. Partial submissions from withdrawn reviewers are discarded to maintain independence.

### 5.2 Conflict of Interest (COI) Replacement
If an assigned reviewer declares prior involvement with a specific site (e.g., conducted forensic post-event analysis on a road failure depicted in `ANN_047`), the coordinator:
1. Logs the conflict in `pilot_issue_log_template.csv`.
2. Leaves the non-conflicted reviewer's submission intact.
3. Reroutes the specific image to the backup reviewer or elevates directly to the Senior Adjudicator.
