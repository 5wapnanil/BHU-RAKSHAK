# PahaarPulse — Phase 2L: Synthetic Test Fixtures

**Status:** `SYNTHETIC_TEST_DATA` ONLY — NOT SCIENTIFIC GROUND TRUTH  
**Project:** PahaarPulse AI/ML Landslide Risk Management System  
**Directory:** `backend/tests/fixtures/phase_2l/`  

---

## 1. Strict Isolation Warning

> [!CAUTION]
> **SYNTHETIC TEST FIXTURES ONLY:**  
> All records, annotations, rationales, and adjudication decisions in this directory were generated purely as **synthetic software test fixtures** to verify the end-to-end execution of the human evaluation pipeline.
>
> - **Zero Genuine Expert Reviews:** None of these rows reflect real human annotations.
> - **Zero Real Reviewer Identities:** Identifiers (`TEST_REVIEWER_A`, `TEST_REVIEWER_B`, `TEST_ADJUDICATOR`) are simulated test stubs.
> - **Zero Scientific Benchmark Authority:** These files must **never** be used as ground-truth labels, imported into production benchmark manifests, or used to score AI vision models.
> - **Benchmark Gate Invariant:** Model inference against the benchmark remains strictly **BLOCKED**.

---

## 2. Fixture Inventory & Test Coverage

| Fixture Filename | Mode / Schema | Description & Test Purpose |
| :--- | :--- | :--- |
| `synthetic_pilot_selection.csv` | `pilot-selection` | 10-row synthetic pilot manifest testing schema conformity and pending status. |
| `synthetic_reviewer_a_submission.csv` | `independent-annotation` | 10-row completed submission from `TEST_REVIEWER_A` with 7 agreement cases and 3 disagreement cases. |
| `synthetic_reviewer_b_submission.csv` | `independent-annotation` | 10-row completed submission from `TEST_REVIEWER_B` paired with Reviewer A. |
| `synthetic_adjudication_submission.csv` | `adjudication` | 10-row completed adjudication from `TEST_ADJUDICATOR` resolving the 3 disagreements and validating dual-reviewer source inputs. |
| `invalid_category_submission.csv` | `independent-annotation` | Negative test fixture with an uncanonical category tag. |
| `duplicate_id_submission.csv` | `independent-annotation` | Negative test fixture containing duplicate `annotation_id` rows. |
| `mismatched_ids_submission.csv` | `independent-annotation` | Negative test fixture with non-matching `annotation_id` set. |
| `unbacked_adjudication_submission.csv` | `adjudication` | Negative test fixture attempting adjudication without source reviewer entries. |
| `premature_pending_submission.csv` | `independent-annotation` | Negative test fixture with `review_status = PENDING` tested against completion enforcement. |
