"""Standalone gated smoke test script for live Backboard API verification.

NON-NEGOTIABLE SAFETY CONSTRAINTS:
1. Strict opt-in required: Will exit immediately with code 1 unless '--live' flag is explicitly passed.
2. Never executed during normal unit tests.
3. Requires valid BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID in the environment or backend/.env.
4. Performs ONE read-only landslide knowledge question on a disposable thread.
5. Does NOT create assistants, upload documents, delete resources, or ingest the knowledge base.
6. Redacts all credentials and private identifiers from console output.
7. Explicitly separates 4 validation layers:
   - Layer 1: HTTP Transport Verification
   - Layer 2: Response Parsing Verification
   - Layer 3: Upstream LLM Generation Verification
   - Layer 4: RAG Retrieval Verification
8. Treats upstream status="FAILED" (including billing restrictions) as test failures (exit code 1).
"""

import argparse
import asyncio
from pathlib import Path
import sys
from typing import Optional

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from backend.app.services.backboard.config import BackboardSettings
from backend.app.services.backboard.exceptions import (
    BackboardAuthenticationError,
    BackboardConfigurationError,
    BackboardConnectionError,
    BackboardError,
    BackboardMalformedOutputError,
    BackboardNotFoundError,
    BackboardRateLimitError,
    BackboardTemporaryUnavailableError,
    BackboardTimeoutError,
)
from backend.app.services.backboard.models import BackboardMessageOutput
from backend.app.services.backboard.providers import (
    BackboardProvider,
    LiveBackboardProvider,
)


def redact_secret(val: Optional[str]) -> str:
    """Safely redact secret tokens, revealing only length and trailing characters."""
    if not val:
        return "<unset>"
    if len(val) <= 8:
        return "***"
    return f"{val[:3]}...{val[-4:]}"


async def run_smoke_test(
    live_flag: bool,
    provider: Optional[BackboardProvider] = None,
    config: Optional[BackboardSettings] = None,
) -> int:
    """Execute Backboard smoke test with multi-layer diagnostic verification.

    Args:
        live_flag: Must be True to proceed (passed via '--live').
        provider: Optional dependency-injected BackboardProvider for deterministic testing.
        config: Optional dependency-injected BackboardSettings.

    Returns:
        0 on complete success (Layers 1-3 pass).
        1 on any failure (Layer 1, 2, or 3 failure, or safety gate violation).
    """
    if not live_flag:
        print("[SAFETY GATE] Live Backboard smoke test aborted.")
        print(
            "Live network calls require explicit opt-in via the '--live' flag to prevent unintended costs or external calls."
        )
        print("\nUsage:")
        print("  python backend/scripts/smoke_test_backboard.py --live\n")
        return 1

    print("=" * 70)
    print("PAHAARPULSE - BACKBOARD API SMOKE TEST (GATED)")
    print("=" * 70)
    print("NOTICE: Executing live API requests may incur Backboard usage and API costs.\n")

    cfg = config or BackboardSettings()

    api_key_redacted = redact_secret(cfg.api_key)
    assistant_id_redacted = redact_secret(cfg.assistant_id)

    print(f"Base URL:     {cfg.base_url}")
    print(f"API Key:      {api_key_redacted}")
    print(f"Assistant ID: {assistant_id_redacted}")
    print(f"Timeout:      {cfg.timeout_seconds}s\n")

    if provider is None and not cfg.is_configured:
        print("[ERROR] Missing required Backboard credentials.")
        print(
            "Please configure BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID in backend/.env or your shell environment."
        )
        return 1

    active_provider = provider or LiveBackboardProvider(config=cfg)

    # ---------------------------------------------------------
    # Layer 1: HTTP Transport Verification (Thread Creation)
    # ---------------------------------------------------------
    print("[1/3] Initializing disposable conversation thread...")
    try:
        thread_id = await active_provider.create_thread()
        print(f"      Thread created successfully: {redact_secret(thread_id)}")
    except BackboardAuthenticationError as e:
        print("\n[LAYER 1 - HTTP TRANSPORT]: FAILED (Authentication Failure)")
        print(f"      Diagnostic: {e}")
        return 1
    except BackboardNotFoundError as e:
        print("\n[LAYER 1 - HTTP TRANSPORT]: FAILED (Resource Not Found - HTTP 404)")
        print(f"      Diagnostic: {e}")
        return 1
    except BackboardRateLimitError as e:
        print("\n[LAYER 1 - HTTP TRANSPORT]: FAILED (Rate Limit Exceeded - HTTP 429)")
        print(f"      Diagnostic: {e}")
        return 1
    except (BackboardTimeoutError, BackboardConnectionError, BackboardTemporaryUnavailableError) as e:
        print(f"\n[LAYER 1 - HTTP TRANSPORT]: FAILED ({e.__class__.__name__})")
        print(f"      Diagnostic: {e}")
        return 1
    except BackboardMalformedOutputError as e:
        print("\n[LAYER 1 - HTTP TRANSPORT]: PASSED (HTTP Response Received)")
        print(f"[LAYER 2 - RESPONSE PARSING]: FAILED ({e})")
        return 1
    except Exception as e:
        print(f"\n[LAYER 1 - HTTP TRANSPORT]: FAILED ({e.__class__.__name__}: {e})")
        return 1

    # ---------------------------------------------------------
    # Layer 1 & 2: HTTP Transport & Response Parsing (Send Message)
    # ---------------------------------------------------------
    print("\n[2/3] Dispatching sample landslide knowledge query (memory='off')...")
    test_query = (
        "What are three common warning signs of possible landslide activity, "
        "and what should people do if they observe them?"
    )

    try:
        output: BackboardMessageOutput = await active_provider.send_message(
            thread_id=thread_id,
            content=test_query,
            memory="off",
        )
    except BackboardAuthenticationError as e:
        print("\n[LAYER 1 - HTTP TRANSPORT]: FAILED (Authentication Failure)")
        print(f"      Diagnostic: {e}")
        return 1
    except BackboardNotFoundError as e:
        print("\n[LAYER 1 - HTTP TRANSPORT]: FAILED (Resource Not Found - HTTP 404)")
        print(f"      Diagnostic: {e}")
        return 1
    except BackboardRateLimitError as e:
        print("\n[LAYER 1 - HTTP TRANSPORT]: FAILED (Rate Limit Exceeded - HTTP 429)")
        print(f"      Diagnostic: {e}")
        return 1
    except (BackboardTimeoutError, BackboardConnectionError, BackboardTemporaryUnavailableError) as e:
        print(f"\n[LAYER 1 - HTTP TRANSPORT]: FAILED ({e.__class__.__name__})")
        print(f"      Diagnostic: {e}")
        return 1
    except BackboardMalformedOutputError as e:
        print("\n[LAYER 1 - HTTP TRANSPORT]: PASSED (HTTP 200 Received)")
        print(f"[LAYER 2 - RESPONSE PARSING]: FAILED (Malformed JSON or missing schema fields: {e})")
        return 1
    except Exception as e:
        print(f"\n[LAYER 1 - HTTP TRANSPORT]: FAILED ({e.__class__.__name__}: {e})")
        return 1

    # If send_message returned successfully, both Layer 1 and Layer 2 passed
    print("\n[3/3] Evaluating multi-layer verification results...")
    print("---------------------------------------------------------")
    print("[LAYER 1 - HTTP TRANSPORT]: PASSED (HTTP 200 OK received from Backboard API)")
    print("[LAYER 2 - RESPONSE PARSING]: PASSED (JSON schema parsed into BackboardMessageOutput)")

    # ---------------------------------------------------------
    # Layer 3: Upstream LLM Generation Verification
    # ---------------------------------------------------------
    generation_passed = False
    if output.is_billing_restricted:
        print("[LAYER 3 - UPSTREAM GENERATION]: FAILED (Billing / Credit Restriction Detected)")
        print("\n[ACTIONABLE DIAGNOSTIC]")
        print("The Backboard API completed the HTTP request, but upstream LLM generation failed")
        print("because the free credit tier is reserved for Memory & RAG and does not cover LLM chat:")
        print("  -> \"Your free credit is reserved for Memory & RAG, so it can't cover LLM chat.\"")
        print("Resolution: Add credits or configure billing on Backboard.io to enable live LLM generation.")
    elif (output.status or "").upper() != "COMPLETED":
        print(f"[LAYER 3 - UPSTREAM GENERATION]: FAILED (Upstream status: '{output.status}')")
        print("\n[ACTIONABLE DIAGNOSTIC]")
        print("The Backboard API completed the HTTP request, but the upstream LLM generation failed.")
        print(f"Upstream status reported: {output.status}")
    elif not output.content or len(output.content.strip()) < 20:
        print("[LAYER 3 - UPSTREAM GENERATION]: FAILED (Content empty or suspiciously short)")
        print("\n[ACTIONABLE DIAGNOSTIC]")
        print("The model returned status 'COMPLETED' but generated content was empty or under 20 characters.")
    else:
        print("[LAYER 3 - UPSTREAM GENERATION]: PASSED (Model generated valid response text)")
        generation_passed = True

    # ---------------------------------------------------------
    # Layer 4: RAG Retrieval Verification
    # ---------------------------------------------------------
    if output.retrieved_files_count > 0:
        print(f"[LAYER 4 - RAG RETRIEVAL]: PASSED ({output.retrieved_files_count} document(s) cited)")
        for f in output.retrieved_files:
            print(f"        - {f}")
    else:
        print("[LAYER 4 - RAG RETRIEVAL]: UNVERIFIED (0 documents cited - Knowledge base not yet ingested)")

    print("\n--- Response Text Excerpt ---")
    content_display = output.content.strip()
    if len(content_display) > 300:
        content_display = content_display[:300] + " ... [TRUNCATED]"
    print(content_display)
    print("-----------------------------\n")

    # Final Verdict
    print("=" * 70)
    if generation_passed:
        print("SMOKE TEST RESULT: PASSED (Layers 1-3 Verified)")
        print("=" * 70)
        return 0
    else:
        print("SMOKE TEST RESULT: FAILED (Layer 3 generation failed)")
        print("=" * 70)
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
