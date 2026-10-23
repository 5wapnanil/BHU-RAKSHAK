# PahaarPulse — Human Review Verification Checklist

**Checklist Version:** v1.0 (Phase 2F)  
**Effective Date:** 2026-10-23  
**Project:** PahaarPulse AI/ML Field-Photo Evaluation Pipeline  
**Target Submission:** Individual Review Forms (`annotation_form_R*.csv`) & Adjudication Forms (`adjudication_form.csv`)  

---

## 1. Reviewer Pre-Submission Checklist

Every reviewer must complete this verification prior to submitting their independent annotation file:

### 1.1 Candidate Integrity & Hash Alignment
- [ ] **Row Count Match:** Exactly 54 rows present, corresponding 1-to-1 with the candidate cohort.
- [ ] **Candidate ID Preservation:** Candidate IDs (`candidate_id`) match the manifest and have not been altered or re-ordered.
- [ ] **Cryptographic Hash Match:** `image_sha256` values match the manifest exactly. No hashes have been modified or truncated.
- [ ] **Annotator Attribution:** `annotator_id` is populated across all rows with the reviewer's assigned identifier (e.g., `EXPERT_GEOTECH_01`).
- [ ] **Prohibited AI Strings:** Confirmed that `annotator_id` contains NO model names, bot prefixes, or automated tags (`gemma`, `gemini`, `ai_`, `bot_`).

### 1.2 Schema & Controlled Vocabulary Compliance
- [ ] **Controlled Indicators Only:** Every entry in `observable_indicators` contains only approved taxonomy terms from `CONTROLLED_OBSERVABLE_INDICATORS`, delimited by semicolons (`;`).
- [ ] **Valid Severity Classes:** Every `reviewer_label` is strictly one of: `low`, `moderate`, `high`, `critical`, or `indeterminate`. No non-standard strings (`medium`, `severe`, `safe`, `dangerous`).
- [ ] **Valid Quality Tiers:** `image_quality` is strictly one of: `high_resolution`, `adequate`, `low_resolution`, or `occluded_or_degraded`.
- [ ] **Valid Confidence Ratings:** `confidence` is strictly one of: `certain`, `probable`, `tentative`, or `indeterminate`.
- [ ] **Review Status:** All rows have `review_status="completed"`. No rows remain in `"pending_review"`.
- [ ] **ISO Timestamp:** `reviewed_at` contains a valid ISO 8601 timestamp (e.g., `2026-10-23T14:30:00Z`).

### 1.3 Scientific & Epistemic Honesty
- [ ] **The Negative Proof Check:** Ensured that `low` hazard was NOT assigned simply because cracks were absent, if the slope crest was out of frame or occluded.
- [ ] **The Abstention Check:** Verified that all photographs with severe fog, heavy blur, or macro close-ups lacking slope context are marked `reviewer_label="indeterminate"`.
- [ ] **Indeterminate vs. Negative Control:** Ensured that `indeterminate` is used exclusively for insufficient visual evidence, whereas `negative_control` / `low` is used for clear evidence of non-hazard terrain.
- [ ] **Evidence Notes Documentation:** Descriptive notes in `evidence_notes` explain the primary geomorphic reasoning for all `high`, `critical`, and `indeterminate` decisions.

---

## 2. Adjudication & Dispute Resolution Checklist

The Senior Adjudicator must verify the following before approving final consensus records:

### 2.1 Independent Review Verification
- [ ] **Double-Blind Integrity:** Confirmed that Reviewer 1 and Reviewer 2 completed their reviews independently without prior access to each other's submissions.
- [ ] **No Discarded Reviews:** Confirmed that all original annotations from both Reviewer 1 and Reviewer 2 are preserved in `adjudication_form.csv`.
- [ ] **Disagreement Typology:** Every disagreement is categorized into one of:
  - `none` (Full agreement on class and primary indicators)
  - `severity_tier_mismatch` (e.g., R1 calls `moderate`, R2 calls `high`)
  - `indicator_mismatch` (Agreement on severity, disagreement on specific geomorphic features)
  - `indeterminate_dispute` (One reviewer assigned determinate class, other assigned `indeterminate`)
  - `exclusion_dispute` (Disagreement on whether the candidate satisfies photographic quality criteria)

### 2.2 Consensus & Escalation Protocol
- [ ] **Documented Consensus Rationale:** Detailed justification provided in `adjudication_rationale` explaining why the final label was chosen.
- [ ] **Escalation Tracking:** If consensus cannot be reached with high scientific confidence, `escalation_required="yes"` is flagged and the candidate is routed to `adjudication_status="escalated"` or `adjudication_status="excluded"`.
- [ ] **Zero Fabricated Consensus:** No coin-toss or automatic averaging between classes. Decisions must be grounded in physical geomorphic evidence.
