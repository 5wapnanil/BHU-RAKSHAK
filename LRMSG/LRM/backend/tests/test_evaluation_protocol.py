"""Unit tests for Phase 2E Evaluation Protocol, Manifest Immutability, and Safety Infrastructure.

Verifies:
1. Dataset manifest SHA-256 hash freezing and tampering detection (ManifestHashMismatchError).
2. Prediction-annotation separation enforcement (PredictionSeparationViolationError).
3. Prediction record validation and execution status handling (success, malformed_output, rate_limit, timeout, abstention_indeterminate, provider_error).
4. Run manifest JSON export and predictions CSV export ensuring zero leakage of ground-truth columns.
5. Safety-critical under-call false negative metrics on synthetic fixtures.
6. Cross-split site/event cluster isolation and data leakage rejection (DataLeakageError).
7. Wilson score confidence interval boundary calculations for small sample sizes.
"""

import csv
import json
from pathlib import Path
import tempfile
import unittest

from backend.app.services.vlm_evaluation import (
    DataLeakageError,
    EvaluationPredictionRecord,
    EvaluationResultLogger,
    EvaluationRunManifest,
    ManifestHashMismatchError,
    PredictionSeparationViolationError,
    VALID_EXECUTION_STATUSES,
    VLMEvaluationHarness,
    VLMEvaluationSample,
)


class TestEvaluationProtocol(unittest.TestCase):
    """Test suite for Phase 2E evaluation protocol tooling, manifest immutability, and metrics."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_sample_manifest(self, rows=None) -> Path:
        """Helper to create a temporary candidate manifest CSV."""
        manifest_path = self.test_dir / "test_manifest.csv"
        fieldnames = [
            "image_id", "image_sha256", "image_path", "source",
            "license_or_permission_reference", "split", "duplicate_group_id",
            "adjudicated_label", "adjudication_status"
        ]
        if rows is None:
            rows = [
                {
                    "image_id": "CAND_001",
                    "image_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
                    "image_path": "img1.jpg",
                    "source": "Wikimedia",
                    "license_or_permission_reference": "CC-BY-4.0",
                    "split": "test",
                    "duplicate_group_id": "SITE_A",
                    "adjudicated_label": "high",
                    "adjudication_status": "adjudicated",
                },
                {
                    "image_id": "CAND_002",
                    "image_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
                    "image_path": "img2.jpg",
                    "source": "USGS",
                    "license_or_permission_reference": "Public Domain",
                    "split": "test",
                    "duplicate_group_id": "SITE_B",
                    "adjudicated_label": "low",
                    "adjudication_status": "adjudicated",
                },
            ]
        with open(manifest_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return manifest_path

    def test_create_run_manifest_freezes_sha256_and_parameters(self):
        """Verifies that create_run_manifest freezes dataset hash and inference hyperparameters."""
        manifest_path = self._create_sample_manifest()
        expected_sha = VLMEvaluationHarness.compute_sha256(manifest_path)

        run = EvaluationResultLogger.create_run_manifest(
            dataset_manifest_path=manifest_path,
            model_id="gemini-3.5-flash",
            prompt_version="v2.1",
            protocol_version="Phase-2E-v1.0",
            inference_parameters={"temperature": 0.0, "timeout_seconds": 30.0},
            notes="Formal frozen evaluation run test",
        )

        self.assertTrue(run.run_id.startswith("eval_"))
        self.assertEqual(run.dataset_manifest_sha256, expected_sha)
        self.assertEqual(run.model_id, "gemini-3.5-flash")
        self.assertEqual(run.prompt_version, "v2.1")
        self.assertEqual(run.protocol_version, "Phase-2E-v1.0")
        self.assertEqual(run.inference_parameters["temperature"], 0.0)
        self.assertEqual(run.inference_parameters["timeout_seconds"], 30.0)
        self.assertEqual(run.total_samples, 0)
        self.assertEqual(run.successful_inferences, 0)
        self.assertEqual(run.failed_inferences, 0)

    def test_manifest_tamper_detection_raises_mismatch_error(self):
        """Verifies that any post-initialization modification of the dataset raises ManifestHashMismatchError."""
        manifest_path = self._create_sample_manifest()
        run = EvaluationResultLogger.create_run_manifest(dataset_manifest_path=manifest_path)

        # Confirm initial integrity passes
        self.assertTrue(EvaluationResultLogger.verify_manifest_integrity(run, manifest_path))

        # Tamper with the dataset file
        with open(manifest_path, "a", encoding="utf-8") as f:
            f.write("TAMPERED_ROW,33333333,img3.jpg,Fake,None,test,SITE_C,high,adjudicated\n")

        with self.assertRaises(ManifestHashMismatchError) as ctx:
            EvaluationResultLogger.verify_manifest_integrity(run, manifest_path)
        self.assertIn("Dataset manifest hash mismatch", str(ctx.exception))

    def test_prediction_separation_prohibits_ground_truth_fields(self):
        """Verifies that model predictions cannot contain ground-truth human annotation fields."""
        prohibited_payload = {
            "candidate_id": "CAND_001",
            "predicted_hazard": "high",
            "adjudicated_label": "high",  # PROHIBITED in prediction payload
        }

        with self.assertRaises(PredictionSeparationViolationError) as ctx:
            EvaluationResultLogger.validate_prediction_separation(prohibited_payload)
        self.assertIn("Prediction-annotation separation violation", str(ctx.exception))

        # Test another prohibited field
        prohibited_payload_2 = {
            "candidate_id": "CAND_001",
            "predicted_hazard": "moderate",
            "expert_ground_truth_hazard": "moderate",
        }
        with self.assertRaises(PredictionSeparationViolationError):
            EvaluationResultLogger.validate_prediction_separation(prohibited_payload_2)

    def test_prediction_record_candidate_id_and_hash_consistency(self):
        """Verifies that logging a prediction requires identity and hash alignment with the sample."""
        manifest_path = self._create_sample_manifest()
        run = EvaluationResultLogger.create_run_manifest(dataset_manifest_path=manifest_path)

        sample = VLMEvaluationSample(
            image_id="CAND_001",
            image_path="img1.jpg",
            image_sha256="1111111111111111111111111111111111111111111111111111111111111111",
            split="test",
        )

        # Mismatched candidate ID
        pred_wrong_id = EvaluationPredictionRecord(
            candidate_id="CAND_MISMATCH",
            image_sha256="1111111111111111111111111111111111111111111111111111111111111111",
            execution_status="success",
        )
        with self.assertRaises(ValueError) as ctx:
            EvaluationResultLogger.log_prediction(run, pred_wrong_id, sample=sample)
        self.assertIn("Candidate ID mismatch", str(ctx.exception))

        # Mismatched image SHA-256
        pred_wrong_hash = EvaluationPredictionRecord(
            candidate_id="CAND_001",
            image_sha256="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            execution_status="success",
        )
        with self.assertRaises(ManifestHashMismatchError) as ctx:
            EvaluationResultLogger.log_prediction(run, pred_wrong_hash, sample=sample)
        self.assertIn("Image hash mismatch", str(ctx.exception))

        # Valid prediction matches sample
        pred_valid = EvaluationPredictionRecord(
            candidate_id="CAND_001",
            image_sha256="1111111111111111111111111111111111111111111111111111111111111111",
            predicted_hazard="high",
            predicted_hazards=["tension_cracks", "slope_displacement"],
            predicted_confidence=0.91,
            execution_status="success",
            latency_ms=850.5,
        )
        EvaluationResultLogger.log_prediction(run, pred_valid, sample=sample)
        self.assertEqual(run.total_samples, 1)
        self.assertEqual(run.successful_inferences, 1)
        self.assertEqual(run.failed_inferences, 0)
        self.assertEqual(len(run.predictions), 1)

    def test_execution_statuses_handling(self):
        """Verifies handling of all valid execution statuses including malformed outputs and timeouts."""
        manifest_path = self._create_sample_manifest()
        run = EvaluationResultLogger.create_run_manifest(dataset_manifest_path=manifest_path)

        # Test all valid execution statuses
        for st in VALID_EXECUTION_STATUSES:
            rec = EvaluationPredictionRecord(
                candidate_id=f"CAND_{st}",
                image_sha256="abc123def456",
                execution_status=st,
                error_message="Test error" if st != "success" else None,
            )
            EvaluationResultLogger.log_prediction(run, rec)

        self.assertEqual(run.total_samples, len(VALID_EXECUTION_STATUSES))
        self.assertEqual(run.successful_inferences, 1)
        self.assertEqual(run.failed_inferences, len(VALID_EXECUTION_STATUSES) - 1)

        # Invalid execution status must raise ValueError
        with self.assertRaises(ValueError):
            EvaluationPredictionRecord(
                candidate_id="CAND_BAD_STATUS",
                image_sha256="abc123def456",
                execution_status="unknown_status",
            )

    def test_export_run_json_and_predictions_csv_isolation(self):
        """Verifies that exported JSON and CSV artifacts do not contain ground-truth adjudication fields."""
        manifest_path = self._create_sample_manifest()
        run = EvaluationResultLogger.create_run_manifest(dataset_manifest_path=manifest_path)

        pred1 = EvaluationPredictionRecord(
            candidate_id="CAND_001",
            image_sha256="1111111111111111111111111111111111111111111111111111111111111111",
            predicted_hazard="high",
            predicted_hazards=["tension_cracks"],
            predicted_confidence=0.88,
            predicted_summary="Severe crown tension cracks visible.",
            execution_status="success",
            latency_ms=620.0,
        )
        pred2 = EvaluationPredictionRecord(
            candidate_id="CAND_002",
            image_sha256="2222222222222222222222222222222222222222222222222222222222222222",
            execution_status="rate_limit",
            error_message="HTTP 429 Too Many Requests",
            latency_ms=120.0,
        )
        EvaluationResultLogger.log_prediction(run, pred1)
        EvaluationResultLogger.log_prediction(run, pred2)

        # Export JSON
        json_path = self.test_dir / "run_output.json"
        EvaluationResultLogger.export_run_json(run, json_path)
        self.assertTrue(json_path.exists())

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["run_id"], run.run_id)
        self.assertEqual(len(data["predictions"]), 2)
        self.assertIn("completed_at", data)

        # Export CSV
        csv_path = self.test_dir / "predictions_output.csv"
        EvaluationResultLogger.export_predictions_csv(run, csv_path)
        self.assertTrue(csv_path.exists())

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            # Ground truth columns must NEVER be in predictions CSV
            self.assertNotIn("adjudicated_label", fieldnames)
            self.assertNotIn("expert_ground_truth_hazard", fieldnames)
            self.assertNotIn("annotator_1_label", fieldnames)
            self.assertNotIn("annotator_2_label", fieldnames)
            self.assertIn("predicted_hazard", fieldnames)
            self.assertIn("execution_status", fieldnames)

            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["candidate_id"], "CAND_001")
            self.assertEqual(rows[0]["predicted_hazard"], "high")
            self.assertEqual(rows[1]["execution_status"], "rate_limit")

    def test_safety_critical_under_call_metrics(self):
        """Verifies calculation of safety-critical false negatives when True High/Critical are under-called as Low/Moderate."""
        synthetic_samples = [
            # True Critical, Pred Low -> Severe under-call
            VLMEvaluationSample(
                image_id="DANGER_01",
                image_path="d1.jpg",
                image_sha256="hash1",
                ground_truth_hazard="critical",
                predicted_hazard="low",
            ),
            # True High, Pred Moderate -> Severe under-call
            VLMEvaluationSample(
                image_id="DANGER_02",
                image_path="d2.jpg",
                image_sha256="hash2",
                ground_truth_hazard="high",
                predicted_hazard="moderate",
            ),
            # True High, Pred High -> Correctly identified high hazard (safe TP)
            VLMEvaluationSample(
                image_id="SAFE_01",
                image_path="s1.jpg",
                image_sha256="hash3",
                ground_truth_hazard="high",
                predicted_hazard="high",
            ),
            # True Low, Pred Critical -> Over-call (conservative false alarm, not safety-critical under-call)
            VLMEvaluationSample(
                image_id="ALARM_01",
                image_path="a1.jpg",
                image_sha256="hash4",
                ground_truth_hazard="low",
                predicted_hazard="critical",
            ),
            # True Moderate, Pred Low -> Non-critical under-call (neither true high nor critical)
            VLMEvaluationSample(
                image_id="MOD_01",
                image_path="m1.jpg",
                image_sha256="hash5",
                ground_truth_hazard="moderate",
                predicted_hazard="low",
            ),
        ]

        metrics = VLMEvaluationHarness.compute_metrics(synthetic_samples)
        self.assertIsNotNone(metrics)

        # High/critical total is 3 (DANGER_01, DANGER_02, SAFE_01)
        # Severe under-calls are 2 (DANGER_01, DANGER_02)
        self.assertEqual(metrics.safety_critical_under_call_count, 2)
        self.assertAlmostEqual(metrics.safety_critical_under_call_rate, 2 / 3, places=3)
        self.assertEqual(len(metrics.critical_false_negatives), 2)
        flagged_ids = [fn["image_id"] for fn in metrics.critical_false_negatives]
        self.assertIn("DANGER_01", flagged_ids)
        self.assertIn("DANGER_02", flagged_ids)

        # Verify report formatting includes the safety alert
        report = VLMEvaluationHarness.format_metrics_report(metrics)
        self.assertIn("Safety-Critical Hazard Under-Call Analysis", report)
        self.assertIn("DANGER_01", report)
        self.assertIn("DANGER_02", report)

    def test_cross_split_site_group_leakage_detection(self):
        """Verifies that photos sharing a site or event cluster group cannot span multiple splits."""
        leaking_samples = [
            VLMEvaluationSample(
                image_id="S1_IMG1",
                image_path="s1_1.jpg",
                image_sha256="hash_a1",
                duplicate_group_id="SERIES_KEDARNATH_2013",
                split="train",
            ),
            VLMEvaluationSample(
                image_id="S1_IMG2",
                image_path="s1_2.jpg",
                image_sha256="hash_a2",
                duplicate_group_id="SERIES_KEDARNATH_2013",
                split="test",  # LEAKAGE: Same site/event in train and test!
            ),
        ]

        with self.assertRaises(DataLeakageError) as ctx:
            VLMEvaluationHarness.validate_split_integrity(leaking_samples)
        self.assertIn("Event/site-group leakage detected", str(ctx.exception))
        self.assertIn("SERIES_KEDARNATH_2013", str(ctx.exception))

    def test_wilson_score_confidence_intervals_boundary_cases(self):
        """Verifies Wilson score confidence intervals for edge boundary conditions (k=0, k=n)."""
        # Boundary k=0, n=54 (0% success rate)
        lower_0, upper_0 = VLMEvaluationHarness.compute_wilson_ci(0, 54)
        self.assertEqual(lower_0, 0.0)
        self.assertGreater(upper_0, 0.0)
        self.assertLess(upper_0, 0.10)  # Rule of three upper bound ~ 3/54 = 0.055

        # Boundary k=54, n=54 (100% success rate)
        lower_100, upper_100 = VLMEvaluationHarness.compute_wilson_ci(54, 54)
        self.assertGreater(lower_100, 0.90)
        self.assertEqual(upper_100, 1.0)

        # Degenerate n=0
        lower_empty, upper_empty = VLMEvaluationHarness.compute_wilson_ci(0, 0)
        self.assertEqual((lower_empty, upper_empty), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
