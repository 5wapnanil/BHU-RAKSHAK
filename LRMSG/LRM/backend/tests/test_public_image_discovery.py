"""Unit tests for Public Landslide Image Discovery, Licensing Gates, and Controlled Ingestion.

Verifies:
1. Licensing gate evaluation for permissive, non-commercial, rejected, and ambiguous licenses.
2. Metadata-only discovery from mocked MediaWiki API responses without downloading files.
3. Rejection of unapproved candidates before downloading.
4. Magic byte and file signature verification (JPEG, PNG, WebP) and rejection of fake extensions.
5. Handling of oversized and zero-byte files with atomic temp file cleanup.
6. Detection of corrupt raster images via Pillow decoding.
7. Duplicate SHA-256 detection avoiding duplicate storage on disk.
8. Filename sanitization and path traversal prevention.
9. Handling of HTTP errors and rate limits.
10. Scientific honesty: Draft benchmark export strictly preserves 'pending' status and empty labels.
11. Manifest validation: Exclusion of unadjudicated images from frozen test benchmarks and site-group leakage prevention.
"""

import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image

from backend.app.services.public_image_acquisition import (
    CandidateImageRecord,
    ControlledImageDownloader,
    DownloadStatus,
    EventSiteConfidence,
    IntendedUseStatus,
    InvalidMediaSignatureError,
    LicenseGate,
    LicenseVerificationStatus,
    OversizedFileError,
    PathTraversalError,
    PublicAcquisitionError,
    PublicImageDiscoveryService,
    PublicImageManifestManager,
    ReviewStatus,
    ScientificSuitabilityStatus,
    compute_image_dhash,
    detect_near_duplicates,
    hamming_distance,
)
from backend.app.services.vlm_evaluation import (
    DataLeakageError,
    InvalidSourceError,
    MissingExpertGroundTruthError,
    MissingPermissionError,
    VLMEvaluationHarness,
    VLMEvaluationSample,
)


class TestPublicImageAcquisition(unittest.TestCase):
    """Test suite for public image discovery and controlled ingestion."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.download_dir = Path(self.temp_dir.name) / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    # --------------------------------------------------------------------------
    # 1. Licensing Gate Tests
    # --------------------------------------------------------------------------
    def test_license_gate_permissive_redistribution(self):
        cases = [
            ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0"),
            ("CC BY 3.0", "https://creativecommons.org/licenses/by/3.0"),
            ("CC0", "https://creativecommons.org/publicdomain/zero/1.0/"),
            ("Public domain", "https://commons.wikimedia.org/wiki/Public_domain"),
            ("PD-USGS", "https://usgs.gov"),
        ]
        for lic, url in cases:
            verif, use, excl = LicenseGate.evaluate_license(lic, url)
            self.assertEqual(verif, LicenseVerificationStatus.VERIFIED, f"Failed for {lic}")
            self.assertEqual(use, IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION, f"Failed for {lic}")
            self.assertEqual(excl, "", f"Failed for {lic}")

    def test_license_gate_non_commercial_internal_only(self):
        cases = [
            ("CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0"),
            ("CC BY-NC-SA 3.0", "https://creativecommons.org/licenses/by-nc-sa/3.0"),
        ]
        for lic, url in cases:
            verif, use, excl = LicenseGate.evaluate_license(lic, url, allow_internal_nc=True)
            self.assertEqual(verif, LicenseVerificationStatus.VERIFIED, f"Failed for {lic}")
            self.assertEqual(use, IntendedUseStatus.APPROVED_FOR_INTERNAL_EVALUATION, f"Failed for {lic}")
            self.assertIn("non_commercial", excl)

    def test_license_gate_rejected_and_nd_licenses(self):
        cases = [
            ("All Rights Reserved", ""),
            ("Copyrighted", "http://example.com/copyright"),
            ("CC BY-ND 4.0", "https://creativecommons.org/licenses/by-nd/4.0"),
            ("CC BY-NC-ND 3.0", "https://creativecommons.org/licenses/by-nc-nd/3.0"),
            ("Fair use", ""),
        ]
        for lic, url in cases:
            verif, use, excl = LicenseGate.evaluate_license(lic, url)
            self.assertEqual(verif, LicenseVerificationStatus.REJECTED, f"Failed for {lic}")
            self.assertEqual(use, IntendedUseStatus.REJECTED, f"Failed for {lic}")
            self.assertIn("prohibits", excl)

    def test_license_gate_ambiguous_and_missing_licenses(self):
        cases = [
            ("", ""),
            ("Unknown", ""),
            ("unverified", ""),
            ("No restrictions", "https://www.flickr.com/commons/usage/"),
            ("Custom University Agreement", "http://univ.edu/terms"),
        ]
        for lic, url in cases:
            verif, use, excl = LicenseGate.evaluate_license(lic, url)
            self.assertIn(verif, (LicenseVerificationStatus.UNVERIFIED, LicenseVerificationStatus.AMBIGUOUS))
            self.assertEqual(use, IntendedUseStatus.PENDING_REVIEW, f"Failed for {lic}")

    def test_license_gate_cleans_html_and_escapes(self):
        raw = '<a href="https://example.com">John Doe</a> &amp; Natural Hazards Center'
        cleaned = LicenseGate.clean_text(raw)
        self.assertEqual(cleaned, "John Doe & Natural Hazards Center")

    # --------------------------------------------------------------------------
    # 2. Metadata-Only Discovery (Mocked API)
    # --------------------------------------------------------------------------
    def test_metadata_only_discovery_with_mocked_wikimedia(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "101": {
                        "title": "File:Himalayan_landslide_crack.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/test1.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Himalayan_landslide_crack.jpg",
                                "mime": "image/jpeg",
                                "width": 1920,
                                "height": 1080,
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                    "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"},
                                    "Artist": {"value": "Geological Survey"},
                                    "GPSLatitude": {"value": "30.3165"},
                                    "GPSLongitude": {"value": "78.0322"},
                                },
                            }
                        ],
                    },
                    "102": {
                        "title": "File:Unknown_diagram.svg",
                        "imageinfo": [{"mime": "image/svg+xml"}],  # Unsupported non-raster
                    },
                }
            }
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        service = PublicImageDiscoveryService(rate_limit_delay=0.0, http_client=mock_client)
        candidates = service.search_wikimedia_commons("landslide tension crack", limit=5)

        # SVG should be filtered out, JPEG should be retained
        self.assertEqual(len(candidates), 1)
        c = candidates[0]
        self.assertEqual(c.candidate_id, "WMC_101")
        self.assertEqual(c.image_title, "Himalayan_landslide_crack.jpg")
        self.assertEqual(c.creator_attribution, "Geological Survey")
        self.assertEqual(c.intended_use_permission_status, IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION)
        self.assertEqual(c.dimensions, "1920x1080")
        self.assertIn("Coordinates: 30.3165, 78.0322", c.approximate_geographic_region)
        self.assertEqual(c.download_status, DownloadStatus.NOT_DOWNLOADED)

    # --------------------------------------------------------------------------
    # 3. Controlled Downloader & Integrity Tests
    # --------------------------------------------------------------------------
    def _create_synthetic_jpeg_bytes(self, width: int = 100, height: int = 100) -> bytes:
        img = Image.new("RGB", (width, height), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    def _create_synthetic_png_bytes(self, width: int = 100, height: int = 100) -> bytes:
        img = Image.new("RGBA", (width, height), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_downloader_rejects_unapproved_candidate(self):
        downloader = ControlledImageDownloader(download_dir=self.download_dir)
        candidate = CandidateImageRecord(
            candidate_id="TEST_001",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="Unapproved.jpg",
            creator_attribution="Unknown",
            license_identifier="Unverified",
            license_url="",
            license_verification_status=LicenseVerificationStatus.UNVERIFIED,
            intended_use_permission_status=IntendedUseStatus.PENDING_REVIEW,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="tension_cracks",
            retrieval_timestamp="",
            direct_download_url="https://example.com/test.jpg",
        )

        success, msg = downloader.download_candidate(candidate)
        self.assertFalse(success)
        self.assertEqual(candidate.download_status, DownloadStatus.SKIPPED_UNAPPROVED)
        self.assertIn("requires explicit approval", msg)

    def test_downloader_validates_magic_bytes_for_valid_jpeg_and_png(self):
        jpeg_bytes = self._create_synthetic_jpeg_bytes()
        png_bytes = self._create_synthetic_png_bytes()

        self.assertEqual(ControlledImageDownloader.verify_magic_bytes(jpeg_bytes[:16]), "jpeg")
        self.assertEqual(ControlledImageDownloader.verify_magic_bytes(png_bytes[:16]), "png")

    def test_downloader_rejects_fake_extension_and_invalid_signature(self):
        fake_bytes = b"THIS IS NOT A VALID JPEG OR PNG IMAGE HEADER TEXT"
        with self.assertRaises(InvalidMediaSignatureError):
            ControlledImageDownloader.verify_magic_bytes(fake_bytes[:16])

    def test_downloader_rejects_oversized_file(self):
        # Limit downloader to 500 KB
        downloader = ControlledImageDownloader(
            download_dir=self.download_dir,
            max_file_size_bytes=500 * 1024,
        )

        candidate = CandidateImageRecord(
            candidate_id="TEST_OVERSIZED",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="Large.jpg",
            creator_attribution="Author",
            license_identifier="CC-BY-4.0",
            license_url="https://creativecommons.org/licenses/by/4.0",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="landslide",
            retrieval_timestamp="",
            direct_download_url="https://example.com/large.jpg",
        )

        # Mock streaming response providing 600 KB in chunks
        chunk = b"\xff\xd8\xff\xe0" + b"X" * 8188
        chunks = [chunk for _ in range(75)]  # ~600 KB total

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.iter_bytes.return_value = chunks

        mock_client = MagicMock()
        mock_client.stream.return_value.__enter__.return_value = mock_resp
        downloader._client = mock_client

        success, msg = downloader.download_candidate(candidate)
        self.assertFalse(success)
        self.assertEqual(candidate.download_status, DownloadStatus.FAILED)
        self.assertIn("exceeded maximum size limit", msg)

        # Ensure no residual temp or target file remains
        files_remaining = list(self.download_dir.glob("TEST_OVERSIZED*"))
        self.assertEqual(len(files_remaining), 0)

    def test_downloader_rejects_zero_byte_file(self):
        downloader = ControlledImageDownloader(download_dir=self.download_dir)
        candidate = CandidateImageRecord(
            candidate_id="TEST_ZERO",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="Empty.jpg",
            creator_attribution="Author",
            license_identifier="CC0",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="debris",
            retrieval_timestamp="",
            direct_download_url="https://example.com/empty.jpg",
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.iter_bytes.return_value = []

        mock_client = MagicMock()
        mock_client.stream.return_value.__enter__.return_value = mock_resp
        downloader._client = mock_client

        success, msg = downloader.download_candidate(candidate)
        self.assertFalse(success)
        self.assertEqual(candidate.download_status, DownloadStatus.FAILED)
        self.assertIn("Zero-byte", msg)

    def test_downloader_rejects_corrupt_raster_image(self):
        downloader = ControlledImageDownloader(download_dir=self.download_dir)
        candidate = CandidateImageRecord(
            candidate_id="TEST_CORRUPT",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="Corrupt.jpg",
            creator_attribution="Author",
            license_identifier="CC0",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="debris",
            retrieval_timestamp="",
            direct_download_url="https://example.com/corrupt.jpg",
        )

        # Starts with valid JPEG header but invalid subsequent payload
        corrupt_bytes = b"\xff\xd8\xff\xe0" + b"CORRUPT_PAYLOAD_NOT_A_REAL_IMAGE"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.iter_bytes.return_value = [corrupt_bytes]

        mock_client = MagicMock()
        mock_client.stream.return_value.__enter__.return_value = mock_resp
        downloader._client = mock_client

        success, msg = downloader.download_candidate(candidate)
        self.assertFalse(success)
        self.assertEqual(candidate.download_status, DownloadStatus.FAILED)
        self.assertIn("Corrupt image", msg)

    def test_downloader_detects_duplicate_sha256(self):
        downloader = ControlledImageDownloader(download_dir=self.download_dir)
        valid_jpeg = self._create_synthetic_jpeg_bytes(width=80, height=80)

        # Mock client returning identical bytes for both candidates
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.iter_bytes.return_value = [valid_jpeg]

        mock_client = MagicMock()
        mock_client.stream.return_value.__enter__.return_value = mock_resp
        downloader._client = mock_client

        c1 = CandidateImageRecord(
            candidate_id="CANDIDATE_A",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="Original.jpg",
            creator_attribution="Author",
            license_identifier="CC-BY-4.0",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="cracks",
            retrieval_timestamp="",
            direct_download_url="https://example.com/img1.jpg",
        )

        c2 = CandidateImageRecord(
            candidate_id="CANDIDATE_B",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="Duplicate.jpg",
            creator_attribution="Author",
            license_identifier="CC-BY-4.0",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="cracks",
            retrieval_timestamp="",
            direct_download_url="https://example.com/img2.jpg",
        )

        hash_index = {}
        s1, m1 = downloader.download_candidate(c1, existing_hashes=hash_index)
        self.assertTrue(s1)
        self.assertEqual(c1.download_status, DownloadStatus.DOWNLOADED)

        s2, m2 = downloader.download_candidate(c2, existing_hashes=hash_index)
        self.assertTrue(s2)
        self.assertEqual(c2.download_status, DownloadStatus.SKIPPED_DUPLICATE)
        self.assertEqual(c2.duplicate_group_id, "CANDIDATE_A")

        # Verify only one physical file was created on disk
        downloaded_files = list(self.download_dir.glob("*.jpg"))
        self.assertEqual(len(downloaded_files), 1)
        self.assertEqual(downloaded_files[0].name, "CANDIDATE_A.jpg")

    def test_downloader_sanitizes_filename_and_blocks_path_traversal(self):
        downloader = ControlledImageDownloader(download_dir=self.download_dir)

        # Sanitizer removes invalid characters and path traversal dots
        sanitized = downloader.sanitize_candidate_id("../../etc/passwd")
        self.assertNotIn("..", sanitized)
        self.assertNotIn("/", sanitized)

        # Direct traversal injection attempt
        candidate = CandidateImageRecord(
            candidate_id="../escape_root",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="Traverse.jpg",
            creator_attribution="Author",
            license_identifier="CC0",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="cracks",
            retrieval_timestamp="",
            direct_download_url="https://example.com/test.jpg",
        )
        safe_id = downloader.sanitize_candidate_id(candidate.candidate_id)
        target = (self.download_dir / f"{safe_id}.jpg").resolve()
        self.assertTrue(target.is_relative_to(self.download_dir.resolve()))

    def test_downloader_handles_network_errors(self):
        downloader = ControlledImageDownloader(download_dir=self.download_dir)
        candidate = CandidateImageRecord(
            candidate_id="TEST_NET_ERR",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="NetErr.jpg",
            creator_attribution="Author",
            license_identifier="CC0",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="cracks",
            retrieval_timestamp="",
            direct_download_url="https://example.com/net_err.jpg",
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 429  # Rate limited

        mock_client = MagicMock()
        mock_client.stream.return_value.__enter__.return_value = mock_resp
        downloader._client = mock_client

        success, msg = downloader.download_candidate(candidate)
        self.assertFalse(success)
        self.assertEqual(candidate.download_status, DownloadStatus.FAILED)
        self.assertIn("HTTP error 429", msg)

    # --------------------------------------------------------------------------
    # 4. Manifest Roundtrip & Benchmark Export Honesty
    # --------------------------------------------------------------------------
    def test_manifest_csv_roundtrip(self):
        c = CandidateImageRecord(
            candidate_id="ROUNDTRIP_001",
            source_repository="Wikimedia Commons",
            source_page_url="https://commons.wikimedia.org/wiki/Search",
            original_image_page_url="https://commons.wikimedia.org/wiki/File:Rockfall.jpg",
            image_title="Rockfall on Mountain Pass.jpg",
            creator_attribution="Jane Smith",
            license_identifier="CC BY-SA 4.0",
            license_url="https://creativecommons.org/licenses/by-sa/4.0",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="3840x2160",
            approximate_geographic_region="Uttarakhand",
            candidate_subject="rockfall_road_blockage",
            retrieval_timestamp="2026-10-23T00:00:00Z",
            download_status=DownloadStatus.DOWNLOADED,
            image_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            duplicate_group_id="",
            review_status=ReviewStatus.UNREVIEWED,
            exclusion_reason="",
        )

        csv_path = Path(self.temp_dir.name) / "test_candidates.csv"
        PublicImageManifestManager.write_candidates_csv([c], csv_path)
        read_back = PublicImageManifestManager.read_candidates_csv(csv_path)

        self.assertEqual(len(read_back), 1)
        r = read_back[0]
        self.assertEqual(r.candidate_id, "ROUNDTRIP_001")
        self.assertEqual(r.image_title, "Rockfall on Mountain Pass.jpg")
        self.assertEqual(r.creator_attribution, "Jane Smith")
        self.assertEqual(r.intended_use_permission_status, IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION)
        self.assertEqual(r.image_sha256, c.image_sha256)

    def test_export_to_draft_benchmark_manifest_enforces_pending_labels(self):
        c = CandidateImageRecord(
            candidate_id="BENCH_001",
            source_repository="Wikimedia Commons",
            source_page_url="https://commons.wikimedia.org/wiki/Search",
            original_image_page_url="https://commons.wikimedia.org/wiki/File:Slide.jpg",
            image_title="Landslide Near Joshimath.jpg",
            creator_attribution="Field Geologist",
            license_identifier="CC BY-SA 4.0",
            license_url="https://creativecommons.org/licenses/by-sa/4.0",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="1920x1080",
            approximate_geographic_region="Joshimath",
            candidate_subject="tension_cracks",
            retrieval_timestamp="2026-10-23T01:00:00Z",
            download_status=DownloadStatus.DOWNLOADED,
            image_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        )

        bench_path = Path(self.temp_dir.name) / "draft_benchmark.csv"
        exported = PublicImageManifestManager.export_to_draft_benchmark_manifest([c], bench_path, split="dev")
        self.assertEqual(exported, 1)

        # In draft benchmark, labels must be strictly empty and adjudication_status must be pending
        loaded_samples = VLMEvaluationHarness.load_dataset_csv(bench_path)
        self.assertEqual(len(loaded_samples), 1)
        s = loaded_samples[0]
        self.assertEqual(s.image_id, "BENCH_001")
        self.assertIsNone(s.ground_truth_hazard)
        self.assertIsNone(s.annotator_1_label)
        self.assertIsNone(s.annotator_2_label)
        self.assertEqual(s.adjudication_status, "pending")
        self.assertIn("UNVERIFIED - REQUIRES INDEPENDENT GEOTECHNICAL REVIEW", s.notes)

    # --------------------------------------------------------------------------
    # 5. Manifest Validation & Leakage Prevention Guards
    # --------------------------------------------------------------------------
    def test_vlm_evaluation_strictly_excludes_unverified_from_test_benchmark(self):
        # When strict_ground_truth is enabled for the test split, unadjudicated samples must be rejected
        bench_csv = """image_id,image_path,source,license_or_permission_reference,adjudication_status,split
SAMPLE_UNADJ,eval/img1.jpg,Wikimedia,CC-BY-4.0,pending,test
"""
        csv_file = Path(self.temp_dir.name) / "test_bench_pending.csv"
        csv_file.write_text(bench_csv, encoding="utf-8")

        with self.assertRaises(MissingExpertGroundTruthError):
            VLMEvaluationHarness.load_dataset_csv(csv_file, strict_ground_truth=True)

    def test_vlm_evaluation_detects_site_group_leakage_across_splits(self):
        # Two photographs from the same event group spanning train and test
        bench_csv = """image_id,image_sha256,image_path,source,license_or_permission_reference,adjudicated_label,adjudication_status,duplicate_group_id,split
SAMPLE_A,hash1,eval/img1.jpg,USGS,CC0,high,adjudicated,CHAMOLI_EVENT_2021,train
SAMPLE_B,hash2,eval/img2.jpg,USGS,CC0,high,adjudicated,CHAMOLI_EVENT_2021,test
"""
        csv_file = Path(self.temp_dir.name) / "group_leakage.csv"
        csv_file.write_text(bench_csv, encoding="utf-8")

        with self.assertRaises(DataLeakageError):
            VLMEvaluationHarness.load_dataset_csv(csv_file)

    def test_vlm_evaluation_rejects_missing_source_under_strict_permissions(self):
        bench_csv = """image_id,image_sha256,image_path,source,license_or_permission_reference,adjudicated_label,adjudication_status,split
SAMPLE_NO_SRC,hash1,eval/img1.jpg,,CC0,high,adjudicated,test
"""
        csv_file = Path(self.temp_dir.name) / "no_source.csv"
        csv_file.write_text(bench_csv, encoding="utf-8")

        with self.assertRaises(InvalidSourceError):
            VLMEvaluationHarness.load_dataset_csv(csv_file, strict_permissions=True)

    # --------------------------------------------------------------------------
    # 6. Phase 2B Testing and Regression Protection
    # --------------------------------------------------------------------------
    def test_pagination_and_repeated_discovery(self):
        """Verify search generator pagination correctly retrieves across pages up to limit."""
        mock_client = MagicMock()
        page1_data = {
            "query": {
                "pages": {
                    "101": {
                        "title": "File:Slide_01.jpg",
                        "imageinfo": [{
                            "mime": "image/jpeg",
                            "url": "https://upload.wikimedia.org/slide_01.jpg",
                            "width": 1920,
                            "height": 1080,
                            "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}},
                        }],
                    }
                }
            },
            "continue": {"gsroffset": 1, "continue": "gsroffset||"},
        }
        page2_data = {
            "query": {
                "pages": {
                    "102": {
                        "title": "File:Slide_02.jpg",
                        "imageinfo": [{
                            "mime": "image/jpeg",
                            "url": "https://upload.wikimedia.org/slide_02.jpg",
                            "width": 1920,
                            "height": 1080,
                            "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}},
                        }],
                    }
                }
            }
        }

        resp1 = MagicMock()
        resp1.json.return_value = page1_data
        resp1.raise_for_status = MagicMock()

        resp2 = MagicMock()
        resp2.json.return_value = page2_data
        resp2.raise_for_status = MagicMock()

        mock_client.get.side_effect = [resp1, resp2]

        service = PublicImageDiscoveryService(http_client=mock_client, rate_limit_delay=0.0)
        recs = service.search_wikimedia_commons(query="landslide", limit=2, paginate=True)

        self.assertEqual(len(recs), 2)
        self.assertEqual(recs[0].candidate_id, "WMC_101")
        self.assertEqual(recs[1].candidate_id, "WMC_102")
        self.assertEqual(mock_client.get.call_count, 2)

    def test_stable_candidate_identity_and_manifest_idempotency(self):
        """Verify candidate identity is preserved stably across serializations."""
        c = CandidateImageRecord(
            candidate_id="WMC_STABLE_001",
            source_repository="Wikimedia Commons",
            source_page_url="https://commons.wikimedia.org",
            original_image_page_url="https://commons.wikimedia.org/wiki/File:Stable.jpg",
            image_title="Stable.jpg",
            creator_attribution="Author Name",
            license_identifier="CC BY-SA 4.0",
            license_url="https://creativecommons.org/licenses/by-sa/4.0",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="1920x1080",
            approximate_geographic_region="Uttarakhand",
            candidate_subject="tension_cracks",
            retrieval_timestamp="2026-10-23T01:00:00Z",
            event_site_group="Joshimath_Cluster",
            event_site_confidence=EventSiteConfidence.CONFIRMED_SITE,
            scientific_suitability_status=ScientificSuitabilityStatus.CANDIDATE,
            scene_type="slope_face",
            image_quality_assessment="high_resolution",
            relevance_to_ground_photo_triage="high",
        )

        p = Path(self.temp_dir.name) / "idempotent_test.csv"
        PublicImageManifestManager.write_candidates_csv([c], p)
        read1 = PublicImageManifestManager.read_candidates_csv(p)

        # Write again and verify perfect identity preservation
        PublicImageManifestManager.write_candidates_csv(read1, p)
        read2 = PublicImageManifestManager.read_candidates_csv(p)

        self.assertEqual(len(read2), 1)
        self.assertEqual(read2[0].candidate_id, "WMC_STABLE_001")
        self.assertEqual(read2[0].event_site_group, "Joshimath_Cluster")
        self.assertEqual(read2[0].scientific_suitability_status, ScientificSuitabilityStatus.CANDIDATE)

    def test_missing_ambiguous_and_changed_license_metadata(self):
        """Verify license evaluation correctly handles missing, ambiguous, and altered terms."""
        # Missing license
        v, u, e = LicenseGate.evaluate_license(None, "")
        self.assertEqual(v, LicenseVerificationStatus.UNVERIFIED)
        self.assertEqual(u, IntendedUseStatus.PENDING_REVIEW)

        v, u, e = LicenseGate.evaluate_license("Unknown", "")
        self.assertEqual(v, LicenseVerificationStatus.UNVERIFIED)
        self.assertEqual(u, IntendedUseStatus.PENDING_REVIEW)

        # Ambiguous custom license (e.g. Flickr Commons 'No restrictions')
        v, u, e = LicenseGate.evaluate_license("No restrictions", "https://www.flickr.com/commons/usage/")
        self.assertEqual(v, LicenseVerificationStatus.AMBIGUOUS)
        self.assertEqual(u, IntendedUseStatus.PENDING_REVIEW)
        self.assertIn("requires_legal_review", e)

        # Restrictive license
        v, u, e = LicenseGate.evaluate_license("CC BY-ND 4.0", "")
        self.assertEqual(v, LicenseVerificationStatus.REJECTED)
        self.assertEqual(u, IntendedUseStatus.REJECTED)

    def test_source_unavailability_and_http_rate_limiting(self):
        """Verify discovery service fails closed gracefully upon HTTP errors or rate limits."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("HTTP 429 Too Many Requests")

        service = PublicImageDiscoveryService(http_client=mock_client, rate_limit_delay=0.0)
        recs = service.search_wikimedia_commons(query="landslide", limit=5)
        # Must return empty list instead of crashing
        self.assertEqual(recs, [])

    def test_duplicate_source_ids_and_file_hashes(self):
        """Verify exact hash duplicates are skipped and assigned duplicate_group_id."""
        downloader = ControlledImageDownloader(download_dir=self.download_dir)
        c = CandidateImageRecord(
            candidate_id="WMC_DUP_002",
            source_repository="Wikimedia",
            source_page_url="url",
            original_image_page_url="url",
            image_title="dup.jpg",
            creator_attribution="Author",
            license_identifier="CC-BY-4.0",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="100x100",
            approximate_geographic_region="Region",
            candidate_subject="scars",
            retrieval_timestamp="ts",
            direct_download_url="http://fake/image.jpg",
        )

        existing = {"existing_sha256_hash_123456789": "WMC_ORIGINAL_001"}

        # Mock download response returning the duplicate hash
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "image/jpeg"}

        img_bytes = io.BytesIO()
        Image.new("RGB", (100, 100), color="blue").save(img_bytes, format="JPEG")
        raw = img_bytes.getvalue()

        # Compute real sha256 of raw
        import hashlib
        real_h = hashlib.sha256(raw).hexdigest()
        existing[real_h] = "WMC_ORIGINAL_001"

        mock_resp.iter_bytes.return_value = [raw]
        mock_client.stream.return_value.__enter__.return_value = mock_resp
        downloader._client = mock_client

        success, msg = downloader.download_candidate(c, existing_hashes=existing)
        self.assertTrue(success)
        self.assertEqual(c.download_status, DownloadStatus.SKIPPED_DUPLICATE)
        self.assertEqual(c.duplicate_group_id, "WMC_ORIGINAL_001")
        self.assertIn("duplicate_of_WMC_ORIGINAL_001", c.exclusion_reason)

    def test_event_site_grouping_behavior(self):
        """Verify physical event/site grouping correctly identifies coordinates, named sites, and uncertainties."""
        # 1. Matching coordinates (~1 km radius)
        grp, conf = PublicImageDiscoveryService._infer_event_site_group(
            clean_title="Rockfall.jpg", gps_lat="44.441195", gps_lon="6.414042"
        )
        self.assertEqual(grp, "GPS_44.44_6.41")
        self.assertEqual(conf, EventSiteConfidence.CONFIRMED_SITE)

        # 2. Recognized named landslide trigger
        grp, conf = PublicImageDiscoveryService._infer_event_site_group(
            clean_title="Bloc Lauzet P1010012mod.jpg"
        )
        self.assertEqual(grp, "Lauzet_Ubaye_Rockfall")
        self.assertEqual(conf, EventSiteConfidence.CONFIRMED_SITE)

        # 3. Uncertain / individual photo
        grp, conf = PublicImageDiscoveryService._infer_event_site_group(
            clean_title="General mountain slope.jpg"
        )
        self.assertEqual(grp, "UNKNOWN_EVENT_OR_SITE")
        self.assertEqual(conf, EventSiteConfidence.UNKNOWN)

    def test_no_automatic_download_of_pending_or_unapproved_candidates(self):
        """Verify candidate marked PENDING_REVIEW or REJECTED is never downloaded."""
        downloader = ControlledImageDownloader(download_dir=self.download_dir)
        c = CandidateImageRecord(
            candidate_id="WMC_PENDING_001",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="Pending.jpg",
            creator_attribution="Author",
            license_identifier="No restrictions",
            license_url="",
            license_verification_status=LicenseVerificationStatus.AMBIGUOUS,
            intended_use_permission_status=IntendedUseStatus.PENDING_REVIEW,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="",
            retrieval_timestamp="",
        )

        success, msg = downloader.download_candidate(c)
        self.assertFalse(success)
        self.assertEqual(c.download_status, DownloadStatus.SKIPPED_UNAPPROVED)
        self.assertIn("requires explicit approval", msg)

    def test_no_leakage_of_grouped_events_across_splits_extended(self):
        """Verify VLM harness detects event/site group leakage across splits."""
        bench_csv = """image_id,image_sha256,image_path,source,license_or_permission_reference,adjudicated_label,adjudication_status,event_site_group,split
SAMPLE_A,hash1,eval/img1.jpg,USGS,CC0,high,adjudicated,Lauzet_Ubaye_Rockfall,train
SAMPLE_B,hash2,eval/img2.jpg,USGS,CC0,high,adjudicated,Lauzet_Ubaye_Rockfall,test
"""
        csv_file = Path(self.temp_dir.name) / "event_leakage.csv"
        csv_file.write_text(bench_csv, encoding="utf-8")

        with self.assertRaises(DataLeakageError):
            VLMEvaluationHarness.load_dataset_csv(csv_file)

        # Verify UNKNOWN_EVENT_OR_SITE does NOT trigger false positive leakage
        bench_csv_ok = """image_id,image_sha256,image_path,source,license_or_permission_reference,adjudicated_label,adjudication_status,event_site_group,split
SAMPLE_C,hash3,eval/img3.jpg,USGS,CC0,high,adjudicated,UNKNOWN_EVENT_OR_SITE,train
SAMPLE_D,hash4,eval/img4.jpg,USGS,CC0,high,adjudicated,UNKNOWN_EVENT_OR_SITE,test
"""
        csv_file_ok = Path(self.temp_dir.name) / "unknown_group_ok.csv"
        csv_file_ok.write_text(bench_csv_ok, encoding="utf-8")
        samples = VLMEvaluationHarness.load_dataset_csv(csv_file_ok)
        self.assertEqual(len(samples), 2)

    def test_safe_failure_when_remote_metadata_cannot_be_verified(self):
        """Verify downloader fails safely when remote source returns 404."""
        downloader = ControlledImageDownloader(download_dir=self.download_dir)
        c = CandidateImageRecord(
            candidate_id="WMC_FAIL_001",
            source_repository="Wikimedia",
            source_page_url="",
            original_image_page_url="",
            image_title="Missing.jpg",
            creator_attribution="Author",
            license_identifier="CC-BY-4.0",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="",
            retrieval_timestamp="",
            direct_download_url="https://commons.wikimedia.org/missing.jpg",
        )

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_client.stream.return_value.__enter__.return_value = mock_resp
        downloader._client = mock_client

        success, msg = downloader.download_candidate(c)
        self.assertFalse(success)
        self.assertEqual(c.download_status, DownloadStatus.FAILED)
        self.assertIn("http_404", c.exclusion_reason)

    def test_manifest_schema_migration_preserves_data(self):
        """Verify schema migration safely converts 21-column records to 28-column format."""
        legacy_csv = """candidate_id,source_repository,source_page_url,original_image_page_url,image_title,creator_attribution,license_identifier,license_url,license_verification_status,intended_use_permission_status,media_type,dimensions,approximate_geographic_region,candidate_subject,retrieval_timestamp,download_status,image_sha256,duplicate_group_id,review_status,exclusion_reason,direct_download_url
LEGACY_001,Wikimedia,https://commons.wikimedia.org,https://commons.wikimedia.org/wiki/File:Bloc_Lauzet.jpg,Bloc Lauzet.jpg,Photographer,CC BY-SA 4.0,https://creativecommons.org,VERIFIED,APPROVED_FOR_REDISTRIBUTION,image/jpeg,1920x1080,"Coordinates: 44.44, 6.41",rockfall_debris,2026-10-23T01:00:00Z,downloaded,hash123,,unreviewed,,https://upload.wikimedia.org/bloc.jpg
"""
        in_p = Path(self.temp_dir.name) / "legacy_in.csv"
        out_p = Path(self.temp_dir.name) / "migrated_out.csv"
        in_p.write_text(legacy_csv, encoding="utf-8")

        count = PublicImageManifestManager.migrate_manifest_schema(in_p, out_p)
        self.assertEqual(count, 1)

        migrated = PublicImageManifestManager.read_candidates_csv(out_p)
        self.assertEqual(len(migrated), 1)
        m = migrated[0]
        self.assertEqual(m.candidate_id, "LEGACY_001")
        self.assertEqual(m.event_site_group, "Lauzet_Ubaye_Rockfall")
        self.assertEqual(m.event_site_confidence, EventSiteConfidence.CONFIRMED_SITE)
        self.assertEqual(m.scientific_suitability_status, ScientificSuitabilityStatus.CANDIDATE)
        self.assertEqual(m.scene_type, "slope_face")
        self.assertEqual(m.image_sha256, "hash123")
        self.assertEqual(m.creator_attribution, "Photographer")


    def test_resolve_derivative_url(self):
        """Verify resolve_derivative_url queries MediaWiki API for thumburl."""
        downloader = ControlledImageDownloader(download_dir=self.download_dir)
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "query": {
                "pages": {
                    "123": {
                        "imageinfo": [
                            {"thumburl": "https://thumb.wikimedia.org/1920px-test.jpg"}
                        ]
                    }
                }
            }
        }
        mock_client.get.return_value = mock_resp
        downloader._client = mock_client

        url = downloader.resolve_derivative_url("File:Test.jpg", target_width=1920)
        self.assertEqual(url, "https://thumb.wikimedia.org/1920px-test.jpg")

    def test_download_oversized_with_derivative_fallback(self):
        """Verify oversized master falls back safely to 1920px derivative."""
        # Generate a small valid JPEG for derivative
        img = Image.new("RGB", (64, 64), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        valid_jpeg_bytes = buf.getvalue()

        max_size = len(valid_jpeg_bytes) + 100
        oversized_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * (max_size + 500)

        downloader = ControlledImageDownloader(
            download_dir=self.download_dir,
            max_file_size_bytes=max_size,
            allow_derivative_fallback=True,
        )
        c = CandidateImageRecord(
            candidate_id="WMC_OVERSIZED_001",
            source_repository="Wikimedia Commons",
            source_page_url="",
            original_image_page_url="",
            image_title="Large_Landslide.jpg",
            creator_attribution="Photographer",
            license_identifier="CC BY-SA 4.0",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="",
            approximate_geographic_region="",
            candidate_subject="mudflow_debris_flow",
            retrieval_timestamp="",
            direct_download_url="https://upload.wikimedia.org/large_master.jpg",
        )

        mock_client = MagicMock()

        def mock_stream(method, url):
            resp = MagicMock()
            resp.status_code = 200
            resp.headers = {"content-type": "image/jpeg"}
            if "derivative" in url:
                resp.iter_bytes.return_value = [valid_jpeg_bytes]
            else:
                resp.iter_bytes.return_value = [oversized_bytes]
            cm = MagicMock()
            cm.__enter__.return_value = resp
            return cm

        mock_client.stream.side_effect = mock_stream
        downloader._client = mock_client

        with patch.object(downloader, "resolve_derivative_url", return_value="https://thumb.wikimedia.org/derivative.jpg"):
            success, msg = downloader.download_candidate(c)

        self.assertTrue(success)
        self.assertEqual(c.download_status, DownloadStatus.DOWNLOADED)
        self.assertTrue((self.download_dir / "WMC_OVERSIZED_001.jpg").exists())
        self.assertTrue(len(c.image_sha256) > 0)

    def test_compute_image_dhash_and_hamming_distance(self):
        """Verify dhash computation and hamming distance metrics."""
        img1 = Image.new("RGB", (100, 100), color="white")
        img2 = Image.new("RGB", (100, 100), color="white")
        h1 = compute_image_dhash(img1)
        h2 = compute_image_dhash(img2)
        self.assertEqual(h1, h2)
        self.assertEqual(hamming_distance(h1, h2), 0)

        # Image with distinct left-to-right contrast (left white, right black)
        img3 = Image.new("L", (100, 100), color=0)
        img3.paste(255, (0, 0, 50, 100))
        h3 = compute_image_dhash(img3)
        dist = hamming_distance(h1, h3)
        self.assertGreater(dist, 0)

    def test_detect_near_duplicates(self):
        """Verify pairwise near-duplicate detection matches close hashes."""
        hashes = {
            "IMG_A": "0000000000000000",
            "IMG_B": "0000000000000001",  # 1 bit diff
            "IMG_C": "ffffffffffffffff",  # 64 bit diff
        }
        dups = detect_near_duplicates(hashes, threshold=10)
        self.assertEqual(len(dups), 1)
        self.assertEqual(dups[0][0], "IMG_A")
        self.assertEqual(dups[0][1], "IMG_B")
        self.assertEqual(dups[0][2], 1)

    def test_export_benchmark_filters_unsuitable_candidates(self):
        """Verify export to benchmark ignores UNSUITABLE or non-CANDIDATE records."""
        c_valid = CandidateImageRecord(
            candidate_id="WMC_VALID_001",
            source_repository="Wikimedia Commons",
            source_page_url="",
            original_image_page_url="https://commons.wikimedia.org/file.jpg",
            image_title="Valid_Slope.jpg",
            creator_attribution="Author",
            license_identifier="CC BY-SA 4.0",
            license_url="https://creativecommons.org",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="1920x1080",
            approximate_geographic_region="Himalayas",
            candidate_subject="slope_face",
            retrieval_timestamp="2026-10-23T01:00:00Z",
            download_status=DownloadStatus.DOWNLOADED,
            image_sha256="abcdef1234567890",
            scientific_suitability_status=ScientificSuitabilityStatus.CANDIDATE,
        )
        c_unsuitable = CandidateImageRecord(
            candidate_id="WMC_UNSUITABLE_001",
            source_repository="Wikimedia Commons",
            source_page_url="",
            original_image_page_url="https://commons.wikimedia.org/file2.jpg",
            image_title="Mars_Crater.jpg",
            creator_attribution="NASA",
            license_identifier="Public domain",
            license_url="",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="1920x1080",
            approximate_geographic_region="Mars",
            candidate_subject="water_seepage_drainage",
            retrieval_timestamp="2026-10-23T01:00:00Z",
            download_status=DownloadStatus.DOWNLOADED,
            image_sha256="123456abcdef7890",
            scientific_suitability_status=ScientificSuitabilityStatus.UNSUITABLE,
        )

        out_csv = Path(self.temp_dir.name) / "draft_bench.csv"
        count = PublicImageManifestManager.export_to_draft_benchmark_manifest(
            [c_valid, c_unsuitable], out_csv, split="dev"
        )
        self.assertEqual(count, 1)

        import csv
        with open(out_csv, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["image_id"], "WMC_VALID_001")

    # --------------------------------------------------------------------------
    # 10. SSRF, URL Safety, Storage Isolation, and Non-Overwrite Tests
    # --------------------------------------------------------------------------
    def test_validate_safe_url_accepts_valid_http_and_https(self):
        """Verify that standard external HTTP and HTTPS URLs pass URL safety validation."""
        valid_urls = [
            "https://upload.wikimedia.org/wikipedia/commons/a/a1/Example.jpg",
            "http://commons.wikimedia.org/wiki/File:Example.jpg",
            "https://example.org/geotechnical_photo.png",
        ]
        for url in valid_urls:
            ControlledImageDownloader.validate_safe_url(url)

    def test_validate_safe_url_blocks_unsafe_schemes(self):
        """Verify that non-HTTP(S) schemes are blocked by URL validation."""
        unsafe_urls = [
            "ftp://ftp.example.com/image.jpg",
            "file:///C:/Windows/System32/cmd.exe",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
            "gopher://example.com/image",
        ]
        for url in unsafe_urls:
            with self.assertRaises(PublicAcquisitionError):
                ControlledImageDownloader.validate_safe_url(url)

    def test_validate_safe_url_blocks_ssrf_and_private_ips(self):
        """Verify that loopbacks, private RFC1918 subnets, cloud metadata, and internal domains are blocked."""
        ssrf_targets = [
            "http://localhost/image.jpg",
            "http://127.0.0.1/admin.jpg",
            "http://127.0.0.2:8000/photo.jpg",
            "http://0.0.0.0/test.png",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.0.1.50/private.jpg",
            "http://192.168.1.100/router.jpg",
            "http://172.16.0.5/infra.png",
            "http://172.31.255.255/internal.png",
            "http://database.internal/secret.jpg",
            "http://cluster.local/img.png",
        ]
        for url in ssrf_targets:
            with self.assertRaises(PublicAcquisitionError):
                ControlledImageDownloader.validate_safe_url(url)

    def test_validate_isolated_download_dir_blocks_production_uploads(self):
        """Verify that ControlledImageDownloader rejects paths inside production upload directories."""
        production_paths = [
            Path("/var/app/backend/uploads"),
            Path("C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/uploads"),
            Path("C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend_uploads"),
            Path("/data/production/upload/photos"),
        ]
        for p in production_paths:
            with self.assertRaises(PublicAcquisitionError):
                ControlledImageDownloader._validate_isolated_download_dir(p)

        # Isolated paths must succeed
        isolated_paths = [
            Path(self.temp_dir.name) / "public_candidates" / "batch_2g",
            Path(self.temp_dir.name) / "temp_images",
            Path("C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/data/public_candidates/images"),
        ]
        for p in isolated_paths:
            # Should not raise
            ControlledImageDownloader._validate_isolated_download_dir(p)

    def test_download_candidate_strict_non_overwrite_preservation(self):
        """Verify that existing downloaded files are strictly preserved without re-downloading or overwriting."""
        downloader = ControlledImageDownloader(
            download_dir=self.download_dir,
            http_client=MagicMock(),
        )
        cand_id = "WMC_PRESERVED_001"
        target_file = self.download_dir / f"{cand_id}.jpg"
        original_bytes = b"EXACT_PRESERVED_FILE_CONTENT_NO_OVERWRITE"
        target_file.write_bytes(original_bytes)

        import hashlib
        expected_sha = hashlib.sha256(original_bytes).hexdigest().lower()

        candidate = CandidateImageRecord(
            candidate_id=cand_id,
            source_repository="Wikimedia Commons",
            source_page_url="",
            original_image_page_url="",
            image_title="Preserved.jpg",
            creator_attribution="Photographer",
            license_identifier="CC BY-SA 4.0",
            license_url="https://creativecommons.org",
            license_verification_status=LicenseVerificationStatus.VERIFIED,
            intended_use_permission_status=IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
            media_type="image/jpeg",
            dimensions="1000x1000",
            approximate_geographic_region="Uttarakhand",
            candidate_subject="slope_face",
            retrieval_timestamp="2026-10-23T00:00:00Z",
            download_status=DownloadStatus.NOT_DOWNLOADED,
            direct_download_url="https://upload.wikimedia.org/file.jpg",
        )

        success, msg = downloader.download_candidate(candidate)
        self.assertTrue(success)
        self.assertIn("already exists", msg)
        self.assertEqual(candidate.download_status, DownloadStatus.DOWNLOADED)
        self.assertEqual(candidate.image_sha256, expected_sha)
        # Content on disk must be unaltered
        self.assertEqual(target_file.read_bytes(), original_bytes)
        # Mock client should not have performed any network stream requests
        downloader._client.stream.assert_not_called()


if __name__ == "__main__":
    unittest.main()
