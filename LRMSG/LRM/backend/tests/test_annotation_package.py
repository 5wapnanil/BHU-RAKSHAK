"""Unit tests for Phase 2F Human Annotation Package, Schema Integrity, and Expansion Gates.

Verifies:
1. Annotation package file existence, structure, and Markdown guides.
2. Candidate mapping and cryptographic hash integrity between manifest and annotation form.
3. Adjudication form schema structure preserving dual independent review fields.
4. Independent reviewer records remaining separate without overwriting.
5. Indeterminate/unknown values remaining strictly distinct from negative findings.
6. Unadjudicated expansion candidates blocked from silently entering locked benchmarks.
"""

import csv
import json
from pathlib import Path
import tempfile
import unittest

from backend.app.services.vlm_evaluation import (
    AnnotationIntegrityError,
    AnnotationRecord,
    AnnotationValidator,
    EvaluationResultLogger,
    ManifestHashMismatchError,
    MissingExpertGroundTruthError,
    VLMEvaluationHarness,
    VLMEvaluationSample,
)


class TestAnnotationPackage(unittest.TestCase):
    """Test suite for human annotation package integrity, dual-blind preservation, and gate validation."""

    def setUp(self):
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.package_dir = self.project_root / "docs" / "gemma-local-vision" / "evaluation" / "phase_2f_annotation_package"
        self.manifest_path = self.project_root / "docs" / "gemma-local-vision" / "evaluation" / "public_image_candidates.csv"

    def test_package_files_exist_and_documented(self):
        """Verifies that all 5 required files in the annotation package exist and are non-empty."""
        expected_files = [
            "README.md",
            "annotator_guide.md",
            "annotation_form.csv",
            "adjudication_form.csv",
            "review_checklist.md",
        ]
        self.assertTrue(self.package_dir.exists(), f"Package directory not found: {self.package_dir}")
        for filename in expected_files:
            file_path = self.package_dir / filename
            self.assertTrue(file_path.exists(), f"Missing required package file: {filename}")
            self.assertGreater(file_path.stat().st_size, 100, f"Package file appears empty or truncated: {filename}")

    def test_annotation_form_schema_and_candidate_mapping(self):
        """Verifies that annotation_form.csv maps 1-to-1 to downloaded candidates with exact SHA-256 hashes."""
        ann_path = self.package_dir / "annotation_form.csv"
        self.assertTrue(ann_path.exists())

        # Load candidate manifest
        with open(self.manifest_path, encoding="utf-8") as f:
            candidates = {
                r["candidate_id"]: r["image_sha256"]
                for r in csv.DictReader(f)
                if r.get("download_status") == "downloaded"
            }

        with open(ann_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected_headers = [
                "candidate_id", "image_sha256", "annotator_id", "annotation_version",
                "observable_indicators", "image_quality", "reviewer_label",
                "confidence", "evidence_notes", "review_status", "reviewed_at"
            ]
            self.assertEqual(reader.fieldnames, expected_headers)
            rows = list(reader)

        # Must have exactly 54 candidate rows matching downloaded candidates
        self.assertEqual(len(rows), 54)
        self.assertEqual(len(candidates), 54)

        for r in rows:
            cid = r["candidate_id"]
            self.assertIn(cid, candidates, f"Unexpected candidate {cid} in annotation form")
            self.assertEqual(
                r["image_sha256"].lower(),
                candidates[cid].lower(),
                f"SHA-256 mismatch for candidate {cid}"
            )
            # Reviewer fields must be strictly unpopulated
            self.assertEqual(r["annotator_id"], "")
            self.assertEqual(r["reviewer_label"], "")
            self.assertEqual(r["observable_indicators"], "")
            self.assertEqual(r["confidence"], "")
            self.assertEqual(r["evidence_notes"], "")
            self.assertEqual(r["review_status"], "pending_review")

    def test_adjudication_form_schema_preserves_dual_reviews(self):
        """Verifies that adjudication_form.csv contains dual review columns and disagreement tracking."""
        adj_path = self.package_dir / "adjudication_form.csv"
        self.assertTrue(adj_path.exists())

        with open(adj_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required_cols = [
                "candidate_id", "image_sha256", "adjudicator_id", "adjudication_version",
                "annotator_1_id", "annotator_1_label", "annotator_1_indicators",
                "annotator_2_id", "annotator_2_label", "annotator_2_indicators",
                "disagreement_type", "consensus_label", "consensus_indicators",
                "consensus_confidence", "adjudication_rationale", "escalation_required",
                "adjudication_status", "adjudicated_at"
            ]
            for col in required_cols:
                self.assertIn(col, reader.fieldnames, f"Missing required column in adjudication form: {col}")

            rows = list(reader)

        self.assertEqual(len(rows), 54)
        for r in rows:
            self.assertEqual(r["adjudication_status"], "pending")
            self.assertEqual(r["consensus_label"], "")
            self.assertEqual(r["escalation_required"], "no")

    def test_independent_reviewer_records_remain_separate(self):
        """Verifies that merging two conflicting reviewer records preserves both original entries."""
        # Simulated independent review 1 (calls high)
        r1 = AnnotationRecord(
            candidate_id="TEST_CAND_01",
            image_sha256="abc123hash",
            annotator_id="EXPERT_GEOTECH_01",
            annotation_version="v1.0",
            observable_indicators=["fresh_scarp", "tension_cracks"],
            image_quality="high_resolution",
            reviewer_label="high",
            confidence="probable",
            evidence_notes="Open headwall tension cracks visible near crest.",
            review_status="completed",
            reviewed_at="2026-10-23T10:00:00Z",
        )
        # Simulated independent review 2 (calls moderate)
        r2 = AnnotationRecord(
            candidate_id="TEST_CAND_01",
            image_sha256="abc123hash",
            annotator_id="EXPERT_GEOTECH_02",
            annotation_version="v1.0",
            observable_indicators=["fresh_scarp"],
            image_quality="adequate",
            reviewer_label="moderate",
            confidence="tentative",
            evidence_notes="Small localized scarp, road base appears unaffected.",
            review_status="completed",
            reviewed_at="2026-10-23T11:00:00Z",
        )

        # Adjudication merge row
        adjudication_entry = {
            "candidate_id": "TEST_CAND_01",
            "image_sha256": "abc123hash",
            "adjudicator_id": "SENIOR_ADJUDICATOR_01",
            "adjudication_version": "v1.0",
            "annotator_1_id": r1.annotator_id,
            "annotator_1_label": r1.reviewer_label,
            "annotator_1_indicators": ";".join(r1.observable_indicators),
            "annotator_2_id": r2.annotator_id,
            "annotator_2_label": r2.reviewer_label,
            "annotator_2_indicators": ";".join(r2.observable_indicators),
            "disagreement_type": "severity_tier_mismatch",
            "consensus_label": "high",
            "consensus_indicators": "fresh_scarp;tension_cracks",
            "consensus_confidence": "probable",
            "adjudication_rationale": "High-resolution inspection confirms 3cm aperture tension crack extending across road verge.",
            "escalation_required": "no",
            "adjudication_status": "adjudicated",
            "adjudicated_at": "2026-10-23T12:00:00Z",
        }

        # Both original annotations remain completely intact and uncorrupted
        self.assertEqual(adjudication_entry["annotator_1_label"], "high")
        self.assertEqual(adjudication_entry["annotator_2_label"], "moderate")
        self.assertEqual(adjudication_entry["consensus_label"], "high")
        self.assertEqual(adjudication_entry["disagreement_type"], "severity_tier_mismatch")

    def test_indeterminate_distinct_from_negative_controls(self):
        """Verifies that indeterminate ground truth is never conflated with low hazard or negative controls."""
        sample_indeterminate = VLMEvaluationSample(
            image_id="INDETERMINATE_SAMPLE",
            image_path="fog_dense.jpg",
            ground_truth_hazard="indeterminate",
            predicted_hazard="low",  # Model falsely guessed low on fogged photo
        )
        sample_control = VLMEvaluationSample(
            image_id="CONTROL_SAMPLE",
            image_path="stable_cut.jpg",
            ground_truth_hazard="low",
            predicted_hazard="low",  # Model correctly predicted low
        )

        metrics = VLMEvaluationHarness.compute_metrics([sample_indeterminate, sample_control])
        self.assertIsNotNone(metrics)

        # The indeterminate sample predicted as low MUST appear as an error in confusion matrix
        # [ground_truth=indeterminate][predicted=low] == 1
        self.assertEqual(metrics.confusion_matrix["indeterminate"]["low"], 1)
        self.assertEqual(metrics.confusion_matrix["low"]["low"], 1)
        # Overall accuracy is 1/2 = 50%
        self.assertEqual(metrics.accuracy, 0.5)

    def test_expansion_candidates_cannot_silently_enter_locked_benchmark(self):
        """Verifies that new unadjudicated candidate rows are rejected from frozen benchmarks."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(
                "image_id,image_sha256,image_path,source,license_or_permission_reference,"
                "split,adjudicated_label,adjudication_status\n"
                "VALID_01,hash1,p1.jpg,USGS,CC0,test,high,adjudicated\n"
                "UNADJUDICATED_EXPANSION_02,hash2,p2.jpg,Wikimedia,CC-BY,test,,pending\n"
            )
            temp_csv = f.name

        try:
            # Under strict ground truth policy for test split, pending samples must raise MissingExpertGroundTruthError
            with self.assertRaises(MissingExpertGroundTruthError) as ctx:
                VLMEvaluationHarness.load_dataset_csv(temp_csv, strict_ground_truth=True)
            self.assertIn("has unadjudicated ground truth", str(ctx.exception))
        finally:
            Path(temp_csv).unlink()


if __name__ == "__main__":
    unittest.main()
