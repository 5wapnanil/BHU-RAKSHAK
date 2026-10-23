# PahaarPulse — Backboard.io API & SDK Technical Verification Report

**Phase:** Phase 1 — Backboard API Verification & RAG Integration Specification  
**System Target:** PahaarPulse Landslide Knowledge Assistant  
**Verification Date:** October 23, 2026  
**Status:** OFFICIAL DOCUMENTATION VERIFIED & SPECIFIED  

---

## 1. Official API Base URL & Authentication

* **Production API Base URL:** `https://app.backboard.io/api`
* **Authentication Header:**
  ```http
  X-API-Key: <BACKBOARD_API_KEY>
  Content-Type: application/json
  ```
* **Dashboard Management:** API keys are generated and revoked in the Backboard Dashboard under *Settings → API Keys*.
* **Transport Security:** All endpoints require TLS 1.3 (HTTPS). Unencrypted HTTP requests are rejected.
* **Official Reference:** [Backboard Quickstart Guide](https://docs.backboard.io/quickstart)

---

## 2. Current Python SDK & Compatibility

* **PyPI Package Name:** `backboard-sdk`
* **Installation Command:**
  ```bash
  pip install backboard-sdk
  ```
* **Python Runtime Requirement:** Python 3.7+ (Fully compatible with PahaarPulse's Python 3.12 environment).
* **Asynchronous Design:** The official client class `BackboardClient` is natively asynchronous:
  ```python
  from backboard import BackboardClient
  client = BackboardClient(api_key=os.environ["BACKBOARD_API_KEY"])
  ```
* **Underlying HTTP Client:** The SDK internally wraps standard asynchronous HTTP requests (`httpx` / `aiohttp`).
* **Official Reference:** [Backboard Python SDK Documentation](https://docs.backboard.io/sdk/quickstart)

---

## 3. Assistant Creation & Configuration

* **Endpoint:** `POST https://app.backboard.io/api/assistants`
* **SDK Method:** `await client.create_assistant(...)`
* **Configuration Parameters:**
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `name` | string | **Yes** | Human-readable identifier (1–255 chars), e.g., `"PahaarPulse Landslide Knowledge Assistant"`. |
  | `system_prompt` | string | **Yes** | Foundational system instructions governing assistant scope, grounding, safety, and disclaimers. |
  | `tools` | array | No | Tool definitions for function calling (web search, custom calculator tools). |
  | `tok_k` / `top_k` | integer | No | Maximum number of document chunks retrieved per query (range: 1–100, default: 10). |
  | `custom_fact_extraction_prompt` | string | No | Custom prompt for extracting memory facts (used when memory is enabled). |
  | `custom_update_memory_prompt` | string | No | Custom prompt for updating, adding, or deleting memory facts. |
  | `embedding_provider` | string | No | Embedding provider (`"openai"`, `"google"`, `"cohere"`). |
  | `embedding_model_name` | string | No | Specific embedding model name (e.g., `"text-embedding-3-large"`). |
  | `embedding_dims` | integer | No | Embedding dimensions (e.g., `3072`). |
* **Immutability Constraint:** Embedding parameters (`embedding_provider`, `embedding_model_name`, `embedding_dims`) are **immutable** upon creation to preserve vector space consistency.
* **Official Reference:** [Backboard Assistant Configuration](https://docs.backboard.io/sdk/assistants)

---

## 4. Conversation Threads Lifecycle

* **Hierarchy:** Assistants act as parents to multiple conversation threads.
* **Thread Initialization Endpoint:** `POST https://app.backboard.io/api/threads`
* **SDK Method:** `await client.create_thread(assistant_id="...")`
* **Implicit Thread Creation:** If `thread_id` is omitted in `POST /api/threads/messages`, Backboard automatically creates a new thread and an underlying assistant behind the scenes.
* **Thread Continuation:** Passing an existing UUID in `thread_id` continues that conversation context.
* **Thread Scoping:** Messages submitted within a thread maintain linear conversational history and context window memory for that thread.
* **Official Reference:** [Backboard Threads Concept](https://docs.backboard.io/concepts/threads)

---

## 5. Document Ingestion & Supported Formats

Backboard supports dual-level document scoping:

1. **Assistant-Level Documents (Shared Domain Corpus):**
   * **Endpoint:** `POST https://app.backboard.io/api/assistants/{assistant_id}/documents`
   * **SDK Method:** `await client.upload_document_to_assistant(assistant_id, file_path)`
   * **Visibility:** Indexed chunks are searchable across **all threads** attached to this assistant. This is the required mechanism for PahaarPulse's scientific articles and emergency safety guidelines.
2. **Thread-Level Documents (User-Specific Context):**
   * **Endpoint:** `POST https://app.backboard.io/api/threads/{thread_id}/documents`
   * **SDK Method:** `await client.upload_document_to_thread(thread_id, file_path)`
   * **Visibility:** Indexed chunks are searchable **only within that specific thread**.
3. **Supported Formats:**
   * **Text / Structured Data:** `.txt`, `.md`, `.markdown`, `.csv`, `.json`, `.jsonl`, `.xml`.
   * **Documents:** `.pdf`, `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`.
   * **Code Files:** `.py`, `.js`, `.ts`, `.html`, `.css`, etc.
   * **Images:** `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.bmp`.
* **Payload Structure:** Multipart form upload with field `file` containing the binary stream and filename.
* **Official Reference:** [Backboard Documents & RAG](https://docs.backboard.io/sdk/documents)

---

## 6. Document Indexing Lifecycle & Status Polling

* **Indexing Lifecycle:** Uploaded files undergo an asynchronous ingestion pipeline:
  $$\text{pending} \longrightarrow \text{processing} \longrightarrow \text{indexed (or error)}$$
* **Status Endpoint:** `GET https://app.backboard.io/api/documents/{document_id}/status`
* **SDK Method:** `await client.get_document_status(document_id)`
* **Status Response Schema:**
  ```json
  {
    "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "status": "indexed",
    "filename": "landslide_science_faq.pdf",
    "chunks": 42,
    "created_at": "2026-10-23T12:00:00Z"
  }
  ```
* **Polling Strategy:** Client should poll every 2–5 seconds with an upper timeout limit of 180 seconds.
* **Error Handling:** If `status == "error"`, inspect `error_message` and retry with clean UTF-8 text formatting.
* **Official Reference:** [Backboard Documents SDK Guide](https://docs.backboard.io/sdk/documents)

---

## 7. Retrieval Mechanism During Query

* **Search Type:** Backboard executes **Hybrid Search** (combining sparse BM25 keyword matching with dense vector similarity search).
* **Chunk Extraction:** During message execution, Backboard queries the assistant's vector index using the user's latest query text (and preceding context).
* **Top-K Retrieval:** Retrieves up to `top_k` (or `tok_k`) chunks configured on the assistant (default: 10 chunks).
* **Context Assembly:** Top-scoring chunks are injected into the model context alongside the system prompt before generating the reply.
* **Official Reference:** [Backboard Architecture Overview](https://docs.backboard.io/concepts/architecture)

---

## 8. Source Attribution & Citation Metadata

* **Message Response Properties:**
  * `retrieved_files`: An array of document filenames and identifiers utilized during retrieval for that query:
    ```json
    "retrieved_files": [
      {"document_id": "doc-uuid-1", "filename": "why-do-landslides-happen.md"},
      {"document_id": "doc-uuid-2", "filename": "rainfall_and_soil_moisture.md"}
    ]
    ```
  * `retrieved_files_count`: Integer indicating the total number of chunks/documents used in context.
* **Memory Citation Flag:**
  * Parameter: `memory_response_citation: true`
  * Instructs the assistant to include fact attribution when assistant memory is active.
* **Technical Limitation:** Backboard does **not** automatically inject inline bracketed academic citation markers (e.g., `[1]`) with character offsets into the generated text.
* **PahaarPulse Engineering Solution:**
  1. The assistant's `system_prompt` must instruct the model to explicitly cite source titles from retrieved context.
  2. The PahaarPulse FastAPI backend will map `retrieved_files` against our local knowledge manifest to attach clean metadata, title, and article URLs in the API response.
* **Official Reference:** [Backboard Messages Concept](https://docs.backboard.io/concepts/messages)

---

## 9. Non-Streaming vs. Streaming Behavior

### Option A: Non-Streaming (`stream=false`) — Recommended for Phase 2 MVP
* **Request:** `POST https://app.backboard.io/api/threads/messages` with `stream: false`.
* **Behavior:** Synchronous HTTP request that blocks until the model completes text generation.
* **Response Payload:**
  ```json
  {
    "message_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "thread_id": "c9a646d3-9c61-4cc9-bc55-e423d242410a",
    "assistant_id": "8a32991a-5f33-4f9e-bc0a-289410d29481",
    "role": "assistant",
    "content": "Landslides are triggered when downward forces exceed resisting forces...",
    "status": "COMPLETED",
    "retrieved_files": ["why-do-landslides-happen.md"],
    "retrieved_files_count": 1,
    "reasoning": null
  }
  ```
* **Pros:** Simplest implementation, deterministic response handling, standard JSON schemas, easiest to test and validate offline.

### Option B: Streaming (`stream=true`) — Target for Phase 3
* **Request:** `POST https://app.backboard.io/api/threads/messages` with `stream: true`.
* **Behavior:** Streams text chunks using Server-Sent Events (SSE).
* **Chunk Format:**
  ```json
  {"type": "content_streaming", "content": "Landslides "}
  {"type": "content_streaming", "content": "are "}
  ...
  {"type": "message_completed", "thread_id": "...", "retrieved_files": [...]}
  ```
* **Pros:** Lower perceived time-to-first-token (TTFT).
* **Cons:** Requires FastAPI `StreamingResponse`, SSE parser on Next.js and React Native, more complex error recovery.

---

## 10. Timeouts, Rate Limits & Error Codes

* **Documented Error Codes:**
  * `400 Bad Request`: Invalid payload parameters or malformed JSON.
  * `401 Unauthorized`: Missing or invalid `X-API-Key`.
  * `404 Not Found`: Referenced `assistant_id`, `thread_id`, or `document_id` does not exist.
  * `422 Unprocessable Entity`: Document upload format or size violation.
  * `429 Too Many Requests`: Exceeded request rate limit or token quota.
  * `500 / 503 Internal Server Error`: Backboard or upstream LLM provider temporary outage.
* **Retry Guidelines:**
  * Do **not** blindly retry non-idempotent message submissions on connection resets without verifying thread state.
  * Use exponential backoff with jitter on `429` and `503`.
* **Recommended Backend Timeout:** 30 seconds for non-streaming queries; 180 seconds for document indexing.

---

## 11. SDK vs. Direct REST API Comparison

| Dimension | `backboard-sdk` (Python Package) | Direct REST via `httpx.AsyncClient` |
| :--- | :--- | :--- |
| **Dependency Footprint** | Adds 1 external package and its transitive dependencies | Zero new dependencies (`httpx` is standard in modern FastAPI) |
| **Async Compatibility** | Native `asyncio` (`async def ... await client`) | Native `httpx.AsyncClient` with connection pooling |
| **Mocking & Testability** | Requires mocking external SDK class methods | Easily mocked using `httpx.MockTransport` or custom protocol |
| **API Drift Resilience** | Dependent on maintainer releasing updates | Direct control over headers, query params, and body parsing |
| **Maintenance Risk** | Breaking changes in SDK could stall backend builds | Stable HTTP contracts matching official REST endpoints |

---

## 12. Dependency Assessment & Decision

**Can the integration work without adding an unnecessary new dependency?**
* **YES.**
* Using `httpx.AsyncClient` with direct REST calls to `https://app.backboard.io/api` gives PahaarPulse 100% of Backboard's functionality with zero SDK vendor lock-in.
* In accordance with PahaarPulse's existing `GemmaAnalysisService` and `GemmaProviders` pattern ([`backend/app/services/gemma_providers.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/gemma_providers.py)), we recommend defining a `BackboardProvider` Protocol with:
  1. `LiveBackboardRESTProvider` (using `httpx.AsyncClient` to call `POST https://app.backboard.io/api/threads/messages`).
  2. `MockBackboardProvider` (returning static verified landslide knowledge responses for unit tests).
