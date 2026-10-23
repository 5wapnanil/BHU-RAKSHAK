# PahaarPulse — Backboard RAG Test & Verification Plan

**Phase:** Phase 1 — Testing Strategy  
**System Target:** PahaarPulse Landslide Knowledge Assistant  
**Date:** October 23, 2026  
**Status:** SPECIFICATION COMPLETE  

---

## 1. Testing Philosophy & Non-Negotiable Constraints

1. **Zero Mandatory Paid API Calls:** The default automated test suite (`python -m unittest discover -s backend/tests`) must run **100% offline and free of cost** using a deterministic `MockBackboardProvider`.
2. **Zero Regressions:** Integration of the assistant must not break any of the 273 existing backend tests or 17 mobile tests.
3. **Gated Smoke Tests:** Live network calls to Backboard.io are restricted to an opt-in CLI smoke test script that requires explicit developer authorization and local credentials.

---

## 2. Test Architecture: `MockBackboardProvider`

Following the pattern established in [`backend/app/services/gemma_providers.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/gemma_providers.py) for the vision AI screening service, a `MockBackboardProvider` implements the `BackboardProvider` Protocol:

```python
class MockBackboardProvider:
    """Deterministic mock provider for offline testing."""
    def __init__(self, mode: str = "success"):
        self.mode = mode  # "success", "timeout", "rate_limit", "unavailable", "empty"

    async def create_thread(self, assistant_id: str) -> str:
        return "mock-thread-uuid-1234"

    async def send_message(self, thread_id: str, assistant_id: str, content: str) -> Dict[str, Any]:
        if self.mode == "timeout":
            raise BackboardTimeoutError("Upstream Backboard timeout (30s)")
        if self.mode == "rate_limit":
            raise BackboardRateLimitError("Rate limit exceeded (HTTP 429)")
        if self.mode == "unavailable":
            raise BackboardAPIError("Service temporarily unavailable (HTTP 503)")
        if self.mode == "empty":
            return {
                "content": "I do not have sufficient information in the knowledge base to answer this question.",
                "retrieved_files": [],
                "retrieved_files_count": 0,
                "status": "COMPLETED",
            }
        return {
            "content": "Landslides occur when gravity overcomes resisting friction along a slope.",
            "retrieved_files": ["01_why_do_landslides_happen.md"],
            "retrieved_files_count": 1,
            "status": "COMPLETED",
        }
```

---

## 3. Test Suites Specification

### Suite A: Unit Tests (`backend/tests/test_backboard_service.py`)

| Test Case | Scenario Description | Expected Outcome |
| :--- | :--- | :--- |
| `test_init_with_valid_config` | Valid configuration with API key and assistant ID | Service instantiates successfully |
| `test_init_missing_key_in_production` | Production environment with missing `BACKBOARD_API_KEY` | Raises `BackboardConfigurationError` |
| `test_create_session_token` | Issue signed session token for a new thread | Returns base64 payload with valid HMAC-SHA256 signature |
| `test_verify_session_token_success` | Valid unexpired session token presented | Validates signature and extracts bound `thread_id` |
| `test_verify_session_token_expired` | Expired session token presented | Raises `SessionExpiredError` (HTTP 401) |
| `test_verify_session_token_tampered` | Altered `thread_id` in token without valid HMAC | Raises `InvalidSessionError` (HTTP 401) |
| `test_query_success_with_citations` | Valid query with mock returning retrieved files | Reply returned with formatted `SourceCitation` objects and disclaimer |
| `test_query_empty_retrieval` | User asks off-topic question without relevant docs | Returns polite acknowledgment of insufficient knowledge |
| `test_query_timeout_resilience` | Mock provider triggers 30s timeout | Returns `fallback_mode=True` with conservative safety advice |
| `test_query_rate_limit_resilience` | Mock provider returns HTTP 429 | Returns `fallback_mode=True` without crashing |
| `test_memory_extraction_disabled` | Inspect payload dispatched to Backboard | Verifies `memory="off"` is explicitly set |

---

### Suite B: API Integration Tests (`backend/tests/test_assistant_api.py`)

| Endpoint | Test Scenario | Expected HTTP Code & Body |
| :--- | :--- | :--- |
| `POST /api/assistant/threads` | Public request to initialize session | `201 Created`, returns `session_token` + sets HttpOnly cookie |
| `POST /api/assistant/query` | Query with valid session cookie/token | `200 OK`, JSON matching `AssistantQueryResponse` schema |
| `POST /api/assistant/query` | Query without session token | `401 Unauthorized`, `detail: "Valid session token required"` |
| `POST /api/assistant/query` | Query with tampered signature | `401 Unauthorized`, `detail: "Session signature mismatch"` |
| `POST /api/assistant/query` | Query exceeding max character length (>1000 chars) | `422 Unprocessable Entity` (Pydantic validation error) |
| `POST /api/assistant/query` | Rapid successive requests (>10 requests/minute) | `429 Too Many Requests` |
| `POST /api/assistant/query` | Prompt injection payload (`"Ignore previous instructions"`) | Model adheres to system prompt; returns grounded domain response |

---

### Suite C: Client & Offline Mobile Tests

1. **Next.js Web Client Tests:**
   * Test `fetchAssistantQuery` in `frontend/src/lib/assistant.ts` with mocked backend responses.
   * Verify UI renders markdown text, source pill links, and geotechnical disclaimer.
2. **React Native Mobile Client Tests (`landslide-app/src/__tests__/run-mobile-tests.mjs`):**
   * Test `assistantApi.ts` query handler.
   * Verify offline handling: when network is disconnected, mobile displays local cached emergency guidelines without crashing or entering infinite retry loops.

---

### Suite D: Live Gated Smoke Test (`backend/scripts/smoke_test_backboard.py`)

A standalone CLI script strictly for manual verification by engineers with valid credentials:
```powershell
# Usage:
$env:BACKBOARD_API_KEY="actual_key_here"
$env:BACKBOARD_ASSISTANT_ID="actual_assistant_id_here"
python backend/scripts/smoke_test_backboard.py --live
```
* **Safety Gate:** Fails immediately with exit code 1 unless `--live` flag is explicitly provided.
* **Checks:**
  1. Ping Backboard API (`GET /api/documents` or list assistants).
  2. Create test thread.
  3. Send test query: `"What are three warning signs of a landslide?"`.
  4. Verify response content, latency, and `retrieved_files`.
  5. Delete test thread.

---

## 4. Regression Test Execution Commands

Existing regression suites must be executed before and after any Phase 2 implementation work:

```powershell
# 1. Backend Regression Suite (273 tests)
cd C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM
$env:PYTHONPATH="."
python -m unittest discover -s backend/tests -p "test_*.py"

# 2. Mobile Regression Suite (17 tests)
cd C:/Users/Swapnanil/Desktop/app2/landslide-app
node src/__tests__/run-mobile-tests.mjs
```
