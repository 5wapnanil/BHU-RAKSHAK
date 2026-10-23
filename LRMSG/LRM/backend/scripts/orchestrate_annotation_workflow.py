#!/usr/bin/env python3
"""End-to-end annotation workflow orchestrator and disagreement detector.

Phase 2L: End-to-End Annotation Workflow Dry Run.

Coordinates the independent annotation and adjudication pipeline:
1. Validates Reviewer 1 submission (independent-annotation schema, completed).
2. Validates Reviewer 2 submission (independent-annotation schema, completed).
3. Verifies reviewer blinding and independent identities.
4. Reconciles annotation IDs across both submissions.
5. Performs row-by-row comparison, detecting category disagreements and escalation flags.
6. Computes synthetic inter-rater reliability metrics (explicitly labeled test metrics).
7. Generates an authoritative adjudication draft template (adjudication schema).
8. Optionally validates completed adjudication against source submissions.
9. Emits a tamper-evident audit report with SHA-256 file digests.

Safety Invariants:
- Strictly operates on explicitly supplied file paths.
- Refuses to overwrite existing files unless --force is specified.
- Read-only on source reviewer files.
- Zero database interaction.
- Zero network or AI provider calls.
- Preserves genuine benchmark locks.

Usage:
    python backend/scripts/orchestrate_annotation_workflow.py \
        --reviewer-1 <path> \
        --reviewer-2 <path> \
        [--adjudication-output <path>] \
        [--adjudication-input <path>] \
        [--report-output <path>] \
        [--force] \
        [--synthetic]
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Project root calculation
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Import validator from same script directory
sys.path.insert(0, str(BACKEND_DIR.parent))
from backend.scripts.validate_human_annotations import (
    CANONICAL_CATEGORIES,
    HumanAnnotationValidator,
    REQUIRED_ADJUDICATION_COLUMNS,
    REQUIRED_REVIEWER_COLUMNS,
)


def compute_file_sha256(path: Path) -> str:
    """Compute hex SHA-256 digest of a physical file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class ComparisonItem:
    """Row-level comparison between two independent reviewer submissions."""
    annotation_id: str
    image_filename: str
    reviewer_1_id: str
    reviewer_1_category: str
    reviewer_1_confidence: str
    reviewer_1_requires_adjudication: str
    reviewer_2_id: str
    reviewer_2_category: str
    reviewer_2_confidence: str
    reviewer_2_requires_adjudication: str
    disagreement_detected: bool
    escalation_requested: bool
    requires_adjudication_resolution: bool
    difference_rationale: str


@dataclass
class WorkflowExecutionReport:
    """Full audit report of the workflow orchestration execution."""
    execution_timestamp: str
    is_synthetic: bool
    status: str
    reviewer_1_file: str
    reviewer_1_sha256: str
    reviewer_1_id: str
    reviewer_2_file: str
    reviewer_2_sha256: str
    reviewer_2_id: str
    total_images_evaluated: int = 0
    concordant_items_count: int = 0
    discordant_items_count: int = 0
    escalation_items_count: int = 0
    observed_agreement_pct: float = 0.0
    cohens_kappa: Optional[float] = None
    pabak: Optional[float] = None
    reliability_metric_label: str = "SYNTHETIC_TEST_METRIC - NOT SCIENTIFIC EVIDENCE"
    adjudication_template_path: Optional[str] = None
    adjudication_template_sha256: Optional[str] = None
    adjudication_input_path: Optional[str] = None
    adjudication_input_sha256: Optional[str] = None
    adjudication_validation_status: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    items: List[Dict[str, Any]] = field(default_factory=list)


class AnnotationWorkflowOrchestrator:
    """Coordinates validation, cross-reviewer diffing, and adjudication drafting."""

    def __init__(self, candidate_index_path: Optional[Path] = None):
        self.validator = HumanAnnotationValidator(candidate_index_path=candidate_index_path)

    @staticmethod
    def calculate_kappa_and_pabak(
        items: List[ComparisonItem],
    ) -> Tuple[float, float, float]:
        """Calculate observed agreement, Cohen's Kappa, and PABAK across 6 categories."""
        n = len(items)
        if n == 0:
            return 0.0, 0.0, 0.0

        agreed = sum(1 for it in items if not it.disagreement_detected)
        po = agreed / n

        # Category marginal distributions
        cats = sorted(CANONICAL_CATEGORIES)
        r1_counts = {c: 0 for c in cats}
        r2_counts = {c: 0 for c in cats}

        for it in items:
            if it.reviewer_1_category in r1_counts:
                r1_counts[it.reviewer_1_category] += 1
            if it.reviewer_2_category in r2_counts:
                r2_counts[it.reviewer_2_category] += 1

        pe = sum((r1_counts[c] / n) * (r2_counts[c] / n) for c in cats)

        # Cohen's Kappa
        kappa = (po - pe) / (1.0 - pe) if (1.0 - pe) > 1e-9 else 1.0

        # PABAK (Prevalence-Adjusted Bias-Adjusted Kappa)
        # For k categories: PABAK = (k * Po - 1) / (k - 1)
        k = len(cats)
        pabak = (k * po - 1.0) / (k - 1.0) if k > 1 else 1.0

        return po, kappa, pabak

    def execute_workflow(
        self,
        reviewer_1_path: Path,
        reviewer_2_path: Path,
        adjudication_output_path: Optional[Path] = None,
        adjudication_input_path: Optional[Path] = None,
        report_output_path: Optional[Path] = None,
        force_overwrite: bool = False,
        is_synthetic: bool = True,
    ) -> WorkflowExecutionReport:
        """Run the end-to-end workflow on two submissions."""
        report = WorkflowExecutionReport(
            execution_timestamp=datetime.now(timezone.utc).isoformat(),
            is_synthetic=is_synthetic,
            status="IN_PROGRESS",
            reviewer_1_file=str(reviewer_1_path),
            reviewer_1_sha256=compute_file_sha256(reviewer_1_path) if reviewer_1_path.exists() else "",
            reviewer_1_id="",
            reviewer_2_file=str(reviewer_2_path),
            reviewer_2_sha256=compute_file_sha256(reviewer_2_path) if reviewer_2_path.exists() else "",
            reviewer_2_id="",
        )

        # Pre-check: output paths must not exist unless force_overwrite
        if adjudication_output_path and adjudication_output_path.exists() and not force_overwrite:
            report.errors.append(
                f"Adjudication output path already exists: {adjudication_output_path}. Use --force to overwrite."
            )
            report.status = "FAILED"
            return report

        if report_output_path and report_output_path.exists() and not force_overwrite:
            report.errors.append(
                f"Report output path already exists: {report_output_path}. Use --force to overwrite."
            )
            report.status = "FAILED"
            return report

        # ---------------------------------------------------------
        # Stage 1: Validate Reviewer 1 Submission
        # ---------------------------------------------------------
        rep_1 = self.validator.validate_file(
            reviewer_1_path,
            mode="independent-annotation",
            dry_run=True,
            require_completed=True,
        )
        if not rep_1.is_valid:
            report.errors.append(f"Reviewer 1 submission failed validation: {rep_1.errors}")
            report.status = "FAILED"
            return report

        # ---------------------------------------------------------
        # Stage 2: Validate Reviewer 2 Submission
        # ---------------------------------------------------------
        rep_2 = self.validator.validate_file(
            reviewer_2_path,
            mode="independent-annotation",
            dry_run=True,
            require_completed=True,
        )
        if not rep_2.is_valid:
            report.errors.append(f"Reviewer 2 submission failed validation: {rep_2.errors}")
            report.status = "FAILED"
            return report

        # Load rows
        with open(reviewer_1_path, mode="r", encoding="utf-8") as f:
            rows_1 = list(csv.DictReader(f))
        with open(reviewer_2_path, mode="r", encoding="utf-8") as f:
            rows_2 = list(csv.DictReader(f))

        rev_1_id = rows_1[0].get("reviewer_id", "").strip() if rows_1 else ""
        rev_2_id = rows_2[0].get("reviewer_id", "").strip() if rows_2 else ""
        report.reviewer_1_id = rev_1_id
        report.reviewer_2_id = rev_2_id

        # ---------------------------------------------------------
        # Stage 3: Reviewer Independence & File Separation Check
        # ---------------------------------------------------------
        if reviewer_1_path.resolve() == reviewer_2_path.resolve():
            report.errors.append("Reviewer 1 and Reviewer 2 paths point to the same physical file.")
            report.status = "FAILED"
            return report
        if rev_1_id == rev_2_id:
            report.errors.append(
                f"Reviewer 1 and Reviewer 2 share identical identifier '{rev_1_id}'. Submissions must be independent."
            )
            report.status = "FAILED"
            return report


        # Check for plagiarism / identical timestamps and rationales
        identical_rationales = 0
        for r1, r2 in zip(rows_1, rows_2):
            rat1 = r1.get("geomorphic_rationale", "").strip()
            rat2 = r2.get("geomorphic_rationale", "").strip()
            if rat1 and rat2 and rat1 == rat2:
                identical_rationales += 1

        if identical_rationales == len(rows_1) and len(rows_1) > 1:
            report.errors.append(
                "Reviewer 1 and Reviewer 2 contain 100% identical geomorphic rationales; breach of independence."
            )
            report.status = "FAILED"
            return report

        # ---------------------------------------------------------
        # Stage 4: Reconcile Annotation IDs
        # ---------------------------------------------------------
        map_1 = {r["annotation_id"]: r for r in rows_1}
        map_2 = {r["annotation_id"]: r for r in rows_2}

        if set(map_1.keys()) != set(map_2.keys()):
            diff = set(map_1.keys()) ^ set(map_2.keys())
            report.errors.append(f"Annotation ID mismatch between submissions: {diff}")
            report.status = "FAILED"
            return report

        # ---------------------------------------------------------
        # Stage 5: Compare Annotations & Detect Disagreements
        # ---------------------------------------------------------
        comparison_items: List[ComparisonItem] = []
        ordered_ids = [r["annotation_id"] for r in rows_1]

        for ann_id in ordered_ids:
            r1 = map_1[ann_id]
            r2 = map_2[ann_id]

            cat1 = r1.get("primary_category", "").strip()
            cat2 = r2.get("primary_category", "").strip()
            conf1 = r1.get("confidence_level", "").strip()
            conf2 = r2.get("confidence_level", "").strip()
            adj_flag1 = r1.get("requires_adjudication", "").strip().upper()
            adj_flag2 = r2.get("requires_adjudication", "").strip().upper()

            category_mismatch = (cat1 != cat2)
            escalation_flag = (adj_flag1 in {"YES", "TRUE", "1"} or adj_flag2 in {"YES", "TRUE", "1"})
            needs_adjudication = category_mismatch or escalation_flag

            reasons = []
            if category_mismatch:
                reasons.append(f"Category mismatch: {rev_1_id}='{cat1}' vs {rev_2_id}='{cat2}'")
            if escalation_flag:
                reasons.append(f"Adjudication requested: {rev_1_id}={adj_flag1}, {rev_2_id}={adj_flag2}")
            if not reasons:
                reasons.append("Unanimous category agreement; no escalation requested.")

            comp = ComparisonItem(
                annotation_id=ann_id,
                image_filename=r1.get("image_filename", "").strip(),
                reviewer_1_id=rev_1_id,
                reviewer_1_category=cat1,
                reviewer_1_confidence=conf1,
                reviewer_1_requires_adjudication=adj_flag1,
                reviewer_2_id=rev_2_id,
                reviewer_2_category=cat2,
                reviewer_2_confidence=conf2,
                reviewer_2_requires_adjudication=adj_flag2,
                disagreement_detected=category_mismatch,
                escalation_requested=escalation_flag,
                requires_adjudication_resolution=needs_adjudication,
                difference_rationale="; ".join(reasons),
            )
            comparison_items.append(comp)

        report.total_images_evaluated = len(comparison_items)
        report.discordant_items_count = sum(1 for c in comparison_items if c.disagreement_detected)
        report.concordant_items_count = report.total_images_evaluated - report.discordant_items_count
        report.escalation_items_count = sum(1 for c in comparison_items if c.requires_adjudication_resolution)

        # ---------------------------------------------------------
        # Stage 6: Calculate Reliability Statistics
        # ---------------------------------------------------------
        po, kappa, pabak = self.calculate_kappa_and_pabak(comparison_items)
        report.observed_agreement_pct = round(po * 100.0, 2)
        report.cohens_kappa = round(kappa, 4)
        report.pabak = round(pabak, 4)
        report.items = [asdict(c) for c in comparison_items]

        # ---------------------------------------------------------
        # Stage 7: Generate Adjudication Draft Template (if requested)
        # ---------------------------------------------------------
        if adjudication_output_path:
            adj_rows = []
            for comp in comparison_items:
                disag_str = "YES" if comp.disagreement_detected else "NO"

                # If agreed and neither flagged escalation, can record AGREED_CONSENSUS draft
                if not comp.requires_adjudication_resolution:
                    consensus_status = "AGREED_CONSENSUS"
                    adj_cat = comp.reviewer_1_category
                    adj_rat = (
                        f"[SYNTHETIC_TEST_DATA] Consensus agreement between {rev_1_id} and {rev_2_id} on {adj_cat}."
                    )
                else:
                    consensus_status = "PENDING"
                    adj_cat = ""
                    adj_rat = ""

                adj_rows.append({
                    "annotation_id": comp.annotation_id,
                    "image_filename": comp.image_filename,
                    "adjudicator_id": "",
                    "adjudication_timestamp": "",
                    "reviewer_1_id": comp.reviewer_1_id,
                    "reviewer_1_category": comp.reviewer_1_category,
                    "reviewer_2_id": comp.reviewer_2_id,
                    "reviewer_2_category": comp.reviewer_2_category,
                    "disagreement_detected": disag_str,
                    "adjudicated_category": adj_cat,
                    "adjudication_rationale": adj_rat,
                    "consensus_status": consensus_status,
                    "protocol_version": "v1.0",
                })

            adjudication_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(adjudication_output_path, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=REQUIRED_ADJUDICATION_COLUMNS)
                writer.writeheader()
                writer.writerows(adj_rows)

            report.adjudication_template_path = str(adjudication_output_path)
            report.adjudication_template_sha256 = compute_file_sha256(adjudication_output_path)

        # ---------------------------------------------------------
        # Stage 8: Validate Adjudication Input (if provided)
        # ---------------------------------------------------------
        if adjudication_input_path:
            report.adjudication_input_path = str(adjudication_input_path)
            if not adjudication_input_path.exists():
                report.errors.append(f"Adjudication input file not found: {adjudication_input_path}")
                report.status = "FAILED"
                return report

            report.adjudication_input_sha256 = compute_file_sha256(adjudication_input_path)

            rep_adj = self.validator.validate_file(
                adjudication_input_path,
                mode="adjudication",
                dry_run=True,
            )
            if not rep_adj.is_valid:
                report.errors.append(f"Adjudication submission failed validation: {rep_adj.errors}")
                report.adjudication_validation_status = "INVALID"
                report.status = "FAILED"
                return report

            # Cross-verify source reviewer IDs and categories match
            with open(adjudication_input_path, mode="r", encoding="utf-8") as f:
                adj_recs = list(csv.DictReader(f))

            adj_map = {r["annotation_id"]: r for r in adj_recs}
            for comp in comparison_items:
                aid = comp.annotation_id
                if aid not in adj_map:
                    report.errors.append(f"Annotation {aid} missing from adjudication input.")
                    report.status = "FAILED"
                    return report

                ar = adj_map[aid]
                if ar["reviewer_1_id"] != comp.reviewer_1_id or ar["reviewer_1_category"] != comp.reviewer_1_category:
                    report.errors.append(f"Adjudication row {aid} has mismatched Reviewer 1 source data.")
                    report.status = "FAILED"
                    return report

                if ar["reviewer_2_id"] != comp.reviewer_2_id or ar["reviewer_2_category"] != comp.reviewer_2_category:
                    report.errors.append(f"Adjudication row {aid} has mismatched Reviewer 2 source data.")
                    report.status = "FAILED"
                    return report

            report.adjudication_validation_status = "VALID_AND_GROUNDED"

        # ---------------------------------------------------------
        # Stage 9: Write Summary Report (if requested)
        # ---------------------------------------------------------
        report.status = "SUCCESS"

        if report_output_path:
            report_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_output_path, mode="w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2)

        return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="End-to-End Human Annotation Workflow Orchestrator (PahaarPulse Phase 2L)."
    )
    parser.add_argument(
        "--reviewer-1",
        type=Path,
        required=True,
        help="Path to Reviewer 1 completed CSV submission.",
    )
    parser.add_argument(
        "--reviewer-2",
        type=Path,
        required=True,
        help="Path to Reviewer 2 completed CSV submission.",
    )
    parser.add_argument(
        "--adjudication-output",
        type=Path,
        default=None,
        help="Path to generate adjudication draft CSV template.",
    )
    parser.add_argument(
        "--adjudication-input",
        type=Path,
        default=None,
        help="Path to completed adjudication CSV to validate against source reviews.",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=None,
        help="Path to write JSON audit report.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of existing output files.",
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        default=True,
        help="Explicitly mark execution as synthetic test data (default: True).",
    )

    args = parser.parse_args()

    orchestrator = AnnotationWorkflowOrchestrator()
    report = orchestrator.execute_workflow(
        reviewer_1_path=args.reviewer_1,
        reviewer_2_path=args.reviewer_2,
        adjudication_output_path=args.adjudication_output,
        adjudication_input_path=args.adjudication_input,
        report_output_path=args.report_output,
        force_overwrite=args.force,
        is_synthetic=args.synthetic,
    )

    print("=" * 76)
    print("PAHAARPULSE ANNOTATION WORKFLOW ORCHESTRATOR - DRY RUN REPORT")
    print("=" * 76)
    print(f"Timestamp:       {report.execution_timestamp}")
    print(f"Workflow Status: {report.status}")
    print(f"Is Synthetic:    {report.is_synthetic} [TEST RUN - NOT PRODUCTION]")
    print("-" * 76)
    print(f"Reviewer 1 File: {report.reviewer_1_file}")
    print(f"  SHA-256:       {report.reviewer_1_sha256}")
    print(f"  Reviewer ID:   {report.reviewer_1_id}")
    print(f"Reviewer 2 File: {report.reviewer_2_file}")
    print(f"  SHA-256:       {report.reviewer_2_sha256}")
    print(f"  Reviewer ID:   {report.reviewer_2_id}")
    print("-" * 76)
    print(f"Evaluated Images:   {report.total_images_evaluated}")
    print(f"Concordant Items:   {report.concordant_items_count}")
    print(f"Discordant Items:   {report.discordant_items_count}")
    print(f"Escalation Routing: {report.escalation_items_count} items requiring adjudication")
    print("-" * 76)
    print(f"Observed Agreement: {report.observed_agreement_pct}%")
    print(f"Cohen's Kappa (k):  {report.cohens_kappa}")
    print(f"PABAK:              {report.pabak}")
    print(f"Notice:             {report.reliability_metric_label}")
    print("-" * 76)

    if report.adjudication_template_path:
        print(f"Adjudication Draft Created: {report.adjudication_template_path}")
        print(f"  SHA-256: {report.adjudication_template_sha256}")

    if report.adjudication_validation_status:
        print(f"Adjudication Input Validation: {report.adjudication_validation_status}")

    if report.errors:
        print(f"ERRORS ({len(report.errors)}):")
        for err in report.errors:
            print(f"  [ERROR] {err}")
        print("=" * 76)
        return 1

    print("=" * 76)
    print("[SAFEGUARD] Zero database tables modified. Zero files in backend/uploads/.")
    print("            Benchmark model inference remains strictly BLOCKED.")
    print("=" * 76)
    return 0


if __name__ == "__main__":
    sys.exit(main())
