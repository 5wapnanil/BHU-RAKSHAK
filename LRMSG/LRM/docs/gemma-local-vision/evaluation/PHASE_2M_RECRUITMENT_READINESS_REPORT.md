# PahaarPulse — Phase 2M: Reviewer Recruitment Readiness & Governance Report

**Document Version:** v1.0  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Authority:** Evaluation Working Group & Geotechnical Quality Lead  
**Operational Status:** **RECRUITMENT PACK READY** (Technical Governance Ready; Human Action Required)  
**Pipeline State:** `AWAITING_REVIEWER_RECRUITMENT`  
**Benchmark Inference Gate:** **STRICTLY BLOCKED**

---

## 1. Executive Summary & Readiness Assessment

Phase 2M prepares the operational bridge between technical workflow testing (Phases 2I–2L) and **authentic human-reviewed ground truth**.

All recruitment briefs, screening rubrics, consent checklists, capacity models, candidate tracking logs, and launch-gate verification mechanisms are operational and staged.

### Operational State Summary:
- **What is Prepared:** 
  - Complete 8-part recruitment package under [`docs/gemma-local-vision/evaluation/phase_2m_recruitment/`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/).
  - Pilot assignment protocol under [`docs/gemma-local-vision/evaluation/PHASE_2M_PILOT_ASSIGNMENT_PROTOCOL.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/PHASE_2M_PILOT_ASSIGNMENT_PROTOCOL.md).
  - Mechanical launch-gate verifier ([`verify_pilot_launch_gate`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/scripts/validate_human_annotations.py#L650-L730)) blocking pilot distribution until 2 qualified human reviewers are approved.
  - Synthetic stub rejection (`--reject-synthetic`) protecting production validation.
- **What Remains Blocked:**
  - Pilot package distribution is blocked (0 real reviewers recruited; launch gate evaluated as `False`).
  - Model inference against the benchmark remains strictly **BLOCKED**.

---

## 2. Reviewer Recruitment Asset Inventory

The following recruitment assets were prepared and verified:

| Deliverable Asset | Path | Scope & Function | Status |
| :--- | :--- | :--- | :--- |
| **Recruitment Readme** | [`phase_2m_recruitment/README.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/README.md) | Guide to recruitment process, privacy rules, and launch checklist. | Complete |
| **Recruitment Brief** | [`phase_2m_recruitment/reviewer_recruitment_brief.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/reviewer_recruitment_brief.md) | Project purpose, image triage scope, 4-zone inspection rules, and workload estimates. | Complete |
| **Invitation Template** | [`phase_2m_recruitment/reviewer_invitation_template.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/reviewer_invitation_template.md) | Formal invitation letter for project owner manual dispatch. | Complete |
| **Screening Questionnaire** | [`phase_2m_recruitment/reviewer_screening_questionnaire.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/reviewer_screening_questionnaire.md) | 16-point technical intake questionnaire assessing degrees, field inspection experience, and epistemic honesty. | Complete |
| **Decision Guide** | [`phase_2m_recruitment/qualification_decision_guide.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/qualification_decision_guide.md) | Rubric mapping candidate evidence to Tier 1/2/3 qualification standards and disqualification triggers. | Complete |
| **Consent & Blinding Checklist** | [`phase_2m_recruitment/reviewer_consent_and_confidentiality_checklist.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/reviewer_consent_and_confidentiality_checklist.md) | Ethical checklist covering voluntary consent, double-blinding, search ban, and attribution handling. | Complete |
| **Capacity Planning Worksheet** | [`phase_2m_recruitment/reviewer_capacity_planning.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/reviewer_capacity_planning.md) | Reviewer time estimates, turnaround windows, adjudicator bandwidth, and backup roster protocols. | Complete |
| **Recruitment Tracker Template** | [`phase_2m_recruitment/PHASE_2M_RECRUITMENT_TRACKER_TEMPLATE.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2m_recruitment/PHASE_2M_RECRUITMENT_TRACKER_TEMPLATE.csv) | Machine-readable candidate pipeline log with zero fictional records. | Complete (Valid) |
| **Pilot Assignment Protocol** | [`PHASE_2M_PILOT_ASSIGNMENT_PROTOCOL.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/PHASE_2M_PILOT_ASSIGNMENT_PROTOCOL.md) | Operational rules governing blinded distribution, conflict of interest, and transition authorization. | Complete |

---

## 3. Launch Gate Enforcement & Blocking Evidence

The automated launch gate check was executed against the repository:

```python
from backend.scripts.validate_human_annotations import verify_pilot_launch_gate

passed, reasons = verify_pilot_launch_gate(assignment_csv, qualification_csv, pilot_manifest_csv)
# Result: passed == False
# Reasons: ['Found 0 approved active reviewers in assignment log; exactly 2 required before pilot launch.']
```

### Why the Pilot Remains Blocked:
1. **Zero Real Reviewers:** No human candidates have applied, submitted credentials, or been audited.
2. **Assignment Placeholders:** [`reviewer_assignment_template.csv`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/gemma-local-vision/evaluation/phase_2k_reviewer_onboarding/reviewer_assignment_template.csv) contains unassigned placeholders.
3. **Double-Blind Prerequisite:** The protocol requires exactly two independently qualified reviewers (`REV_A1` and `REV_B2`) before package dispatch.
4. **Benchmark Lock Invariant:** AI model evaluation against the benchmark remains strictly locked.

---

## 4. Human Coordinator Action Items (Next Steps for Project Owner)

To transition from `AWAITING_REVIEWER_RECRUITMENT` to `PILOT_IN_PROGRESS`, the Project Owner must manually execute the following actions:

1. **Set Engagement Terms:** Finalize compensation, honorarium, or formal research credit/co-authorship terms in `reviewer_invitation_template.md`.
2. **Conduct Outreach:** Send invitations to qualified civil engineering departments, geology faculties, or geotechnical consulting networks.
3. **Maintain Offline Registry:** Receive CVs and screening questionnaires, storing real personal data in an offline, password-protected registry.
4. **Audit Qualifications:** Review submissions using `qualification_decision_guide.md`, verify degrees, and assign Tier 1/2/3 ratings.
5. **Populate Tracking Logs:** Record verified pseudonymous entries in `reviewer_qualification_log_template.csv` and `reviewer_assignment_template.csv`.
6. **Dispatch Blinded Packages:** Once `verify_pilot_launch_gate()` returns `True`, distribute the 10-image blinded package to Reviewer 1 and Reviewer 2 independently.
