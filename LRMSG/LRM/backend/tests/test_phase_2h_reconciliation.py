"""Unit tests for Phase 2H Dataset Reconciliation, Site/Event Grouping & Annotation Readiness.

Verifies:
1. Manifest reconciliation consistency across baseline and Phase 2G.
2. Quarantining of unverified or pending licenses from the cleared annotation package.
3. Exclusion of unsuitable records (such as non-geotechnical barn roof trusses).
4. Atomic cluster integrity for confirmed multi-member site/event groups.
5. Enforcement of the 'Unknown != Independent' evaluation splitting invariant.
6. Preservation of cross-batch duplicates without destructive file deletion.
7. Integrity of the frozen benchmark draft (all ground truth strictly pending).
8. Absence of public candidate rasters in production upload directories.
"""

import csv
import hashlib
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestPhase2HDatasetReconciliation(unittest.TestCase):
    """Test suite for Phase 2H reconciliation, grouping, and annotation gates."""

    @classmethod
    def setUpClass(cls):
        cls.eval_dir = PROJECT_ROOT / "docs" / "gemma-local-vision" / "evaluation"
        cls.base_images_dir = PROJECT_ROOT / "data" / "public_candidates" / "images"
        cls.g2_images_dir = PROJECT_ROOT / "data" / "public_candidates" / "batch_2g"
        cls.recon_manifest = cls.eval_dir / "PHASE_2H_RECONCILIATION_MANIFEST.csv"
        cls.group_manifest = cls.eval_dir / "PHASE_2H_GROUPING_MANIFEST.csv"
        cls.bench_draft = cls.eval_dir / "public_benchmark_draft.csv"

        # Load reconciliation manifest
        cls.recon_rows = []
        if cls.recon_manifest.exists():
            with open(cls.recon_manifest, mode="r", encoding="utf-8") as f:
                cls.recon_rows = list(csv.DictReader(f))

        # Load grouping manifest
        cls.group_rows = []
        if cls.group_manifest.exists():
            with open(cls.group_manifest, mode="r", encoding="utf-8") as f:
                cls.group_rows = list(csv.DictReader(f))

    def test_reconciliation_manifest_counts_and_uniqueness(self):
        """Verify reconciliation manifest has exactly 117 unique candidates and 103 on-disk images."""
        self.assertTrue(self.recon_manifest.exists(), "Reconciliation manifest must exist")
        self.assertEqual(len(self.recon_rows), 117, "Must contain exactly 117 unique candidate records")

        cids = [r["candidate_id"] for r in self.recon_rows]
        self.assertEqual(len(cids), len(set(cids)), "All candidate IDs in reconciliation manifest must be unique")

        on_disk_rows = [r for r in self.recon_rows if r["on_disk_status"] != "NOT_DOWNLOADED"]
        self.assertEqual(len(on_disk_rows), 103, "Must have exactly 103 unique images on disk across both batches")

        # Verify active file exists on disk for every on-disk row
        for r in on_disk_rows:
            p = r["phase_2g_path"] or r["baseline_path"]
            self.assertTrue(Path(PROJECT_ROOT / p).exists(), f"Image path {p} must exist on disk")

    def test_unresolved_licenses_cannot_enter_cleared_annotation_package(self):
        """Verify that any candidate with PENDING_REVIEW or unverified license is barred from annotation."""
        for r in self.recon_rows:
            lic_stat = r["license_audit_status"]
            ann_ready = r["annotation_readiness"]
            if lic_stat in ("PENDING_REVIEW", "REJECTED", "SOURCE_UNVERIFIED"):
                self.assertNotEqual(
                    ann_ready,
                    "CLEARED_FOR_ANNOTATION",
                    f"Candidate {r['candidate_id']} with license status {lic_stat} must not be cleared for annotation",
                )

    def test_unsuitable_candidates_barred_from_cleared_annotation_package(self):
        """Verify that non-geotechnical or unsuitable candidates are excluded from annotation."""
        # Specifically test WMC_21449778 (interior barn roof truss)
        r_barn = next((r for r in self.recon_rows if r["candidate_id"] == "WMC_21449778"), None)
        self.assertIsNotNone(r_barn, "WMC_21449778 must exist in reconciliation manifest")
        self.assertEqual(r_barn["scientific_suitability_status"], "UNSUITABLE")
        self.assertEqual(r_barn["annotation_readiness"], "EXCLUDED_UNSUITABLE")

        # Verify all unsuitable rows are excluded
        for r in self.recon_rows:
            if r["scientific_suitability_status"] in ("UNSUITABLE", "REQUIRES_QUALITY_REVIEW"):
                self.assertNotEqual(
                    r["annotation_readiness"],
                    "CLEARED_FOR_ANNOTATION",
                    f"Unsuitable candidate {r['candidate_id']} must not be cleared for annotation",
                )

    def test_cleared_annotation_package_count(self):
        """Verify that exactly 102 verified field candidate photos are cleared for annotation."""
        cleared = [r for r in self.recon_rows if r["annotation_readiness"] == "CLEARED_FOR_ANNOTATION"]
        self.assertEqual(len(cleared), 102, "Exactly 102 candidates must be cleared for annotation")

        for r in cleared:
            self.assertEqual(r["license_audit_status"], "LICENSE_VERIFIED")
            self.assertEqual(r["scientific_suitability_status"], "CANDIDATE")
            self.assertIn(r["on_disk_status"], ("DOWNLOADED_BASELINE", "DOWNLOADED_BATCH_2G", "DOWNLOADED_BOTH"))

    def test_grouping_manifest_atomic_clusters(self):
        """Verify multi-member confirmed clusters have consistent group IDs and split recommendations."""
        self.assertTrue(self.group_manifest.exists(), "Grouping manifest must exist")
        self.assertEqual(len(self.group_rows), 117, "Grouping manifest must contain all 117 records")

        # Check ODOT 10-image helicopter rockfall mesh series
        odot_rows = [r for r in self.group_rows if "ODOT_Helicopter_Rockfall_Mesh_Series" in r["site_event_group_id"]]
        self.assertEqual(len(odot_rows), 10, "ODOT mesh series must have exactly 10 records")
        for r in odot_rows:
            self.assertEqual(r["site_event_group_confidence"], "CONFIRMED_SITE_EVENT")
            self.assertEqual(r["group_member_count"], "10")

        # Check Rohtang Pass 2-image clearing series
        rohtang_rows = [r for r in self.group_rows if "Himachal_Rohtang_Pass_Clearing" in r["site_event_group_id"]]
        self.assertEqual(len(rohtang_rows), 2, "Rohtang clearing series must have exactly 2 records")
        for r in rohtang_rows:
            self.assertEqual(r["site_event_group_confidence"], "CONFIRMED_SITE_EVENT")
            self.assertEqual(r["group_member_count"], "2")

    def test_unknown_site_event_does_not_imply_independence(self):
        """Verify UNKNOWN_SITE_EVENT records are not marked as pre-cleared for test evaluation split."""
        for r in self.group_rows:
            if r["site_event_group_confidence"] == "UNKNOWN_SITE_EVENT":
                self.assertNotEqual(
                    r["evaluation_split_recommendation"],
                    "ALLOCATE_AS_UNIT_TEST",
                    f"Unknown candidate {r['candidate_id']} must not be directly allocated to TEST split without verification",
                )

    def test_cross_batch_duplicates_detected_without_file_deletion(self):
        """Verify the 4 overlapping images exist simultaneously in both batches without deletion."""
        overlap_cids = ["WMC_14428956", "WMC_21449778", "WMC_37943355", "WMC_37943361"]
        for cid in overlap_cids:
            p_base = self.base_images_dir / f"{cid}.jpg"
            p_g2 = self.g2_images_dir / f"{cid}.jpg"
            self.assertTrue(p_base.exists(), f"Baseline file {p_base} must not be deleted")
            self.assertTrue(p_g2.exists(), f"Phase 2G file {p_g2} must not be deleted")

            h_base = hashlib.sha256(p_base.read_bytes()).hexdigest()
            h_g2 = hashlib.sha256(p_g2.read_bytes()).hexdigest()
            self.assertEqual(h_base, h_g2, f"Hashes for {cid} across batches must be bit-for-bit identical")

    def test_draft_benchmark_adjudication_status_strictly_pending(self):
        """Verify all records in public_benchmark_draft.csv have empty labels and pending status."""
        self.assertTrue(self.bench_draft.exists(), "Benchmark draft must exist")
        with open(self.bench_draft, mode="r", encoding="utf-8") as f:
            bench_rows = list(csv.DictReader(f))

        self.assertEqual(len(bench_rows), 54, "Benchmark draft must preserve original 54 baseline records")
        for r in bench_rows:
            self.assertEqual(r["adjudication_status"], "pending", f"Image {r['image_id']} must have pending status")
            self.assertEqual(r["adjudicated_label"], "", f"Image {r['image_id']} must have empty adjudicated label")
            self.assertEqual(r["annotator_1_label"], "", f"Image {r['image_id']} must have empty annotator 1 label")
            self.assertEqual(r["annotator_2_label"], "", f"Image {r['image_id']} must have empty annotator 2 label")

    def test_no_candidate_images_in_production_uploads(self):
        """Verify candidate images have not leaked into production upload directories."""
        prod_upload_dir = PROJECT_ROOT / "backend" / "uploads"
        if prod_upload_dir.exists():
            for f in prod_upload_dir.iterdir():
                self.assertFalse(
                    f.name.startswith("WMC_"),
                    f"Public candidate image {f.name} must never reside in production uploads: {prod_upload_dir}",
                )


if __name__ == "__main__":
    unittest.main()
