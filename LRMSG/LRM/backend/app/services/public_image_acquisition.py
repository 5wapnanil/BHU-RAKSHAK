"""Public Landslide Image Discovery, Licensing Gate, and Controlled Ingestion Service.

Provides automated, license-aware discovery from public repositories (such as Wikimedia Commons),
enforces strict 4-state licensing gates, performs safe streaming downloads with magic-byte and
integrity validation, and securely formats candidates for expert geotechnical review.
"""

import csv
import hashlib
import html
import io
import logging
import os
from pathlib import Path
import re
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import httpx
from PIL import Image

logger = logging.getLogger(__name__)

# Standard 4-state intended use permission classification
class IntendedUseStatus:
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED_FOR_INTERNAL_EVALUATION = "APPROVED_FOR_INTERNAL_EVALUATION"
    APPROVED_FOR_REDISTRIBUTION = "APPROVED_FOR_REDISTRIBUTION"
    REJECTED = "REJECTED"


class LicenseVerificationStatus:
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    AMBIGUOUS = "AMBIGUOUS"
    REJECTED = "REJECTED"


class DownloadStatus:
    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADED = "downloaded"
    SKIPPED_UNAPPROVED = "skipped_unapproved"
    SKIPPED_DUPLICATE = "skipped_duplicate"
    FAILED = "failed"


class ReviewStatus:
    UNREVIEWED = "unreviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ScientificSuitabilityStatus:
    CANDIDATE = "CANDIDATE"
    REQUIRES_QUALITY_REVIEW = "REQUIRES_QUALITY_REVIEW"
    UNSUITABLE = "UNSUITABLE"
    AWAITING_EXPERT_ANNOTATION = "AWAITING_EXPERT_ANNOTATION"


class EventSiteConfidence:
    CONFIRMED_SITE = "CONFIRMED_SITE"
    TENTATIVE_GEOGRAPHIC_CLUSTER = "TENTATIVE_GEOGRAPHIC_CLUSTER"
    UNKNOWN = "UNKNOWN"


# Formats & Magic Bytes
ALLOWED_RASTER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Standard magic bytes for image formats
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
WEBP_RIFF = b"RIFF"
WEBP_HEADER = b"WEBP"

DEFAULT_MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
DEFAULT_USER_AGENT = (
    "PahaarPulse-ScientificBenchmark/1.0 "
    "(https://pahaarpulse.org/; contact: scientific-evaluation@pahaarpulse.org) httpx/0.28"
)

# Standard candidate topics mapping to visible hazard indicators and controls
STANDARD_CANDIDATE_TOPICS = {
    "landslide_scars": "landslide scar",
    "roadside_slope_failures": "landslide blocked road",
    "tension_cracks": "tension crack slope",
    "rockfall_debris": "rockfall boulder",
    "mudflow_debris_flow": "debris flow",
    "slope_displacement": "rotational slide scarp",
    "water_seepage_drainage": "water seepage slope",
    "non_landslide_controls": "mountain pass road",
}

# License Taxonomy Sets
PERMISSIVE_REDISTRIBUTION_LICENSES = {
    "cc0",
    "cc0 1.0",
    "cc0-1.0",
    "public domain",
    "pd",
    "cc-pd-mark",
    "pd-usgov",
    "pd-usgs",
    "pd-nasa",
    "cc-by-4.0",
    "cc by 4.0",
    "cc-by-3.0",
    "cc by 3.0",
    "cc-by-2.5",
    "cc by 2.5",
    "cc-by-2.0",
    "cc by 2.0",
    "cc-by-sa-4.0",
    "cc by-sa 4.0",
    "cc-by-sa-3.0",
    "cc by-sa 3.0",
    "cc-by-sa-2.5",
    "cc by-sa 2.5",
    "cc-by-sa-2.0",
    "cc by-sa 2.0",
}

INTERNAL_EVALUATION_ONLY_LICENSES = {
    "cc-by-nc-4.0",
    "cc by-nc 4.0",
    "cc-by-nc-3.0",
    "cc by-nc 3.0",
    "cc-by-nc-sa-4.0",
    "cc by-nc-sa 4.0",
    "cc-by-nc-sa-3.0",
    "cc by-nc-sa 3.0",
}

EXPLICITLY_REJECTED_LICENSES = {
    "all rights reserved",
    "copyrighted",
    "fair use",
    "cc-by-nd-4.0",
    "cc by-nd 4.0",
    "cc-by-nd-3.0",
    "cc by-nd 3.0",
    "cc-by-nc-nd-4.0",
    "cc by-nc-nd 4.0",
    "cc-by-nc-nd-3.0",
    "cc by-nc-nd 3.0",
}

CANDIDATE_CSV_HEADERS = [
    "candidate_id",
    "source_repository",
    "source_page_url",
    "original_image_page_url",
    "image_title",
    "creator_attribution",
    "license_identifier",
    "license_url",
    "license_verification_status",
    "intended_use_permission_status",
    "media_type",
    "dimensions",
    "approximate_geographic_region",
    "candidate_subject",
    "retrieval_timestamp",
    "download_status",
    "image_sha256",
    "duplicate_group_id",
    "event_site_group",
    "event_site_confidence",
    "scientific_suitability_status",
    "scene_type",
    "image_quality_assessment",
    "relevance_to_ground_photo_triage",
    "suitability_exclusion_reason",
    "review_status",
    "exclusion_reason",
    "direct_download_url",
]


class PublicAcquisitionError(Exception):
    """Base exception for public acquisition operations."""
    pass


class LicenseRejectionError(PublicAcquisitionError):
    """Raised when an unapproved or rejected license is encountered."""
    pass


class InvalidMediaSignatureError(PublicAcquisitionError):
    """Raised when downloaded bytes do not match expected image magic bytes."""
    pass


class OversizedFileError(PublicAcquisitionError):
    """Raised when candidate file exceeds maximum allowed bytes."""
    pass


class CorruptImageError(PublicAcquisitionError):
    """Raised when image bytes fail decoding or raster verification."""
    pass


class PathTraversalError(PublicAcquisitionError):
    """Raised when a candidate filename or path escapes the designated download folder."""
    pass


class DuplicateContentError(PublicAcquisitionError):
    """Raised when duplicate content is detected across candidate downloads."""
    pass


class CandidateImageRecord:
    """Represents a discovered public landslide candidate photograph."""

    def __init__(
        self,
        candidate_id: str,
        source_repository: str,
        source_page_url: str,
        original_image_page_url: str,
        image_title: str,
        creator_attribution: str,
        license_identifier: str,
        license_url: str,
        license_verification_status: str,
        intended_use_permission_status: str,
        media_type: str,
        dimensions: str,
        approximate_geographic_region: str,
        candidate_subject: str,
        retrieval_timestamp: str,
        download_status: str = DownloadStatus.NOT_DOWNLOADED,
        image_sha256: str = "",
        duplicate_group_id: str = "",
        event_site_group: str = "UNKNOWN_EVENT_OR_SITE",
        event_site_confidence: str = EventSiteConfidence.UNKNOWN,
        scientific_suitability_status: str = ScientificSuitabilityStatus.CANDIDATE,
        scene_type: str = "unknown",
        image_quality_assessment: str = "unreviewed",
        relevance_to_ground_photo_triage: str = "unreviewed",
        suitability_exclusion_reason: str = "",
        review_status: str = ReviewStatus.UNREVIEWED,
        exclusion_reason: str = "",
        direct_download_url: str = "",
    ):
        self.candidate_id = candidate_id
        self.source_repository = source_repository
        self.source_page_url = source_page_url
        self.original_image_page_url = original_image_page_url
        self.image_title = image_title
        self.creator_attribution = creator_attribution
        self.license_identifier = license_identifier
        self.license_url = license_url
        self.license_verification_status = license_verification_status
        self.intended_use_permission_status = intended_use_permission_status
        self.media_type = media_type
        self.dimensions = dimensions
        self.approximate_geographic_region = approximate_geographic_region
        self.candidate_subject = candidate_subject
        self.retrieval_timestamp = retrieval_timestamp
        self.download_status = download_status
        self.image_sha256 = image_sha256
        self.duplicate_group_id = duplicate_group_id
        self.event_site_group = event_site_group
        self.event_site_confidence = event_site_confidence
        self.scientific_suitability_status = scientific_suitability_status
        self.scene_type = scene_type
        self.image_quality_assessment = image_quality_assessment
        self.relevance_to_ground_photo_triage = relevance_to_ground_photo_triage
        self.suitability_exclusion_reason = suitability_exclusion_reason
        self.review_status = review_status
        self.exclusion_reason = exclusion_reason
        self.direct_download_url = direct_download_url

    def to_dict(self) -> Dict[str, str]:
        """Convert record to dictionary matching CANDIDATE_CSV_HEADERS."""
        return {
            "candidate_id": self.candidate_id,
            "source_repository": self.source_repository,
            "source_page_url": self.source_page_url,
            "original_image_page_url": self.original_image_page_url,
            "image_title": self.image_title,
            "creator_attribution": self.creator_attribution,
            "license_identifier": self.license_identifier,
            "license_url": self.license_url,
            "license_verification_status": self.license_verification_status,
            "intended_use_permission_status": self.intended_use_permission_status,
            "media_type": self.media_type,
            "dimensions": self.dimensions,
            "approximate_geographic_region": self.approximate_geographic_region,
            "candidate_subject": self.candidate_subject,
            "retrieval_timestamp": self.retrieval_timestamp,
            "download_status": self.download_status,
            "image_sha256": self.image_sha256,
            "duplicate_group_id": self.duplicate_group_id,
            "event_site_group": self.event_site_group,
            "event_site_confidence": self.event_site_confidence,
            "scientific_suitability_status": self.scientific_suitability_status,
            "scene_type": self.scene_type,
            "image_quality_assessment": self.image_quality_assessment,
            "relevance_to_ground_photo_triage": self.relevance_to_ground_photo_triage,
            "suitability_exclusion_reason": self.suitability_exclusion_reason,
            "review_status": self.review_status,
            "exclusion_reason": self.exclusion_reason,
            "direct_download_url": self.direct_download_url,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, str], direct_download_url: str = "") -> "CandidateImageRecord":
        return cls(
            candidate_id=d.get("candidate_id", ""),
            source_repository=d.get("source_repository", ""),
            source_page_url=d.get("source_page_url", ""),
            original_image_page_url=d.get("original_image_page_url", ""),
            image_title=d.get("image_title", ""),
            creator_attribution=d.get("creator_attribution", ""),
            license_identifier=d.get("license_identifier", ""),
            license_url=d.get("license_url", ""),
            license_verification_status=d.get("license_verification_status", LicenseVerificationStatus.UNVERIFIED),
            intended_use_permission_status=d.get("intended_use_permission_status", IntendedUseStatus.PENDING_REVIEW),
            media_type=d.get("media_type", ""),
            dimensions=d.get("dimensions", ""),
            approximate_geographic_region=d.get("approximate_geographic_region", ""),
            candidate_subject=d.get("candidate_subject", ""),
            retrieval_timestamp=d.get("retrieval_timestamp", ""),
            download_status=d.get("download_status", DownloadStatus.NOT_DOWNLOADED),
            image_sha256=d.get("image_sha256", ""),
            duplicate_group_id=d.get("duplicate_group_id", ""),
            event_site_group=d.get("event_site_group") or "UNKNOWN_EVENT_OR_SITE",
            event_site_confidence=d.get("event_site_confidence") or EventSiteConfidence.UNKNOWN,
            scientific_suitability_status=d.get("scientific_suitability_status") or ScientificSuitabilityStatus.CANDIDATE,
            scene_type=d.get("scene_type") or "unknown",
            image_quality_assessment=d.get("image_quality_assessment") or "unreviewed",
            relevance_to_ground_photo_triage=d.get("relevance_to_ground_photo_triage") or "unreviewed",
            suitability_exclusion_reason=d.get("suitability_exclusion_reason", ""),
            review_status=d.get("review_status", ReviewStatus.UNREVIEWED),
            exclusion_reason=d.get("exclusion_reason", ""),
            direct_download_url=direct_download_url or d.get("direct_download_url", ""),
        )


class LicenseGate:
    """Evaluates and enforces licensing gates for candidate public images."""

    @staticmethod
    def clean_text(raw_text: Optional[str]) -> str:
        """Strip HTML tags, decode entities, and normalize whitespace."""
        if not raw_text:
            return ""
        no_html = re.sub(r"<[^>]+>", " ", str(raw_text))
        unescaped = html.unescape(no_html)
        return " ".join(unescaped.split())

    @staticmethod
    def evaluate_license(
        raw_license: Optional[str],
        license_url: Optional[str] = "",
        allow_internal_nc: bool = True,
    ) -> Tuple[str, str, str]:
        """Evaluate licensing status and assign permission level.

        Returns:
            Tuple of (verification_status, intended_use_status, exclusion_reason)
        """
        lic_clean = LicenseGate.clean_text(raw_license).strip()
        url_clean = (license_url or "").strip()

        if not lic_clean or lic_clean.lower() in ("unknown", "unverified", "none", "blank"):
            return (
                LicenseVerificationStatus.UNVERIFIED,
                IntendedUseStatus.PENDING_REVIEW,
                "missing_or_unverified_license_field",
            )

        lic_lower = lic_clean.lower().replace("_", "-")

        # 1. Check for explicitly rejected / proprietary / ND licenses
        for rej in EXPLICITLY_REJECTED_LICENSES:
            if rej in lic_lower:
                return (
                    LicenseVerificationStatus.REJECTED,
                    IntendedUseStatus.REJECTED,
                    f"license_prohibits_derivative_or_redistribution ({lic_clean})",
                )

        # 2. Check for permissive redistribution licenses
        for perm in PERMISSIVE_REDISTRIBUTION_LICENSES:
            if perm == lic_lower or f"{perm} " in lic_lower or f" {perm}" in lic_lower:
                return (
                    LicenseVerificationStatus.VERIFIED,
                    IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
                    "",
                )

        # Also inspect license_url if present
        if url_clean:
            parsed = urlparse(url_clean)
            path = parsed.path.lower()
            if "/publicdomain/zero/" in path or "/publicdomain/mark/" in path:
                return (
                    LicenseVerificationStatus.VERIFIED,
                    IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
                    "",
                )
            if "/licenses/by/" in path or "/licenses/by-sa/" in path:
                if "/by-nc/" not in path and "/by-nd/" not in path:
                    return (
                        LicenseVerificationStatus.VERIFIED,
                        IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
                        "",
                    )

        # 3. Check for non-commercial internal evaluation licenses
        for nc in INTERNAL_EVALUATION_ONLY_LICENSES:
            if nc in lic_lower:
                if allow_internal_nc:
                    return (
                        LicenseVerificationStatus.VERIFIED,
                        IntendedUseStatus.APPROVED_FOR_INTERNAL_EVALUATION,
                        "non_commercial_clause_restricts_redistribution",
                    )
                else:
                    return (
                        LicenseVerificationStatus.REJECTED,
                        IntendedUseStatus.REJECTED,
                        "non_commercial_license_disallowed_under_strict_redistribution",
                    )

        if url_clean and ("/licenses/by-nc/" in url_clean.lower() or "/licenses/by-nc-sa/" in url_clean.lower()):
            if allow_internal_nc:
                return (
                    LicenseVerificationStatus.VERIFIED,
                    IntendedUseStatus.APPROVED_FOR_INTERNAL_EVALUATION,
                    "non_commercial_clause_restricts_redistribution",
                )
            else:
                return (
                    LicenseVerificationStatus.REJECTED,
                    IntendedUseStatus.REJECTED,
                    "non_commercial_license_disallowed_under_strict_redistribution",
                )

        # 4. Unrecognized or ambiguous license terms -> PENDING_REVIEW
        return (
            LicenseVerificationStatus.AMBIGUOUS,
            IntendedUseStatus.PENDING_REVIEW,
            f"unrecognized_custom_license_requires_legal_review ({lic_clean})",
        )


class PublicImageDiscoveryService:
    """Discovers public candidate photographs from legitimate repositories."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        rate_limit_delay: float = 1.0,
        http_client: Optional[httpx.Client] = None,
    ):
        self.user_agent = user_agent
        self.rate_limit_delay = rate_limit_delay
        self._client = http_client

    def _get_client(self) -> httpx.Client:
        if self._client:
            return self._client
        return httpx.Client(
            headers={"User-Agent": self.user_agent},
            timeout=15.0,
            follow_redirects=True,
        )

    @staticmethod
    def _infer_event_site_group(
        clean_title: str,
        gps_lat: str = "",
        gps_lon: str = "",
        region: str = "",
        categories: str = "",
    ) -> Tuple[str, str]:
        """Infer physical event or site group to prevent evaluation split leakage.

        Returns:
            Tuple of (event_site_group, event_site_confidence)
        """
        # 1. Geographic coordinate cluster (~1.1 km radius)
        if gps_lat and gps_lon:
            try:
                lat_f = round(float(gps_lat), 2)
                lon_f = round(float(gps_lon), 2)
                return f"GPS_{lat_f}_{lon_f}", EventSiteConfidence.CONFIRMED_SITE
            except (ValueError, TypeError):
                pass

        # 2. Known named site clusters
        title_lower = clean_title.lower()
        cats_lower = categories.lower()

        known_sites = [
            ("lauzet", "Lauzet_Ubaye_Rockfall"),
            ("sesvenna", "Sesvenna_Alps_Torrent"),
            ("sirac", "Sirac_Ecrins_Torrent"),
            ("parnidis", "Nida_Parnidis_Dune"),
            ("vitkai", "Vitkaiciai_Lithuania_Outcrop"),
            ("kinnaur", "Kinnaur_Himachal_Pradesh"),
            ("oeschinen", "Oeschinensee_Switzerland"),
            ("chamoli", "Chamoli_Event_2021"),
            ("joshimath", "Joshimath_Subsidence"),
            ("seba beach", "Seba_Beach_Alberta"),
            ("moosfluh", "Moosfluh_Aletsch"),
            ("curral das freiras", "Curral_das_Freiras_Madeira"),
            ("salapungan", "Candaba_Pampanga_Slips"),
            ("magumbali", "Candaba_Pampanga_Slips"),
        ]

        for trigger, group_id in known_sites:
            if trigger in title_lower or trigger in cats_lower:
                return group_id, EventSiteConfidence.CONFIRMED_SITE

        # Geograph pattern with no specific cluster -> UNKNOWN
        if "geograph.org.uk" in title_lower:
            return "UNKNOWN_EVENT_OR_SITE", EventSiteConfidence.UNKNOWN

        # Series number pattern (e.g., Series_Name_01.jpg, Series_Name_02.jpg)
        m_series = re.match(r"^(.+?)[-_\s]+(?:\d{2,4}|[a-z]?\d{1,3})\.(?:jpg|jpeg|png|webp)$", title_lower)
        if m_series:
            base_prefix = re.sub(r"[^a-z0-9]", "_", m_series.group(1)).strip("_")
            if len(base_prefix) > 6:
                return f"Series_{base_prefix[:30]}", EventSiteConfidence.TENTATIVE_GEOGRAPHIC_CLUSTER

        # When event/site identity is unknown, explicitly record UNKNOWN_EVENT_OR_SITE
        return "UNKNOWN_EVENT_OR_SITE", EventSiteConfidence.UNKNOWN

    @staticmethod
    def _assess_scientific_suitability(
        clean_title: str,
        mime: str,
        width: int,
        height: int,
        subject_category: str,
        categories: str = "",
        credit: str = "",
        author: str = "",
    ) -> Tuple[str, str, str, str, str]:
        """Assess scientific suitability for ground-photo hazard screening.

        Returns:
            Tuple of (suitability_status, scene_type, quality, relevance, exclusion_reason)
        """
        title_lower = clean_title.lower()
        cats_lower = categories.lower()
        combined_text = f"{title_lower} {cats_lower} {credit.lower()} {author.lower()}"

        # 1. Historical printed documents / scans
        historical_markers = [
            "annual report",
            "physiography",
            "internet archive book images",
            "flickr's 'the commons'",
            "geological survey bulletin",
            "memoir",
            "handbook",
            "engraving",
            "vintage print",
            "(1910)",
            "(1911)",
            "(190",
            "(18",
        ]
        if any(marker in combined_text for marker in historical_markers):
            return (
                ScientificSuitabilityStatus.UNSUITABLE,
                "historical_book_scan",
                "adequate",
                "irrelevant",
                "historical_printed_document_scan",
            )

        # 2. Diagrams, charts, maps, and drawings (ensure 'geograph' is not mistaken for 'graph')
        diagram_regex = r"\b(diagram|diagrams|cross[- ]section|schematic|topographic map|map of|chart|graphs?|drawing|illustration)\b"
        # Temporarily mask geograph.org.uk
        masked_title = re.sub(r"geograph\.org\.uk", "geograph_token", title_lower)
        if re.search(diagram_regex, masked_title):
            return (
                ScientificSuitabilityStatus.UNSUITABLE,
                "diagram_or_map",
                "adequate",
                "irrelevant",
                "diagram_or_non_photographic_raster",
            )

        # 3. Aerial or satellite remote sensing
        aerial_markers = ["aerial photograph", "aerial view", "satellite image", "orthophoto", "sentinel", "landsat"]
        if any(marker in combined_text for marker in aerial_markers):
            return (
                ScientificSuitabilityStatus.REQUIRES_QUALITY_REVIEW,
                "aerial_or_distant",
                "high_resolution" if width >= 1920 else "adequate",
                "low",
                "aerial_perspective_requires_ground_triage_review",
            )

        # 4. Low resolution raster
        if width > 0 and height > 0 and min(width, height) < 400:
            return (
                ScientificSuitabilityStatus.REQUIRES_QUALITY_REVIEW,
                "slope_face",
                "low_resolution",
                "moderate",
                "dimensions_below_400px",
            )

        # 5. Non-landslide control scene
        if subject_category == "non_landslide_controls" or "mountain pass" in title_lower:
            return (
                ScientificSuitabilityStatus.CANDIDATE,
                "landscape_pass",
                "high_resolution" if width >= 1920 else "adequate",
                "moderate",
                "",
            )

        # 6. Roadside / ground-level field landslide photograph
        scene_type = (
            "ground_level_roadside"
            if any(w in title_lower for w in ("road", "highway", "pass", "block"))
            else "slope_face"
        )
        quality = "high_resolution" if width >= 1920 else ("adequate" if width >= 640 else "low_resolution")
        return (
            ScientificSuitabilityStatus.CANDIDATE,
            scene_type,
            quality,
            "high",
            "",
        )

    def search_wikimedia_commons(
        self,
        query: str,
        subject_category: str = "general_landslide",
        limit: int = 10,
        paginate: bool = True,
    ) -> List[CandidateImageRecord]:
        """Query Wikimedia Commons MediaWiki API for candidate files.

        Supports pagination across search generator pages.
        Returns candidate metadata records without downloading full image files.
        """
        api_url = "https://commons.wikimedia.org/w/api.php"
        client = self._get_client()
        candidates: List[CandidateImageRecord] = []
        seen_page_ids: Set[str] = set()
        continue_params: Dict[str, str] = {}
        retrieval_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        page_fetches = 0
        max_page_fetches = 3
        while len(candidates) < limit and page_fetches < max_page_fetches:
            page_fetches += 1
            batch_limit = 50  # Fetch 50 items per call for maximum raster throughput
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": "6",  # File: namespace
                "gsrlimit": str(batch_limit),
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata|sha1",
            }
            params.update(continue_params)

            try:
                resp = client.get(api_url, params=params)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error("Wikimedia Commons query failed for '%s': %s", query, e)
                break

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                break

            for page_id, page in pages.items():
                if page_id in seen_page_ids:
                    continue
                seen_page_ids.add(page_id)

                title = page.get("title", "")
                imageinfo_list = page.get("imageinfo", [])
                if not imageinfo_list:
                    continue

                ii = imageinfo_list[0]
                mime = (ii.get("mime") or "").lower()
                url = ii.get("url") or ""
                desc_url = ii.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}"
                width = ii.get("width", 0)
                height = ii.get("height", 0)
                mw_sha1 = ii.get("sha1", "")

                # Skip non-raster media (SVGs, PDFs, videos, audio)
                if mime not in ALLOWED_MIME_TYPES:
                    continue

                extmeta = ii.get("extmetadata", {})
                raw_lic = extmeta.get("LicenseShortName", {}).get("value", "")
                lic_url = extmeta.get("LicenseUrl", {}).get("value", "")
                artist = extmeta.get("Artist", {}).get("value", "")
                credit = extmeta.get("Credit", {}).get("value", "")
                author = LicenseGate.clean_text(artist) or LicenseGate.clean_text(credit) or "Unknown Creator"

                # Geographic estimation from metadata
                gps_lat = extmeta.get("GPSLatitude", {}).get("value", "")
                gps_lon = extmeta.get("GPSLongitude", {}).get("value", "")
                cats = extmeta.get("Categories", {}).get("value", "")
                region = ""
                if gps_lat and gps_lon:
                    region = f"Coordinates: {gps_lat}, {gps_lon}"
                elif "India" in cats or "Himalaya" in cats or "Uttarakhand" in cats:
                    region = "Himalayan Region (Categorized)"
                elif cats:
                    region = cats.split(";")[0].strip()

                clean_title = title.removeprefix("File:").strip()

                # Evaluate licensing gates
                verif_status, use_status, excl_reason = LicenseGate.evaluate_license(raw_lic, lic_url)

                # Heuristic Event/Site Grouping
                event_grp, event_conf = self._infer_event_site_group(
                    clean_title=clean_title,
                    gps_lat=gps_lat,
                    gps_lon=gps_lon,
                    region=region,
                    categories=cats,
                )

                # Scientific Suitability Assessment
                suitability, scene_type, quality, relevance, suit_reason = self._assess_scientific_suitability(
                    clean_title=clean_title,
                    mime=mime,
                    width=width,
                    height=height,
                    subject_category=subject_category,
                    categories=cats,
                    credit=credit,
                    author=author,
                )

                cand_id = f"WMC_{page_id}"

                rec = CandidateImageRecord(
                    candidate_id=cand_id,
                    source_repository="Wikimedia Commons",
                    source_page_url=f"https://commons.wikimedia.org/wiki/Special:Search?search={query.replace(' ', '+')}",
                    original_image_page_url=desc_url,
                    image_title=clean_title,
                    creator_attribution=author,
                    license_identifier=LicenseGate.clean_text(raw_lic) or "Unverified",
                    license_url=lic_url or "",
                    license_verification_status=verif_status,
                    intended_use_permission_status=use_status,
                    media_type=mime,
                    dimensions=f"{width}x{height}",
                    approximate_geographic_region=region,
                    candidate_subject=subject_category,
                    retrieval_timestamp=retrieval_ts,
                    download_status=DownloadStatus.NOT_DOWNLOADED,
                    image_sha256="",
                    duplicate_group_id="",
                    event_site_group=event_grp,
                    event_site_confidence=event_conf,
                    scientific_suitability_status=suitability,
                    scene_type=scene_type,
                    image_quality_assessment=quality,
                    relevance_to_ground_photo_triage=relevance,
                    suitability_exclusion_reason=suit_reason,
                    review_status=ReviewStatus.UNREVIEWED,
                    exclusion_reason=excl_reason,
                    direct_download_url=url,
                )
                candidates.append(rec)
                if len(candidates) >= limit:
                    break

            if not paginate:
                break

            cont = data.get("continue")
            if not cont:
                break
            continue_params = cont
            if self.rate_limit_delay > 0:
                time.sleep(self.rate_limit_delay * 0.5)

        return candidates

    def discover_all_topics(
        self,
        topics: Optional[Dict[str, str]] = None,
        limit_per_topic: int = 10,
    ) -> List[CandidateImageRecord]:
        """Perform discovery across standard geotechnical hazard topics."""
        search_topics = topics or STANDARD_CANDIDATE_TOPICS
        all_records: List[CandidateImageRecord] = []
        seen_cand_ids: Set[str] = set()
        seen_titles: Dict[str, str] = {}

        for category, query in search_topics.items():
            logger.info("Discovering candidates for topic '%s' (query: '%s')...", category, query)
            recs = self.search_wikimedia_commons(query=query, subject_category=category, limit=limit_per_topic)
            for r in recs:
                if r.candidate_id in seen_cand_ids:
                    continue
                seen_cand_ids.add(r.candidate_id)

                # Check for near duplicate titles
                norm_title = re.sub(r"[^a-z0-9]", "", r.image_title.lower())
                if norm_title in seen_titles:
                    r.duplicate_group_id = seen_titles[norm_title]
                    r.exclusion_reason = f"potential_near_duplicate_of_{seen_titles[norm_title]}"
                else:
                    seen_titles[norm_title] = r.candidate_id

                all_records.append(r)

            if self.rate_limit_delay > 0:
                time.sleep(self.rate_limit_delay)

        return all_records


class ControlledImageDownloader:
    """Manages secure downloading, magic-byte verification, and storage of approved images."""

    def __init__(
        self,
        download_dir: Path,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
        user_agent: str = DEFAULT_USER_AGENT,
        http_client: Optional[httpx.Client] = None,
        allow_derivative_fallback: bool = True,
    ):
        self.download_dir = Path(download_dir)
        self.max_file_size_bytes = max_file_size_bytes
        self.user_agent = user_agent
        self._client = http_client
        self.allow_derivative_fallback = allow_derivative_fallback
        self._validate_isolated_download_dir(self.download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _validate_isolated_download_dir(cls, dir_path: Path) -> None:
        """Validate that download directory is safely isolated from production upload folders."""
        resolved = dir_path.resolve()
        parts_lower = [p.lower() for p in resolved.parts]
        str_resolved = str(resolved).lower()
        if "public_candidates" not in str_resolved and "tmp" not in str_resolved and "temp" not in str_resolved:
            if "uploads" in parts_lower or "backend_uploads" in parts_lower or "upload" in parts_lower:
                raise PublicAcquisitionError(
                    f"Security violation: ControlledImageDownloader cannot write to production upload directory: {resolved}"
                )

    @staticmethod
    def validate_safe_url(url: str) -> None:
        """Verify that candidate download URL uses safe scheme and does not target private networks."""
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()
        if scheme not in ("http", "https"):
            raise PublicAcquisitionError(f"Unsupported or unsafe URL scheme: '{scheme}' in {url}")

        host = (parsed.hostname or "").lower()
        if not host:
            raise PublicAcquisitionError(f"Missing hostname in URL: {url}")

        # Block localhost, loopbacks, internal IPs, link-local, and cloud metadata endpoints
        if (
            host in ("localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254")
            or host.startswith("127.")
            or host.startswith("10.")
            or host.startswith("192.168.")
            or host.startswith("172.16.")
            or host.startswith("172.17.")
            or host.startswith("172.18.")
            or host.startswith("172.19.")
            or host.startswith("172.2")
            or host.startswith("172.30.")
            or host.startswith("172.31.")
            or host.endswith(".internal")
            or host.endswith(".local")
        ):
            raise PublicAcquisitionError(f"Security violation: Rejected private or internal network host: '{host}'")

    def _get_client(self) -> httpx.Client:
        if self._client:
            return self._client
        return httpx.Client(
            headers={"User-Agent": self.user_agent},
            timeout=30.0,
            follow_redirects=True,
        )

    @staticmethod
    def sanitize_candidate_id(cand_id: str) -> str:
        """Sanitize candidate ID to prevent directory traversal or invalid filename characters."""
        clean = re.sub(r"[^A-Za-z0-9_-]", "_", cand_id)
        if not clean:
            clean = f"candidate_{int(time.time())}"
        return clean

    @staticmethod
    def verify_magic_bytes(header: bytes) -> str:
        """Verify image magic bytes against supported raster types.

        Returns format string ('jpeg', 'png', 'webp').
        Raises InvalidMediaSignatureError if unrecognized.
        """
        if len(header) < 12:
            raise InvalidMediaSignatureError(f"File too small for magic byte validation ({len(header)} bytes)")

        if header.startswith(JPEG_MAGIC):
            return "jpeg"
        if header.startswith(PNG_MAGIC):
            return "png"
        if header[:4] == WEBP_RIFF and header[8:12] == WEBP_HEADER:
            return "webp"

        raise InvalidMediaSignatureError(
            f"Invalid file signature! First 12 bytes {header[:12]!r} do not match JPEG, PNG, or WebP standards."
        )

    def resolve_derivative_url(self, image_title: str, target_width: int = 1920) -> Optional[str]:
        """Query Wikimedia Commons API for a scaled derivative of the given width."""
        title = image_title.strip()
        if not title:
            return None
        if not title.startswith("File:"):
            title = f"File:{title}"
        client = self._get_client()
        try:
            res = client.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "titles": title,
                    "prop": "imageinfo",
                    "iiprop": "url|size",
                    "iiurlwidth": target_width,
                },
            )
            if res.status_code == 200:
                pages = res.json().get("query", {}).get("pages", {})
                for p in pages.values():
                    ii = p.get("imageinfo", [])
                    if ii and ii[0].get("thumburl"):
                        return ii[0].get("thumburl")
        except Exception as e:
            logger.warning("Could not resolve derivative URL for %s: %s", title, e)
        return None

    def _stream_and_verify(
        self,
        url: str,
        candidate: CandidateImageRecord,
        temp_path: Path,
        target_path: Path,
        existing_hashes: Optional[Dict[str, str]] = None,
        is_derivative: bool = False,
    ) -> Tuple[bool, str, bool]:
        """Stream image from url, verify magic bytes, size, Pillow decode, and write to target.

        Returns (success, message, oversized).
        """
        client = self._get_client()
        try:
            with client.stream("GET", url) as response:
                if response.status_code != 200:
                    candidate.download_status = DownloadStatus.FAILED
                    candidate.exclusion_reason = f"http_{response.status_code}"
                    return (False, f"HTTP error {response.status_code}", False)

                # Check Content-Type header if provided
                ct = response.headers.get("content-type", "").lower()
                if ct and not any(allowed in ct for allowed in ("image/jpeg", "image/png", "image/webp", "octet-stream")):
                    candidate.download_status = DownloadStatus.FAILED
                    candidate.exclusion_reason = f"unsupported_content_type_{ct}"
                    return (False, f"Unsupported Content-Type header '{ct}'", False)

                # Stream and validate bytes
                hasher = hashlib.sha256()
                total_bytes = 0
                first_chunk = True
                oversized = False

                with open(temp_path, "wb") as f_out:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        if not chunk:
                            continue

                        # Check magic bytes on first chunk
                        if first_chunk:
                            first_chunk = False
                            self.verify_magic_bytes(chunk)

                        total_bytes += len(chunk)
                        if total_bytes > self.max_file_size_bytes:
                            oversized = True
                            break

                        f_out.write(chunk)
                        hasher.update(chunk)

                if oversized:
                    temp_path.unlink(missing_ok=True)
                    return (False, f"File exceeded maximum size limit ({self.max_file_size_bytes} bytes)", True)

            if total_bytes == 0:
                temp_path.unlink(missing_ok=True)
                candidate.download_status = DownloadStatus.FAILED
                candidate.exclusion_reason = "zero_byte_file"
                return (False, "Zero-byte file received", False)

            # Validate raster integrity via Pillow using in-memory bytes to avoid Windows file locks
            try:
                with open(temp_path, "rb") as f_img:
                    raw_bytes = f_img.read()
                with Image.open(io.BytesIO(raw_bytes)) as img:
                    img.verify()
                with Image.open(io.BytesIO(raw_bytes)) as img:
                    w, h = img.size
                    candidate.dimensions = f"{w}x{h}"
            except Exception as pe:
                temp_path.unlink(missing_ok=True)
                candidate.download_status = DownloadStatus.FAILED
                candidate.exclusion_reason = f"corrupt_raster_file: {pe}"
                return (False, f"Corrupt image file: {pe}", False)

            # Compute SHA-256 digest
            sha256 = hasher.hexdigest().lower()

            # Check duplicate hash against index
            if existing_hashes and sha256 in existing_hashes:
                dup_id = existing_hashes[sha256]
                temp_path.unlink(missing_ok=True)
                candidate.download_status = DownloadStatus.SKIPPED_DUPLICATE
                candidate.image_sha256 = sha256
                candidate.duplicate_group_id = dup_id
                candidate.exclusion_reason = f"duplicate_of_{dup_id}"
                return (True, f"Skipped duplicate of {dup_id}", False)

            # Move verified file to final target destination
            temp_path.replace(target_path)
            candidate.download_status = DownloadStatus.DOWNLOADED
            candidate.image_sha256 = sha256
            candidate.exclusion_reason = ""

            if existing_hashes is not None:
                existing_hashes[sha256] = candidate.candidate_id

            label = "1920px derivative" if is_derivative else "image"
            logger.info("Successfully downloaded and verified %s %s (%s)", label, candidate.candidate_id, sha256[:12])
            return (True, f"Downloaded {label} successfully ({total_bytes} bytes, SHA-256: {sha256[:12]})", False)

        except Exception as e:
            temp_path.unlink(missing_ok=True)
            candidate.download_status = DownloadStatus.FAILED
            candidate.exclusion_reason = f"download_exception: {e}"
            logger.error("Download failed for candidate %s: %s", candidate.candidate_id, e)
            return (False, str(e), False)

    def download_candidate(
        self,
        candidate: CandidateImageRecord,
        existing_hashes: Optional[Dict[str, str]] = None,
        allow_derivative: bool = True,
    ) -> Tuple[bool, str]:
        """Safely download and validate an approved candidate photograph.

        Returns (success, message).
        """
        # 1. Gate check: must be approved for evaluation or redistribution
        allowed_statuses = {
            IntendedUseStatus.APPROVED_FOR_INTERNAL_EVALUATION,
            IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
        }
        if candidate.intended_use_permission_status not in allowed_statuses:
            candidate.download_status = DownloadStatus.SKIPPED_UNAPPROVED
            msg = (
                f"Candidate {candidate.candidate_id} skipped: Intended-use status is "
                f"'{candidate.intended_use_permission_status}'. Download requires explicit approval."
            )
            logger.warning(msg)
            return (False, msg)

        # 2. Check direct download URL (resolve dynamically via MediaWiki API if needed)
        client = self._get_client()
        url = candidate.direct_download_url
        if not url and candidate.image_title:
            title = candidate.image_title
            if not title.startswith("File:"):
                title = f"File:{title}"
            try:
                res = client.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "titles": title,
                        "prop": "imageinfo",
                        "iiprop": "url",
                    },
                )
                if res.status_code == 200:
                    pages = res.json().get("query", {}).get("pages", {})
                    for p in pages.values():
                        ii = p.get("imageinfo", [])
                        if ii and ii[0].get("url"):
                            url = ii[0].get("url")
                            candidate.direct_download_url = url
                            break
            except Exception as e:
                logger.warning("Could not resolve download URL for %s: %s", title, e)

        if not url:
            candidate.download_status = DownloadStatus.FAILED
            candidate.exclusion_reason = "missing_direct_download_url"
            return (False, "Missing direct download URL")

        # Validate URL safety
        try:
            self.validate_safe_url(url)
        except PublicAcquisitionError as pe:
            candidate.download_status = DownloadStatus.FAILED
            candidate.exclusion_reason = f"unsafe_url: {pe}"
            return (False, str(pe))

        # 3. Path traversal protection
        safe_base = self.sanitize_candidate_id(candidate.candidate_id)
        # Infer extension from URL or media_type
        ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
        ext = ext_map.get(candidate.media_type, ".jpg")
        target_filename = f"{safe_base}{ext}"
        target_path = (self.download_dir / target_filename).resolve()

        if not target_path.is_relative_to(self.download_dir.resolve()):
            candidate.download_status = DownloadStatus.FAILED
            candidate.exclusion_reason = "path_traversal_attempt"
            raise PathTraversalError(f"Path traversal detected for candidate {candidate.candidate_id}")

        # 4. Strict non-overwrite protection
        if target_path.exists():
            h = hashlib.sha256()
            with open(target_path, "rb") as f_ex:
                while chunk := f_ex.read(65536):
                    h.update(chunk)
            existing_sha = h.hexdigest().lower()
            candidate.download_status = DownloadStatus.DOWNLOADED
            candidate.image_sha256 = existing_sha
            logger.info("Candidate file already exists at %s; preserved without overwriting.", target_filename)
            return (True, f"File already exists on disk at {target_filename}; preserved without overwriting.")

        temp_path = self.download_dir / f"{target_filename}.tmp_{int(time.time()*1000)}"

        success, msg, oversized = self._stream_and_verify(
            url=url,
            candidate=candidate,
            temp_path=temp_path,
            target_path=target_path,
            existing_hashes=existing_hashes,
            is_derivative=False,
        )

        if oversized:
            if allow_derivative and self.allow_derivative_fallback and candidate.source_repository == "Wikimedia Commons" and candidate.image_title:
                derivative_url = self.resolve_derivative_url(candidate.image_title, target_width=1920)
                if derivative_url and derivative_url != url:
                    try:
                        self.validate_safe_url(derivative_url)
                    except PublicAcquisitionError:
                        derivative_url = None
                    if derivative_url:
                        logger.info("Master image oversized; trying 1920px derivative for %s: %s", candidate.candidate_id, derivative_url)
                        d_success, d_msg, d_oversized = self._stream_and_verify(
                            url=derivative_url,
                            candidate=candidate,
                            temp_path=temp_path,
                            target_path=target_path,
                            existing_hashes=existing_hashes,
                            is_derivative=True,
                        )
                        if d_success:
                            return (True, d_msg)

            candidate.download_status = DownloadStatus.FAILED
            candidate.exclusion_reason = f"file_size_exceeded_maximum_limit"
            return (False, msg)

        return (success, msg)


class PublicImageManifestManager:
    """Manages public candidate CSV manifests and exports to benchmark templates."""

    @staticmethod
    def write_candidates_csv(candidates: List[CandidateImageRecord], csv_path: Union[str, Path]) -> None:
        """Write candidate records to CSV."""
        path = Path(csv_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CANDIDATE_CSV_HEADERS)
            writer.writeheader()
            for c in candidates:
                writer.writerow(c.to_dict())

    @staticmethod
    def read_candidates_csv(csv_path: Union[str, Path]) -> List[CandidateImageRecord]:
        """Read candidate records from CSV."""
        path = Path(csv_path)
        if not path.exists():
            return []

        candidates: List[CandidateImageRecord] = []
        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                candidates.append(CandidateImageRecord.from_dict(row))

        return candidates

    @staticmethod
    def migrate_manifest_schema(
        input_csv: Union[str, Path],
        output_csv: Optional[Union[str, Path]] = None,
    ) -> int:
        """Migrate older candidate manifest CSV to latest 28-column schema with event and suitability inferences.

        Preserves all existing data while applying event clustering and suitability heuristics
        to unpopulated fields.
        """
        in_path = Path(input_csv)
        out_path = Path(output_csv) if output_csv else in_path
        if not in_path.exists():
            return 0

        candidates = PublicImageManifestManager.read_candidates_csv(in_path)
        for c in candidates:
            # If event_site_group is default or empty, attempt inference
            if not c.event_site_group or c.event_site_group == "UNKNOWN_EVENT_OR_SITE":
                grp, conf = PublicImageDiscoveryService._infer_event_site_group(
                    clean_title=c.image_title,
                    region=c.approximate_geographic_region,
                )
                c.event_site_group = grp
                c.event_site_confidence = conf

            # If suitability is default or unreviewed, attempt assessment
            if c.scientific_suitability_status == ScientificSuitabilityStatus.CANDIDATE and c.scene_type == "unknown":
                suit, scene, qual, rel, reason = PublicImageDiscoveryService._assess_scientific_suitability(
                    clean_title=c.image_title,
                    mime=c.media_type,
                    width=int(c.dimensions.split("x")[0]) if "x" in c.dimensions else 0,
                    height=int(c.dimensions.split("x")[1]) if "x" in c.dimensions else 0,
                    subject_category=c.candidate_subject,
                    author=c.creator_attribution,
                )
                c.scientific_suitability_status = suit
                c.scene_type = scene
                c.image_quality_assessment = qual
                c.relevance_to_ground_photo_triage = rel
                c.suitability_exclusion_reason = reason

        PublicImageManifestManager.write_candidates_csv(candidates, out_path)
        return len(candidates)

    @staticmethod
    def export_to_draft_benchmark_manifest(
        candidates: List[CandidateImageRecord],
        output_benchmark_csv: Union[str, Path],
        split: str = "dev",
    ) -> int:
        """Export downloaded and verified candidates into the 18-column benchmark format.

        CRITICAL GEOTECHNICAL HONESTY RULE:
        Ground-truth labels (annotator_1, annotator_2, adjudicated) remain strictly empty
        and adjudication_status is set to 'pending'. Search queries and candidate subjects
        are recorded in 'notes' as unverified hints only and NEVER as ground truth.
        """
        path = Path(output_benchmark_csv)
        path.parent.mkdir(parents=True, exist_ok=True)

        benchmark_headers = [
            "image_id",
            "image_sha256",
            "image_path_or_controlled_reference",
            "source",
            "license_or_permission_reference",
            "capture_date",
            "region",
            "image_quality",
            "observable_indicators",
            "annotator_1_id",
            "annotator_1_label",
            "annotator_2_id",
            "annotator_2_label",
            "adjudicated_label",
            "adjudication_status",
            "exclusion_reason",
            "duplicate_group_id",
            "split",
            "notes",
        ]

        count = 0
        rows = []
        for c in candidates:
            # Only export downloaded images with valid SHA-256 and approved licenses
            if c.download_status != DownloadStatus.DOWNLOADED or not c.image_sha256:
                continue
            if c.intended_use_permission_status not in (
                IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION,
                IntendedUseStatus.APPROVED_FOR_INTERNAL_EVALUATION,
            ):
                continue
            if c.scientific_suitability_status != ScientificSuitabilityStatus.CANDIDATE:
                continue

            event_or_dup = (
                c.event_site_group
                if c.event_site_group and c.event_site_group != "UNKNOWN_EVENT_OR_SITE"
                else (c.duplicate_group_id or "")
            )

            # Determine actual file extension
            ext = ".png" if c.media_type == "image/png" else (".webp" if c.media_type == "image/webp" else ".jpg")
            img_rel_path = f"data/public_candidates/images/{c.candidate_id}{ext}"
            for check_ext in (".jpg", ".jpeg", ".png", ".webp"):
                candidate_disk_file = Path(f"data/public_candidates/images/{c.candidate_id}{check_ext}")
                if candidate_disk_file.exists():
                    img_rel_path = f"data/public_candidates/images/{c.candidate_id}{check_ext}"
                    break

            # In draft benchmark manifest, labels are strictly empty and status is pending
            row = {
                "image_id": c.candidate_id,
                "image_sha256": c.image_sha256,
                "image_path_or_controlled_reference": img_rel_path,
                "source": f"{c.source_repository} ({c.original_image_page_url})",
                "license_or_permission_reference": f"{c.license_identifier} ({c.license_url})",
                "capture_date": c.retrieval_timestamp.split("T")[0] if c.retrieval_timestamp else "",
                "region": c.approximate_geographic_region or "Unknown Region",
                "image_quality": "adequate",
                "observable_indicators": "",
                "annotator_1_id": "",
                "annotator_1_label": "",
                "annotator_2_id": "",
                "annotator_2_label": "",
                "adjudicated_label": "",
                "adjudication_status": "pending",
                "exclusion_reason": "",
                "duplicate_group_id": event_or_dup,
                "split": split,
                "notes": (
                    f"Candidate title: '{c.image_title}'. "
                    f"Candidate subject query: '{c.candidate_subject}'. "
                    f"Author: {c.creator_attribution}. "
                    f"Scene type: {c.scene_type}. "
                    f"Suitability: {c.scientific_suitability_status}. "
                    f"Event group: {c.event_site_group} ({c.event_site_confidence}). "
                    f"STATUS: UNVERIFIED - REQUIRES INDEPENDENT GEOTECHNICAL REVIEW."
                ),
            }
            rows.append(row)
            count += 1

        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=benchmark_headers)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        return count


def compute_image_dhash(image_path_or_bytes: Union[str, Path, bytes, Image.Image], hash_size: int = 8) -> str:
    """Compute difference hash (dhash) for perceptual near-duplicate detection.

    Resizes image to (hash_size + 1, hash_size), converts to grayscale,
    and compares adjacent horizontal pixels.
    """
    if isinstance(image_path_or_bytes, Image.Image):
        gray = image_path_or_bytes.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    elif isinstance(image_path_or_bytes, (str, Path)):
        with Image.open(image_path_or_bytes) as img:
            gray = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    else:
        with Image.open(io.BytesIO(image_path_or_bytes)) as img:
            gray = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)

    if hasattr(gray, "get_flattened_data"):
        pixels = list(gray.get_flattened_data())
    else:
        pixels = list(gray.getdata())

    diff = []
    for row in range(hash_size):
        row_start = row * (hash_size + 1)
        for col in range(hash_size):
            diff.append(pixels[row_start + col] > pixels[row_start + col + 1])

    val = 0
    for bit in diff:
        val = (val << 1) | bit
    return f"{val:016x}"


def hamming_distance(hash1_hex: str, hash2_hex: str) -> int:
    """Compute Hamming distance between two hex-encoded hashes."""
    val1 = int(hash1_hex, 16)
    val2 = int(hash2_hex, 16)
    return bin(val1 ^ val2).count("1")


def detect_near_duplicates(
    image_hashes: Dict[str, str],
    threshold: int = 10,
) -> List[Tuple[str, str, int]]:
    """Compare dhashes pairwise and identify suspected near-duplicate pairs (distance <= threshold).

    Returns list of (id_a, id_b, distance).
    """
    items = list(image_hashes.items())
    near_dups = []
    for i in range(len(items)):
        id_a, h_a = items[i]
        for j in range(i + 1, len(items)):
            id_b, h_b = items[j]
            dist = hamming_distance(h_a, h_b)
            if dist <= threshold:
                near_dups.append((id_a, id_b, dist))
    return near_dups
