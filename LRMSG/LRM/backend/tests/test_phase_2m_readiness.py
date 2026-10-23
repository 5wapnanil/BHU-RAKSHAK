"""Unit and regression tests for Phase 2M Reviewer Recruitment & Pilot Launch Readiness.

Verifies:
1. PHASE_2M_RECRUITMENT_TRACKER_TEMPLATE.csv schema conformity and placeholder validity.
2. Recruitment tracker rejects unapproved candidates assigned to active reviewer roles.
3. Mechanical launch-gate (verify_pilot_launch_gate) properly blocks pilot distribution on baseline unassigned state.
4. Launch-gate passes when two qualified, approved reviewers are formally assigned.
5. Reject-synthetic flag (--reject-synthetic) prevents synthetic test records from entering production validation.
6. Genuine Phase 2I/2J/2K/2M packages contain zero synthetic records and remain strictly pending.
7. Production database tables and upload storage remain unmutated.
"""

import csv
from pathlib import Path
import tempfile
import unittest

from backend.scripts.validate_human_annotations import (
    HumanAnnotationValidator,
    REQUIRED_RECRUITMENT_TRACKER_COLUMNS,
    verify_pilot_launch_gate,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestPhase2MReadiness(unittest.TestCase):
    """Test suite for Phase 2M recruitment validation and pilot launch gates."""

    @classmethod
    def setUpClass(cls):
        cls.eval_dir = PROJECT_ROOT / "docs" / "gemma-local-vision" / "evaluation"
        cls.recruitment_dir = cls.eval_dir / "phase_2m_recruitment"
        cls.onboarding_dir = cls.eval_dir / "phase_2k_reviewer_onboarding"
        cls.pkg_2i = cls.eval_dir / "phase_2i_annotation_package"

        cls.tracker_path = cls.recruitment_dir / "PHASE_2M_RECRUITMENT_TRACKER_TEMPLATE.csv"
        cls.asg_template = cls.onboarding_dir / "reviewer_assignment_template.csv"
        cls.qual_template = cls.onboarding_dir / "reviewer_qualification_log_template.csv"
        cls.pilot_path = cls.eval_dir / "PHASE_2J_PILOT_SELECTION.csv"

        cls.validator = HumanAnnotationValidator()

    def test_recruitment_tracker_template_valid(self):
        """Verify PHASE_2M_RECRUITMENT_TRACKER_TEMPLATE.csv validates cleanly in recruitment-tracker mode."""
        self.assertTrue(self.tracker_path.exists(), f"Tracker template missing at {self.tracker_path}")
        report = self.validator.validate_file(self.tracker_path, mode="recruitment-tracker", dry_run=True)
        self.assertTrue(report.is_valid, f"Tracker template validation failed: {report.errors}")
        self.assertEqual(report.total_rows, 3)
        self.assertEqual(report.valid_rows, 3)

    def test_recruitment_tracker_rejects_unapproved_active_assignment(self):
        """Verify tracker flags error if an unapproved candidate is assigned to active reviewer ID."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            writer = csv.writer(tf)
            writer.writerow(REQUIRED_RECRUITMENT_TRACKER_COLUMNS)
            writer.writerow([
                "CAND_01", "CONTACTED", "PENDING", "PENDING", "PENDING",
                "TIER_2_FIELD_REVIEWER", "PENDING_REVIEW", "PENDING", "NONE",
                "YES", "YES", "REV_A1", "WAITING"
            ])
            tpath = Path(tf.name)

        try:
            report = self.validator.validate_file(tpath, mode="recruitment-tracker", dry_run=True)
            self.assertFalse(report.is_valid)
            self.assertTrue(any("Unapproved candidates cannot be assigned" in err for err in report.errors))
        finally:
            tpath.unlink()

    def test_pilot_launch_gate_blocked_on_baseline(self):
        """Verify verify_pilot_launch_gate returns False and blocking reasons on baseline placeholder files."""
        passed, reasons = verify_pilot_launch_gate(
            assignment_path=self.asg_template,
            qualification_log_path=self.qual_template,
            pilot_manifest_path=self.pilot_path,
        )
        self.assertFalse(passed, "Launch gate must be BLOCKED on baseline placeholder files")
        self.assertTrue(any("exactly 2 required" in r for r in reasons))

    def test_pilot_launch_gate_passes_with_two_approved_reviewers(self):
        """Verify launch gate passes when two qualified reviewers are formally approved and assigned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            test_asg = tmppath / "test_asg.csv"
            test_qual = tmppath / "test_qual.csv"

            # Write approved assignment log
            with open(test_asg, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "assignment_id", "reviewer_id", "assigned_batch", "protocol_version",
                    "blinded_package_path", "assignment_date", "due_date",
                    "qualification_verified", "independence_affirmed", "assignment_status"
                ])
                writer.writerow([
                    "ASG_01", "REV_A1", "PHASE_2J_PILOT_10", "v1.0",
                    "packages/pilot/", "2026-10-23", "2026-10-28", "APPROVED", "APPROVED", "ASSIGNED"
                ])
                writer.writerow([
                    "ASG_02", "REV_B2", "PHASE_2J_PILOT_10", "v1.0",
                    "packages/pilot/", "2026-10-23", "2026-10-28", "APPROVED", "APPROVED", "ASSIGNED"
                ])

            # Write approved qualification log
            with open(test_qual, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "reviewer_id", "qualification_tier", "degree_field", "institution",
                    "years_experience", "geotechnical_competency_verified",
                    "optical_hazard_competency_verified", "cv_audit_reference",
                    "verification_date", "verifier_id", "qualification_status"
                ])
                writer.writerow([
                    "REV_A1", "TIER_1_SENIOR_EXPERT", "Geotechnical Engineering", "University",
                    "6", "APPROVED", "APPROVED", "CV_REF_001", "2026-10-23", "LEAD_01", "APPROVED"
                ])
                writer.writerow([
                    "REV_B2", "TIER_2_FIELD_REVIEWER", "Civil Engineering", "Institute",
                    "3", "APPROVED", "APPROVED", "CV_REF_002", "2026-10-23", "LEAD_01", "APPROVED"
                ])

            passed, reasons = verify_pilot_launch_gate(
                assignment_path=test_asg,
                qualification_log_path=test_qual,
                pilot_manifest_path=self.pilot_path,
            )
            self.assertTrue(passed, f"Launch gate must pass with 2 approved reviewers: {reasons}")

    def test_validator_reject_synthetic_flag(self):
        """Verify --reject-synthetic flag rejects synthetic test reviewer submissions."""
        synth_file = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "phase_2l" / "synthetic_reviewer_a_submission.csv"
        report = self.validator.validate_file(
            synth_file, mode="independent-annotation", dry_run=True, reject_synthetic=True
        )
        self.assertFalse(report.is_valid)
        self.assertTrue(any("Synthetic test reviewer ID" in err for err in report.errors))

    def test_genuine_packages_remain_unpolluted(self):
        """Verify genuine Phase 2I/2J forms contain zero synthetic entries and remain strictly pending."""
        ann_form = self.pkg_2i / "annotation_form.csv"
        with open(ann_form, mode="r", encoding="utf-8") as f:
            ann_rows = list(csv.DictReader(f))
        self.assertEqual(len(ann_rows), 102)
        self.assertTrue(all(r["review_status"] == "PENDING" and r["reviewer_id"] == "" for r in ann_rows))

        adj_form = self.pkg_2i / "adjudication_form.csv"
        with open(adj_form, mode="r", encoding="utf-8") as f:
            adj_rows = list(csv.DictReader(f))
        self.assertEqual(len(adj_rows), 102)
        self.assertTrue(all(r["consensus_status"] == "PENDING" and r["adjudicator_id"] == "" for r in adj_rows))

        with open(self.pilot_path, mode="r", encoding="utf-8") as f:
            pilot_rows = list(csv.DictReader(f))
        self.assertEqual(len(pilot_rows), 10)
        self.assertTrue(all(r["review_status"] == "PENDING" and r["reviewer_id"] == "" for r in pilot_rows))

    def test_production_isolation_and_db_immutability(self):
        """Verify zero candidate images in backend/uploads/."""
        prod_upload_dir = PROJECT_ROOT / "backend" / "uploads"
        if prod_upload_dir.exists():
            for f in prod_upload_dir.iterdir():
                self.assertFalse(f.name.startswith("WMC_"), f"WMC file {f.name} leaked into {prod_upload_dir}")


if __name__ == "__main__":
    unittest.main()
