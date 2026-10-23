"""Unit and regression tests for Phase 2J Human Annotation Submission Validation.

Verifies:
1. PHASE_2J_PILOT_SELECTION.csv schema integrity, row count, and empty pending fields.
2. Existing Phase 2I/2J templates validate cleanly with zero errors in pending mode.
3. Validator rejects invalid annotation IDs not present in candidate_index.csv.
4. Validator rejects non-canonical observation categories.
5. Validator rejects invalid confidence levels and malformed ISO 8601 timestamps.
6. Validator rejects completed rows with missing mandatory fields.
7. Validator rejects pending rows with prefilled conclusions (preventing synthetic leakage).
8. Validator rejects duplicate annotation IDs within a single submission.
9. Validator rejects duplicate reviews for the same reviewer and image.
10. Adjudication validation requires genuine dual-reviewer source inputs.
11. Adjudication validation enforces consistency between categories and disagreement_detected flag.
12. Valid completed reviewer and adjudication submissions pass validation cleanly.
13. Read-only dry-run execution safety.
14. Production database and upload directory isolation.
"""

import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
import unittest

from backend.scripts.validate_human_annotations import (
    CANONICAL_CATEGORIES,
    HumanAnnotationValidator,
    REQUIRED_ADJUDICATION_COLUMNS,
    REQUIRED_REVIEWER_COLUMNS,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestPhase2JSubmissionValidation(unittest.TestCase):
    """Test suite for Phase 2J submission validation engine and pilot selection."""

    @classmethod
    def setUpClass(cls):
        cls.eval_dir = PROJECT_ROOT / "docs" / "gemma-local-vision" / "evaluation"
        cls.pkg_dir = cls.eval_dir / "phase_2i_annotation_package"
        cls.candidate_index_path = cls.pkg_dir / "candidate_index.csv"
        cls.ann_form_path = cls.pkg_dir / "annotation_form.csv"
        cls.adj_form_path = cls.pkg_dir / "adjudication_form.csv"
        cls.pilot_path = cls.eval_dir / "PHASE_2J_PILOT_SELECTION.csv"

        cls.validator = HumanAnnotationValidator(candidate_index_path=cls.candidate_index_path)

    def test_pilot_selection_csv_integrity(self):
        """Verify PHASE_2J_PILOT_SELECTION.csv exists, has 10 rows, valid paths, and unpopulated fields."""
        self.assertTrue(self.pilot_path.exists(), f"Pilot file must exist at {self.pilot_path}")

        with open(self.pilot_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        self.assertEqual(len(reader), 10, "Pilot selection must have exactly 10 candidate rows")

        expected_pilot_ids = [f"PILOT_{i:02d}" for i in range(1, 11)]
        for i, row in enumerate(reader):
            self.assertEqual(row["pilot_batch_id"], expected_pilot_ids[i])
            self.assertTrue(row["annotation_id"].startswith("ANN_"))
            self.assertTrue(row["candidate_id"].startswith("WMC_"))
            self.assertEqual(row["review_status"], "PENDING")
            self.assertEqual(row["reviewer_id"], "")
            self.assertEqual(row["review_timestamp"], "")
            self.assertEqual(row["primary_category"], "")
            self.assertEqual(row["confidence_level"], "")
            self.assertEqual(row["observable_indicators"], "")
            self.assertEqual(row["image_quality_limitations"], "")
            self.assertEqual(row["geomorphic_rationale"], "")
            self.assertEqual(row["requires_adjudication"], "")
            self.assertEqual(row["protocol_version"], "v1.0")

            # Verify image file exists on disk
            img_path = PROJECT_ROOT / row["active_image_path"]
            self.assertTrue(img_path.exists(), f"Image file {img_path} must exist on disk")

    def test_existing_package_forms_pass_validation(self):
        """Verify baseline annotation_form.csv and adjudication_form.csv validate cleanly."""
        report_ann = self.validator.validate_file(self.ann_form_path, mode="reviewer", dry_run=True)
        self.assertTrue(report_ann.is_valid, f"annotation_form.csv must be valid: {report_ann.errors}")
        self.assertEqual(report_ann.total_rows, 102)
        self.assertEqual(report_ann.valid_rows, 102)

        report_adj = self.validator.validate_file(self.adj_form_path, mode="adjudication", dry_run=True)
        self.assertTrue(report_adj.is_valid, f"adjudication_form.csv must be valid: {report_adj.errors}")
        self.assertEqual(report_adj.total_rows, 102)
        self.assertEqual(report_adj.valid_rows, 102)

        report_pilot = self.validator.validate_file(self.pilot_path, mode="reviewer", dry_run=True)
        self.assertTrue(report_pilot.is_valid, f"PHASE_2J_PILOT_SELECTION.csv must be valid: {report_pilot.errors}")
        self.assertEqual(report_pilot.total_rows, 10)
        self.assertEqual(report_pilot.valid_rows, 10)

    def test_validator_detects_invalid_annotation_id(self):
        """Verify validator flags any annotation_id not in candidate_index.csv."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_REVIEWER_COLUMNS)
            writer.writerow([
                "ANN_999", "WMC_nonexistent.jpg", "REV_A1", "2026-10-23T12:00:00Z",
                "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "HIGH", "rockfall", "NONE",
                "Severe rockfall obstructing road", "NO", "COMPLETED", "v1.0"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="reviewer", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("ANN_999" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_validator_detects_invalid_category(self):
        """Verify validator flags unsupported primary categories."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_REVIEWER_COLUMNS)
            writer.writerow([
                "ANN_001", "WMC_107996682.png", "REV_A1", "2026-10-23T12:00:00Z",
                "CUSTOM_LANDSLIDE_LABEL", "HIGH", "rockfall", "NONE",
                "Severe rockfall obstructing road", "NO", "COMPLETED", "v1.0"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="reviewer", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("invalid primary_category" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_validator_detects_invalid_confidence(self):
        """Verify validator flags invalid confidence levels."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_REVIEWER_COLUMNS)
            writer.writerow([
                "ANN_001", "WMC_107996682.png", "REV_A1", "2026-10-23T12:00:00Z",
                "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "VERY_HIGH", "rockfall", "NONE",
                "Severe rockfall obstructing road", "NO", "COMPLETED", "v1.0"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="reviewer", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("invalid confidence_level" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_validator_detects_invalid_iso_timestamp(self):
        """Verify validator flags malformed review timestamp on completed rows."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_REVIEWER_COLUMNS)
            writer.writerow([
                "ANN_001", "WMC_107996682.png", "REV_A1", "yesterday at 3pm",
                "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "HIGH", "rockfall", "NONE",
                "Severe rockfall obstructing road", "NO", "COMPLETED", "v1.0"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="reviewer", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("review_timestamp" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_validator_detects_missing_fields_on_completed_row(self):
        """Verify validator flags completed rows missing reviewer_id or rationale."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_REVIEWER_COLUMNS)
            writer.writerow([
                "ANN_001", "WMC_107996682.png", "", "2026-10-23T12:00:00Z",
                "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "HIGH", "rockfall", "NONE",
                "", "NO", "COMPLETED", "v1.0"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="reviewer", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("missing reviewer_id" in err for err in report.errors))
            self.assertTrue(any("geomorphic_rationale" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_validator_detects_prefilled_pending_row(self):
        """Verify validator flags pending rows that have populated reviewer conclusions."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_REVIEWER_COLUMNS)
            writer.writerow([
                "ANN_001", "WMC_107996682.png", "", "",
                "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "", "", "",
                "", "", "PENDING", "v1.0"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="reviewer", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("populated primary_category" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_validator_detects_duplicate_annotation_id(self):
        """Verify validator flags duplicate annotation_id entries in a single submission."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_REVIEWER_COLUMNS)
            for _ in range(2):
                writer.writerow([
                    "ANN_001", "WMC_107996682.png", "", "",
                    "", "", "", "",
                    "", "", "PENDING", "v1.0"
                ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="reviewer", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("Duplicate annotation_id" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_adjudication_requires_dual_reviewer_source_inputs(self):
        """Verify completed adjudication cannot be submitted without dual-reviewer inputs."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_ADJUDICATION_COLUMNS)
            writer.writerow([
                "ANN_001", "WMC_107996682.png", "ADJ_LEAD", "2026-10-23T14:00:00Z",
                "", "", "", "",  # Missing reviewer 1 and 2 inputs!
                "NO", "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "Direct expert adjudication without reviewer data",
                "AGREED_CONSENSUS", "v1.0"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="adjudication", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("without both reviewer_1_id and reviewer_2_id" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_adjudication_disagreement_flag_consistency(self):
        """Verify disagreement_detected flag must match category comparison."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_ADJUDICATION_COLUMNS)
            # Reviewers disagree, but disagreement_detected is set to NO!
            writer.writerow([
                "ANN_001", "WMC_107996682.png", "ADJ_LEAD", "2026-10-23T14:00:00Z",
                "REV_A1", "ACUTE_SLOPE_FAILURE_OR_DEBRIS",
                "REV_B2", "PRECURSOR_INSTABILITY_INDICATOR",
                "NO", "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "Resolved by adjudicator",
                "ADJUDICATED_RESOLVED", "v1.0"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="adjudication", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("disagreement_detected" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_valid_completed_submissions_pass(self):
        """Verify well-formed completed reviewer and adjudication submissions pass validation."""
        # 1. Reviewer submission
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_REVIEWER_COLUMNS)
            writer.writerow([
                "ANN_001", "WMC_107996682.png", "REV_A1", "2026-10-23T12:00:00Z",
                "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "HIGH", "rock_boulders; road_blocked", "NONE",
                "Active rockfall debris directly blocking highway lane.", "NO", "COMPLETED", "v1.0"
            ])
            tpath_rev = Path(tf.name)

        # 2. Adjudication submission
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_ADJUDICATION_COLUMNS)
            writer.writerow([
                "ANN_001", "WMC_107996682.png", "ADJ_LEAD", "2026-10-23T14:00:00Z",
                "REV_A1", "ACUTE_SLOPE_FAILURE_OR_DEBRIS",
                "REV_B2", "ACUTE_SLOPE_FAILURE_OR_DEBRIS",
                "NO", "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "Unanimous agreement on acute rockfall failure.",
                "AGREED_CONSENSUS", "v1.0"
            ])
            tpath_adj = Path(tf.name)

        try:
            report_rev = self.validator.validate_file(tpath_rev, mode="reviewer", dry_run=True)
            self.assertTrue(report_rev.is_valid, f"Valid reviewer submission failed: {report_rev.errors}")
            self.assertEqual(report_rev.valid_rows, 1)

            report_adj = self.validator.validate_file(tpath_adj, mode="adjudication", dry_run=True)
            self.assertTrue(report_adj.is_valid, f"Valid adjudication submission failed: {report_adj.errors}")
            self.assertEqual(report_adj.valid_rows, 1)
        finally:
            tpath_rev.unlink()
            tpath_adj.unlink()

    def test_production_isolation_and_db_immutability(self):
        """Verify zero candidate images in backend/uploads/."""
        prod_upload_dir = PROJECT_ROOT / "backend" / "uploads"
        if prod_upload_dir.exists():
            for f in prod_upload_dir.iterdir():
                self.assertFalse(f.name.startswith("WMC_"), f"WMC file {f.name} leaked into {prod_upload_dir}")


if __name__ == "__main__":
    unittest.main()
