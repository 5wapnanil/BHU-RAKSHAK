"""CLI script to run reproducible VLM evaluation against an explicit evaluation dataset.

Usage:
  python backend/scripts/evaluate_vlm.py --dataset docs/gemma-local-vision/evaluation/field_photo_benchmark_template.csv --provider ollama
"""

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid

# Add project root to sys.path
backend_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_root))

from dotenv import load_dotenv
load_dotenv(backend_root / "backend" / ".env")

from backend.app.services.gemma_providers import (
    GoogleGenAIGemmaProvider,
    MockGemmaProvider,
    OllamaGemmaProvider,
    get_gemma_provider,
)
from backend.app.services.vlm_evaluation import VLMEvaluationHarness


async def run_evaluation(args):
    dataset_path = Path(args.dataset).resolve()
    if not dataset_path.exists():
        print(f"[ERROR] Dataset file not found: {dataset_path}")
        return 1

    manifest_hash = VLMEvaluationHarness.compute_sha256(dataset_path)

    print("=" * 78)
    print("PAHAARPULSE VLM GEOTECHNICAL EVALUATION HARNESS - SCIENTIFIC BENCHMARK")
    print("=" * 78)
    print(f"Dataset Manifest: {dataset_path}")
    print(f"Manifest SHA-256: {manifest_hash}")
    print(f"Split Filter:     {args.split}")
    print(f"Provider:         {args.provider}")

    # Optional provenance verification if dataset_id supplied
    if args.dataset_id:
        print(f"\nVerifying dataset '{args.dataset_id}' in provenance register...")
        try:
            record = VLMEvaluationHarness.validate_dataset_provenance(args.dataset_id)
            print(f" [PASS] Provenance verified: {record['name']} (License: {record['license_status']})")
        except Exception as pe:
            print(f" [BLOCKED] Dataset provenance validation failed: {pe}")
            return 1

    # Load dataset
    try:
        split_arg = None if args.split == "all" else args.split
        samples = VLMEvaluationHarness.load_dataset_csv(
            dataset_path,
            split_filter=split_arg,
            strict_permissions=args.strict_permissions,
        )
    except Exception as e:
        print(f"[ERROR] Failed to load dataset: {e}")
        return 1

    print(f"Loaded {len(samples)} evaluation sample(s).")
    labeled_count = sum(1 for s in samples if s.ground_truth_hazard and s.adjudication_status != "excluded")
    excluded_count = sum(1 for s in samples if s.adjudication_status == "excluded")
    print(f" - Expert Adjudicated:    {labeled_count}")
    print(f" - Unlabeled / Pending:  {len(samples) - labeled_count - excluded_count}")
    print(f" - Excluded:             {excluded_count}")

    # Instantiate provider
    if args.provider == "ollama":
        provider = OllamaGemmaProvider(
            base_url=args.ollama_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model_name=args.model or os.environ.get("OLLAMA_MODEL", "gemma3:4b"),
            timeout=float(args.timeout),
        )
    elif args.provider == "google":
        provider = GoogleGenAIGemmaProvider(
            api_key=os.environ.get("GEMINI_API_KEY"),
            model_name=args.model or os.environ.get("GEMMA_MODEL", "gemini-3.5-flash"),
        )
    elif args.provider == "mock":
        provider = MockGemmaProvider()
    else:
        provider = get_gemma_provider()

    print(f"Selected Provider: {provider.provider_name} (Available: {provider.is_available()})")

    # Run inference on each sample
    print("\nExecuting model inference...")
    for idx, sample in enumerate(samples, 1):
        if sample.adjudication_status == "excluded":
            print(f" [{idx}/{len(samples)}] Skipping excluded {sample.image_id} (Reason: {sample.exclusion_reason})...")
            continue

        print(f" [{idx}/{len(samples)}] Evaluating {sample.image_id} ({Path(sample.image_path).name})...", end="", flush=True)
        sample = await VLMEvaluationHarness.evaluate_sample(sample, provider)
        if sample.error:
            print(f" [ERROR: {sample.error}]")
        else:
            print(f" -> Predicted: {sample.predicted_hazard} (Conf: {sample.predicted_confidence})")

    # Compute metrics
    metrics = VLMEvaluationHarness.compute_metrics(samples)
    report = VLMEvaluationHarness.format_metrics_report(metrics)
    print("\n" + report + "\n")

    # Export results CSV
    output_path = Path(args.output) if args.output else dataset_path.parent / f"evaluated_{dataset_path.name}"
    VLMEvaluationHarness.export_results_csv(samples, output_path)
    print(f"[SUCCESS] Exported evaluated predictions to: {output_path}")

    # Export reproducible run metadata JSON
    metadata_path = output_path.with_suffix(".metadata.json")
    run_meta = {
        "run_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_manifest_path": str(dataset_path),
        "manifest_sha256": manifest_hash,
        "split_evaluated": args.split,
        "strict_permissions_enforced": args.strict_permissions,
        "provider_name": provider.provider_name,
        "model_name": getattr(provider, "model_name", "unknown"),
        "total_samples": len(samples),
        "labeled_ground_truth_samples": labeled_count,
        "excluded_samples": excluded_count,
        "metrics_summary": {
            "accuracy": metrics.accuracy if metrics else None,
            "macro_f1": metrics.macro_f1 if metrics else None,
            "weighted_f1": metrics.weighted_f1 if metrics else None,
            "coverage_rate": metrics.coverage_rate if metrics else None,
            "wilson_ci_accuracy": metrics.wilson_ci_accuracy if metrics else None,
            "wilson_ci_coverage": metrics.wilson_ci_coverage if metrics else None,
            "inter_annotator_agreement": metrics.inter_annotator_agreement if metrics else None,
            "multi_label_indicators": metrics.multi_label_indicators if metrics else None,
            "inference_failure_rate": metrics.inference_failure_rate if metrics else None,
        } if metrics else None,
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(run_meta, f, indent=2)
    print(f"[SUCCESS] Saved evaluation run metadata to: {metadata_path}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Evaluate VLM on landslide photograph datasets.")
    parser.add_argument(
        "--dataset",
        type=str,
        default="docs/gemma-local-vision/evaluation/field_photo_benchmark_template.csv",
        help="Path to evaluation dataset CSV file.",
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default=None,
        help="Optional dataset ID from provenance register (e.g. HLAD, Landslide4Sense, PahaarPulse-Field-Benchmark).",
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "google", "mock", "auto"],
        default="mock",
        help="Inference provider to evaluate.",
    )
    parser.add_argument(
        "--split",
        choices=["all", "train", "dev", "test"],
        default="test",
        help="Evaluation split to process (default: test).",
    )
    parser.add_argument(
        "--strict-permissions",
        action="store_true",
        help="Enforce strict rejection if legal license/permission is unverified or blank.",
    )
    parser.add_argument("--model", type=str, default=None, help="Model identifier override.")
    parser.add_argument("--ollama-url", type=str, default=None, help="Ollama daemon base URL.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout in seconds.")
    parser.add_argument("--output", type=str, default=None, help="Path to write evaluated CSV output.")

    args = parser.parse_args()
    return asyncio.run(run_evaluation(args))


if __name__ == "__main__":
    sys.exit(main())
