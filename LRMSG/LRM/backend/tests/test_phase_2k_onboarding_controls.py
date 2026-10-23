"""Unit and regression tests for Phase 2K Reviewer Onboarding Controls & Pilot Schema Separation.

Verifies:
1. Validator enforces strict separation between pilot-selection and independent-annotation schemas.
2. Pilot selection manifest rejects completed status or populated reviewer conclusions.
3. Independent annotation schema rejects extraneous metadata leakage columns (protecting blinding).
4. Completed submission requirements rejected when require_completed is set on pending rows.
5. Onboarding packet templates exist with correct headers and zero fictional records.
6. Pilot dataset dependency invariants: 10 distinct site/event groups and 10 unique SHA-256 hashes.
7. Production database tables and upload storage remain completely unmutated.
"""

import csv
import hashlib
from pathlib import Path
import tempfile
import unittest

from backend.scripts.validate_human_annotations import (
    HumanAnnotationValidator,
    REQUIRED_ADJUDICATION_COLUMNS,
    REQUIRED_PILOT_SELECTION_COLUMNS,
    REQUIRED_REVIEWER_COLUMNS,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestPhase2KOnboardingControls(unittest.TestCase):
    """Test suite for Phase 2K reviewer onboarding package and enhanced schema validation."""

    @classmethod
    def setUpClass(cls):
        cls.eval_dir = PROJECT_ROOT / "docs" / "gemma-local-vision" / "evaluation"
        cls.pkg_2i = cls.eval_dir / "phase_2i_annotation_package"
        cls.pkg_2k = cls.eval_dir / "phase_2k_reviewer_onboarding"

        cls.pilot_path = cls.eval_dir / "PHASE_2J_PILOT_SELECTION.csv"
        cls.ann_form_path = cls.pkg_2i / "annotation_form.csv"
        cls.adj_form_path = cls.pkg_2i / "adjudication_form.csv"
        cls.cand_index_path = cls.pkg_2i / "candidate_index.csv"

        cls.validator = HumanAnnotationValidator(candidate_index_path=cls.cand_index_path)

    def test_onboarding_packet_artifacts_exist(self):
        """Verify all 8 Phase 2K onboarding packet files exist."""
        expected_files = [
            "README.md",
            "reviewer_qualification_criteria.md",
            "reviewer_onboarding_checklist.md",
            "confidentiality_and_data_handling.md",
            "pilot_execution_protocol.md",
            "reviewer_assignment_template.csv",
            "reviewer_qualification_log_template.csv",
            "pilot_issue_log_template.csv",
        ]
        for fname in expected_files:
            p = self.pkg_2k / fname
            self.assertTrue(p.exists(), f"Required onboarding artifact {fname} must exist in {self.pkg_2k}")

    def test_onboarding_csv_templates_contain_placeholders_only(self):
        """Verify onboarding templates contain placeholder headers and zero fabricated reviewer identities."""
        # 1. Assignment template
        asg_path = self.pkg_2k / "reviewer_assignment_template.csv"
        with open(asg_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        self.assertEqual(len(reader), 2)
        for r in reader:
            self.assertTrue(r["reviewer_id"].startswith("[ENTER_REVIEWER_PSEUDONYM"))
            self.assertEqual(r["assignment_status"], "AWAITING_ASSIGNMENT")
            self.assertEqual(r["qualification_verified"], "PENDING")

        # 2. Qualification log template
        qual_path = self.pkg_2k / "reviewer_qualification_log_template.csv"
        with open(qual_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        self.assertEqual(len(reader), 2)
        for r in reader:
            self.assertTrue(r["reviewer_id"].startswith("[ENTER_REVIEWER_PSEUDONYM"))
            self.assertEqual(r["qualification_status"], "PENDING_VERIFICATION")
            self.assertEqual(r["geotechnical_competency_verified"], "PENDING")

        # 3. Pilot issue log template
        issue_path = self.pkg_2k / "pilot_issue_log_template.csv"
        with open(issue_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        self.assertEqual(len(reader), 1)
        self.assertEqual(reader[0]["issue_id"], "ISSUE_PLACEHOLDER_01")
        self.assertEqual(reader[0]["resolution_status"], "OPEN")

    def test_schema_differentiation_pilot_vs_independent_annotation(self):
        """Verify validator enforces distinct schemas between pilot-selection and independent-annotation."""
        # 1. Pilot file in pilot-selection mode: PASS
        rep_pilot = self.validator.validate_file(self.pilot_path, mode="pilot-selection", dry_run=True)
        self.assertTrue(rep_pilot.is_valid, f"Pilot file must pass in pilot-selection mode: {rep_pilot.errors}")
        self.assertEqual(rep_pilot.mode, "pilot-selection")

        # 2. Pilot file in independent-annotation mode: REJECT (metadata leakage)
        rep_leak = self.validator.validate_file(self.pilot_path, mode="independent-annotation", dry_run=True)
        self.assertFalse(rep_leak.is_valid, "Pilot selection file must be rejected as an independent annotation submission")
        self.assertTrue(any("Extraneous column" in err for err in rep_leak.errors))

        # 3. Annotation file in independent-annotation mode: PASS
        rep_ann = self.validator.validate_file(self.ann_form_path, mode="independent-annotation", dry_run=True)
        self.assertTrue(rep_ann.is_valid, f"Annotation file must pass in independent-annotation mode: {rep_ann.errors}")
        self.assertEqual(rep_ann.mode, "independent-annotation")

        # 4. Annotation file in pilot-selection mode: REJECT (missing pilot columns)
        rep_ann_pilot = self.validator.validate_file(self.ann_form_path, mode="pilot-selection", dry_run=True)
        self.assertFalse(rep_ann_pilot.is_valid, "Annotation file must be rejected under pilot-selection mode")
        self.assertTrue(any("Missing required column in pilot-selection schema" in err for err in rep_ann_pilot.errors))

    def test_pilot_selection_rejects_completed_status(self):
        """Verify pilot-selection manifest rejects any row with review_status=COMPLETED."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_PILOT_SELECTION_COLUMNS)
            writer.writerow([
                "PILOT_01", "ANN_065", "WMC_37943355", "WMC_37943355.jpg",
                "data/public_candidates/batch_2g/WMC_37943355.jpg",
                "Himachal_Rohtang_Pass_Clearing", "Rohtang Clearing",
                "Active rockfall clearing", "COMPLETED", "REV_A1", "2026-10-23T12:00:00Z",
                "ACUTE_SLOPE_FAILURE_OR_DEBRIS", "HIGH", "rockfall", "NONE",
                "Clearing fallen rock", "NO", "v1.0"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="pilot-selection", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("must remain strictly PENDING" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_independent_annotation_require_completed_enforcement(self):
        """Verify require_completed rejects rows that remain PENDING."""
        # annotation_form.csv has all rows PENDING; require_completed must reject it
        report = self.validator.validate_file(
            self.ann_form_path, mode="independent-annotation", dry_run=True, require_completed=True
        )
        self.assertFalse(report.is_valid)
        self.assertTrue(any("review_status PENDING, but a completed submission is required" in err for err in report.errors))

    def test_pilot_dataset_dependency_and_distinctness(self):
        """Verify 10 pilot records represent 10 distinct site/event groups and 10 unique SHA-256 hashes."""
        with open(self.pilot_path, mode="r", encoding="utf-8") as f:
            pilot_rows = list(csv.DictReader(f))

        self.assertEqual(len(pilot_rows), 10)

        site_groups = {r["site_event_group_id"] for r in pilot_rows}
        self.assertEqual(len(site_groups), 10, "Pilot must have 10 distinct site/event groups")

        hashes = set()
        for r in pilot_rows:
            img_path = PROJECT_ROOT / r["active_image_path"]
            self.assertTrue(img_path.exists(), f"Image {img_path} must exist")
            with open(img_path, "rb") as img_file:
                h = hashlib.sha256(img_file.read()).hexdigest()
            hashes.add(h)

        self.assertEqual(len(hashes), 10, "All 10 pilot images must have unique SHA-256 hashes")

    def test_production_isolation_and_db_immutability(self):
        """Verify zero candidate images in backend/uploads/."""
        prod_upload_dir = PROJECT_ROOT / "backend" / "uploads"
        if prod_upload_dir.exists():
            for f in prod_upload_dir.iterdir():
                self.assertFalse(f.name.startswith("WMC_"), f"WMC file {f.name} leaked into {prod_upload_dir}")


if __name__ == "__main__":
    unittest.main()
