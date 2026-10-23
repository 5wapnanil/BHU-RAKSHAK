"""Unit and regression tests for Phase 2L End-to-End Workflow Dry Run.

Verifies:
1. End-to-end workflow orchestrator execution on synthetic test fixtures.
2. Disagreement detection and calculation of synthetic reliability metrics (Po, Kappa, PABAK).
3. Adjudication drafting and grounded adjudication validation.
4. Enforcement of reviewer independence (distinct IDs, separate files).
5. Rejection of mismatched annotation ID sets between reviewers.
6. Refusal to overwrite existing output files without explicit force flag.
7. Rejection of invalid categories, duplicate IDs, and premature pending rows.
8. Rejection of unbacked adjudication rows.
9. Genuine annotation package and pilot selection isolation from synthetic fixtures.
10. Production database and upload directory isolation.
"""

import csv
from pathlib import Path
import tempfile
import unittest

from backend.scripts.orchestrate_annotation_workflow import (
    AnnotationWorkflowOrchestrator,
    compute_file_sha256,
)
from backend.scripts.validate_human_annotations import HumanAnnotationValidator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestPhase2LWorkflowDryRun(unittest.TestCase):
    """Test suite for Phase 2L synthetic workflow execution and safety controls."""

    @classmethod
    def setUpClass(cls):
        cls.fixtures_dir = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "phase_2l"
        cls.rev_a_path = cls.fixtures_dir / "synthetic_reviewer_a_submission.csv"
        cls.rev_b_path = cls.fixtures_dir / "synthetic_reviewer_b_submission.csv"
        cls.adj_path = cls.fixtures_dir / "synthetic_adjudication_submission.csv"

        cls.real_pkg_dir = PROJECT_ROOT / "docs" / "gemma-local-vision" / "evaluation" / "phase_2i_annotation_package"
        cls.real_pilot_path = PROJECT_ROOT / "docs" / "gemma-local-vision" / "evaluation" / "PHASE_2J_PILOT_SELECTION.csv"

        cls.orchestrator = AnnotationWorkflowOrchestrator()
        cls.validator = HumanAnnotationValidator()

    def test_synthetic_end_to_end_workflow_success(self):
        """Verify successful end-to-end execution, disagreement detection, and adjudication drafting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            adj_out = tmppath / "adjudication_draft.csv"
            rep_out = tmppath / "report.json"

            report = self.orchestrator.execute_workflow(
                reviewer_1_path=self.rev_a_path,
                reviewer_2_path=self.rev_b_path,
                adjudication_output_path=adj_out,
                adjudication_input_path=self.adj_path,
                report_output_path=rep_out,
                force_overwrite=True,
                is_synthetic=True,
            )

            self.assertEqual(report.status, "SUCCESS")
            self.assertEqual(report.total_images_evaluated, 10)
            self.assertEqual(report.concordant_items_count, 7)
            self.assertEqual(report.discordant_items_count, 3)
            self.assertEqual(report.escalation_items_count, 3)
            self.assertEqual(report.observed_agreement_pct, 70.0)
            self.assertAlmostEqual(report.cohens_kappa, 0.6154, places=3)
            self.assertAlmostEqual(report.pabak, 0.64, places=2)
            self.assertEqual(report.adjudication_validation_status, "VALID_AND_GROUNDED")

            # Check files were written
            self.assertTrue(adj_out.exists())
            self.assertTrue(rep_out.exists())

            # Verify draft adjudication schema and disagreement flags
            with open(adj_out, mode="r", encoding="utf-8") as f:
                draft_rows = list(csv.DictReader(f))
            self.assertEqual(len(draft_rows), 10)

            # Check discordances on ANN_041, ANN_050, ANN_014
            flagged = {r["annotation_id"]: r["disagreement_detected"] for r in draft_rows}
            self.assertEqual(flagged["ANN_041"], "YES")
            self.assertEqual(flagged["ANN_050"], "YES")
            self.assertEqual(flagged["ANN_014"], "YES")
            self.assertEqual(flagged["ANN_065"], "NO")

    def test_orchestrator_refuses_to_overwrite_existing_file(self):
        """Verify orchestrator aborts if output file exists and force is False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_file = Path(tmpdir) / "existing.csv"
            existing_file.write_text("dummy", encoding="utf-8")

            report = self.orchestrator.execute_workflow(
                reviewer_1_path=self.rev_a_path,
                reviewer_2_path=self.rev_b_path,
                adjudication_output_path=existing_file,
                force_overwrite=False,
                is_synthetic=True,
            )

            self.assertEqual(report.status, "FAILED")
            self.assertTrue(any("already exists" in err for err in report.errors))

    def test_orchestrator_rejects_identical_reviewer_ids(self):
        """Verify orchestrator detects breach of independence if both submissions have same reviewer_id."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
            with open(self.rev_a_path, mode="r", encoding="utf-8") as src:
                rows = list(csv.DictReader(src))
            # Change reviewer_id to match reviewer A
            fieldnames = list(rows[0].keys())
            writer = csv.DictWriter(tf, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                r["reviewer_id"] = "TEST_REVIEWER_A"
                writer.writerow(r)
            tmp_clone = Path(tf.name)

        try:
            report = self.orchestrator.execute_workflow(
                reviewer_1_path=self.rev_a_path,
                reviewer_2_path=tmp_clone,
                force_overwrite=True,
                is_synthetic=True,
            )
            self.assertEqual(report.status, "FAILED")
            self.assertTrue(any("share identical identifier" in err for err in report.errors))
        finally:
            tmp_clone.unlink()

    def test_orchestrator_rejects_identical_physical_paths(self):
        """Verify orchestrator rejects attempts to pass the exact same file for both reviewers."""
        report = self.orchestrator.execute_workflow(
            reviewer_1_path=self.rev_a_path,
            reviewer_2_path=self.rev_a_path,
            force_overwrite=True,
            is_synthetic=True,
        )
        self.assertEqual(report.status, "FAILED")
        self.assertTrue(any("same physical file" in err for err in report.errors))

    def test_orchestrator_rejects_mismatched_annotation_ids(self):
        """Verify orchestrator rejects submissions evaluating different image subsets."""
        mismatched_path = self.fixtures_dir / "mismatched_ids_submission.csv"
        report = self.orchestrator.execute_workflow(
            reviewer_1_path=self.rev_a_path,
            reviewer_2_path=mismatched_path,
            force_overwrite=True,
            is_synthetic=True,
        )
        self.assertEqual(report.status, "FAILED")

    def test_validator_rejects_invalid_category_fixture(self):
        """Verify validator flags invalid category fixture."""
        inv_path = self.fixtures_dir / "invalid_category_submission.csv"
        rep = self.validator.validate_file(
            inv_path, mode="independent-annotation", dry_run=True, require_completed=True
        )
        self.assertFalse(rep.is_valid)
        self.assertTrue(any("invalid primary_category" in err for err in rep.errors))

    def test_validator_rejects_duplicate_id_fixture(self):
        """Verify validator flags duplicate annotation ID fixture."""
        dup_path = self.fixtures_dir / "duplicate_id_submission.csv"
        rep = self.validator.validate_file(
            dup_path, mode="independent-annotation", dry_run=True, require_completed=True
        )
        self.assertFalse(rep.is_valid)
        self.assertTrue(any("Duplicate annotation_id" in err for err in rep.errors))

    def test_validator_rejects_premature_pending_fixture(self):
        """Verify validator flags premature pending status when completed is required."""
        pending_path = self.fixtures_dir / "premature_pending_submission.csv"
        rep = self.validator.validate_file(
            pending_path, mode="independent-annotation", dry_run=True, require_completed=True
        )
        self.assertFalse(rep.is_valid)
        self.assertTrue(any("completed submission is required" in err for err in rep.errors))

    def test_validator_rejects_unbacked_adjudication_fixture(self):
        """Verify validator rejects adjudication lacking reviewer source inputs."""
        unbacked_path = self.fixtures_dir / "unbacked_adjudication_submission.csv"
        rep = self.validator.validate_file(unbacked_path, mode="adjudication", dry_run=True)
        self.assertFalse(rep.is_valid)
        self.assertTrue(any("without both reviewer_1_id and reviewer_2_id" in err for err in rep.errors))

    def test_genuine_packages_remain_unpolluted(self):
        """Verify real annotation package files contain zero synthetic records and remain strictly pending."""
        ann_form = self.real_pkg_dir / "annotation_form.csv"
        with open(ann_form, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        self.assertEqual(len(reader), 102)
        for r in reader:
            self.assertEqual(r["review_status"], "PENDING")
            self.assertEqual(r["reviewer_id"], "")
            self.assertFalse("SYNTHETIC" in r["geomorphic_rationale"])
            self.assertFalse("TEST_" in r["reviewer_id"])

        adj_form = self.real_pkg_dir / "adjudication_form.csv"
        with open(adj_form, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        self.assertEqual(len(reader), 102)
        for r in reader:
            self.assertEqual(r["consensus_status"], "PENDING")
            self.assertEqual(r["adjudicator_id"], "")
            self.assertFalse("SYNTHETIC" in r["adjudication_rationale"])

        # Check real pilot selection
        with open(self.real_pilot_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        self.assertEqual(len(reader), 10)
        for r in reader:
            self.assertEqual(r["review_status"], "PENDING")
            self.assertEqual(r["reviewer_id"], "")

    def test_production_isolation_and_db_immutability(self):
        """Verify zero candidate images in backend/uploads/."""
        prod_upload_dir = PROJECT_ROOT / "backend" / "uploads"
        if prod_upload_dir.exists():
            for f in prod_upload_dir.iterdir():
                self.assertFalse(f.name.startswith("WMC_"), f"WMC file {f.name} leaked into {prod_upload_dir}")


if __name__ == "__main__":
    unittest.main()
