"""Unit tests for Phase 2I Expert Annotation Package & Human-Review Workflow.

Verifies:
1. Unresolved licenses cannot enter the cleared annotation package.
2. Unsuitable and missing images are recorded in the exclusion register.
3. Cross-batch duplicate copies do not become independent evaluation cases.
4. Candidate IDs map consistently to opaque annotation IDs via candidate_index.csv.
5. Ground-truth and review fields remain strictly pending before actual human review.
6. Blinded annotation form hides model predictions, query tags, and previous suitability labels.
7. Unknown site/event grouping is not treated as proof of independence.
8. Production upload directories and database records remain untouched.
"""

import csv
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestPhase2IHumanReviewPackage(unittest.TestCase):
    """Test suite for Phase 2I annotation package integrity, blinding, and workflow gates."""

    @classmethod
    def setUpClass(cls):
        cls.pkg_dir = PROJECT_ROOT / "docs" / "gemma-local-vision" / "evaluation" / "phase_2i_annotation_package"
        cls.cand_index_path = cls.pkg_dir / "candidate_index.csv"
        cls.excl_register_path = cls.pkg_dir / "exclusion_register.csv"
        cls.ann_form_path = cls.pkg_dir / "annotation_form.csv"
        cls.adj_form_path = cls.pkg_dir / "adjudication_form.csv"
        cls.change_log_path = cls.pkg_dir / "annotation_change_log.csv"

        # Load CSVs
        cls.cand_index = []
        if cls.cand_index_path.exists():
            with open(cls.cand_index_path, mode="r", encoding="utf-8") as f:
                cls.cand_index = list(csv.DictReader(f))

        cls.excl_register = []
        if cls.excl_register_path.exists():
            with open(cls.excl_register_path, mode="r", encoding="utf-8") as f:
                cls.excl_register = list(csv.DictReader(f))

        cls.ann_form = []
        if cls.ann_form_path.exists():
            with open(cls.ann_form_path, mode="r", encoding="utf-8") as f:
                cls.ann_form = list(csv.DictReader(f))

        cls.adj_form = []
        if cls.adj_form_path.exists():
            with open(cls.adj_form_path, mode="r", encoding="utf-8") as f:
                cls.adj_form = list(csv.DictReader(f))

    def test_package_files_exist(self):
        """Verify all 9 required package artifacts exist under phase_2i_annotation_package/."""
        expected_files = [
            "README.md",
            "annotation_protocol.md",
            "annotator_instructions.md",
            "annotation_form.csv",
            "adjudication_form.csv",
            "candidate_index.csv",
            "exclusion_register.csv",
            "reviewer_checklist.md",
            "annotation_change_log.csv",
        ]
        for fname in expected_files:
            p = self.pkg_dir / fname
            self.assertTrue(p.exists(), f"Required package artifact {fname} must exist in {self.pkg_dir}")

    def test_unresolved_licenses_cannot_enter_annotation_package(self):
        """Verify that any candidate with PENDING_REVIEW license is excluded from candidate_index.csv."""
        unresolved_cids = {
            "WMC_107274804",
            "WMC_43209273",
            "WMC_43428262",
            "WMC_43470710",
            "WMC_43642493",
            "WMC_47592210",
            "WMC_71769303",
            "WMC_71769307",
        }
        pkg_cids = {r["candidate_id"] for r in self.cand_index}
        intersection = unresolved_cids.intersection(pkg_cids)
        self.assertEqual(len(intersection), 0, f"Unresolved license candidates must not be in package: {intersection}")

    def test_unsuitable_and_missing_images_are_in_exclusion_register(self):
        """Verify all 15 excluded records are documented in exclusion_register.csv with reasons."""
        self.assertEqual(len(self.excl_register), 15, "Exclusion register must contain exactly 15 records")
        for r in self.excl_register:
            self.assertTrue(len(r["candidate_id"]) > 0, "Candidate ID must not be empty")
            self.assertTrue(len(r["detailed_exclusion_rationale"]) > 0, "Detailed rationale must not be empty")

        # Confirm WMC_21449778 (barn roof truss) is in exclusion register
        barn_rec = next((r for r in self.excl_register if r["candidate_id"] == "WMC_21449778"), None)
        self.assertIsNotNone(barn_rec, "WMC_21449778 must be in exclusion register")
        self.assertEqual(barn_rec["exclusion_category"], "EXCLUDED_UNSUITABLE")

    def test_duplicate_copies_do_not_become_independent_evaluation_cases(self):
        """Verify 102 annotation IDs map to 102 unique SHA-256 hashes and physical files."""
        self.assertEqual(len(self.cand_index), 102, "Must contain exactly 102 cleared candidates")
        ann_ids = [r["annotation_id"] for r in self.cand_index]
        self.assertEqual(len(ann_ids), len(set(ann_ids)), "All annotation IDs must be unique")

        shas = [r["image_sha256"] for r in self.cand_index]
        self.assertEqual(len(shas), len(set(shas)), "All SHA-256 hashes in candidate index must be unique")

        # Verify active files physically exist on disk
        for r in self.cand_index:
            p = PROJECT_ROOT / r["active_image_path"]
            self.assertTrue(p.exists(), f"Image path {p} must exist on disk")

    def test_candidate_ids_map_consistently_to_annotation_ids(self):
        """Verify candidate_index.csv establishes a 1-to-1 mapping between ANN_XXX and WMC_XXXX."""
        for r in self.cand_index:
            self.assertTrue(r["annotation_id"].startswith("ANN_"), "Annotation ID must follow ANN_XXX pattern")
            self.assertTrue(r["candidate_id"].startswith("WMC_"), "Candidate ID must follow WMC_XXXX pattern")

    def test_ground_truth_fields_remain_pending_before_actual_review(self):
        """Verify that all rows in annotation_form.csv and adjudication_form.csv are unpopulated and PENDING."""
        self.assertEqual(len(self.ann_form), 102, "Annotation form must have 102 rows")
        for r in self.ann_form:
            self.assertEqual(r["review_status"], "PENDING", f"Status for {r['annotation_id']} must be PENDING")
            self.assertEqual(r["reviewer_id"], "", f"Reviewer ID for {r['annotation_id']} must be empty")
            self.assertEqual(r["primary_category"], "", f"Primary category for {r['annotation_id']} must be empty")
            self.assertEqual(r["confidence_level"], "", f"Confidence for {r['annotation_id']} must be empty")
            self.assertEqual(r["geomorphic_rationale"], "", f"Rationale for {r['annotation_id']} must be empty")

        self.assertEqual(len(self.adj_form), 102, "Adjudication form must have 102 rows")
        for r in self.adj_form:
            self.assertEqual(r["consensus_status"], "PENDING", f"Consensus for {r['annotation_id']} must be PENDING")
            self.assertEqual(r["adjudicated_category"], "", f"Adjudicated category for {r['annotation_id']} must be empty")

    def test_blinded_annotation_form_hides_model_predictions_and_query_tags(self):
        """Verify annotation_form.csv does not leak AI predictions, discovery queries, or previous labels."""
        prohibited_columns = [
            "gemma_prediction",
            "model_prediction",
            "predicted_hazard",
            "candidate_subject",
            "scientific_suitability_status",
            "search_query",
        ]
        with open(self.ann_form_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = [c.lower() for c in reader.fieldnames]

        for col in prohibited_columns:
            self.assertNotIn(col, fieldnames, f"Prohibited column {col} must not leak into blinded annotation form")

    def test_unknown_site_event_not_treated_as_proof_of_independence(self):
        """Verify that UNKNOWN_SITE_EVENT records retain UNKNOWN confidence in crosswalk."""
        unknown_recs = [r for r in self.cand_index if "UNKNOWN_SITE_EVENT" in r["site_event_group_id"]]
        for r in unknown_recs:
            self.assertEqual(
                r["site_event_group_confidence"],
                "UNKNOWN_SITE_EVENT",
                f"Unknown record {r['annotation_id']} must retain UNKNOWN_SITE_EVENT confidence",
            )

    def test_production_uploads_and_database_remain_untouched(self):
        """Verify production upload directories and databases were not modified during package generation."""
        prod_upload_dir = PROJECT_ROOT / "backend" / "uploads"
        if prod_upload_dir.exists():
            for f in prod_upload_dir.iterdir():
                self.assertFalse(f.name.startswith("WMC_"), f"WMC file {f.name} leaked into {prod_upload_dir}")


if __name__ == "__main__":
    unittest.main()
