"""VLM Evaluation Harness for PahaarPulse Geotechnical Vision Screening.

Provides reproducible dataset ingestion, strict validation, inference execution against AnalysisProvider,
and rigorous classification metrics (Confusion Matrix, Precision, Recall, F1, Wilson CIs, Cohen's Kappa).
Enforces zero metric fabrication when ground truth is absent.
"""

import csv
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from backend.app.services.gemma_providers import (
    AnalysisProvider,
    GemmaHazardOutput,
    GemmaProviderError,
)

logger = logging.getLogger(__name__)

VALID_HAZARD_CLASSES = ("low", "moderate", "high", "critical", "indeterminate")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
UNSUPPORTED_REMOTE_SENSING_EXTENSIONS = {".tif", ".tiff", ".npy", ".h5", ".hdf5", ".nc", ".geotiff"}
ALLOWED_SPLITS = {"train", "dev", "test"}
STANDARD_INDICATORS = (
    "tension_cracks",
    "slope_displacement",
    "road_blockage",
    "rockfall_debris",
    "structural_damage",
    "toe_erosion",
    "mudflow",
    "water_seepage",
    "stable_vegetation",
)


class EvaluationError(Exception):
    """Base exception for evaluation harness errors."""
    pass


class UnsupportedModalityError(EvaluationError):
    """Raised when an unsupported image modality or remote sensing tensor is supplied."""
    pass


class MismatchedAnnotationSchemaError(EvaluationError):
    """Raised when dataset annotations (e.g. segmentation masks, bounding boxes) do not match categorical hazard triage."""
    pass


class UnverifiedLicenseError(EvaluationError):
    """Raised when an external dataset has an unverified or blank license terms field."""
    pass


class MissingPermissionError(EvaluationError):
    """Raised when a benchmark sample or dataset lacks documented legal permission or license."""
    pass


class DataLeakageError(EvaluationError):
    """Raised when identical image hashes appear across different evaluation splits (e.g., train and test)."""
    pass


class InvalidLabelError(EvaluationError):
    """Raised when ground-truth or adjudicated hazard labels violate the categorical taxonomy."""
    pass


class MissingAdjudicationError(EvaluationError):
    """Raised when a sample marked as adjudicated lacks a final adjudicated label."""
    pass


class InvalidSourceError(EvaluationError):
    """Raised when a benchmark sample lacks a verified source repository or URL."""
    pass


class MissingExpertGroundTruthError(EvaluationError):
    """Raised when an unadjudicated or pending sample is placed in a frozen test benchmark."""
    pass


class AnnotationIntegrityError(EvaluationError):
    """Raised when an annotation record violates schema, provenance, or scientific constraints."""
    pass


class AIAnnotatorProhibitedError(AnnotationIntegrityError):
    """Raised when an AI model identifier is used as a human annotator ID."""
    pass


class ManifestHashMismatchError(EvaluationError):
    """Raised when a candidate manifest or benchmark dataset does not match its expected SHA-256 digest."""
    pass


class PredictionSeparationViolationError(EvaluationError):
    """Raised when model predictions attempt to overwrite or contaminate ground-truth annotation fields."""
    pass


# Dataset Compatibility and Provenance Register
DATASET_PROVENANCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "HLAD": {
        "dataset_id": "HLAD",
        "name": "Himalayan Landslide Detection Dataset",
        "source_url": "https://doi.org/10.5281/zenodo.22811448",
        "doi": "10.5281/zenodo.22811448",
        "modality": "high_resolution_optical_drone",
        "supported_formats": [".jpg", ".png"],
        "annotation_type": "bounding_box_and_scar_mask",
        "license_status": "unverified_blank",
        "license_verified": False,
        "geographic_coverage": "Himalayan Region",
        "compatible_with_gemma_field_vlm": False,
        "suitability_limitations": (
            "Blank license on Zenodo legally precludes downloading or redistribution without explicit permission. "
            "Annotations are scar masks/bounding boxes rather than categorical geotechnical hazard severity triage "
            "and lack ground-level road/infrastructure context."
        ),
        "admission_decision": "REJECTED_BLOCKED",
    },
    "Landslide4Sense": {
        "dataset_id": "Landslide4Sense",
        "name": "Landslide4Sense Multispectral Satellite Benchmark",
        "source_url": "https://landslide4sense.github.io/",
        "doi": "10.1109/MGRS.2022.3168877",
        "modality": "14_band_multispectral_satellite",
        "supported_formats": [".tif", ".tiff", ".npy", ".h5"],
        "annotation_type": "pixel_binary_segmentation_mask",
        "license_status": "academic_competition_only",
        "license_verified": True,
        "geographic_coverage": "Global Mountainous Regions",
        "compatible_with_gemma_field_vlm": False,
        "suitability_limitations": (
            "Incompatible 14-band remote sensing modality (Sentinel-2, ALOS DEM). Binary pixel masks are for spatial segmentation, "
            "not geotechnical triage. Belongs to macro-scale satellite GIS pipeline, not conversational RGB vision model."
        ),
        "admission_decision": "REJECTED_BLOCKED",
    },
    "PahaarPulse-Field-Benchmark": {
        "dataset_id": "PahaarPulse-Field-Benchmark",
        "name": "PahaarPulse Ground Field Report Benchmark",
        "source_url": "internal://evaluation/field_photo_benchmark_template.csv",
        "doi": None,
        "modality": "ground_field_photograph_rgb",
        "supported_formats": [".jpg", ".jpeg", ".png", ".webp"],
        "annotation_type": "categorical_hazard_triage_plus_indicators",
        "license_status": "internal_project_license_cc_by_4_0",
        "license_verified": True,
        "geographic_coverage": "Indian Himalayan Region (Uttarakhand, Sikkim, Himachal Pradesh)",
        "compatible_with_gemma_field_vlm": True,
        "suitability_limitations": (
            "Target architecture schema. Requires independent dual-expert geotechnical adjudication "
            "prior to computing benchmark scorecards."
        ),
        "admission_decision": "APPROVED_TARGET_SCHEMA",
    },
}


@dataclass
class VLMEvaluationSample:
    """A single evaluation record with ground truth and model predictions."""

    image_id: str
    image_path: str
    source: str = ""
    image_sha256: Optional[str] = None
    license_reference: Optional[str] = None
    capture_date: Optional[str] = None
    region: Optional[str] = None
    image_quality: str = "adequate"
    split: str = "test"
    ground_truth_hazard: Optional[str] = None
    ground_truth_indicators: List[str] = field(default_factory=list)
    annotator_1_id: Optional[str] = None
    annotator_1_label: Optional[str] = None
    annotator_2_id: Optional[str] = None
    annotator_2_label: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewer_notes: Optional[str] = None
    adjudication_status: str = "pending"
    exclusion_reason: Optional[str] = None
    duplicate_group_id: Optional[str] = None
    notes: Optional[str] = None

    # Prediction fields
    predicted_hazard: Optional[str] = None
    predicted_hazards: List[str] = field(default_factory=list)
    predicted_confidence: Optional[float] = None
    predicted_summary: Optional[str] = None
    predicted_limitations: Optional[str] = None
    error: Optional[str] = None


@dataclass
class EvaluationMetrics:
    """Rigorous evaluation metrics computed over ground-truth adjudicated samples."""

    total_samples: int
    labeled_samples: int
    unlabeled_samples: int
    excluded_samples: int
    classes: List[str]
    confusion_matrix: Dict[str, Dict[str, int]]  # [ground_truth][predicted] -> count
    per_class_precision: Dict[str, float]
    per_class_recall: Dict[str, float]
    per_class_f1: Dict[str, float]
    per_class_support: Dict[str, int]
    macro_f1: float
    weighted_f1: float
    accuracy: float
    wilson_ci_accuracy: Tuple[float, float]
    coverage_rate: float  # Percentage of non-indeterminate predictions
    wilson_ci_coverage: Tuple[float, float]
    determinate_accuracy: Optional[float] = None  # Accuracy computed solely on determinate predictions
    inter_annotator_agreement: Optional[Dict[str, Any]] = None  # Cohen's Kappa, percent agreement
    multi_label_indicators: Optional[Dict[str, Any]] = None  # Precision/Recall/F1 for visible features
    stratified_by_quality: Optional[Dict[str, Dict[str, float]]] = None
    inference_failure_count: int = 0
    inference_failure_rate: float = 0.0
    safety_critical_under_call_count: int = 0
    safety_critical_under_call_rate: float = 0.0
    critical_false_negatives: List[Dict[str, Any]] = field(default_factory=list)


VALID_EXECUTION_STATUSES = {
    "success",
    "malformed_output",
    "rate_limit",
    "timeout",
    "abstention_indeterminate",
    "provider_error",
}

PROHIBITED_PREDICTION_FIELDS = {
    "adjudicated_label",
    "expert_ground_truth_hazard",
    "annotator_1_label",
    "annotator_2_label",
    "ground_truth_indicators",
    "annotator_1_id",
    "annotator_2_id",
    "reviewer_name",
    "review_status",
}


@dataclass
class EvaluationPredictionRecord:
    """An immutable record of model inference on an evaluation sample.

    Strictly separates model outputs from ground-truth human annotations.
    """
    candidate_id: str
    image_sha256: str
    split: str = "test"
    model_id: str = "gemini-3.5-flash"
    prompt_version: str = "v1.0"
    protocol_version: str = "Phase-2E-v1.0"
    run_timestamp: str = ""
    inference_parameters: Dict[str, Any] = field(default_factory=lambda: {"temperature": 0.0, "timeout_seconds": 30.0})
    execution_status: str = "success"
    raw_response: Optional[str] = None
    structured_output: Optional[Dict[str, Any]] = None
    predicted_hazard: Optional[str] = None
    predicted_hazards: List[str] = field(default_factory=list)
    predicted_confidence: Optional[float] = None
    predicted_summary: Optional[str] = None
    predicted_limitations: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: Optional[float] = None

    def __post_init__(self):
        if not self.run_timestamp:
            self.run_timestamp = datetime.now(timezone.utc).isoformat()
        if self.execution_status not in VALID_EXECUTION_STATUSES:
            raise ValueError(
                f"Invalid execution_status '{self.execution_status}'. "
                f"Must be one of {sorted(list(VALID_EXECUTION_STATUSES))}"
            )


@dataclass
class EvaluationRunManifest:
    """Immutable manifest for an entire evaluation execution run."""
    run_id: str
    protocol_version: str
    dataset_manifest_path: str
    dataset_manifest_sha256: str
    model_id: str
    prompt_version: str
    inference_parameters: Dict[str, Any]
    started_at: str
    completed_at: Optional[str] = None
    total_samples: int = 0
    successful_inferences: int = 0
    failed_inferences: int = 0
    predictions: List[EvaluationPredictionRecord] = field(default_factory=list)
    notes: Optional[str] = None


class EvaluationResultLogger:
    """Logs and exports evaluation run predictions while enforcing strict separation from ground truth."""

    @staticmethod
    def compute_manifest_hash(file_path: Union[str, Path]) -> str:
        """Compute SHA-256 digest of a manifest file."""
        return VLMEvaluationHarness.compute_sha256(file_path)

    @classmethod
    def create_run_manifest(
        cls,
        dataset_manifest_path: Union[str, Path],
        model_id: str = "gemini-3.5-flash",
        prompt_version: str = "v1.0",
        protocol_version: str = "Phase-2E-v1.0",
        inference_parameters: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> EvaluationRunManifest:
        """Initialize an immutable evaluation run manifest with frozen dataset SHA-256."""
        path = Path(dataset_manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset manifest not found at: {path}")

        manifest_sha = cls.compute_manifest_hash(path)
        params = {"temperature": 0.0, "timeout_seconds": 30.0}
        if inference_parameters:
            params.update(inference_parameters)

        run_id = f"eval_{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        return EvaluationRunManifest(
            run_id=run_id,
            protocol_version=protocol_version,
            dataset_manifest_path=str(path.resolve()),
            dataset_manifest_sha256=manifest_sha,
            model_id=model_id,
            prompt_version=prompt_version,
            inference_parameters=params,
            started_at=now_str,
            notes=notes,
        )

    @staticmethod
    def validate_prediction_separation(data: Union[EvaluationPredictionRecord, Dict[str, Any]]) -> None:
        """Verify that prediction records do not contain or attempt to overwrite ground-truth fields.

        Raises:
            PredictionSeparationViolationError: If ground-truth fields are detected.
        """
        if isinstance(data, dict):
            keys = set(data.keys())
            prohibited = keys.intersection(PROHIBITED_PREDICTION_FIELDS)
            if prohibited:
                raise PredictionSeparationViolationError(
                    f"Prediction-annotation separation violation! Prohibited ground-truth fields "
                    f"detected in prediction payload: {sorted(list(prohibited))}. "
                    f"Model predictions must never write to or overwrite ground truth."
                )
        if hasattr(data, "__dict__"):
            overlap = set(data.__dict__.keys()).intersection(PROHIBITED_PREDICTION_FIELDS)
            if overlap:
                raise PredictionSeparationViolationError(
                    f"Prediction-annotation separation violation! Prohibited ground-truth fields "
                    f"found in record: {sorted(list(overlap))}."
                )

    @classmethod
    def log_prediction(
        cls,
        manifest: EvaluationRunManifest,
        prediction: EvaluationPredictionRecord,
        sample: Optional[VLMEvaluationSample] = None,
    ) -> None:
        """Log a prediction record into the run manifest with separation and identity validation."""
        cls.validate_prediction_separation(prediction)

        if sample is not None:
            if sample.image_id != prediction.candidate_id:
                raise ValueError(
                    f"Candidate ID mismatch between sample '{sample.image_id}' "
                    f"and prediction record '{prediction.candidate_id}'"
                )
            if sample.image_sha256 and prediction.image_sha256:
                if sample.image_sha256.strip().lower() != prediction.image_sha256.strip().lower():
                    raise ManifestHashMismatchError(
                        f"Image hash mismatch for candidate '{prediction.candidate_id}'. "
                        f"Sample hash '{sample.image_sha256}' != prediction hash '{prediction.image_sha256}'"
                    )

        manifest.predictions.append(prediction)
        manifest.total_samples += 1
        if prediction.execution_status == "success":
            manifest.successful_inferences += 1
        else:
            manifest.failed_inferences += 1

    @classmethod
    def verify_manifest_integrity(
        cls,
        manifest: EvaluationRunManifest,
        current_dataset_path: Union[str, Path],
        raise_on_mismatch: bool = True,
    ) -> bool:
        """Verify that current dataset manifest file has not been altered since run creation."""
        curr_hash = cls.compute_manifest_hash(current_dataset_path)
        is_match = (curr_hash == manifest.dataset_manifest_sha256)
        if not is_match and raise_on_mismatch:
            raise ManifestHashMismatchError(
                f"Dataset manifest hash mismatch! Manifest recorded hash '{manifest.dataset_manifest_sha256}', "
                f"but current file has hash '{curr_hash}'. Dataset has been modified after run initialization."
            )
        return is_match

    @staticmethod
    def export_run_json(manifest: EvaluationRunManifest, output_path: Union[str, Path]) -> Path:
        """Export the complete evaluation run manifest and predictions to JSON."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not manifest.completed_at:
            manifest.completed_at = datetime.now(timezone.utc).isoformat()

        def _to_dict(obj):
            if hasattr(obj, "__dict__"):
                return {k: _to_dict(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [_to_dict(v) for v in obj]
            elif isinstance(obj, dict):
                return {k: _to_dict(v) for k, v in obj.items()}
            return obj

        data = _to_dict(manifest)
        with open(path, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return path

    @staticmethod
    def export_predictions_csv(manifest: EvaluationRunManifest, output_path: Union[str, Path]) -> Path:
        """Export only prediction fields to CSV, strictly omitting human ground-truth labels."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "candidate_id",
            "image_sha256",
            "split",
            "model_id",
            "prompt_version",
            "protocol_version",
            "run_timestamp",
            "execution_status",
            "predicted_hazard",
            "predicted_hazards",
            "predicted_confidence",
            "predicted_summary",
            "predicted_limitations",
            "error_message",
            "latency_ms",
        ]

        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in manifest.predictions:
                writer.writerow({
                    "candidate_id": p.candidate_id,
                    "image_sha256": p.image_sha256,
                    "split": p.split,
                    "model_id": p.model_id,
                    "prompt_version": p.prompt_version,
                    "protocol_version": p.protocol_version,
                    "run_timestamp": p.run_timestamp,
                    "execution_status": p.execution_status,
                    "predicted_hazard": p.predicted_hazard or "",
                    "predicted_hazards": ";".join(p.predicted_hazards),
                    "predicted_confidence": p.predicted_confidence if p.predicted_confidence is not None else "",
                    "predicted_summary": p.predicted_summary or "",
                    "predicted_limitations": p.predicted_limitations or "",
                    "error_message": p.error_message or "",
                    "latency_ms": p.latency_ms if p.latency_ms is not None else "",
                })

        return path


ALLOWED_ANNOTATION_QUALITIES = {"high_resolution", "adequate", "low_resolution", "occluded_or_degraded"}
ALLOWED_REVIEWER_LABELS = {"none", "low", "moderate", "medium", "high", "critical", "indeterminate"}
ALLOWED_CONFIDENCE_LEVELS = {"certain", "probable", "tentative", "indeterminate"}
ALLOWED_REVIEW_STATUSES = {"draft", "completed", "adjudicated", "rejected", "pending_review"}
CONTROLLED_OBSERVABLE_INDICATORS = {
    "fresh_scarp",
    "displaced_soil",
    "displaced_rock",
    "rockfall_debris",
    "tension_cracks",
    "ground_deformation",
    "debris_flow_deposit",
    "channel_obstruction",
    "road_damage_slope_movement",
    "stable_slope",
    "negative_control",
    "water_seepage",
    "vegetated_relict_scarp",
    "occluded_or_degraded",
    "insufficient_evidence",
}
PROHIBITED_AI_ANNOTATOR_PREFIXES = (
    "gemma", "gemini", "ollama", "gpt", "claude", "ai_", "model_", "bot_", "auto_"
)


@dataclass
class AnnotationRecord:
    """Represents a human geotechnical annotation for a field photograph."""
    candidate_id: str
    image_sha256: str
    annotator_id: str
    annotation_version: str
    observable_indicators: List[str]
    image_quality: str
    reviewer_label: str
    confidence: str
    evidence_notes: str
    review_status: str
    reviewed_at: str


class AnnotationValidator:
    """Validates human geotechnical annotations against schema, manifest, and scientific honesty rules."""

    @staticmethod
    def validate_record(
        rec: AnnotationRecord,
        known_candidates: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """Validate an individual annotation record.

        known_candidates: Optional mapping from candidate_id to verified image_sha256.
        Returns list of error messages (empty if valid).
        """
        errors = []
        if not rec.candidate_id or not rec.candidate_id.strip():
            errors.append("Missing candidate_id")

        if not rec.annotation_version or not rec.annotation_version.strip():
            errors.append(f"Sample {rec.candidate_id}: Missing annotation_version")

        # Prohibit AI model identifiers as human annotators
        aid = (rec.annotator_id or "").strip().lower()
        if not aid and rec.review_status not in ("draft", "pending_review"):
            errors.append(f"Sample {rec.candidate_id}: Completed or adjudicated annotations require non-empty annotator_id")
        elif aid:
            for prefix in PROHIBITED_AI_ANNOTATOR_PREFIXES:
                if aid.startswith(prefix):
                    raise AIAnnotatorProhibitedError(
                        f"Prohibited AI annotator '{rec.annotator_id}' for candidate {rec.candidate_id}. "
                        f"AI model predictions must NEVER be recorded as ground-truth annotator reviews."
                    )

        # Validate known candidate and hash
        if known_candidates is not None and rec.candidate_id:
            if rec.candidate_id not in known_candidates:
                errors.append(f"Referenced candidate_id '{rec.candidate_id}' does not exist in candidate manifest")
            else:
                expected_sha = known_candidates[rec.candidate_id]
                if rec.image_sha256 and expected_sha and rec.image_sha256.strip().lower() != expected_sha.strip().lower():
                    errors.append(
                        f"Sample {rec.candidate_id}: Hash mismatch! Record has '{rec.image_sha256}', "
                        f"expected manifest hash '{expected_sha}'"
                    )

        # Validate review_status
        status = (rec.review_status or "").strip().lower()
        if status and status not in ALLOWED_REVIEW_STATUSES:
            errors.append(f"Sample {rec.candidate_id}: Invalid review_status '{rec.review_status}'. Allowed: {ALLOWED_REVIEW_STATUSES}")

        # Enforce consistency between review_status and reviewer_label
        label = (rec.reviewer_label or "").strip().lower()
        if status == "adjudicated":
            if not label or label in ("pending", "unknown"):
                errors.append(f"Sample {rec.candidate_id}: Marked 'adjudicated' but reviewer_label is empty or pending")
        elif status == "pending_review":
            if label and label not in ("pending", "indeterminate", ""):
                errors.append(f"Sample {rec.candidate_id}: Marked 'pending_review' but has non-empty label '{label}'")

        if label and label not in ALLOWED_REVIEWER_LABELS and label != "pending":
            errors.append(f"Sample {rec.candidate_id}: Invalid reviewer_label '{rec.reviewer_label}'. Allowed: {ALLOWED_REVIEWER_LABELS}")

        # Validate image_quality if populated
        quality = (rec.image_quality or "").strip().lower()
        if quality and quality not in ALLOWED_ANNOTATION_QUALITIES:
            errors.append(f"Sample {rec.candidate_id}: Invalid image_quality '{rec.image_quality}'. Allowed: {ALLOWED_ANNOTATION_QUALITIES}")

        # Validate confidence if populated
        conf = (rec.confidence or "").strip().lower()
        if conf and conf not in ALLOWED_CONFIDENCE_LEVELS:
            errors.append(f"Sample {rec.candidate_id}: Invalid confidence '{rec.confidence}'. Allowed: {ALLOWED_CONFIDENCE_LEVELS}")

        return errors

    @classmethod
    def load_and_validate_annotations_csv(
        cls,
        csv_path: Union[str, Path],
        known_candidates: Optional[Dict[str, str]] = None,
    ) -> Tuple[List[AnnotationRecord], List[str]]:
        """Parse annotation CSV, checking duplicates, schema, and candidate validity.

        Returns (records, all_errors).
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Annotation file not found at: {path}")

        records: List[AnnotationRecord] = []
        all_errors: List[str] = []
        seen_keys: Set[Tuple[str, str, str]] = set()

        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            required_cols = [
                "candidate_id", "image_sha256", "annotator_id", "annotation_version",
                "observable_indicators", "image_quality", "reviewer_label",
                "confidence", "evidence_notes", "review_status", "reviewed_at"
            ]
            for col in required_cols:
                if reader.fieldnames is None or col not in reader.fieldnames:
                    all_errors.append(f"Missing required annotation header: '{col}'")
            if all_errors:
                return ([], all_errors)

            for i, row in enumerate(reader, start=2):
                cid = row.get("candidate_id", "").strip()
                aid = row.get("annotator_id", "").strip()
                ver = row.get("annotation_version", "").strip()

                # Duplicate record detection
                record_key = (cid, aid, ver)
                if cid and aid and ver and record_key in seen_keys:
                    all_errors.append(
                        f"Line {i}: Duplicate annotation record for candidate '{cid}', "
                        f"annotator '{aid}', version '{ver}'"
                    )
                seen_keys.add(record_key)

                raw_indicators = [
                    ind.strip().lower()
                    for ind in (row.get("observable_indicators") or "").split(";")
                    if ind.strip()
                ]

                rec = AnnotationRecord(
                    candidate_id=cid,
                    image_sha256=row.get("image_sha256", "").strip(),
                    annotator_id=aid,
                    annotation_version=ver,
                    observable_indicators=raw_indicators,
                    image_quality=row.get("image_quality", "").strip(),
                    reviewer_label=row.get("reviewer_label", "").strip(),
                    confidence=row.get("confidence", "").strip(),
                    evidence_notes=row.get("evidence_notes", "").strip(),
                    review_status=row.get("review_status", "").strip(),
                    reviewed_at=row.get("reviewed_at", "").strip(),
                )

                rec_errors = cls.validate_record(rec, known_candidates=known_candidates)
                if rec_errors:
                    for e in rec_errors:
                        all_errors.append(f"Line {i} ({cid}): {e}")
                records.append(rec)

        return (records, all_errors)

    @classmethod
    def generate_blank_annotation_template(
        cls,
        candidates_manifest_path: Union[str, Path],
        output_template_path: Union[str, Path],
        annotation_version: str = "v1.0",
        downloaded_only: bool = True,
    ) -> int:
        """Generate a clean annotation CSV template with verified non-label metadata.

        All reviewer judgment fields remain strictly empty with review_status='pending_review'.
        """
        in_p = Path(candidates_manifest_path)
        out_p = Path(output_template_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        rows = []
        with open(in_p, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if downloaded_only and r.get("download_status") != "downloaded":
                    continue
                rows.append({
                    "candidate_id": r["candidate_id"],
                    "image_sha256": r.get("image_sha256", ""),
                    "annotator_id": "",
                    "annotation_version": annotation_version,
                    "observable_indicators": "",
                    "image_quality": "",
                    "reviewer_label": "",
                    "confidence": "",
                    "evidence_notes": "",
                    "review_status": "pending_review",
                    "reviewed_at": "",
                })

        fieldnames = [
            "candidate_id", "image_sha256", "annotator_id", "annotation_version",
            "observable_indicators", "image_quality", "reviewer_label",
            "confidence", "evidence_notes", "review_status", "reviewed_at"
        ]
        with open(out_p, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return len(rows)


class VLMEvaluationHarness:
    """Loads benchmark datasets, executes model evaluation, and computes metrics."""

    @staticmethod
    def compute_sha256(file_path: Union[str, Path]) -> str:
        """Compute SHA-256 digest of file bytes."""
        path = Path(file_path)
        if not path.exists():
            return ""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest().lower()

    @staticmethod
    def compute_wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
        """Compute Wilson score interval for binomial proportions.

        Robust for small sample sizes and boundary cases (k=0, k=n).
        """
        if n <= 0:
            return (0.0, 0.0)
        # z for 95% confidence is ~1.95996
        z = 1.959964 if math.isclose(confidence, 0.95, rel_tol=1e-2) else 1.644853
        p = k / n
        denom = 1.0 + (z**2) / n
        center = (p + (z**2) / (2 * n)) / denom
        margin = (z * math.sqrt((p * (1.0 - p) + (z**2) / (4 * n)) / n)) / denom
        lower = max(0.0, round(center - margin, 4))
        upper = min(1.0, round(center + margin, 4))
        return (lower, upper)

    @staticmethod
    def validate_dataset_provenance(dataset_id: str) -> Dict[str, Any]:
        """Validate dataset against the provenance register.

        Raises:
            UnverifiedLicenseError: If license is unverified/blank.
            UnsupportedModalityError: If modality is incompatible with Gemma field VLM.
            KeyError: If dataset_id is unknown.
        """
        record = DATASET_PROVENANCE_REGISTRY.get(dataset_id)
        if not record:
            raise KeyError(f"Dataset '{dataset_id}' not found in provenance register.")

        if not record.get("license_verified", False):
            raise UnverifiedLicenseError(
                f"Dataset '{dataset_id}' has unverified or blank license terms ({record.get('license_status')}). "
                f"Per PahaarPulse research policy, datasets cannot be downloaded, ingested, or used until usage permissions are verified."
            )

        if not record.get("compatible_with_gemma_field_vlm", False):
            raise UnsupportedModalityError(
                f"Dataset '{dataset_id}' is incompatible with Gemma field VLM. "
                f"{record.get('suitability_limitations')}"
            )

        return record

    @staticmethod
    def validate_sample_modality(file_path: Union[str, Path]) -> str:
        """Validate that the file path corresponds to a supported optical field photograph.

        Raises:
            UnsupportedModalityError: If the file is remote-sensing multispectral data or unsupported format.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext in UNSUPPORTED_REMOTE_SENSING_EXTENSIONS:
            raise UnsupportedModalityError(
                f"Unsupported image modality '{ext}' for file {path.name}. "
                f"Multispectral satellite bands and raster grids (such as Landslide4Sense) require specialized remote-sensing "
                f"segmentation pipelines and cannot be processed by the Gemma field-photo VLM."
            )

        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise UnsupportedModalityError(
                f"Unsupported file format '{ext}' for file {path.name}. "
                f"Supported optical field photograph formats: {sorted(list(ALLOWED_IMAGE_EXTENSIONS))}."
            )

        return ext

    @staticmethod
    def validate_annotation_schema(headers: List[str], row_sample: Optional[Dict[str, str]] = None) -> None:
        """Validate dataset headers and values against categorical hazard triage schema.

        Raises:
            MismatchedAnnotationSchemaError: If dataset contains binary masks, bounding boxes, or non-geotechnical schemas.
        """
        headers_lower = {h.strip().lower() for h in headers}

        # Check for remote sensing segmentation or detection headers
        incompatible_headers = {
            "mask_path", "segmentation_mask", "mask", "bbox", "bbox_coords",
            "polygon", "wkt", "pixel_mask", "binary_mask"
        }
        intersect = headers_lower.intersection(incompatible_headers)
        if intersect:
            raise MismatchedAnnotationSchemaError(
                f"Mismatched annotation schema: Dataset provides spatial mask/bounding box columns {sorted(list(intersect))} "
                f"instead of categorical hazard triage levels. Remote-sensing segmentation masks cannot be silently converted to "
                f"geotechnical hazard severity triage."
            )

        # Check for binary 0/1 labels in ground truth
        if row_sample:
            gt = (
                row_sample.get("adjudicated_label")
                or row_sample.get("expert_ground_truth_hazard", "")
            ).strip().lower()
            if gt in ("0", "1", "true", "false", "landslide", "non_landslide"):
                raise MismatchedAnnotationSchemaError(
                    f"Mismatched annotation schema: Detected binary segmentation/detection label '{gt}'. "
                    f"PahaarPulse Gemma evaluation requires categorical geotechnical triage classes "
                    f"('low', 'moderate', 'high', 'critical', 'indeterminate')."
                )

    @staticmethod
    def validate_split_integrity(samples: List[VLMEvaluationSample]) -> None:
        """Verify that identical image hashes and event groups do not leak across evaluation splits.

        Raises:
            DataLeakageError: If an image SHA-256 or group ID is present in more than one split.
        """
        split_hashes: Dict[str, Set[str]] = {"train": set(), "dev": set(), "test": set()}
        split_groups: Dict[str, Set[str]] = {"train": set(), "dev": set(), "test": set()}

        for s in samples:
            h = (s.image_sha256 or "").strip().lower()
            split = s.split.lower()
            if split not in ALLOWED_SPLITS:
                split = "test"

            # Check SHA-256 duplicate leakage
            if h:
                for other_split, hash_set in split_hashes.items():
                    if other_split != split and h in hash_set:
                        raise DataLeakageError(
                            f"Data leakage detected! Image hash '{h[:12]}...' (sample {s.image_id}) is present in both "
                            f"'{split}' and '{other_split}' splits. All near-duplicates and photos from the same event "
                            f"must reside strictly within a single split."
                        )
                split_hashes[split].add(h)

            # Check duplicate/event group leakage
            grp = (s.duplicate_group_id or "").strip()
            if grp and grp.upper() not in ("UNKNOWN_EVENT_OR_SITE", "UNKNOWN", "NONE", "N/A", "NULL"):
                for other_split, grp_set in split_groups.items():
                    if other_split != split and grp in grp_set:
                        raise DataLeakageError(
                            f"Event/site-group leakage detected! Duplicate/event group '{grp}' (sample {s.image_id}) "
                            f"spans both '{split}' and '{other_split}' splits. All photos from the same physical site "
                            f"or event cluster must be assigned to the same split."
                        )
                split_groups[split].add(grp)

    @staticmethod
    def load_dataset_csv(
        csv_path: Union[str, Path],
        base_dir: Optional[Union[str, Path]] = None,
        split_filter: Optional[str] = None,
        strict_permissions: bool = False,
        strict_ground_truth: bool = False,
    ) -> List[VLMEvaluationSample]:
        """Parse dataset CSV with schema validation, permission checks, and split isolation."""
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Evaluation dataset CSV not found at {path}")

        samples: List[VLMEvaluationSample] = []
        base = Path(base_dir) if base_dir else path.parent

        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = None

            for row in reader:
                if not row or not any(row):
                    continue
                first_cell = row[0].strip()
                if first_cell.startswith("#"):
                    continue

                if headers is None:
                    headers = [c.strip().lower() for c in row]
                    VLMEvaluationHarness.validate_annotation_schema(headers)
                    continue

                row_dict = {headers[i]: row[i].strip() for i in range(min(len(headers), len(row)))}
                VLMEvaluationHarness.validate_annotation_schema(headers, row_dict)

                # Resolve ground truth from either new 'adjudicated_label' or legacy 'expert_ground_truth_hazard'
                gt_raw = (
                    row_dict.get("adjudicated_label")
                    or row_dict.get("expert_ground_truth_hazard")
                    or ""
                ).strip().lower()
                adj_status = row_dict.get("adjudication_status", "pending").strip().lower()

                gt_hazard: Optional[str] = None
                if gt_raw:
                    if gt_raw not in VALID_HAZARD_CLASSES:
                        raise InvalidLabelError(
                            f"Invalid hazard label '{gt_raw}' in sample {row_dict.get('image_id')}. "
                            f"Must be one of: {VALID_HAZARD_CLASSES}."
                        )
                    gt_hazard = gt_raw

                # Enforce adjudication consistency
                if adj_status == "adjudicated" and not gt_hazard:
                    raise MissingAdjudicationError(
                        f"Sample {row_dict.get('image_id')} is marked as 'adjudicated' but has no adjudicated label."
                    )

                # Check permissions and source if strict_permissions requested
                lic_ref = row_dict.get("license_or_permission_reference", "").strip()
                source_val = row_dict.get("source", "").strip()
                if strict_permissions:
                    if not source_val:
                        raise InvalidSourceError(
                            f"Sample {row_dict.get('image_id')} lacks a documented source identifier. "
                            f"Source provenance is required under strict benchmark policy."
                        )
                    if not lic_ref or lic_ref.lower() in ("unverified", "blank", "pending-verification", "none"):
                        raise MissingPermissionError(
                            f"Sample {row_dict.get('image_id')} lacks verified legal permissions or license reference "
                            f"(found: '{lic_ref}'). Model evaluation cannot proceed without documented data rights."
                        )

                split = row_dict.get("split", "test").strip().lower()
                if split not in ALLOWED_SPLITS:
                    split = "test"

                # Check strict ground truth for frozen test split
                if strict_ground_truth and split == "test":
                    if adj_status != "adjudicated" or not gt_hazard:
                        raise MissingExpertGroundTruthError(
                            f"Sample {row_dict.get('image_id')} in 'test' split has unadjudicated ground truth "
                            f"(status: '{adj_status}'). Unadjudicated or pending samples are prohibited from frozen test benchmarks."
                        )

                # Parse observable indicators
                raw_indicators = row_dict.get("observable_indicators") or row_dict.get("visible_indicators", "")
                indicators = [ind.strip().lower() for ind in raw_indicators.split(";") if ind.strip()]

                # Resolve image path (with fallback to project root and data directory)
                img_path_raw = (
                    row_dict.get("image_path_or_controlled_reference")
                    or row_dict.get("image_path", "")
                )
                if Path(img_path_raw).is_absolute():
                    img_path = img_path_raw
                else:
                    cand_path = (base / img_path_raw).resolve()
                    if cand_path.exists():
                        img_path = str(cand_path)
                    else:
                        # Fallback to project root / data resolution
                        project_root = Path(__file__).resolve().parent.parent.parent.parent
                        proj_cand = (project_root / img_path_raw).resolve()
                        proj_data_cand = (project_root / "data" / img_path_raw).resolve()
                        if proj_cand.exists():
                            img_path = str(proj_cand)
                        elif proj_data_cand.exists():
                            img_path = str(proj_data_cand)
                        else:
                            img_path = str(cand_path)

                # Validate modality on extension
                raw_ext = Path(img_path_raw).suffix.lower()
                if raw_ext in UNSUPPORTED_REMOTE_SENSING_EXTENSIONS:
                    raise UnsupportedModalityError(
                        f"Unsupported image modality '{raw_ext}' for sample {row_dict.get('image_id')}. "
                        f"Remote-sensing multispectral tensors (e.g. Landslide4Sense) require separate satellite segmentation pipelines."
                    )

                if split_filter and split != split_filter.lower():
                    continue

                dup_grp = (
                    row_dict.get("duplicate_group_id")
                    or row_dict.get("event_site_group")
                    or row_dict.get("duplicate_group")
                    or row_dict.get("site_group_id")
                    or None
                )

                sample = VLMEvaluationSample(
                    image_id=row_dict.get("image_id", f"sample_{len(samples)+1}"),
                    image_path=img_path,
                    source=source_val,
                    image_sha256=row_dict.get("image_sha256") or None,
                    license_reference=lic_ref or None,
                    capture_date=row_dict.get("capture_date") or None,
                    region=row_dict.get("region") or None,
                    image_quality=row_dict.get("image_quality", "adequate").lower(),
                    split=split,
                    ground_truth_hazard=gt_hazard,
                    ground_truth_indicators=indicators,
                    annotator_1_id=row_dict.get("annotator_1_id") or None,
                    annotator_1_label=row_dict.get("annotator_1_label", "").lower() or None,
                    annotator_2_id=row_dict.get("annotator_2_id") or None,
                    annotator_2_label=row_dict.get("annotator_2_label", "").lower() or None,
                    reviewer_name=row_dict.get("reviewer_name") or None,
                    reviewer_notes=row_dict.get("reviewer_notes") or row_dict.get("notes") or None,
                    adjudication_status=adj_status,
                    exclusion_reason=row_dict.get("exclusion_reason") or None,
                    duplicate_group_id=dup_grp,
                    notes=row_dict.get("notes") or None,
                )
                samples.append(sample)

        # Validate cross-split leakage across loaded samples
        VLMEvaluationHarness.validate_split_integrity(samples)

        return samples

    @staticmethod
    def compute_inter_annotator_agreement(samples: List[VLMEvaluationSample]) -> Optional[Dict[str, Any]]:
        """Compute Cohen's Kappa and observed percent agreement across double-annotated samples."""
        pairs = [
            (s.annotator_1_label, s.annotator_2_label)
            for s in samples
            if s.annotator_1_label and s.annotator_2_label
        ]
        if not pairs:
            return None

        n = len(pairs)
        classes = list(VALID_HAZARD_CLASSES)
        cm: Dict[str, Dict[str, int]] = {c1: {c2: 0 for c2 in classes} for c1 in classes}

        agree_count = 0
        for l1, l2 in pairs:
            if l1 in cm and l2 in cm[l1]:
                cm[l1][l2] += 1
            if l1 == l2:
                agree_count += 1

        po = agree_count / n

        # Expected chance agreement Pe
        pe = 0.0
        for c in classes:
            r1 = sum(cm[c][c2] for c2 in classes) / n
            r2 = sum(cm[c1][c] for c1 in classes) / n
            pe += r1 * r2

        kappa = (po - pe) / (1.0 - pe) if not math.isclose(pe, 1.0) else 1.0

        if kappa >= 0.70:
            interp = "High reliability (qualified for model validation)"
        elif kappa >= 0.50:
            interp = "Moderate reliability (requires focused category review)"
        else:
            interp = "Low / Poor reliability (unacceptable for model benchmarking)"

        return {
            "double_annotated_count": n,
            "observed_agreement": round(po, 4),
            "cohens_kappa": round(kappa, 4),
            "chance_agreement": round(pe, 4),
            "interpretation": interp,
        }

    @staticmethod
    async def evaluate_sample(
        sample: VLMEvaluationSample,
        provider: AnalysisProvider,
    ) -> VLMEvaluationSample:
        """Run inference on a single sample using the provided AnalysisProvider."""
        img_file = Path(sample.image_path)
        if not img_file.exists():
            sample.error = f"Image file not found: {sample.image_path}"
            sample.predicted_hazard = "indeterminate"
            return sample

        try:
            VLMEvaluationHarness.validate_sample_modality(img_file)
        except UnsupportedModalityError as me:
            sample.error = str(me)
            sample.predicted_hazard = "indeterminate"
            return sample

        try:
            with open(img_file, "rb") as f:
                photo_bytes = f.read()

            ext = img_file.suffix.lower()
            mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
            mime = mime_map.get(ext, "image/jpeg")

            output: GemmaHazardOutput = await provider.analyze(
                notes=f"Evaluation Sample {sample.image_id}. Source: {sample.source}",
                location_name="Evaluation Site",
                photo_bytes=photo_bytes,
                photo_mime=mime,
            )

            sample.predicted_hazard = output.hazard_level
            sample.predicted_hazards = output.detected_hazards
            sample.predicted_confidence = output.confidence
            sample.predicted_summary = output.summary
            sample.predicted_limitations = output.limitations
            sample.error = None

        except GemmaProviderError as ge:
            sample.error = f"Provider error: {ge}"
            sample.predicted_hazard = "indeterminate"
        except Exception as e:
            sample.error = f"Unexpected evaluation error: {e}"
            sample.predicted_hazard = "indeterminate"

        return sample

    @staticmethod
    def compute_metrics(samples: List[VLMEvaluationSample]) -> Optional[EvaluationMetrics]:
        """Compute precision, recall, F1, Wilson CIs, inter-annotator agreement, and confusion matrix."""
        # Active evaluation set excludes samples marked as 'excluded'
        eval_samples = [s for s in samples if s.adjudication_status != "excluded"]
        excluded_count = len(samples) - len(eval_samples)

        labeled = [s for s in eval_samples if s.ground_truth_hazard and s.predicted_hazard]
        unlabeled = [s for s in eval_samples if not s.ground_truth_hazard]

        if not labeled:
            logger.info("No expert ground-truth labeled samples present in dataset. Skipping metric computation.")
            return None

        classes = list(VALID_HAZARD_CLASSES)
        cm: Dict[str, Dict[str, int]] = {true_c: {pred_c: 0 for pred_c in classes} for true_c in classes}

        total_correct = 0
        failure_count = sum(1 for s in eval_samples if s.error is not None)

        for s in labeled:
            t = s.ground_truth_hazard
            p = s.predicted_hazard
            if t in cm and p in cm[t]:
                cm[t][p] += 1
            if t == p:
                total_correct += 1

        per_class_precision: Dict[str, float] = {}
        per_class_recall: Dict[str, float] = {}
        per_class_f1: Dict[str, float] = {}
        per_class_support: Dict[str, int] = {}

        for c in classes:
            tp = cm[c][c]
            support = sum(cm[c][p] for p in classes)
            predicted_as_c = sum(cm[t][c] for t in classes)

            per_class_support[c] = support

            prec = tp / predicted_as_c if predicted_as_c > 0 else 0.0
            rec = tp / support if support > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            per_class_precision[c] = round(prec, 4)
            per_class_recall[c] = round(rec, 4)
            per_class_f1[c] = round(f1, 4)

        active_classes = [c for c in classes if per_class_support[c] > 0]
        macro_f1 = (
            round(sum(per_class_f1[c] for c in active_classes) / len(active_classes), 4)
            if active_classes
            else 0.0
        )

        total_labeled = len(labeled)
        weighted_f1 = (
            round(sum(per_class_f1[c] * per_class_support[c] for c in classes) / total_labeled, 4)
            if total_labeled > 0
            else 0.0
        )

        overall_acc = round(total_correct / total_labeled, 4) if total_labeled > 0 else 0.0
        ci_acc = VLMEvaluationHarness.compute_wilson_ci(total_correct, total_labeled)

        # Coverage rate
        determinate_predictions = [s for s in labeled if s.predicted_hazard != "indeterminate"]
        coverage = round(len(determinate_predictions) / total_labeled, 4) if total_labeled > 0 else 0.0
        ci_cov = VLMEvaluationHarness.compute_wilson_ci(len(determinate_predictions), total_labeled)

        det_acc = None
        if determinate_predictions:
            det_correct = sum(1 for s in determinate_predictions if s.ground_truth_hazard == s.predicted_hazard)
            det_acc = round(det_correct / len(determinate_predictions), 4)

        # Inter-annotator agreement
        iaa = VLMEvaluationHarness.compute_inter_annotator_agreement(samples)

        # Multi-label indicator metrics (Target 1)
        multi_label = None
        samples_with_ind_gt = [s for s in labeled if s.ground_truth_indicators]
        if samples_with_ind_gt:
            tp_total, fp_total, fn_total = 0, 0, 0
            for s in samples_with_ind_gt:
                gt_set = set(s.ground_truth_indicators)
                pred_set = set(s.predicted_hazards)
                tp_total += len(gt_set.intersection(pred_set))
                fp_total += len(pred_set.difference(gt_set))
                fn_total += len(gt_set.difference(pred_set))

            p_ind = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
            r_ind = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
            f1_ind = (2 * p_ind * r_ind) / (p_ind + r_ind) if (p_ind + r_ind) > 0 else 0.0

            multi_label = {
                "samples_evaluated": len(samples_with_ind_gt),
                "precision": round(p_ind, 4),
                "recall": round(r_ind, 4),
                "f1_score": round(f1_ind, 4),
            }

        # Stratified results by image quality
        stratified = {}
        for q in ("excellent", "adequate", "degraded", "obscured"):
            q_samples = [s for s in labeled if s.image_quality == q]
            if len(q_samples) >= 2:
                q_correct = sum(1 for s in q_samples if s.ground_truth_hazard == s.predicted_hazard)
                stratified[q] = {
                    "count": len(q_samples),
                    "accuracy": round(q_correct / len(q_samples), 4),
                }

        fail_rate = round(failure_count / len(eval_samples), 4) if eval_samples else 0.0

        # Safety-critical under-call analysis (severe false negatives on high/critical slopes)
        under_calls = []
        for s in labeled:
            t = (s.ground_truth_hazard or "").lower()
            p = (s.predicted_hazard or "").lower()
            if t in ("critical", "high") and p in ("low", "moderate"):
                under_calls.append({
                    "image_id": s.image_id,
                    "ground_truth": t,
                    "predicted": p,
                    "image_sha256": s.image_sha256,
                })
        high_critical_total = sum(1 for s in labeled if (s.ground_truth_hazard or "").lower() in ("critical", "high"))
        under_call_rate = round(len(under_calls) / high_critical_total, 4) if high_critical_total > 0 else 0.0

        return EvaluationMetrics(
            total_samples=len(samples),
            labeled_samples=total_labeled,
            unlabeled_samples=len(unlabeled),
            excluded_samples=excluded_count,
            classes=classes,
            confusion_matrix=cm,
            per_class_precision=per_class_precision,
            per_class_recall=per_class_recall,
            per_class_f1=per_class_f1,
            per_class_support=per_class_support,
            macro_f1=macro_f1,
            weighted_f1=weighted_f1,
            accuracy=overall_acc,
            wilson_ci_accuracy=ci_acc,
            coverage_rate=coverage,
            wilson_ci_coverage=ci_cov,
            determinate_accuracy=det_acc,
            inter_annotator_agreement=iaa,
            multi_label_indicators=multi_label,
            stratified_by_quality=stratified if stratified else None,
            inference_failure_count=failure_count,
            inference_failure_rate=fail_rate,
            safety_critical_under_call_count=len(under_calls),
            safety_critical_under_call_rate=under_call_rate,
            critical_false_negatives=under_calls,
        )

    @staticmethod
    def format_metrics_report(metrics: Optional[EvaluationMetrics]) -> str:
        """Format a comprehensive Markdown evaluation summary report."""
        if metrics is None:
            return (
                "### VLM Evaluation Report\n\n"
                "> [!WARNING]\n"
                "> **No expert-reviewed ground-truth labels available.**\n"
                "> Zero metrics calculated. Accuracy, precision, recall, and F1 scores are withheld "
                "to prevent metric fabrication on unadjudicated field photographs."
            )

        lines = [
            "### VLM Geotechnical Evaluation Report",
            f"- **Total Dataset Samples:** {metrics.total_samples}",
            f"- **Adjudicated Ground-Truth Samples:** {metrics.labeled_samples}",
            f"- **Unlabeled / Pending Samples:** {metrics.unlabeled_samples}",
            f"- **Excluded Samples:** {metrics.excluded_samples}",
            f"- **Inference Failures (Network/Model Error):** {metrics.inference_failure_count} ({metrics.inference_failure_rate * 100:.2f}%)",
            "",
            "#### Overall Triage Metrics (Target 2)",
            f"- **Overall Accuracy:** {metrics.accuracy * 100:.2f}% (95% Wilson CI: [{metrics.wilson_ci_accuracy[0]*100:.1f}%, {metrics.wilson_ci_accuracy[1]*100:.1f}%])",
            f"- **Macro F1-Score:** {metrics.macro_f1:.4f}",
            f"- **Weighted F1-Score:** {metrics.weighted_f1:.4f}",
            f"- **Determinate Coverage Rate:** {metrics.coverage_rate * 100:.2f}% (95% Wilson CI: [{metrics.wilson_ci_coverage[0]*100:.1f}%, {metrics.wilson_ci_coverage[1]*100:.1f}%])",
        ]

        if metrics.determinate_accuracy is not None:
            lines.append(f"- **Determinate-Only Accuracy:** {metrics.determinate_accuracy * 100:.2f}%")

        if metrics.inter_annotator_agreement:
            iaa = metrics.inter_annotator_agreement
            lines.extend([
                "",
                "#### Inter-Annotator Agreement (Ground Truth Reliability)",
                f"- **Double-Annotated Evaluation Pairs:** {iaa['double_annotated_count']}",
                f"- **Observed Agreement ($P_o$):** {iaa['observed_agreement'] * 100:.2f}%",
                f"- **Cohen's Kappa (k):** {iaa['cohens_kappa']:.4f}",
                f"- **Reliability Status:** {iaa['interpretation']}",
            ])

        if metrics.multi_label_indicators:
            m = metrics.multi_label_indicators
            lines.extend([
                "",
                "#### Observable Indicators Multi-Label Performance (Target 1)",
                f"- **Indicator Precision:** {m['precision']:.4f}",
                f"- **Indicator Recall:** {m['recall']:.4f}",
                f"- **Indicator F1-Score:** {m['f1_score']:.4f}",
            ])

        if metrics.stratified_by_quality:
            lines.extend([
                "",
                "#### Stratified Performance by Image Quality",
                "| Quality Tier | Sample Count | Accuracy |",
                "| :--- | :---: | :---: |",
            ])
            for q, stat in metrics.stratified_by_quality.items():
                lines.append(f"| **`{q}`** | {stat['count']} | {stat['accuracy'] * 100:.2f}% |")

        lines.extend([
            "",
            "#### Per-Class Performance Breakdown",
            "| Hazard Class | Precision | Recall | F1-Score | Support (Ground Truth) |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])

        for c in metrics.classes:
            supp = metrics.per_class_support[c]
            prec = f"{metrics.per_class_precision[c]:.4f}" if supp > 0 else "-"
            rec = f"{metrics.per_class_recall[c]:.4f}" if supp > 0 else "-"
            f1 = f"{metrics.per_class_f1[c]:.4f}" if supp > 0 else "-"
            lines.append(f"| **`{c}`** | {prec} | {rec} | {f1} | {supp} |")

        lines.extend([
            "",
            "#### Safety-Critical Hazard Under-Call Analysis (High/Critical False Negatives)",
            f"- **Severe Under-Calls (True High/Critical Predicted as Low/Moderate):** {metrics.safety_critical_under_call_count}",
            f"- **Safety Under-Call Rate:** {metrics.safety_critical_under_call_rate * 100:.2f}%",
        ])
        if metrics.critical_false_negatives:
            lines.append("- **Flagged Dangerous Under-Calls:**")
            for fn in metrics.critical_false_negatives:
                lines.append(f"  - Candidate `{fn['image_id']}`: True `{fn['ground_truth']}` -> Predicted `{fn['predicted']}`")

        lines.extend([
            "",
            "#### Confusion Matrix (Rows = Ground Truth, Columns = Predicted)",
            f"| Ground Truth \\ Predicted | {' | '.join(metrics.classes)} |",
            f"| :--- | {' | '.join([':---:'] * len(metrics.classes))} |",
        ])

        for true_c in metrics.classes:
            row_vals = [str(metrics.confusion_matrix[true_c][pred_c]) for pred_c in metrics.classes]
            lines.append(f"| **`{true_c}`** | {' | '.join(row_vals)} |")

        lines.extend([
            "",
            "> [!NOTE]",
            "> **Geotechnical Boundary Reminder:** Reported model confidence reflects visual interpretation certainty, "
            "not a calibrated physical probability of future slope failure.",
        ])

        return "\n".join(lines)

    @staticmethod
    def export_results_csv(samples: List[VLMEvaluationSample], output_path: Union[str, Path]) -> None:
        """Export evaluated samples with model predictions and audit fields to CSV."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "image_id",
            "image_sha256",
            "image_path",
            "source",
            "split",
            "license_reference",
            "region",
            "image_quality",
            "expert_ground_truth_hazard",
            "ground_truth_indicators",
            "annotator_1_label",
            "annotator_2_label",
            "adjudication_status",
            "model_predicted_hazard",
            "model_predicted_hazards",
            "model_confidence",
            "model_summary",
            "model_limitations",
            "error",
            "exclusion_reason",
            "notes",
        ]

        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in samples:
                writer.writerow({
                    "image_id": s.image_id,
                    "image_sha256": s.image_sha256 or "",
                    "image_path": s.image_path,
                    "source": s.source,
                    "split": s.split,
                    "license_reference": s.license_reference or "",
                    "region": s.region or "",
                    "image_quality": s.image_quality,
                    "expert_ground_truth_hazard": s.ground_truth_hazard or "",
                    "ground_truth_indicators": ";".join(s.ground_truth_indicators),
                    "annotator_1_label": s.annotator_1_label or "",
                    "annotator_2_label": s.annotator_2_label or "",
                    "adjudication_status": s.adjudication_status,
                    "model_predicted_hazard": s.predicted_hazard or "",
                    "model_predicted_hazards": ";".join(s.predicted_hazards),
                    "model_confidence": s.predicted_confidence if s.predicted_confidence is not None else "",
                    "model_summary": s.predicted_summary or "",
                    "model_limitations": s.predicted_limitations or "",
                    "error": s.error or "",
                    "exclusion_reason": s.exclusion_reason or "",
                    "notes": s.notes or "",
                })
