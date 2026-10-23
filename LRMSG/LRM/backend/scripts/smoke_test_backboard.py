"""Standalone gated smoke test script for live Backboard API verification.

NON-NEGOTIABLE SAFETY CONSTRAINTS:
1. Strict opt-in required: Will exit immediately with code 1 unless '--live' flag is explicitly passed.
2. Never executed during normal unit tests.
3. Requires valid BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID in the environment or backend/.env.
4. Performs ONE read-only landslide knowledge question on a disposable thread.
5. Does NOT create assistants, upload documents, delete resources, or ingest the knowledge base.
6. Redacts all credentials and private identifiers from console output.
7. Explicitly notifies developer that running this test may incur provider usage or cost.
"""

import argparse
import asyncio
from pathlib import Path
import sys

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from backend.app.services.backboard.config import BackboardSettings
from backend.app.services.backboard.providers import LiveBackboardProvider


def redact_secret(val: str) -> str:
    """Safely redact secret tokens, revealing only length and trailing characters."""
    if not val:
        return "<unset>"
    if len(val) <= 8:
        return "***"
    return f"{val[:3]}...{val[-4:]}"


async def run_smoke_test(live_flag: bool) -> int:
    """Execute live smoke test if explicitly authorized via --live flag."""
    if not live_flag:
        print("[SAFETY GATE] Live Backboard smoke test aborted.")
        print("Live network calls require explicit opt-in via the '--live' flag to prevent unintended costs or external calls.")
        print("\nUsage:")
        print("  python backend/scripts/smoke_test_backboard.py --live\n")
        return 1

    print("=" * 70)
    print("PAHAARPULSE - LIVE BACKBOARD API SMOKE TEST (GATED)")
    print("=" * 70)
    print("NOTICE: Executing live API requests may incur Backboard usage and API costs.\n")

    cfg = BackboardSettings()

    api_key_redacted = redact_secret(cfg.api_key)
    assistant_id_redacted = redact_secret(cfg.assistant_id)

    print(f"Base URL:     {cfg.base_url}")
    print(f"API Key:      {api_key_redacted}")
    print(f"Assistant ID: {assistant_id_redacted}")
    print(f"Timeout:      {cfg.timeout_seconds}s\n")

    if not cfg.is_configured:
        print("[ERROR] Missing required live Backboard credentials.")
        print("Please configure BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID in backend/.env or your shell environment.")
        return 1

    try:
        provider = LiveBackboardProvider(config=cfg)

        print("[1/3] Initializing disposable live conversation thread...")
        thread_id = await provider.create_thread()
        print(f"      Thread created successfully: {redact_secret(thread_id)}")

        print("\n[2/3] Dispatching sample landslide knowledge query...")
        test_query = "What are three common warning signs of possible landslide activity, and what should people do if they observe them?"
        output = await provider.send_message(
            thread_id=thread_id,
            content=test_query,
            memory="off",
        )

        print("\n[3/3] Inspecting live response payload structure...")
        print(f"      Status:          {output.status}")
        print(f"      Content length:  {len(output.content)} characters")
        print(f"      Retrieved files: {output.retrieved_files_count} file(s) cited")
        for f in output.retrieved_files:
            print(f"        - {f}")

        print("\n--- Model Response Text ---")
        print(output.content.strip())
        print("---------------------------")

        # Basic structural assertions
        if not output.content or len(output.content) < 20:
            print("\n[FAIL] Live Backboard response content was empty or suspiciously short.")
            return 1

        print("\n" + "=" * 70)
        print("SMOKE TEST RESULT: PASSED (Live provider contract structurally verified)")
        print("=" * 70)
        return 0

    except Exception as e:
        print(f"\n[FAIL] Live smoke test encountered an error: {e.__class__.__name__}: {e}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gated live Backboard smoke test.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicit confirmation to execute live network requests against Backboard.io (incurs costs).",
    )
    args = parser.parse_args()

    exit_code = asyncio.run(run_smoke_test(args.live))
    sys.exit(exit_code)
