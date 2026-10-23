"""Unit tests for VLMEvaluationHarness, dataset manifests, and scientific evaluation metrics.

Verifies:
1. Manifest ingestion and parsing for legacy and multi-annotator benchmark templates.
2. Missing or unverified permissions raise MissingPermissionError under strict policy.
3. Cross-split data leakage detection via SHA-256 digests raises DataLeakageError.
4. Invalid hazard labels raise InvalidLabelError.
5. Adjudication inconsistency raises MissingAdjudicationError.
6. Unsupported modalities and mismatched annotation schemas are rejected.
7. Wilson score confidence intervals are correctly computed on proportions.
8. Cohen's Kappa and inter-annotator agreement are computed accurately on synthetic double annotations.
9. Multi-label observable indicator metrics are computed cleanly.
10. Excluded samples are properly isolated from model metrics.
11. Abstains from metric fabrication when ground truth is absent.
12. End-to-end evaluation with MockGemmaProvider without DB interference.
"""

import asyncio
from pathlib import Path
import tempfile
import unittest

from backend.app.api.schemas.gemma_analysis import GemmaHazardOutput
from backend.app.services.gemma_providers import MockGemmaProvider
from backend.app.services.vlm_evaluation import (
    DATASET_PROVENANCE_REGISTRY,
    DataLeakageError,
    EvaluationMetrics,
    InvalidLabelError,
    MismatchedAnnotationSchemaError,
    MissingAdjudicationError,
    MissingPermissionError,
    UnsupportedModalityError,
    UnverifiedLicenseError,
    VLMEvaluationHarness,
    VLMEvaluationSample,
)


class TestVLMEvaluationHarness(unittest.TestCase):
    """Test suite for VLM evaluation harness and scientific validation pipeline."""

    def test_load_dataset_csv_ignores_comments_and_empty_lines(self):
        csv_content = """# Header comment
image_id,image_path,source,expert_ground_truth_hazard,visible_indicators,image_quality,reviewer_name,adjudication_status
# Another comment
SAMPLE_001,eval/img1.jpg,USGS,high,tension_cracks;slope_displacement,adequate,Dr. Geologist,adjudicated

SAMPLE_002,eval/img2.jpg,Border Roads,moderate,road_blockage,adequate,Dr. Geologist,adjudicated
SAMPLE_003,eval/img3.jpg,Local Survey,,tension_cracks,degraded,Dr. Geologist,pending
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            samples = VLMEvaluationHarness.load_dataset_csv(temp_path)
            self.assertEqual(len(samples), 3)
            self.assertEqual(samples[0].image_id, "SAMPLE_001")
            self.assertEqual(samples[0].ground_truth_hazard, "high")
            self.assertEqual(samples[0].ground_truth_indicators, ["tension_cracks", "slope_displacement"])
            self.assertEqual(samples[0].adjudication_status, "adjudicated")

            self.assertEqual(samples[1].image_id, "SAMPLE_002")
            self.assertEqual(samples[1].ground_truth_hazard, "moderate")

            # Sample 3 has pending/unadjudicated ground truth
            self.assertEqual(samples[2].image_id, "SAMPLE_003")
            self.assertIsNone(samples[2].ground_truth_hazard)
            self.assertEqual(samples[2].adjudication_status, "pending")
        finally:
            Path(temp_path).unlink()

    def test_load_benchmark_template_with_full_columns(self):
        """Loads and parses the formal multi-annotator benchmark manifest template."""
        manifest_path = Path("docs/gemma-local-vision/evaluation/field_photo_benchmark_template.csv")
        self.assertTrue(manifest_path.exists())

        samples = VLMEvaluationHarness.load_dataset_csv(manifest_path)
        self.assertGreaterEqual(len(samples), 4)

        s1 = samples[0]
        self.assertEqual(s1.image_id, "FPB_TEMPLATE_001")
        self.assertEqual(s1.ground_truth_hazard, "high")
        self.assertEqual(s1.annotator_1_label, "high")
        self.assertEqual(s1.annotator_2_label, "high")
        self.assertEqual(s1.adjudication_status, "adjudicated")
        self.assertEqual(s1.split, "test")
        self.assertIn("tension_cracks", s1.ground_truth_indicators)

    def test_missing_permission_rejected_under_strict_policy(self):
        """Under strict permissions enforcement, unverified or blank license raises MissingPermissionError."""
        bad_manifest = """image_id,image_sha256,image_path,source,license_or_permission_reference,image_quality,adjudicated_label,adjudication_status,split
FPB_001,e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855,img1.jpg,Gov,unverified,adequate,high,adjudicated,test
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(bad_manifest)
            temp_path = f.name

        try:
            with self.assertRaises(MissingPermissionError) as ctx:
                VLMEvaluationHarness.load_dataset_csv(temp_path, strict_permissions=True)
            self.assertIn("lacks verified legal permissions", str(ctx.exception))
        finally:
            Path(temp_path).unlink()

    def test_split_leakage_detected_on_duplicate_hashes(self):
        """Identical image SHA-256 hashes present across different splits raises DataLeakageError."""
        leaky_manifest = """image_id,image_sha256,image_path,source,license_or_permission_reference,image_quality,adjudicated_label,adjudication_status,split
FPB_TRAIN_01,aaaabbbbcccc1111222233334444555566667777888899990000aaaabbbbcccc,img1.jpg,SourceA,CC-BY-4.0,adequate,high,adjudicated,train
FPB_TEST_01,aaaabbbbcccc1111222233334444555566667777888899990000aaaabbbbcccc,img2.jpg,SourceB,CC-BY-4.0,adequate,high,adjudicated,test
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(leaky_manifest)
            temp_path = f.name

        try:
            with self.assertRaises(DataLeakageError) as ctx:
                VLMEvaluationHarness.load_dataset_csv(temp_path)
            self.assertIn("Data leakage detected", str(ctx.exception))
            self.assertIn("is present in both 'test' and 'train'", str(ctx.exception))
        finally:
            Path(temp_path).unlink()

    def test_invalid_hazard_label_rejected(self):
        """Invalid hazard labels outside the categorical taxonomy raise InvalidLabelError."""
        bad_manifest = """image_id,image_path,adjudicated_label,adjudication_status
FPB_001,img1.jpg,catastrophic,adjudicated
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(bad_manifest)
            temp_path = f.name

        try:
            with self.assertRaises(InvalidLabelError) as ctx:
                VLMEvaluationHarness.load_dataset_csv(temp_path)
            self.assertIn("Invalid hazard label 'catastrophic'", str(ctx.exception))
        finally:
            Path(temp_path).unlink()

    def test_missing_adjudication_label_when_status_adjudicated(self):
        """When adjudication_status is 'adjudicated', empty adjudicated_label raises MissingAdjudicationError."""
        bad_manifest = """image_id,image_path,adjudicated_label,adjudication_status
FPB_001,img1.jpg,,adjudicated
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(bad_manifest)
            temp_path = f.name

        try:
            with self.assertRaises(MissingAdjudicationError) as ctx:
                VLMEvaluationHarness.load_dataset_csv(temp_path)
            self.assertIn("marked as 'adjudicated' but has no adjudicated label", str(ctx.exception))
        finally:
            Path(temp_path).unlink()

    def test_abstains_from_metric_calculation_when_ground_truth_absent(self):
        """When dataset has zero expert ground truth, compute_metrics returns None."""
        samples = [
            VLMEvaluationSample(
                image_id="UNLABELED_01",
                image_path="dummy.jpg",
                ground_truth_hazard=None,
                predicted_hazard="high",
            ),
            VLMEvaluationSample(
                image_id="UNLABELED_02",
                image_path="dummy.jpg",
                ground_truth_hazard=None,
                predicted_hazard="low",
            ),
        ]
        metrics = VLMEvaluationHarness.compute_metrics(samples)
        self.assertIsNone(metrics)

        report = VLMEvaluationHarness.format_metrics_report(metrics)
        self.assertIn("No expert-reviewed ground-truth labels available", report)
        self.assertIn("Zero metrics calculated", report)

    def test_computes_exact_classification_metrics_and_confusion_matrix(self):
        """When genuine ground truth is present, computes exact mathematical metrics on synthetic test fixtures."""
        samples = [
            # True High, Pred High (TP High)
            VLMEvaluationSample(image_id="1", image_path="d.jpg", ground_truth_hazard="high", predicted_hazard="high"),
            # True High, Pred Moderate (FN High, FP Moderate)
            VLMEvaluationSample(image_id="2", image_path="d.jpg", ground_truth_hazard="high", predicted_hazard="moderate"),
            # True Moderate, Pred Moderate (TP Moderate)
            VLMEvaluationSample(image_id="3", image_path="d.jpg", ground_truth_hazard="moderate", predicted_hazard="moderate"),
            # True Low, Pred Low (TP Low)
            VLMEvaluationSample(image_id="4", image_path="d.jpg", ground_truth_hazard="low", predicted_hazard="low"),
            # True Critical, Pred Indeterminate (FN Critical, Indeterminate coverage drop)
            VLMEvaluationSample(image_id="5", image_path="d.jpg", ground_truth_hazard="critical", predicted_hazard="indeterminate"),
        ]

        metrics = VLMEvaluationHarness.compute_metrics(samples)
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.total_samples, 5)
        self.assertEqual(metrics.labeled_samples, 5)

        # Confusion matrix checks:
        self.assertEqual(metrics.confusion_matrix["high"]["high"], 1)
        self.assertEqual(metrics.confusion_matrix["high"]["moderate"], 1)
        self.assertEqual(metrics.confusion_matrix["moderate"]["moderate"], 1)
        self.assertEqual(metrics.confusion_matrix["low"]["low"], 1)
        self.assertEqual(metrics.confusion_matrix["critical"]["indeterminate"], 1)

        # Supports:
        self.assertEqual(metrics.per_class_support["high"], 2)
        self.assertEqual(metrics.per_class_support["moderate"], 1)
        self.assertEqual(metrics.per_class_support["low"], 1)
        self.assertEqual(metrics.per_class_support["critical"], 1)
        self.assertEqual(metrics.per_class_support["indeterminate"], 0)

        # Precision & Recall:
        self.assertEqual(metrics.per_class_precision["high"], 1.0)
        self.assertEqual(metrics.per_class_recall["high"], 0.5)
        self.assertEqual(metrics.per_class_precision["moderate"], 0.5)
        self.assertEqual(metrics.per_class_recall["moderate"], 1.0)

        # Overall accuracy: 3 correct out of 5 = 0.60
        self.assertEqual(metrics.accuracy, 0.60)

        # Coverage rate: 4 determinate predictions out of 5 = 0.80
        self.assertEqual(metrics.coverage_rate, 0.80)

        # Determinate accuracy: 3 correct out of 4 determinate = 0.75
        self.assertEqual(metrics.determinate_accuracy, 0.75)

        # Wilson Confidence Intervals
        self.assertTrue(0.0 <= metrics.wilson_ci_accuracy[0] <= metrics.accuracy <= metrics.wilson_ci_accuracy[1] <= 1.0)
        self.assertTrue(0.0 <= metrics.wilson_ci_coverage[0] <= metrics.coverage_rate <= metrics.wilson_ci_coverage[1] <= 1.0)

        report = VLMEvaluationHarness.format_metrics_report(metrics)
        self.assertIn("**Overall Accuracy:** 60.00%", report)
        self.assertIn("**Determinate Coverage Rate:** 80.00%", report)
        self.assertIn("Confusion Matrix", report)

    def test_wilson_ci_computation_bounds(self):
        """Wilson score confidence interval computes cleanly on boundary cases."""
        # 0 of 10
        ci_zero = VLMEvaluationHarness.compute_wilson_ci(0, 10)
        self.assertEqual(ci_zero[0], 0.0)
        self.assertGreater(ci_zero[1], 0.0)

        # 10 of 10
        ci_full = VLMEvaluationHarness.compute_wilson_ci(10, 10)
        self.assertLess(ci_full[0], 1.0)
        self.assertEqual(ci_full[1], 1.0)

        # 0 of 0
        ci_empty = VLMEvaluationHarness.compute_wilson_ci(0, 0)
        self.assertEqual(ci_empty, (0.0, 0.0))

    def test_inter_annotator_agreement_cohens_kappa(self):
        """Calculates exact Cohen's Kappa on synthetic double-annotated pairs."""
        # Perfect agreement
        samples_perfect = [
            VLMEvaluationSample(image_id="1", image_path="d.jpg", annotator_1_label="high", annotator_2_label="high"),
            VLMEvaluationSample(image_id="2", image_path="d.jpg", annotator_1_label="low", annotator_2_label="low"),
            VLMEvaluationSample(image_id="3", image_path="d.jpg", annotator_1_label="critical", annotator_2_label="critical"),
            VLMEvaluationSample(image_id="4", image_path="d.jpg", annotator_1_label="moderate", annotator_2_label="moderate"),
        ]
        iaa_perfect = VLMEvaluationHarness.compute_inter_annotator_agreement(samples_perfect)
        self.assertIsNotNone(iaa_perfect)
        self.assertEqual(iaa_perfect["observed_agreement"], 1.0)
        self.assertEqual(iaa_perfect["cohens_kappa"], 1.0)
        self.assertIn("High reliability", iaa_perfect["interpretation"])

        # Disagreement
        samples_disagree = [
            VLMEvaluationSample(image_id="1", image_path="d.jpg", annotator_1_label="high", annotator_2_label="moderate"),
            VLMEvaluationSample(image_id="2", image_path="d.jpg", annotator_1_label="high", annotator_2_label="high"),
            VLMEvaluationSample(image_id="3", image_path="d.jpg", annotator_1_label="low", annotator_2_label="moderate"),
            VLMEvaluationSample(image_id="4", image_path="d.jpg", annotator_1_label="low", annotator_2_label="low"),
        ]
        iaa_disagree = VLMEvaluationHarness.compute_inter_annotator_agreement(samples_disagree)
        self.assertEqual(iaa_disagree["observed_agreement"], 0.50)
        self.assertLess(iaa_disagree["cohens_kappa"], 1.0)

    def test_multi_label_indicator_metrics(self):
        """Calculates precision, recall, and F1 on observable multi-label physical features."""
        samples = [
            VLMEvaluationSample(
                image_id="1",
                image_path="d.jpg",
                ground_truth_hazard="high",
                predicted_hazard="high",
                ground_truth_indicators=["tension_cracks", "slope_displacement"],
                predicted_hazards=["tension_cracks", "rockfall_debris"],  # TP=1, FP=1, FN=1
            )
        ]
        metrics = VLMEvaluationHarness.compute_metrics(samples)
        self.assertIsNotNone(metrics)
        self.assertIsNotNone(metrics.multi_label_indicators)
        # TP=1, FP=1 -> Prec = 0.5; TP=1, FN=1 -> Rec = 0.5; F1 = 0.5
        self.assertEqual(metrics.multi_label_indicators["precision"], 0.5)
        self.assertEqual(metrics.multi_label_indicators["recall"], 0.5)
        self.assertEqual(metrics.multi_label_indicators["f1_score"], 0.5)

    def test_exclusion_handling(self):
        """Samples marked as excluded are not evaluated or counted in performance metrics."""
        samples = [
            VLMEvaluationSample(
                image_id="VALID_01",
                image_path="d.jpg",
                ground_truth_hazard="high",
                predicted_hazard="high",
                adjudication_status="adjudicated",
            ),
            VLMEvaluationSample(
                image_id="EXCLUDED_01",
                image_path="d.jpg",
                ground_truth_hazard="high",
                predicted_hazard="low",
                adjudication_status="excluded",
                exclusion_reason="severe_privacy_violation",
            ),
        ]
        metrics = VLMEvaluationHarness.compute_metrics(samples)
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.total_samples, 2)
        self.assertEqual(metrics.labeled_samples, 1)  # Only 1 evaluated
        self.assertEqual(metrics.excluded_samples, 1)
        self.assertEqual(metrics.accuracy, 1.0)  # Excluded sample ignored

    def test_empty_evaluation_set_handling(self):
        """Empty evaluation set returns None without dividing by zero."""
        metrics = VLMEvaluationHarness.compute_metrics([])
        self.assertIsNone(metrics)

    def test_evaluate_sample_with_mock_provider(self):
        """End-to-end evaluation execution using MockGemmaProvider without DB interference."""
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".jpg") as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9")
            temp_img = f.name

        try:
            sample = VLMEvaluationSample(
                image_id="TEST_MOCK_1",
                image_path=temp_img,
                ground_truth_hazard="moderate",
            )
            provider = MockGemmaProvider(
                custom_output=GemmaHazardOutput(
                    hazard_level="moderate",
                    detected_hazards=["tension_cracks"],
                    confidence=0.88,
                    summary="Test summary",
                    limitations="Test limitations",
                )
            )

            evaluated = asyncio.run(VLMEvaluationHarness.evaluate_sample(sample, provider))
            self.assertIsNone(evaluated.error)
            self.assertEqual(evaluated.predicted_hazard, "moderate")
            self.assertEqual(evaluated.predicted_hazards, ["tension_cracks"])
            self.assertEqual(evaluated.predicted_confidence, 0.88)
        finally:
            Path(temp_img).unlink()

    def test_export_results_csv(self):
        """Results are written cleanly to output CSV."""
        samples = [
            VLMEvaluationSample(
                image_id="OUT_01",
                image_path="img1.jpg",
                ground_truth_hazard="high",
                predicted_hazard="high",
                predicted_confidence=0.91,
                predicted_summary="Severe scarp",
            )
        ]
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as f:
            temp_out = f.name

        try:
            VLMEvaluationHarness.export_results_csv(samples, temp_out)
            self.assertTrue(Path(temp_out).exists())
            with open(temp_out, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("OUT_01", content)
            self.assertIn("high", content)
            self.assertIn("0.91", content)
        finally:
            Path(temp_out).unlink()

    def test_provenance_registry_contains_evaluated_datasets(self):
        """Dataset provenance registry contains entries for HLAD, Landslide4Sense, and internal benchmark."""
        self.assertIn("HLAD", DATASET_PROVENANCE_REGISTRY)
        self.assertIn("Landslide4Sense", DATASET_PROVENANCE_REGISTRY)
        self.assertIn("PahaarPulse-Field-Benchmark", DATASET_PROVENANCE_REGISTRY)

    def test_hlad_rejected_due_to_unverified_license(self):
        """HLAD must be blocked due to blank license terms on Zenodo."""
        with self.assertRaises(UnverifiedLicenseError) as ctx:
            VLMEvaluationHarness.validate_dataset_provenance("HLAD")
        self.assertIn("unverified or blank license terms", str(ctx.exception))

    def test_landslide4sense_rejected_due_to_unsupported_modality(self):
        """Landslide4Sense must be blocked due to incompatible 14-band multispectral satellite modality."""
        with self.assertRaises(UnsupportedModalityError) as ctx:
            VLMEvaluationHarness.validate_dataset_provenance("Landslide4Sense")
        self.assertIn("incompatible with Gemma field VLM", str(ctx.exception))

    def test_pahaarpulse_benchmark_provenance_valid(self):
        """Internal field benchmark is valid and verified in registry."""
        record = VLMEvaluationHarness.validate_dataset_provenance("PahaarPulse-Field-Benchmark")
        self.assertTrue(record["license_verified"])
        self.assertTrue(record["compatible_with_gemma_field_vlm"])
        self.assertEqual(record["admission_decision"], "APPROVED_TARGET_SCHEMA")

    def test_unsupported_modality_file_extensions_rejected(self):
        """Multispectral raster formats (.tif, .npy, .h5) raise UnsupportedModalityError."""
        for ext in [".tif", ".tiff", ".npy", ".h5", ".hdf5"]:
            with self.assertRaises(UnsupportedModalityError):
                VLMEvaluationHarness.validate_sample_modality(f"eval/satellite_patch{ext}")

        # Supported optical formats pass
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            validated = VLMEvaluationHarness.validate_sample_modality(f"eval/photo{ext}")
            self.assertEqual(validated, ext)

    def test_mismatched_segmentation_headers_rejected(self):
        """Datasets with mask or bbox columns raise MismatchedAnnotationSchemaError."""
        bad_csv = """image_id,image_path,mask_path,segmentation_mask
SAMPLE_001,eval/img1.jpg,masks/mask1.png,1
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(bad_csv)
            temp_path = f.name

        try:
            with self.assertRaises(MismatchedAnnotationSchemaError) as ctx:
                VLMEvaluationHarness.load_dataset_csv(temp_path)
            self.assertIn("spatial mask/bounding box columns", str(ctx.exception))
        finally:
            Path(temp_path).unlink()

    def test_binary_segmentation_labels_rejected(self):
        """Binary 0/1 labels raise MismatchedAnnotationSchemaError instead of being treated as hazard levels."""
        bad_csv = """image_id,image_path,expert_ground_truth_hazard
SAMPLE_001,eval/img1.jpg,1
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(bad_csv)
            temp_path = f.name

        try:
            with self.assertRaises(MismatchedAnnotationSchemaError) as ctx:
                VLMEvaluationHarness.load_dataset_csv(temp_path)
            self.assertIn("binary segmentation/detection label", str(ctx.exception))
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    unittest.main()
