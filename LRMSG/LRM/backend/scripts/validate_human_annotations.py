#!/usr/bin/env python3
"""Validation utility and CLI for PahaarPulse human annotation, pilot, and recruitment files.

Phase 2J / 2K / 2L / 2M: Human Annotation Pilot, Reviewer Operations & Submission Validation.

Supported Validation Modes:
1. 'pilot-selection': Validates pilot selection manifest (18 columns, all PENDING, physical files exist).
2. 'independent-annotation': Validates independent reviewer submissions (12 blinded columns, PENDING or COMPLETED).
3. 'adjudication': Validates expert adjudication submissions (13 columns, dual-reviewer source enforcement).
4. 'recruitment-tracker': Validates recruitment candidate pipeline tracker (13 columns, decision consistency).
5. 'reviewer': Backwards-compatible alias for reviewer and pilot workflows.
6. 'auto': Dispatches based on header signature.

Safety Invariants:
- Read-only execution by default (--dry-run).
- Enforces strict taxonomy across the 6 canonical categories.
- Optional --reject-synthetic flag to reject synthetic stubs in production mode.
- Verification function verify_pilot_launch_gate() evaluates operational transition criteria.
- Structural verification only: does not imply that human reviews have been conducted or that benchmark inference is unlocked.

Usage:
    python backend/scripts/validate_human_annotations.py --file <path> [--mode auto|pilot-selection|independent-annotation|adjudication|recruitment-tracker] [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

# Project root calculation
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

DEFAULT_CANDIDATE_INDEX = (
    PROJECT_ROOT / "docs" / "gemma-local-vision" / "evaluation" / "phase_2i_annotation_package" / "candidate_index.csv"
)

CANONICAL_CATEGORIES: Set[str] = {
    "ACUTE_SLOPE_FAILURE_OR_DEBRIS",
    "PRECURSOR_INSTABILITY_INDICATOR",
    "INTACT_ENGINEERING_CONTROL",
    "CONTEXTUAL_TERRAIN_LANDSCAPE",
    "UNCERTAIN_INSUFFICIENT_CONTEXT",
    "UNUSABLE_OUT_OF_SCOPE",
}

ALLOWED_CONFIDENCES: Set[str] = {"HIGH", "MEDIUM", "LOW"}

ALLOWED_QUALITY_LIMITATIONS: Set[str] = {
    "NONE",
    "BLURRED",
    "DISTANT",
    "LOW_CONTRAST",
    "OCCLUDED",
}

REVIEWER_STATUSES: Set[str] = {"PENDING", "COMPLETED"}

ADJUDICATION_CONSENSUS_STATUSES: Set[str] = {
    "PENDING",
    "AGREED_CONSENSUS",
    "ADJUDICATED_RESOLVED",
    "FLAGGED_DISPUTED_INSUFFICIENT_CONTEXT",
}

REQUIRED_REVIEWER_COLUMNS: List[str] = [
    "annotation_id",
    "image_filename",
    "reviewer_id",
    "review_timestamp",
    "primary_category",
    "confidence_level",
    "observable_indicators",
    "image_quality_limitations",
    "geomorphic_rationale",
    "requires_adjudication",
    "review_status",
    "protocol_version",
]

REQUIRED_PILOT_SELECTION_COLUMNS: List[str] = [
    "pilot_batch_id",
    "annotation_id",
    "candidate_id",
    "image_filename",
    "active_image_path",
    "site_event_group_id",
    "site_event_group_name",
    "target_category_rationale",
    "review_status",
    "reviewer_id",
    "review_timestamp",
    "primary_category",
    "confidence_level",
    "observable_indicators",
    "image_quality_limitations",
    "geomorphic_rationale",
    "requires_adjudication",
    "protocol_version",
]

REQUIRED_ADJUDICATION_COLUMNS: List[str] = [
    "annotation_id",
    "image_filename",
    "adjudicator_id",
    "adjudication_timestamp",
    "reviewer_1_id",
    "reviewer_1_category",
    "reviewer_2_id",
    "reviewer_2_category",
    "disagreement_detected",
    "adjudicated_category",
    "adjudication_rationale",
    "consensus_status",
    "protocol_version",
]

REQUIRED_RECRUITMENT_TRACKER_COLUMNS: List[str] = [
    "candidate_ref",
    "contact_status",
    "screening_completed",
    "degree_verified",
    "cv_verified",
    "assigned_tier",
    "qualification_decision",
    "consent_status",
    "coi_flag",
    "pilot_available",
    "full_cohort_available",
    "assigned_reviewer_id",
    "next_action",
]

# Columns forbidden in independent reviewer forms to prevent unblinding
PROHIBITED_REVIEWER_COLUMNS: Set[str] = {
    "pilot_batch_id",
    "candidate_id",
    "target_category_rationale",
    "gemma_prediction",
    "model_prediction",
    "search_query",
    "site_event_group_id",
    "site_event_group_name",
}


@dataclass
class ValidationReport:
    """Detailed validation results report."""
    file_path: str
    mode: str
    total_rows: int = 0
    valid_rows: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_run: bool = True

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, line_num: Optional[int], msg: str) -> None:
        loc = f"Line {line_num}: " if line_num is not None else ""
        self.errors.append(f"{loc}{msg}")

    def add_warning(self, line_num: Optional[int], msg: str) -> None:
        loc = f"Line {line_num}: " if line_num is not None else ""
        self.warnings.append(f"{loc}{msg}")


class HumanAnnotationValidator:
    """Validates human reviewer, pilot selection, adjudication, and recruitment files against protocol requirements."""

    def __init__(self, candidate_index_path: Optional[Path] = None):
        self.index_path = candidate_index_path or DEFAULT_CANDIDATE_INDEX
        self.candidate_index: Dict[str, Dict[str, str]] = {}
        self._load_candidate_index()

    def _load_candidate_index(self) -> None:
        if not self.index_path.exists():
            return

        with open(self.index_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ann_id = row.get("annotation_id", "").strip()
                if ann_id:
                    self.candidate_index[ann_id] = row

    @staticmethod
    def is_valid_iso_timestamp(ts: str) -> bool:
        """Validate whether string represents an ISO 8601 UTC timestamp."""
        if not ts:
            return False
        clean_ts = ts.strip().replace("Z", "+00:00")
        try:
            datetime.fromisoformat(clean_ts)
            return True
        except ValueError:
            return False

    @staticmethod
    def parse_boolean_flag(val: str) -> Optional[bool]:
        """Parse common boolean representations (YES/NO, TRUE/FALSE, 1/0)."""
        clean = val.strip().upper()
        if clean in {"YES", "TRUE", "1"}:
            return True
        if clean in {"NO", "FALSE", "0"}:
            return False
        return None

    def detect_mode(self, fieldnames: List[str]) -> str:
        """Detect whether the submission is pilot selection, independent annotation, adjudication, or recruitment tracker."""
        fn_set = {f.strip().lower() for f in fieldnames}
        if "candidate_ref" in fn_set and "qualification_decision" in fn_set:
            return "recruitment-tracker"
        if "pilot_batch_id" in fn_set or "target_category_rationale" in fn_set:
            return "pilot-selection"
        if "adjudicator_id" in fn_set or "consensus_status" in fn_set:
            return "adjudication"
        return "independent-annotation"

    def validate_file(
        self,
        file_path: Path,
        mode: str = "auto",
        dry_run: bool = True,
        require_completed: bool = False,
        reject_synthetic: bool = False,
    ) -> ValidationReport:
        """Validate an annotation, pilot-selection, adjudication, or recruitment CSV file."""
        report = ValidationReport(
            file_path=str(file_path),
            mode=mode,
            dry_run=dry_run,
        )

        if not file_path.exists():
            report.add_error(None, f"File not found: {file_path}")
            return report

        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                try:
                    header = next(reader)
                except StopIteration:
                    report.add_error(None, "File is empty.")
                    return report
        except Exception as e:
            report.add_error(None, f"Failed to open or decode CSV file: {e}")
            return report

        clean_header = [h.strip() for h in header]

        # Auto-detect mode if requested
        if mode == "auto":
            detected_mode = self.detect_mode(clean_header)
            report.mode = detected_mode
        else:
            detected_mode = mode.lower().replace("_", "-")
            report.mode = detected_mode

        if detected_mode == "pilot-selection":
            self._validate_pilot_selection_csv(file_path, clean_header, report)
        elif detected_mode in {"independent-annotation", "independent_annotation"}:
            self._validate_independent_annotation_csv(
                file_path,
                clean_header,
                report,
                strict_blinding=True,
                require_completed=require_completed,
                reject_synthetic=reject_synthetic,
            )
        elif detected_mode == "reviewer":
            # Backwards-compatible alias for Phase 2J
            if "pilot_batch_id" in [c.lower() for c in clean_header]:
                report.add_warning(
                    1,
                    "File contains pilot selection schema; validating under pilot-selection rules in compatibility mode."
                )
                self._validate_pilot_selection_csv(file_path, clean_header, report)
            else:
                self._validate_independent_annotation_csv(
                    file_path,
                    clean_header,
                    report,
                    strict_blinding=False,
                    require_completed=require_completed,
                    reject_synthetic=reject_synthetic,
                )
        elif detected_mode == "adjudication":
            self._validate_adjudication_csv(file_path, clean_header, report, reject_synthetic=reject_synthetic)
        elif detected_mode in {"recruitment-tracker", "recruitment_tracker"}:
            self._validate_recruitment_tracker_csv(file_path, clean_header, report)
        else:
            report.add_error(None, f"Unsupported validation mode: {mode}")

        return report

    def _validate_pilot_selection_csv(
        self,
        file_path: Path,
        header: List[str],
        report: ValidationReport,
    ) -> None:
        """Validate pilot selection manifest (e.g., PHASE_2J_PILOT_SELECTION.csv)."""
        for col in REQUIRED_PILOT_SELECTION_COLUMNS:
            if col not in header:
                report.add_error(1, f"Missing required column in pilot-selection schema: '{col}'")

        if report.errors:
            return

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            seen_pilot_ids: Set[str] = set()
            seen_annotation_ids: Set[str] = set()

            for line_idx, row in enumerate(reader, start=2):
                report.total_rows += 1
                row_valid = True

                pid = row.get("pilot_batch_id", "").strip()
                ann_id = row.get("annotation_id", "").strip()
                cid = row.get("candidate_id", "").strip()
                img_name = row.get("image_filename", "").strip()
                act_path = row.get("active_image_path", "").strip()
                target_rat = row.get("target_category_rationale", "").strip()
                status = row.get("review_status", "").strip().upper()
                rev_id = row.get("reviewer_id", "").strip()
                rev_ts = row.get("review_timestamp", "").strip()
                cat = row.get("primary_category", "").strip()
                conf = row.get("confidence_level", "").strip()
                rat = row.get("geomorphic_rationale", "").strip()
                proto = row.get("protocol_version", "").strip()

                if not pid or not pid.startswith("PILOT_"):
                    report.add_error(line_idx, f"Invalid pilot_batch_id '{pid}'; must start with 'PILOT_'.")
                    row_valid = False
                elif pid in seen_pilot_ids:
                    report.add_error(line_idx, f"Duplicate pilot_batch_id '{pid}' in manifest.")
                    row_valid = False
                seen_pilot_ids.add(pid)

                if not ann_id or not ann_id.startswith("ANN_"):
                    report.add_error(line_idx, f"Invalid annotation_id '{ann_id}'; must start with 'ANN_'.")
                    row_valid = False
                elif ann_id in seen_annotation_ids:
                    report.add_error(line_idx, f"Duplicate annotation_id '{ann_id}' in pilot selection.")
                    row_valid = False
                seen_annotation_ids.add(ann_id)

                if self.candidate_index:
                    if ann_id not in self.candidate_index:
                        report.add_error(line_idx, f"Annotation ID '{ann_id}' not found in candidate index.")
                        row_valid = False
                    else:
                        ci = self.candidate_index[ann_id]
                        exp_cid = ci.get("candidate_id", "").strip()
                        exp_img = ci.get("image_filename", "").strip()
                        if cid and exp_cid and cid != exp_cid:
                            report.add_error(line_idx, f"candidate_id '{cid}' does not match index expected '{exp_cid}'.")
                            row_valid = False
                        if img_name and exp_img and img_name != exp_img:
                            report.add_error(line_idx, f"image_filename '{img_name}' does not match index expected '{exp_img}'.")
                            row_valid = False

                if not act_path:
                    report.add_error(line_idx, f"Missing active_image_path for {ann_id}.")
                    row_valid = False
                else:
                    phys_path = PROJECT_ROOT / act_path
                    if not phys_path.exists():
                        report.add_error(line_idx, f"Referenced image file does not exist on disk: {act_path}")
                        row_valid = False

                if not target_rat:
                    report.add_error(line_idx, f"Missing target_category_rationale for pilot row {pid}.")
                    row_valid = False

                if status != "PENDING":
                    report.add_error(
                        line_idx,
                        f"Pilot selection row {pid} ({ann_id}) has status '{status}'. "
                        "Pilot selection manifests must remain strictly PENDING; completed annotations "
                        "cannot be submitted inside a selection manifest."
                    )
                    row_valid = False

                if rev_id:
                    report.add_error(line_idx, f"Pilot selection row {pid} has populated reviewer_id: '{rev_id}'.")
                    row_valid = False
                if rev_ts:
                    report.add_error(line_idx, f"Pilot selection row {pid} has populated review_timestamp.")
                    row_valid = False
                if cat:
                    report.add_error(line_idx, f"Pilot selection row {pid} has populated primary_category: '{cat}'.")
                    row_valid = False
                if conf:
                    report.add_error(line_idx, f"Pilot selection row {pid} has populated confidence_level: '{conf}'.")
                    row_valid = False
                if rat:
                    report.add_error(line_idx, f"Pilot selection row {pid} has populated geomorphic_rationale.")
                    row_valid = False

                if proto != "v1.0":
                    report.add_warning(line_idx, f"protocol_version is '{proto}', expected 'v1.0'.")

                if row_valid:
                    report.valid_rows += 1

    def _validate_independent_annotation_csv(
        self,
        file_path: Path,
        header: List[str],
        report: ValidationReport,
        strict_blinding: bool = True,
        require_completed: bool = False,
        reject_synthetic: bool = False,
    ) -> None:
        """Validate human reviewer submission CSV."""
        for col in REQUIRED_REVIEWER_COLUMNS:
            if col not in header:
                report.add_error(1, f"Missing required column in independent annotation schema: '{col}'")

        if strict_blinding:
            for col in header:
                if col in PROHIBITED_REVIEWER_COLUMNS:
                    report.add_error(
                        1,
                        f"Extraneous column '{col}' not permitted in independent annotation schema; "
                        "metadata and target rationales must be blinded from reviewer submissions."
                    )

        if report.errors:
            return

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            seen_annotation_ids: Set[str] = set()
            seen_reviewer_pairs: Set[Tuple[str, str]] = set()

            for line_idx, row in enumerate(reader, start=2):
                report.total_rows += 1
                row_valid = True

                ann_id = row.get("annotation_id", "").strip()
                img_name = row.get("image_filename", "").strip()
                rev_id = row.get("reviewer_id", "").strip()
                rev_ts = row.get("review_timestamp", "").strip()
                cat = row.get("primary_category", "").strip()
                conf = row.get("confidence_level", "").strip()
                qual = row.get("image_quality_limitations", "").strip()
                rat = row.get("geomorphic_rationale", "").strip()
                req_adj = row.get("requires_adjudication", "").strip()
                status = row.get("review_status", "").strip().upper()
                proto = row.get("protocol_version", "").strip()

                # Rejection of synthetic test stubs in genuine production mode
                if reject_synthetic:
                    if rev_id.startswith("TEST_") or "SYNTHETIC" in rev_id.upper():
                        report.add_error(
                            line_idx,
                            f"Synthetic test reviewer ID '{rev_id}' rejected in genuine production mode."
                        )
                        row_valid = False
                    if "[SYNTHETIC_TEST_DATA]" in rat:
                        report.add_error(
                            line_idx,
                            f"Synthetic rationale detected for {ann_id} in genuine production mode."
                        )
                        row_valid = False

                # 1. Annotation ID checks
                if not ann_id:
                    report.add_error(line_idx, "Empty annotation_id.")
                    row_valid = False
                elif not ann_id.startswith("ANN_"):
                    report.add_error(line_idx, f"Invalid annotation_id pattern '{ann_id}'; must start with 'ANN_'.")
                    row_valid = False
                elif self.candidate_index and ann_id not in self.candidate_index:
                    report.add_error(
                        line_idx,
                        f"Unrecognized annotation_id '{ann_id}'; not found in candidate index."
                    )
                    row_valid = False

                if ann_id:
                    if ann_id in seen_annotation_ids:
                        report.add_error(line_idx, f"Duplicate annotation_id '{ann_id}' in submission file.")
                        row_valid = False
                    seen_annotation_ids.add(ann_id)

                if rev_id and ann_id:
                    pair = (rev_id, ann_id)
                    if pair in seen_reviewer_pairs:
                        report.add_error(line_idx, f"Duplicate review for reviewer '{rev_id}' on image '{ann_id}'.")
                        row_valid = False
                    seen_reviewer_pairs.add(pair)

                # 2. Image filename check against index
                if ann_id in self.candidate_index and img_name:
                    expected_img = self.candidate_index[ann_id].get("image_filename", "").strip()
                    if expected_img and img_name != expected_img:
                        report.add_error(
                            line_idx,
                            f"image_filename '{img_name}' does not match index expected '{expected_img}' for {ann_id}."
                        )
                        row_valid = False

                # 3. Status invariant checks
                if status not in REVIEWER_STATUSES:
                    report.add_error(
                        line_idx,
                        f"Invalid review_status '{status}'; must be one of {sorted(REVIEWER_STATUSES)}."
                    )
                    row_valid = False
                elif status == "PENDING":
                    if require_completed:
                        report.add_error(
                            line_idx,
                            f"Row {ann_id} has review_status PENDING, but a completed submission is required."
                        )
                        row_valid = False

                    if rev_id:
                        report.add_error(line_idx, f"Pending row {ann_id} has populated reviewer_id: '{rev_id}'.")
                        row_valid = False
                    if cat:
                        report.add_error(line_idx, f"Pending row {ann_id} has populated primary_category: '{cat}'.")
                        row_valid = False
                    if conf:
                        report.add_error(line_idx, f"Pending row {ann_id} has populated confidence_level: '{conf}'.")
                        row_valid = False
                    if rat:
                        report.add_error(line_idx, f"Pending row {ann_id} has populated geomorphic_rationale.")
                        row_valid = False
                elif status == "COMPLETED":
                    if not rev_id:
                        report.add_error(line_idx, f"Completed row {ann_id} is missing reviewer_id.")
                        row_valid = False

                    if not rev_ts or not self.is_valid_iso_timestamp(rev_ts):
                        report.add_error(
                            line_idx,
                            f"Completed row {ann_id} has invalid or missing ISO 8601 review_timestamp: '{rev_ts}'."
                        )
                        row_valid = False

                    if not cat or cat not in CANONICAL_CATEGORIES:
                        report.add_error(
                            line_idx,
                            f"Completed row {ann_id} has invalid primary_category '{cat}'. Allowed: {sorted(CANONICAL_CATEGORIES)}."
                        )
                        row_valid = False

                    if not conf or conf.upper() not in ALLOWED_CONFIDENCES:
                        report.add_error(
                            line_idx,
                            f"Completed row {ann_id} has invalid confidence_level '{conf}'. Allowed: {sorted(ALLOWED_CONFIDENCES)}."
                        )
                        row_valid = False

                    if qual:
                        tokens = [t.strip().upper() for t in re.split(r"[;, ]+", qual) if t.strip()]
                        for token in tokens:
                            if token not in ALLOWED_QUALITY_LIMITATIONS:
                                report.add_error(
                                    line_idx,
                                    f"Completed row {ann_id} has invalid quality limitation '{token}'."
                                )
                                row_valid = False

                    if not rat or len(rat.strip()) < 5:
                        report.add_error(
                            line_idx,
                            f"Completed row {ann_id} has missing or excessively short geomorphic_rationale (min 5 chars)."
                        )
                        row_valid = False

                    if self.parse_boolean_flag(req_adj) is None:
                        report.add_error(
                            line_idx,
                            f"Completed row {ann_id} has invalid requires_adjudication flag '{req_adj}'. Must be YES/NO."
                        )
                        row_valid = False

                if proto and proto != "v1.0":
                    report.add_warning(
                        line_idx,
                        f"Non-standard protocol_version '{proto}'; expected 'v1.0'."
                    )

                if row_valid:
                    report.valid_rows += 1

    def _validate_adjudication_csv(
        self,
        file_path: Path,
        header: List[str],
        report: ValidationReport,
        reject_synthetic: bool = False,
    ) -> None:
        """Validate senior expert adjudication CSV."""
        for col in REQUIRED_ADJUDICATION_COLUMNS:
            if col not in header:
                report.add_error(1, f"Missing required column in adjudication schema: '{col}'")

        if report.errors:
            return

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            seen_annotation_ids: Set[str] = set()

            for line_idx, row in enumerate(reader, start=2):
                report.total_rows += 1
                row_valid = True

                ann_id = row.get("annotation_id", "").strip()
                adj_id = row.get("adjudicator_id", "").strip()
                adj_ts = row.get("adjudication_timestamp", "").strip()
                r1_id = row.get("reviewer_1_id", "").strip()
                r1_cat = row.get("reviewer_1_category", "").strip()
                r2_id = row.get("reviewer_2_id", "").strip()
                r2_cat = row.get("reviewer_2_category", "").strip()
                disagreement = row.get("disagreement_detected", "").strip()
                adj_cat = row.get("adjudicated_category", "").strip()
                adj_rat = row.get("adjudication_rationale", "").strip()
                status = row.get("consensus_status", "").strip().upper()

                if reject_synthetic:
                    if adj_id.startswith("TEST_") or "SYNTHETIC" in adj_id.upper():
                        report.add_error(
                            line_idx,
                            f"Synthetic adjudicator ID '{adj_id}' rejected in genuine production mode."
                        )
                        row_valid = False

                if not ann_id:
                    report.add_error(line_idx, "Empty annotation_id in adjudication row.")
                    row_valid = False
                elif not ann_id.startswith("ANN_"):
                    report.add_error(line_idx, f"Invalid annotation_id '{ann_id}'.")
                    row_valid = False
                elif self.candidate_index and ann_id not in self.candidate_index:
                    report.add_error(line_idx, f"Unrecognized annotation_id '{ann_id}' in adjudication.")
                    row_valid = False

                if ann_id:
                    if ann_id in seen_annotation_ids:
                        report.add_error(line_idx, f"Duplicate annotation_id '{ann_id}' in adjudication file.")
                        row_valid = False
                    seen_annotation_ids.add(ann_id)

                if status not in ADJUDICATION_CONSENSUS_STATUSES:
                    report.add_error(
                        line_idx,
                        f"Invalid consensus_status '{status}'. Allowed: {sorted(ADJUDICATION_CONSENSUS_STATUSES)}."
                    )
                    row_valid = False
                elif status == "PENDING":
                    if adj_id:
                        report.add_error(line_idx, f"Pending row {ann_id} has populated adjudicator_id: '{adj_id}'.")
                        row_valid = False
                    if adj_cat:
                        report.add_error(line_idx, f"Pending row {ann_id} has populated adjudicated_category: '{adj_cat}'.")
                        row_valid = False
                else:
                    if not r1_id or not r2_id:
                        report.add_error(
                            line_idx,
                            f"Adjudication cannot be completed for {ann_id} without both reviewer_1_id and reviewer_2_id."
                        )
                        row_valid = False

                    if r1_cat not in CANONICAL_CATEGORIES:
                        report.add_error(
                            line_idx,
                            f"reviewer_1_category '{r1_cat}' is invalid for {ann_id}."
                        )
                        row_valid = False

                    if r2_cat not in CANONICAL_CATEGORIES:
                        report.add_error(
                            line_idx,
                            f"reviewer_2_category '{r2_cat}' is invalid for {ann_id}."
                        )
                        row_valid = False

                    if not adj_id:
                        report.add_error(line_idx, f"Completed adjudication {ann_id} is missing adjudicator_id.")
                        row_valid = False

                    if not adj_ts or not self.is_valid_iso_timestamp(adj_ts):
                        report.add_error(
                            line_idx,
                            f"Completed adjudication {ann_id} has invalid adjudication_timestamp: '{adj_ts}'."
                        )
                        row_valid = False

                    if adj_cat not in CANONICAL_CATEGORIES:
                        report.add_error(
                            line_idx,
                            f"adjudicated_category '{adj_cat}' is invalid for {ann_id}."
                        )
                        row_valid = False

                    if not adj_rat or len(adj_rat.strip()) < 5:
                        report.add_error(
                            line_idx,
                            f"adjudication_rationale is missing or too short for {ann_id}."
                        )
                        row_valid = False

                    disag_bool = self.parse_boolean_flag(disagreement)
                    if disag_bool is None:
                        report.add_error(
                            line_idx,
                            f"disagreement_detected '{disagreement}' must be YES/NO."
                        )
                        row_valid = False
                    else:
                        expected_disag = (r1_cat != r2_cat)
                        if disag_bool != expected_disag:
                            report.add_error(
                                line_idx,
                                f"disagreement_detected flag ({disag_bool}) does not match category comparison "
                                f"(reviewer_1='{r1_cat}', reviewer_2='{r2_cat}', expected={expected_disag})."
                            )
                            row_valid = False

                if row_valid:
                    report.valid_rows += 1

    def _validate_recruitment_tracker_csv(
        self,
        file_path: Path,
        header: List[str],
        report: ValidationReport,
    ) -> None:
        """Validate recruitment candidate tracking pipeline CSV."""
        for col in REQUIRED_RECRUITMENT_TRACKER_COLUMNS:
            if col not in header:
                report.add_error(1, f"Missing required column in recruitment-tracker schema: '{col}'")

        if report.errors:
            return

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            seen_refs: Set[str] = set()

            for line_idx, row in enumerate(reader, start=2):
                report.total_rows += 1
                row_valid = True

                cref = row.get("candidate_ref", "").strip()
                qdec = row.get("qualification_decision", "").strip().upper()
                assigned_rev = row.get("assigned_reviewer_id", "").strip()

                if not cref:
                    report.add_error(line_idx, "Missing candidate_ref.")
                    row_valid = False
                elif cref in seen_refs:
                    report.add_error(line_idx, f"Duplicate candidate_ref '{cref}'.")
                    row_valid = False
                seen_refs.add(cref)

                # Consistency rule: Cannot assign active reviewer ID if qualification is not APPROVED
                if qdec != "APPROVED" and assigned_rev and not assigned_rev.startswith("[") and assigned_rev != "UNASSIGNED":
                    report.add_error(
                        line_idx,
                        f"Candidate '{cref}' has qualification_decision '{qdec}' but active assigned_reviewer_id '{assigned_rev}'. "
                        "Unapproved candidates cannot be assigned active reviewer roles."
                    )
                    row_valid = False

                if row_valid:
                    report.valid_rows += 1


def verify_pilot_launch_gate(
    assignment_path: Path,
    qualification_log_path: Path,
    pilot_manifest_path: Path,
) -> Tuple[bool, List[str]]:
    """Evaluates whether all requirements are satisfied to transition from READY_FOR_PILOT_DISTRIBUTION to PILOT_IN_PROGRESS."""
    reasons: List[str] = []

    if not assignment_path.exists():
        return False, [f"Assignment record file not found: {assignment_path}"]
    if not qualification_log_path.exists():
        return False, [f"Qualification log file not found: {qualification_log_path}"]
    if not pilot_manifest_path.exists():
        return False, [f"Pilot manifest file not found: {pilot_manifest_path}"]

    # Check pilot manifest
    with open(pilot_manifest_path, mode="r", encoding="utf-8") as f:
        pilot_rows = list(csv.DictReader(f))
    if len(pilot_rows) != 10:
        reasons.append(f"Pilot manifest contains {len(pilot_rows)} rows; exactly 10 required.")
    for pr in pilot_rows:
        if pr.get("review_status") != "PENDING":
            reasons.append(f"Pilot candidate {pr.get('annotation_id')} has status {pr.get('review_status')}; must be PENDING.")

    # Check assignments
    with open(assignment_path, mode="r", encoding="utf-8") as f:
        asg_rows = list(csv.DictReader(f))

    active_reviewers = []
    for ar in asg_rows:
        rev_id = ar.get("reviewer_id", "").strip()
        status = ar.get("assignment_status", "").strip().upper()
        qual_ver = ar.get("qualification_verified", "").strip().upper()
        indep_aff = ar.get("independence_affirmed", "").strip().upper()

        if not rev_id or rev_id.startswith("[ENTER_") or "PLACEHOLDER" in rev_id.upper():
            continue

        if qual_ver != "APPROVED":
            reasons.append(f"Reviewer {rev_id} qualification is '{qual_ver}'; must be APPROVED.")
        if indep_aff not in {"APPROVED", "YES"}:
            reasons.append(f"Reviewer {rev_id} independence affirmation is '{indep_aff}'; must be APPROVED.")
        if status in {"APPROVED", "ASSIGNED", "ACTIVE"}:
            active_reviewers.append(rev_id)

    if len(set(active_reviewers)) < 2:
        reasons.append(
            f"Found {len(set(active_reviewers))} approved active reviewers in assignment log; exactly 2 required before pilot launch."
        )

    # Check qualification log for active reviewers
    with open(qualification_log_path, mode="r", encoding="utf-8") as f:
        qual_rows = list(csv.DictReader(f))
    qual_map = {r.get("reviewer_id", "").strip(): r for r in qual_rows}

    for rev_id in active_reviewers:
        if rev_id not in qual_map:
            reasons.append(f"Assigned reviewer {rev_id} is missing from qualification log.")
        else:
            qr = qual_map[rev_id]
            q_status = qr.get("qualification_status", "").strip().upper()
            if q_status != "APPROVED":
                reasons.append(f"Reviewer {rev_id} has qualification status '{q_status}' in log; must be APPROVED.")

    if reasons:
        return False, reasons
    return True, ["All launch gate checks passed: 2 qualified reviewers approved, pilot manifest ready."]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate human annotation, pilot selection, adjudication, and recruitment files for PahaarPulse."
    )
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to the CSV file to validate.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "pilot-selection", "independent-annotation", "adjudication", "recruitment-tracker", "reviewer"],
        default="auto",
        help="Validation mode (default: auto).",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_CANDIDATE_INDEX,
        help="Path to candidate_index.csv for ID verification.",
    )
    parser.add_argument(
        "--require-completed",
        action="store_true",
        help="Reject rows with review_status=PENDING (enforce submission completeness).",
    )
    parser.add_argument(
        "--reject-synthetic",
        action="store_true",
        help="Reject synthetic test records (e.g., TEST_REVIEWER, [SYNTHETIC_TEST_DATA]) in genuine production mode.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Execute in read-only mode without mutating any files (default: True).",
    )

    args = parser.parse_args()

    validator = HumanAnnotationValidator(candidate_index_path=args.index)
    report = validator.validate_file(
        args.file,
        mode=args.mode,
        dry_run=args.dry_run,
        require_completed=args.require_completed,
        reject_synthetic=args.reject_synthetic,
    )

    print("=" * 72)
    print("PAHAARPULSE HUMAN ANNOTATION SUBMISSION VALIDATOR")
    print("=" * 72)
    print(f"Target File:   {report.file_path}")
    print(f"Detected Mode: {report.mode}")
    print(f"Dry Run:       {report.dry_run} (Read-only execution)")
    print(f"Total Rows:    {report.total_rows}")
    print(f"Valid Rows:    {report.valid_rows}")
    print(f"Status:        {'VALID' if report.is_valid else 'INVALID'}")
    print("-" * 72)

    if report.warnings:
        print(f"WARNINGS ({len(report.warnings)}):")
        for w in report.warnings[:20]:
            print(f"  [WARN] {w}")
        if len(report.warnings) > 20:
            print(f"  ... and {len(report.warnings) - 20} more warnings.")

    if report.errors:
        print(f"ERRORS ({len(report.errors)}):")
        for err in report.errors[:25]:
            print(f"  [ERROR] {err}")
        if len(report.errors) > 25:
            print(f"  ... and {len(report.errors) - 25} more errors.")
        print("=" * 72)
        print("[NOTICE] File failed structural/schema verification.")
        return 1

    print("Validation passed successfully with zero errors.")
    print("[NOTICE] Successful schema validation verifies format and structural invariants only.")
    print("         It does NOT imply that a human review was completed, that annotations are")
    print("         scientifically valid, or that benchmark inference is unlocked.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
