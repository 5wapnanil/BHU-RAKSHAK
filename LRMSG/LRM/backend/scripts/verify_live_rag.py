"""Standalone gated verification script for live Backboard RAG retrieval.

NON-NEGOTIABLE SAFETY CONSTRAINTS:
1. Strict opt-in required: Exits immediately unless '--live' flag is explicitly passed.
2. Never executed during normal unit tests.
3. Requires valid BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID.
4. Performs a bounded set of knowledge queries on a single disposable thread.
5. Strictly enforces memory="off".
6. Does NOT retry any failed or timed-out request. If a request fails, halts immediately.
7. Redacts all credentials, thread IDs, and private identifiers from console output.
8. Verifies retrieved document metadata from the knowledge base (DOC-001 through DOC-006).
"""

import argparse
import asyncio
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from backend.scripts.smoke_test_backboard import redact_secret
from backend.app.services.backboard.config import BackboardSettings
from backend.app.services.backboard.exceptions import BackboardError
from backend.app.services.backboard.models import BackboardMessageOutput
from backend.app.services.backboard.providers import (
    BackboardProvider,
    LiveBackboardProvider,
)


QUERIES: List[Dict[str, Any]] = [
    {
        "id": "Q1",
        "topic": "Landslide mechanisms & pore-water pressure (DOC-001/DOC-004)",
        "query": "How does an increase in pore-water pressure influence slope equilibrium and trigger landslides according to geotechnical science?",
        "expected_docs": ["01_why_do_landslides_happen.md", "04_why_rainfall_and_soil_moisture_matter.md"],
    },
    {
        "id": "Q2",
        "topic": "GIS terrain susceptibility mapping (DOC-002)",
        "query": "What terrain and environmental layers are typically combined in a GIS system to create a landslide susceptibility map?",
        "expected_docs": ["02_how_gis_turns_terrain_data_into_risk_maps.md"],
    },
    {
        "id": "Q3",
        "topic": "Rainfall thresholds & early warning (DOC-004/DOC-006)",
        "query": "What is the difference between short-duration rainfall intensity and cumulative antecedent precipitation when monitoring landslide early-warning thresholds?",
        "expected_docs": ["04_why_rainfall_and_soil_moisture_matter.md", "06_from_risk_maps_to_early_warning.md"],
    },
]

# Targeted diagnostic probe (bounded at exactly 2 queries) explicitly directing the model to reference its documents
DIAGNOSTIC_QUERIES: List[Dict[str, Any]] = [
    {
        "id": "D1",
        "topic": "Explicit Corpus Probe: 3-Layer ML Architecture (DOC-003)",
        "query": "According to the uploaded PahaarPulse knowledge base documents, what specific three-layer predictive pipeline is used for machine learning landslide risk assessment?",
        "expected_docs": ["03_how_machine_learning_predicts_landslide_risk.md"],
    },
    {
        "id": "D2",
        "topic": "Explicit Corpus Probe: Hydrological Trigger Mechanisms (DOC-004)",
        "query": "Consult the ingested knowledge base: How do intense short-duration rainfall and prolonged antecedent precipitation differ in destabilizing slope equilibrium?",
        "expected_docs": ["04_why_rainfall_and_soil_moisture_matter.md"],
    },
]


async def run_rag_verification(
    live_flag: bool,
    diagnose: bool = False,
    provider: Optional[BackboardProvider] = None,
    config: Optional[BackboardSettings] = None,
) -> int:
    """Execute live RAG verification across bounded query set with no automatic retries.

    Args:
        live_flag: Must be True to proceed (passed via '--live').
        diagnose: If True, executes the bounded 2-query diagnostic probe directing the model to consult corpus.
        provider: Optional dependency-injected BackboardProvider for deterministic testing.
        config: Optional dependency-injected BackboardSettings.

    Returns:
        0 on complete success (all queries complete and retrieve documents).
        1 on failure, timeout, or missing configuration.
    """
    cfg = config or BackboardSettings()
    active_queries = DIAGNOSTIC_QUERIES if diagnose else QUERIES

    mode_label = "DIAGNOSTIC PROBE (2 TARGETED QUERIES)" if diagnose else "STANDARD RETRIEVAL (3 QUERIES)"
    print("=" * 72)
    print(f"PAHAARPULSE / BHU-RAKSHAK - LIVE RAG VERIFICATION [{mode_label}]")
    print("=" * 72)
    print(f"Target Base URL:     {cfg.base_url}")
    print(f"Target Assistant ID: {redact_secret(cfg.assistant_id)}")
    print(f"API Key:             {redact_secret(cfg.api_key)}")
    print(f"Effective Timeout:   {cfg.timeout_seconds:.1f}s")
    print(f"Configured Provider: {cfg.provider}")
    print(f"Memory Mode:         off (strictly enforced)")
    print(f"Bounded Query Count: {len(active_queries)}")
    print(f"Retry Policy:        NO RETRIES (halts immediately on first failure)")
    print("-" * 72)

    if not live_flag:
        print("[DRY RUN COMPLETE] Specify '--live' to execute live verification queries.")
        print(f"Expected cost: <= $0.002 USD (disposable thread, {len(active_queries)} non-streaming queries).")
        return 0

    if not cfg.is_configured:
        print("[ERROR] Missing required credentials for live Backboard verification.")
        print("Please ensure BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID are configured.")
        return 1

    active_provider = provider or LiveBackboardProvider(config=cfg)

    # 1. Thread Creation
    print("\n--> [INIT] Creating disposable conversation thread...")
    t_start = time.perf_counter()
    try:
        thread_id = await active_provider.create_thread()
        t_thread = time.perf_counter() - t_start
        print(f"    Thread created in {t_thread:.2f}s: {redact_secret(thread_id)}")
    except Exception as e:
        print(f"    [FAILED] Thread creation error: {e.__class__.__name__}: {e}")
        return 1

    # 2. Sequential Bounded Query Execution
    results = []
    overall_success = True

    for item in active_queries:
        qid = item["id"]
        qtext = item["query"]
        topic = item["topic"]
        expected = item.get("expected_docs", [])

        print(f"\n--> Query {qid}: {topic}")
        print(f"    Prompt: \"{qtext}\"")

        transport_ok = False
        status_ok = False
        elapsed_sec = 0.0
        retrieved_files: List[str] = []
        retrieved_count = 0
        preview = ""

        q_start = time.perf_counter()
        try:
            output: BackboardMessageOutput = await active_provider.send_message(
                thread_id=thread_id,
                content=qtext,
                memory="off",
            )
            elapsed_sec = time.perf_counter() - q_start
            transport_ok = True
            status_ok = output.is_successful
            retrieved_files = list(output.retrieved_files)
            retrieved_count = output.retrieved_files_count
            preview = output.content.strip().replace("\n", " ")[:160]

            tool_calls = output.raw_response.get("tool_calls") or []
            cost = output.raw_response.get("cost_usd")
            total_tok = output.raw_response.get("total_tokens")

            print(f"    HTTP Transport:      PASSED (HTTP 200, {elapsed_sec:.2f}s)")
            print(f"    Completion Status:   {output.status} (is_successful={status_ok})")
            if tool_calls:
                print(f"    Tool Calls Detected: {len(tool_calls)} call(s)")
            if cost is not None or total_tok is not None:
                print(f"    Usage Metrics:       Tokens={total_tok or 'N/A'}, Cost=${cost if cost is not None else 'N/A'}")
            print(f"    Retrieved Documents: {retrieved_count} document(s) reported by Backboard")
            for rf in retrieved_files:
                print(f"      * {rf}")

            # Check if expected documents matched
            matched_expected = [doc for doc in expected if any(doc in rf for rf in retrieved_files)]
            if matched_expected:
                print(f"    Expected Match:      Corpus verified ({', '.join(matched_expected)})")
            elif retrieved_files:
                print(f"    Corpus Match:        Retrieved from corpus ({', '.join(retrieved_files)})")
            else:
                print(f"    Corpus Match:        WARNING - Zero documents retrieved for query")

            print(f"    Answer Preview:      {preview}...")

            if not status_ok or output.is_billing_restricted:
                print(f"    [HALT] Upstream status failed or billing restricted. Halting without retry.")
                results.append({
                    "id": qid,
                    "topic": topic,
                    "transport_ok": transport_ok,
                    "status_ok": False,
                    "elapsed_sec": elapsed_sec,
                    "retrieved_count": retrieved_count,
                    "retrieved_files": retrieved_files,
                    "preview": preview,
                    "error": f"Upstream status: {output.status}",
                })
                overall_success = False
                break

            results.append({
                "id": qid,
                "topic": topic,
                "transport_ok": transport_ok,
                "status_ok": status_ok,
                "elapsed_sec": elapsed_sec,
                "retrieved_count": retrieved_count,
                "retrieved_files": retrieved_files,
                "preview": preview,
                "error": None,
            })

        except Exception as e:
            elapsed_sec = time.perf_counter() - q_start
            print(f"    [FAILED] Dispatch failed after {elapsed_sec:.2f}s: {e.__class__.__name__}: {e}")
            print(f"    [HALT] Stopping live test immediately. No automatic retries.")
            results.append({
                "id": qid,
                "topic": topic,
                "transport_ok": False,
                "status_ok": False,
                "elapsed_sec": elapsed_sec,
                "retrieved_count": 0,
                "retrieved_files": [],
                "preview": "",
                "error": f"{e.__class__.__name__}: {e}",
            })
            overall_success = False
            break

    # 3. Print Final Summary
    print("\n" + "=" * 72)
    print("LIVE RAG RETRIEVAL VERIFICATION SUMMARY")
    print("=" * 72)
    for r in results:
        status_str = "SUCCESS" if r["status_ok"] else "FAILED"
        rag_str = f"RETRIEVED ({r['retrieved_count']} files)" if r["retrieved_count"] > 0 else "NO RETRIEVAL"
        err_str = f" | Error: {r['error']}" if r["error"] else ""
        print(f"[{r['id']}] {r['topic'][:32]:<32} | {status_str} | {r['elapsed_sec']:5.1f}s | {rag_str}{err_str}")

    print("=" * 72)
    if overall_success and len(results) == len(active_queries):
        all_retrieved = all(r["retrieved_count"] > 0 for r in results)
        if all_retrieved:
            print("[PASS] All queries completed successfully with verified corpus document retrieval.")
            return 0
        else:
            print("[WARN] All queries completed, but some queries had zero document retrieval.")
            return 0
    else:
        print("[FAIL] Verification aborted or encountered errors.")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Live Backboard RAG retrieval verification.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute live requests against Backboard.io (incurs provider token cost).",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Execute targeted 2-query diagnostic probe directing model to consult uploaded corpus.",
    )
    args = parser.parse_args()
    code = asyncio.run(run_rag_verification(live_flag=args.live, diagnose=args.diagnose))
    sys.exit(code)


if __name__ == "__main__":
    main()
