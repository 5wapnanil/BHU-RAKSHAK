"""End-to-End integration verification for PahaarPulse Assistant API.

NON-NEGOTIABLE SAFETY CONSTRAINTS:
1. Strict opt-in required for live testing: defaults to offline mock provider unless '--live' flag is passed.
2. Exercises the exact user-facing FastAPI endpoints:
   - POST /api/assistant/threads (both cookie and bearer transports)
   - POST /api/assistant/query (both cookie and bearer transports)
3. For live test, sends AT MOST 1 domain question through the application backend.
4. Preserves memory="off".
5. No automatic retries.
6. Does NOT upload, modify, or delete any documents or change assistant settings.
7. Redacts all session tokens, cookies, and identifiers in console output.
"""

import argparse
import asyncio
from pathlib import Path
import sys
import time

# Ensure repo root on sys.path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi.testclient import TestClient

from backend.app.api.deps import assistant_rate_limiter, get_backboard_service
from backend.app.main import app
from backend.app.services.backboard.config import BackboardSettings
from backend.app.services.backboard.providers import LiveBackboardProvider, MockBackboardProvider
from backend.app.services.backboard_service import BackboardService
from backend.scripts.smoke_test_backboard import redact_secret


def run_e2e_verification(live_mode: bool = False) -> int:
    cfg = BackboardSettings()

    print("=" * 72)
    mode_str = "LIVE BACKBOARD END-TO-END" if live_mode else "OFFLINE MOCK END-TO-END"
    print(f"PAHAARPULSE - ASSISTANT END-TO-END INTEGRATION [{mode_str}]")
    print("=" * 72)
    print(f"Base URL:         {cfg.base_url}")
    print(f"Effective Timeout:{cfg.timeout_seconds:.1f}s")
    print(f"Memory Mode:      off (strictly enforced)")
    print(f"Execution Target: FastAPI app endpoints (/api/assistant/threads, /api/assistant/query)")
    print("-" * 72)

    assistant_rate_limiter.clear()

    if live_mode:
        if not cfg.is_configured:
            print("[ERROR] Live mode requires BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID.")
            return 1
        provider = LiveBackboardProvider(config=cfg)
        print(f"Live Assistant:   {redact_secret(cfg.assistant_id)}")
        print(f"Live API Key:     {redact_secret(cfg.api_key)}")
    else:
        provider = MockBackboardProvider(mode="success")
        print("Using deterministic offline MockBackboardProvider.")

    service = BackboardService(
        provider=provider,
        config=cfg,
        signing_key="e2e-test-session-signing-key-minimum-32chars-xyz",
        session_expiry_seconds=3600,
        is_production=False,
    )

    app.dependency_overrides[get_backboard_service] = lambda: service
    client = TestClient(app)

    try:
        # -------------------------------------------------------------
        # 1. Flow A: Web Client Session (Cookie Transport)
        # -------------------------------------------------------------
        print("\n--> [Flow 1] Web Browser: Session Initialization (Cookie Transport)...")
        res_thread = client.post(
            "/api/assistant/threads?transport=cookie",
            headers={"Origin": "http://localhost:3000"},
        )
        print(f"    HTTP Status:      {res_thread.status_code} ({'PASSED' if res_thread.status_code == 201 else 'FAILED'})")
        if res_thread.status_code != 201:
            print(f"    [FAIL] Thread creation failed: {res_thread.text}")
            return 1

        thread_data = res_thread.json()
        cookie_val = res_thread.cookies.get("pp_assistant_session")
        set_cookie_header = res_thread.headers.get("set-cookie", "")

        print(f"    Transport:        {thread_data.get('transport')}")
        print(f"    Body Token:       {thread_data.get('session_token')} (Correctly OMITTED from JSON body)")
        print(f"    Cookie Received:  {redact_secret(cookie_val)} (HttpOnly={'HttpOnly' in set_cookie_header})")

        if not cookie_val or "HttpOnly" not in set_cookie_header or thread_data.get("session_token") is not None:
            print("    [FAIL] Web cookie security requirements not met.")
            return 1

        print("\n--> [Flow 2] Web Browser: Query Submission with HttpOnly Cookie...")
        web_query = (
            "According to the ingested knowledge base, what is the three-layer predictive pipeline "
            "used for machine learning landslide risk assessment?"
            if live_mode
            else "What are early warning signs of slope failure?"
        )
        print(f"    Prompt:           \"{web_query[:80]}...\"")

        t_start = time.perf_counter()
        res_query = client.post(
            "/api/assistant/query",
            headers={"Origin": "http://localhost:3000"},
            cookies={"pp_assistant_session": cookie_val},
            json={"query": web_query},
        )
        elapsed = time.perf_counter() - t_start
        print(f"    HTTP Status:      {res_query.status_code} ({'PASSED' if res_query.status_code == 200 else 'FAILED'}, {elapsed:.2f}s)")
        if res_query.status_code != 200:
            print(f"    [FAIL] Query submission failed: {res_query.text}")
            return 1

        q_data = res_query.json()
        print(f"    Fallback Mode:    {q_data.get('fallback_mode')}")
        print(f"    Sources Returned: {len(q_data.get('sources', []))} citation(s)")
        for src in q_data.get("sources", []):
            print(f"      * [{src.get('document_id')}] {src.get('title')} (curated={src.get('is_curated')})")

        reply_snippet = q_data.get("reply", "").strip().replace("\n", " ")[:150]
        print(f"    Reply Snippet:    {reply_snippet}...")
        print(f"    Disclaimer:       {q_data.get('disclaimer')[:60]}...")

        # If in live mode, exactly 1 query is executed to minimize usage
        if live_mode:
            print("\n" + "=" * 72)
            print("LIVE END-TO-END VERIFICATION RESULT: PASSED")
            print("=" * 72)
            return 0

        # -------------------------------------------------------------
        # 2. Flow B: Mobile Client Session (Bearer Transport - Offline)
        # -------------------------------------------------------------
        print("\n--> [Flow 3] Mobile App: Session Initialization (Bearer Transport)...")
        res_mobile_thread = client.post("/api/assistant/threads?transport=bearer")
        print(f"    HTTP Status:      {res_mobile_thread.status_code} ({'PASSED' if res_mobile_thread.status_code == 201 else 'FAILED'})")
        if res_mobile_thread.status_code != 201:
            print(f"    [FAIL] Mobile thread creation failed: {res_mobile_thread.text}")
            return 1

        m_data = res_mobile_thread.json()
        bearer_token = m_data.get("session_token")
        print(f"    Transport:        {m_data.get('transport')}")
        print(f"    Bearer Token:     {redact_secret(bearer_token)}")
        print(f"    Cookie Attached:  {'pp_assistant_session' in res_mobile_thread.cookies} (Correctly FALSE)")

        if not bearer_token or "pp_assistant_session" in res_mobile_thread.cookies:
            print("    [FAIL] Mobile bearer requirements not met.")
            return 1

        print("\n--> [Flow 4] Mobile App: Query Submission with Authorization: Bearer...")
        res_mobile_query = client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {bearer_token}"},
            json={"query": "What should people do during heavy rainfall?"},
        )
        print(f"    HTTP Status:      {res_mobile_query.status_code} ({'PASSED' if res_mobile_query.status_code == 200 else 'FAILED'})")
        if res_mobile_query.status_code != 200:
            print(f"    [FAIL] Mobile query failed: {res_mobile_query.text}")
            return 1

        mq_data = res_mobile_query.json()
        print(f"    Fallback Mode:    {mq_data.get('fallback_mode')}")
        print(f"    Sources Returned: {len(mq_data.get('sources', []))} citation(s)")
        print(f"    Reply Snippet:    {mq_data.get('reply', '')[:120]}...")

        # -------------------------------------------------------------
        # 3. Security Boundary Verification
        # -------------------------------------------------------------
        print("\n--> [Flow 5] Security Boundary Check: Injected thread_id in query body...")
        res_injected = client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {bearer_token}"},
            json={"query": "Test query", "thread_id": "malicious-injected-id"},
        )
        print(f"    Injected thread_id rejected with HTTP {res_injected.status_code} (Expected 422: {'PASSED' if res_injected.status_code == 422 else 'FAILED'})")
        if res_injected.status_code != 422:
            return 1

        print("\n--> [Flow 6] Security Boundary Check: Tampered session token...")
        res_tampered = client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {bearer_token[:-5]}AAAAA"},
            json={"query": "Test query"},
        )
        print(f"    Tampered token rejected with HTTP {res_tampered.status_code} (Expected 401: {'PASSED' if res_tampered.status_code == 401 else 'FAILED'})")
        if res_tampered.status_code != 401:
            return 1

        print("\n" + "=" * 72)
        print("OFFLINE END-TO-END VERIFICATION RESULT: ALL FLOWS PASSED (6/6)")
        print("=" * 72)
        return 0

    finally:
        app.dependency_overrides.clear()
        assistant_rate_limiter.clear()


def main() -> None:
    parser = argparse.ArgumentParser(description="End-to-End Assistant Integration Verification.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute exactly 1 live query through application API against Backboard (incurs minimal cost).",
    )
    args = parser.parse_args()
    code = run_e2e_verification(live_mode=args.live)
    sys.exit(code)


if __name__ == "__main__":
    main()
