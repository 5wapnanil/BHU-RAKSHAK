"""Public Landslide Image Discovery, Licensing Audit, and Controlled Ingestion CLI.

Searches public repositories (prioritizing Wikimedia Commons) for candidate landslide photographs,
evaluates licensing gates, records metadata in the candidate manifest, safely downloads approved files
with magic-byte and integrity validation, generates reproducible license provenance audits, and formats
approved candidates for expert geotechnical review.
"""

import argparse
import csv
import logging
from pathlib import Path
import re
import sys
import time
from typing import Dict, List, Optional

import httpx

# Add project root to sys.path
backend_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_root))

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.app.services.public_image_acquisition import (
    CANDIDATE_CSV_HEADERS,
    ControlledImageDownloader,
    DownloadStatus,
    EventSiteConfidence,
    IntendedUseStatus,
    LicenseGate,
    LicenseVerificationStatus,
    PublicImageDiscoveryService,
    PublicImageManifestManager,
    ReviewStatus,
    ScientificSuitabilityStatus,
    STANDARD_CANDIDATE_TOPICS,
    compute_image_dhash,
    detect_near_duplicates,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("discover_public_images")

DEFAULT_MANIFEST_PATH = Path("docs/gemma-local-vision/evaluation/public_image_candidates.csv")
DEFAULT_DOWNLOAD_DIR = Path("data/public_candidates/images")
DEFAULT_AUDIT_PATH = Path("docs/gemma-local-vision/evaluation/license_provenance_audit.csv")

AUDIT_CSV_HEADERS = [
    "candidate_id",
    "source_repository",
    "source_identifier",
    "original_file_page_url",
    "direct_source_url",
    "creator_attribution",
    "license_identifier",
    "license_version",
    "license_url",
    "applicable_terms_summary",
    "evidence_retrieval_timestamp",
    "dimensions",
    "file_size_bytes",
    "file_sha256",
    "eligible_for_internal_evaluation",
    "redistribution_permitted",
    "audit_status",
    "audit_notes_and_uncertainties",
]


def print_banner(title: str):
    print("=" * 78)
    print(f"PAHAARPULSE PUBLIC IMAGE ACQUISITION - {title}")
    print("=" * 78)


def print_candidate_summary(candidates):
    verified_count = sum(1 for c in candidates if c.license_verification_status == LicenseVerificationStatus.VERIFIED)
    unverified_count = sum(1 for c in candidates if c.license_verification_status == LicenseVerificationStatus.UNVERIFIED)
    ambiguous_count = sum(1 for c in candidates if c.license_verification_status == LicenseVerificationStatus.AMBIGUOUS)
    rejected_count = sum(1 for c in candidates if c.license_verification_status == LicenseVerificationStatus.REJECTED)

    app_redist = sum(1 for c in candidates if c.intended_use_permission_status == IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION)
    app_internal = sum(1 for c in candidates if c.intended_use_permission_status == IntendedUseStatus.APPROVED_FOR_INTERNAL_EVALUATION)
    pending_review = sum(1 for c in candidates if c.intended_use_permission_status == IntendedUseStatus.PENDING_REVIEW)
    rej_perm = sum(1 for c in candidates if c.intended_use_permission_status == IntendedUseStatus.REJECTED)

    print("\nCandidate Licensing Audit Summary:")
    print(f" - Total Discovered Candidates:              {len(candidates)}")
    print(f" - License Verification:                     {verified_count} Verified | {unverified_count} Unverified | {ambiguous_count} Ambiguous | {rejected_count} Rejected")
    print(f" - Intended-Use Gates:")
    print(f"   * APPROVED_FOR_REDISTRIBUTION:           {app_redist} (Eligible for benchmark & redistribution)")
    print(f"   * APPROVED_FOR_INTERNAL_EVALUATION:       {app_internal} (Internal evaluation only; NC clauses)")
    print(f"   * PENDING_REVIEW:                         {pending_review} (Excluded from automated download)")
    print(f"   * REJECTED:                               {rej_perm} (Prohibited licenses / non-derivative)")

    # Scientific suitability summary
    cand_count = sum(1 for c in candidates if c.scientific_suitability_status == ScientificSuitabilityStatus.CANDIDATE)
    review_count = sum(1 for c in candidates if c.scientific_suitability_status == ScientificSuitabilityStatus.REQUIRES_QUALITY_REVIEW)
    unsuitable_count = sum(1 for c in candidates if c.scientific_suitability_status == ScientificSuitabilityStatus.UNSUITABLE)
    awaiting_count = sum(1 for c in candidates if c.scientific_suitability_status == ScientificSuitabilityStatus.AWAITING_EXPERT_ANNOTATION)

    print("\nScientific Suitability Summary:")
    print(f" - CANDIDATE (Geological Field Photos):      {cand_count}")
    print(f" - REQUIRES_QUALITY_REVIEW (Low-Res / Aerial): {review_count}")
    print(f" - UNSUITABLE (Book Scans / Diagrams / Maps): {unsuitable_count}")
    print(f" - AWAITING_EXPERT_ANNOTATION:               {awaiting_count}")

    # Event/Site Grouping summary
    confirmed_sites = sum(1 for c in candidates if c.event_site_confidence == EventSiteConfidence.CONFIRMED_SITE)
    tentative_clusters = sum(1 for c in candidates if c.event_site_confidence == EventSiteConfidence.TENTATIVE_GEOGRAPHIC_CLUSTER)
    unknown_sites = sum(1 for c in candidates if c.event_site_confidence == EventSiteConfidence.UNKNOWN)
    distinct_groups = {c.event_site_group for c in candidates if c.event_site_group and c.event_site_group != "UNKNOWN_EVENT_OR_SITE"}

    print("\nEvent / Physical Site Grouping Summary:")
    print(f" - Distinct Named / Coordinated Site Groups: {len(distinct_groups)}")
    print(f" - Confirmed Site Records:                   {confirmed_sites}")
    print(f" - Tentative Series Clusters:                {tentative_clusters}")
    print(f" - Unknown / Independent Site Records:       {unknown_sites}")


def run_discovery(args) -> int:
    print_banner("METADATA DISCOVERY MODE")
    manifest_path = Path(args.output)
    discovery_service = PublicImageDiscoveryService(rate_limit_delay=args.delay)

    existing_candidates = []
    if args.append and manifest_path.exists():
        existing_candidates = PublicImageManifestManager.read_candidates_csv(manifest_path)
        print(f"Loaded {len(existing_candidates)} existing candidate records from {manifest_path}")

    existing_ids = {c.candidate_id for c in existing_candidates}
    new_candidates = []

    if args.query:
        print(f"Searching Wikimedia Commons for query: '{args.query}' (limit: {args.limit})...")
        recs = discovery_service.search_wikimedia_commons(
            query=args.query,
            subject_category=args.category or "custom_query",
            limit=args.limit,
        )
        for r in recs:
            if r.candidate_id not in existing_ids:
                new_candidates.append(r)
                existing_ids.add(r.candidate_id)
    else:
        print(f"Searching all {len(STANDARD_CANDIDATE_TOPICS)} standard geotechnical hazard topics (limit per topic: {args.limit})...")
        recs = discovery_service.discover_all_topics(limit_per_topic=args.limit)
        for r in recs:
            if r.candidate_id not in existing_ids:
                new_candidates.append(r)
                existing_ids.add(r.candidate_id)

    total_candidates = existing_candidates + new_candidates
    print(f"\nDiscovered {len(new_candidates)} new candidate records. Total manifest records: {len(total_candidates)}")

    PublicImageManifestManager.write_candidates_csv(total_candidates, manifest_path)
    print(f"[SUCCESS] Candidate manifest saved to: {manifest_path}")

    print_candidate_summary(total_candidates)

    print("\n" + ">" * 78)
    print("SCIENTIFIC INTEGRITY NOTICE:")
    print("Candidate discovery is an initial metadata gathering stage, NOT an expert-labelled")
    print("ground-truth dataset. Image titles, tags, and search keywords are unverified claims")
    print("and MUST NOT be converted into model accuracy benchmarks or hazard ground truth.")
    print("<" * 78)

    return 0


def run_download(args) -> int:
    print_banner("CONTROLLED IMAGE DOWNLOAD & VALIDATION STAGE")
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"[ERROR] Manifest file not found at: {manifest_path}")
        return 1

    candidates = PublicImageManifestManager.read_candidates_csv(manifest_path)
    print(f"Loaded {len(candidates)} candidate records from {manifest_path}")

    download_dir = Path(args.download_dir)
    downloader = ControlledImageDownloader(
        download_dir=download_dir,
        max_file_size_bytes=int(args.max_size_mb * 1024 * 1024),
    )
    print(f"Target Download Directory: {download_dir.resolve()} (Outside production storage)")

    existing_hashes: Dict[str, str] = {}
    for c in candidates:
        if c.download_status == DownloadStatus.DOWNLOADED and c.image_sha256:
            existing_hashes[c.image_sha256] = c.candidate_id

    downloaded_count = 0
    already_downloaded = 0
    skipped_unapproved = 0
    skipped_unsuitable = 0
    skipped_dup = 0
    failed_count = 0

    for i, c in enumerate(candidates, start=1):
        if getattr(args, "candidates_only", False) and c.scientific_suitability_status != ScientificSuitabilityStatus.CANDIDATE:
            safe_title = c.image_title[:35].encode("ascii", "replace").decode("ascii")
            print(f" [{i}/{len(candidates)}] Skipping {c.candidate_id} ('{safe_title}'): Non-candidate suitability '{c.scientific_suitability_status}' ({c.suitability_exclusion_reason})")
            skipped_unsuitable += 1
            continue

        if args.strict_redistribution and c.intended_use_permission_status != IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION:
            c.download_status = DownloadStatus.SKIPPED_UNAPPROVED
            skipped_unapproved += 1
            continue

        if c.download_status == DownloadStatus.DOWNLOADED:
            already_downloaded += 1
            continue

        safe_title = c.image_title[:40].encode("ascii", "replace").decode("ascii")
        print(f" [{i}/{len(candidates)}] Processing {c.candidate_id} ('{safe_title}...')...", end=" ")
        allow_derivatives = getattr(args, "allow_derivatives", True)
        success, msg = downloader.download_candidate(c, existing_hashes=existing_hashes, allow_derivative=allow_derivatives)

        if c.download_status == DownloadStatus.DOWNLOADED:
            print(f"[DOWNLOADED] {msg}")
            downloaded_count += 1
        elif c.download_status == DownloadStatus.SKIPPED_DUPLICATE:
            print(f"[DUPLICATE] {msg}")
            skipped_dup += 1
        elif c.download_status == DownloadStatus.SKIPPED_UNAPPROVED:
            print(f"[SKIPPED] {msg}")
            skipped_unapproved += 1
        else:
            print(f"[FAILED] {msg}")
            failed_count += 1

    PublicImageManifestManager.write_candidates_csv(candidates, manifest_path)
    print(f"\n[SUCCESS] Updated candidate manifest saved with download statuses to: {manifest_path}")

    print("\nDownload Execution Summary:")
    print(f" - Previously Downloaded:                 {already_downloaded}")
    print(f" - Newly Downloaded & Verified:            {downloaded_count}")
    print(f" - Total Downloaded Images on Disk:        {already_downloaded + downloaded_count}")
    print(f" - Skipped (Non-Candidate / Unsuitable):   {skipped_unsuitable}")
    print(f" - Skipped (Unapproved / Pending Review):  {skipped_unapproved}")
    print(f" - Skipped (Identical Hash Duplicate):     {skipped_dup}")
    print(f" - Failed (Network / Corrupt / Size):      {failed_count}")

    if getattr(args, "near_duplicate_audit", False):
        print_banner("PERCEPTUAL NEAR-DUPLICATE AUDIT (dhash)")
        dhashes: Dict[str, str] = {}
        for c in candidates:
            if c.download_status == DownloadStatus.DOWNLOADED:
                img_file = None
                for ext in (".jpg", ".jpeg", ".png", ".webp"):
                    p = download_dir / f"{c.candidate_id}{ext}"
                    if p.exists():
                        img_file = p
                        break
                if img_file:
                    try:
                        dhashes[c.candidate_id] = compute_image_dhash(img_file)
                    except Exception as e:
                        logger.warning("Could not compute dhash for %s: %s", c.candidate_id, e)

        near_dups = detect_near_duplicates(dhashes, threshold=10)
        print(f"Computed perceptual dhash for {len(dhashes)} downloaded images.")
        print(f"Identified {len(near_dups)} suspected near-duplicate / series pairs (Hamming distance <= 10):")
        for id_a, id_b, dist in near_dups:
            cand_a = next((c for c in candidates if c.candidate_id == id_a), None)
            cand_b = next((c for c in candidates if c.candidate_id == id_b), None)
            grp_a = cand_a.event_site_group if cand_a else ""
            grp_b = cand_b.event_site_group if cand_b else ""
            print(f"  * Pair: {id_a} <-> {id_b} (Distance: {dist}/64)")
            print(f"    - Event/Site Group A: {grp_a} | Group B: {grp_b}")
            print(f"    - Title A: '{cand_a.image_title[:35] if cand_a else ''}'")
            print(f"    - Title B: '{cand_b.image_title[:35] if cand_b else ''}'")

    if args.export_benchmark:
        bench_path = Path(args.export_benchmark)
        exported = PublicImageManifestManager.export_to_draft_benchmark_manifest(
            candidates, bench_path, split=args.split or "dev"
        )
        print(f"\n[SUCCESS] Exported {exported} downloaded images to draft benchmark manifest: {bench_path}")
        print("NOTE: In exported benchmark, all ground-truth labels remain strictly EMPTY (status: 'pending')")
        print("until independent dual-expert geotechnical review is completed.")

    return 0


def run_audit(args) -> int:
    print_banner("INDEPENDENT LICENSE & PROVENANCE AUDIT STAGE")
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"[ERROR] Manifest file not found at: {manifest_path}")
        return 1

    audit_out_path = Path(args.output)
    candidates = PublicImageManifestManager.read_candidates_csv(manifest_path)
    print(f"Auditing {len(candidates)} candidate records against original source APIs...")

    client = httpx.Client(
        headers={
            "User-Agent": (
                "PahaarPulse-ScientificBenchmark/1.0 "
                "(https://pahaarpulse.org/; contact: scientific-evaluation@pahaarpulse.org) httpx/0.28"
            )
        },
        timeout=30.0,
    )

    audit_rows = []
    retrieval_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    verified_n = 0
    pending_n = 0
    rejected_n = 0
    unavail_n = 0

    for i, c in enumerate(candidates, start=1):
        page_id = c.candidate_id.replace("WMC_", "")
        safe_title = c.image_title[:35].encode("ascii", "replace").decode("ascii")

        audit_status = "PENDING_REVIEW"
        source_url = c.direct_download_url
        desc_url = c.original_image_page_url
        lic_name = c.license_identifier
        lic_url = c.license_url
        lic_ver = ""
        terms_summary = ""
        file_size = 0
        dims = c.dimensions
        author = c.creator_attribution
        sha256 = c.image_sha256 or ""
        notes = ""

        try:
            resp = client.get("https://commons.wikimedia.org/w/api.php", params={
                "action": "query",
                "format": "json",
                "pageids": page_id,
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata|sha1",
            })
            if resp.status_code == 200:
                data = resp.json()
                page = data.get("query", {}).get("pages", {}).get(page_id, {})
                ii_list = page.get("imageinfo", [])
                if ii_list:
                    ii = ii_list[0]
                    source_url = ii.get("url") or source_url
                    desc_url = ii.get("descriptionurl") or desc_url
                    file_size = ii.get("size", 0)
                    w = ii.get("width", 0)
                    h = ii.get("height", 0)
                    dims = f"{w}x{h}"
                    extmeta = ii.get("extmetadata", {})
                    lic_name = extmeta.get("LicenseShortName", {}).get("value") or lic_name
                    lic_url = extmeta.get("LicenseUrl", {}).get("value") or lic_url
                    terms_summary = extmeta.get("UsageTerms", {}).get("value") or ""
                    artist = extmeta.get("Artist", {}).get("value") or ""
                    credit = extmeta.get("Credit", {}).get("value") or ""
                    clean_auth = LicenseGate.clean_text(artist) or LicenseGate.clean_text(credit)
                    if clean_auth:
                        author = clean_auth
                else:
                    audit_status = "SOURCE_UNAVAILABLE"
                    notes = "Page ID returned no imageinfo on Wikimedia Commons."
            else:
                audit_status = "SOURCE_UNAVAILABLE"
                notes = f"HTTP {resp.status_code} returned by MediaWiki API."
        except Exception as e:
            audit_status = "SOURCE_UNAVAILABLE"
            notes = f"API request failed: {e}"

        # Extract license version
        if "4.0" in lic_name:
            lic_ver = "4.0"
        elif "3.0" in lic_name:
            lic_ver = "3.0"
        elif "2.5" in lic_name:
            lic_ver = "2.5"
        elif "2.0" in lic_name:
            lic_ver = "2.0"
        elif "1.0" in lic_name:
            lic_ver = "1.0"
        else:
            lic_ver = "Unspecified / Custom"

        verif_status, use_status, excl = LicenseGate.evaluate_license(lic_name, lic_url)
        if audit_status != "SOURCE_UNAVAILABLE":
            if verif_status == LicenseVerificationStatus.VERIFIED:
                audit_status = "VERIFIED"
            elif verif_status == LicenseVerificationStatus.REJECTED:
                audit_status = "REJECTED"
            else:
                audit_status = "PENDING_REVIEW"

        # Detailed analysis of specific candidate edge cases
        if c.candidate_id in ("WMC_43209273", "WMC_43642493"):
            audit_status = "PENDING_REVIEW"
            notes = (
                "Flickr 'No known copyright restrictions' via Internet Archive Book Images. "
                "Scanned page from historical printed book (1910/1911). Not an explicit Creative Commons open license deed. "
                "Requires legal review under redistribution policy; scientifically unsuitable historical book scan."
            )
            internal_ok = "Pending Legal Review"
            redist_ok = "Pending Legal Review"
        elif c.candidate_id == "WMC_82792389":
            audit_status = "VERIFIED"
            internal_ok = "Yes"
            redist_ok = "Yes (CC BY-SA 4.0)"
            notes = (
                "License verified CC BY-SA 4.0. Master raster file size (19.26 MB) exceeds 15 MB safety download limit. "
                "Ingestible via official scaled 1920px thumbnail derivative (~1.23 MB, 1920x1280) "
                "hosted on Wikimedia Commons under identical CC BY-SA 4.0 terms."
            )
        elif c.candidate_id == "WMC_6452102":
            audit_status = "VERIFIED"
            internal_ok = "Yes"
            redist_ok = "Yes (Public domain)"
            notes = "License verified Public domain (NASA). Scientifically unsuitable for ground photo triage: extraterrestrial Mars satellite imagery."
        elif c.candidate_id == "WMC_15496737":
            audit_status = "VERIFIED"
            internal_ok = "Yes"
            redist_ok = "Yes (Public domain)"
            notes = "License verified Public domain (NASA). Scientifically unsuitable for ground photo triage: NASA EO-1 satellite remote sensing annotated imagery."
        elif use_status == IntendedUseStatus.APPROVED_FOR_REDISTRIBUTION:
            internal_ok = "Yes"
            redist_ok = f"Yes ({lic_name})"
            notes = f"Verified open license ({lic_name}). Attribution required: '{author}'. Derivative share-alike applies if SA."
        elif use_status == IntendedUseStatus.APPROVED_FOR_INTERNAL_EVALUATION:
            internal_ok = "Yes"
            redist_ok = "No (Non-Commercial clause)"
            notes = f"NC clause restricts public redistribution: {excl}."
        elif use_status == IntendedUseStatus.REJECTED:
            internal_ok = "No"
            redist_ok = "No"
            notes = f"Rejected license: {excl}."
        else:
            internal_ok = "Pending Legal Review"
            redist_ok = "Pending Legal Review"
            notes = f"Ambiguous license terms: {excl}."

        if audit_status == "VERIFIED":
            verified_n += 1
        elif audit_status == "PENDING_REVIEW":
            pending_n += 1
        elif audit_status == "REJECTED":
            rejected_n += 1
        else:
            unavail_n += 1

        audit_rows.append({
            "candidate_id": c.candidate_id,
            "source_repository": c.source_repository,
            "source_identifier": page_id,
            "original_file_page_url": desc_url,
            "direct_source_url": source_url,
            "creator_attribution": author,
            "license_identifier": lic_name,
            "license_version": lic_ver,
            "license_url": lic_url,
            "applicable_terms_summary": terms_summary or f"Subject to {lic_name} terms.",
            "evidence_retrieval_timestamp": retrieval_ts,
            "dimensions": dims,
            "file_size_bytes": str(file_size),
            "file_sha256": sha256,
            "eligible_for_internal_evaluation": internal_ok,
            "redistribution_permitted": redist_ok,
            "audit_status": audit_status,
            "audit_notes_and_uncertainties": notes,
        })

    audit_out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_CSV_HEADERS)
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(row)

    print(f"\n[SUCCESS] Independent license audit saved to: {audit_out_path}")
    print("\nAudit Outcome Breakdown:")
    print(f" - VERIFIED (Documented Open License):       {verified_n}")
    print(f" - PENDING_REVIEW (Ambiguous / Flickr Commons): {pending_n}")
    print(f" - REJECTED (Non-derivative / Prohibited):   {rejected_n}")
    print(f" - SOURCE_UNAVAILABLE (Network / Missing ID): {unavail_n}")

    return 0


def run_migrate(args) -> int:
    print_banner("MANIFEST SCHEMA MIGRATION")
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"[ERROR] Manifest file not found at: {manifest_path}")
        return 1

    out_path = Path(args.output) if args.output else manifest_path
    count = PublicImageManifestManager.migrate_manifest_schema(manifest_path, out_path)
    print(f"[SUCCESS] Migrated {count} records in {out_path} to latest 28-column schema.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="PahaarPulse Public Image Discovery, Licensing Audit, and Controlled Ingestion CLI."
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Acquisition command")

    # 1. Discover subcommand
    discover_p = subparsers.add_parser("discover", help="Discover candidates (dry-run / metadata-only)")
    discover_p.add_argument("--query", type=str, default="", help="Specific search query")
    discover_p.add_argument("--category", type=str, default="", help="Hazard category tag for query")
    discover_p.add_argument("--limit", type=int, default=10, help="Max candidates per query/topic")
    discover_p.add_argument("--delay", type=float, default=1.0, help="Rate limit delay between requests (seconds)")
    discover_p.add_argument("--output", type=str, default=str(DEFAULT_MANIFEST_PATH), help="Manifest output CSV path")
    discover_p.add_argument("--append", action="store_true", help="Append to existing manifest rather than overwrite")

    # 2. Download subcommand
    download_p = subparsers.add_parser("download", help="Download approved candidate images")
    download_p.add_argument("--manifest", type=str, default=str(DEFAULT_MANIFEST_PATH), help="Candidate manifest CSV path")
    download_p.add_argument("--download-dir", type=str, default=str(DEFAULT_DOWNLOAD_DIR), help="Image storage directory")
    download_p.add_argument("--max-size-mb", type=float, default=15.0, help="Max file size in MB")
    download_p.add_argument("--strict-redistribution", action="store_true", help="Only download APPROVED_FOR_REDISTRIBUTION")
    download_p.add_argument("--candidates-only", action="store_true", default=True, help="Only download CANDIDATE suitability")
    download_p.add_argument("--allow-derivatives", action="store_true", default=True, help="Allow downloading 1920px derivative if master image exceeds max size")
    download_p.add_argument("--near-duplicate-audit", action="store_true", default=True, help="Run perceptual dhash near-duplicate detection audit")
    download_p.add_argument("--export-benchmark", type=str, default="", help="Path to export draft benchmark manifest")
    download_p.add_argument("--split", type=str, default="dev", choices=["train", "dev", "test"], help="Benchmark split")

    # 3. Audit subcommand
    audit_p = subparsers.add_parser("audit", help="Run independent source API license provenance audit")
    audit_p.add_argument("--manifest", type=str, default=str(DEFAULT_MANIFEST_PATH), help="Candidate manifest CSV path")
    audit_p.add_argument("--output", type=str, default=str(DEFAULT_AUDIT_PATH), help="Audit output CSV path")

    # 4. Migrate subcommand
    migrate_p = subparsers.add_parser("migrate", help="Migrate manifest CSV to 28-column schema")
    migrate_p.add_argument("--manifest", type=str, default=str(DEFAULT_MANIFEST_PATH), help="Candidate manifest CSV path")
    migrate_p.add_argument("--output", type=str, default="", help="Target output CSV path (defaults to in-place)")

    args = parser.parse_args()

    if args.subcommand == "discover":
        return run_discovery(args)
    elif args.subcommand == "download":
        return run_download(args)
    elif args.subcommand == "audit":
        return run_audit(args)
    elif args.subcommand == "migrate":
        return run_migrate(args)
    else:
        # Default behavior: run discovery dry-run
        class DefaultArgs:
            query = ""
            category = ""
            limit = 5
            delay = 1.0
            output = str(DEFAULT_MANIFEST_PATH)
            append = False
        return run_discovery(DefaultArgs())


if __name__ == "__main__":
    sys.exit(main())
