# PahaarPulse — Phase 1: Backboard API Verification & RAG Integration Report

**Project:** PahaarPulse Landslide Risk Management Platform  
**Phase:** Phase 1 — Technical Verification & Integration Specification  
**Author:** Senior Backend Architect, AI/RAG Engineer & Application Security Reviewer  
**Date:** October 23, 2026  
**Status:** COMPLETE (READ-ONLY SPECIFICATION DELIVERED)  

---

## 1. Executive Summary

Phase 1 technical verification for integrating **Backboard.io** as a Retrieval-Augmented Generation (RAG) Landslide Knowledge Assistant in PahaarPulse has been completed.

The investigation verified Backboard's official API contracts, evaluated the existing PahaarPulse codebase across backend, web, and mobile subsystems, and formulated an implementation-ready specification that:
1. **Brokers all interactions through the existing FastAPI backend**, ensuring the `BACKBOARD_API_KEY` never reaches browser or mobile environments.
2. **Solves the conversation ownership problem** in an unauthenticated system using cryptographic HMAC-SHA256 session tokens.
3. **Guarantees multi-user privacy** by strictly disabling Backboard's cross-user memory extraction (`memory: "off"`).
4. **Preserves complete separation** between the informational RAG assistant and PahaarPulse's real-time numerical GIS/XGBoost models and emergency response pipelines.
5. **Maintains 100% offline testability** by designing a deterministic `MockBackboardProvider`, preventing paid API dependencies in CI/CD.

No application code or database records were modified during this phase.

---

## 2. Actual Architecture Findings & File Inventory

The existing repository architecture was traced directly from source files:

* **Backend Entry & Routing:** [`LRMSG/LRM/backend/app/main.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/main.py) registers modular routers via `app.include_router(..., prefix="/api/...")` and mounts `/uploads` for static media.
* **Database & Sessions:** PostgreSQL 16 / PostGIS managed via SQLAlchemy 2.0 in [`backend/app/database/base.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/database/base.py) with `get_db` dependency injection and 7 active Alembic migrations.
* **Existing AI Service Pattern:** [`backend/app/services/gemma_analysis_service.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/gemma_analysis_service.py) and [`backend/app/services/gemma_providers.py`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/services/gemma_providers.py) implement a clean `Protocol` abstraction separating the live model client from a deterministic mock provider with custom error hierarchies.
* **Web Frontend:** Next.js 16.3.4 (App Router) in [`frontend/src/app/`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/frontend/src/app). API requests are dispatched via [`apiFetch<T>`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/frontend/src/lib/api.ts#L27) in [`frontend/src/lib/api.ts`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/frontend/src/lib/api.ts). Privileged coordinator requests utilize Next.js Route Handlers as Backend-For-Frontend (BFF) proxies.
* **Mobile Subsystem:** React Native 0.76.7 / Expo ~52.0.0 in [`landslide-app/`](file:///C:/Users/Swapnanil/Desktop/app2/landslide-app), communicating through [`apiClient`](file:///C:/Users/Swapnanil/Desktop/app2/landslide-app/src/services/api/client.ts) with offline priority queueing in [`syncQueue.ts`](file:///C:/Users/Swapnanil/Desktop/app2/landslide-app/src/services/sync/syncQueue.ts).
* **Existing Domain Knowledge Base:** 6 structured scientific articles authored by the research team reside in [`frontend/src/data/articles.ts`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/frontend/src/data/articles.ts), covering landslide triggering mechanisms, GIS risk maps, ML prediction, soil moisture, and satellite monitoring.

---

## 3. Backboard API Verification Summary

Based on official documentation at `https://docs.backboard.io`:

1. **Base URL & Auth:** `https://app.backboard.io/api` using header `X-API-Key: <KEY>`.
2. **SDK:** `backboard-sdk` on PyPI (Python 3.7+), async-first client `BackboardClient`.
3. **Core Endpoints:**
   * Assistant: `POST /api/assistants` (defines name, `system_prompt`, `tok_k`/`top_k`, tools, and immutable embedding configs).
   * Threads: `POST /api/threads` (creates thread tied to an `assistant_id`).
   * Messages: `POST /api/threads/messages` (submits query; supports non-streaming JSON or SSE streaming).
   * Document Ingestion: `POST /api/assistants/{id}/documents` (assistant-level shared context) and `POST /api/threads/{id}/documents` (thread-specific context).
   * Status Polling: `GET /api/documents/{id}/status` (`pending` $\rightarrow$ `processing` $\rightarrow$ `indexed`).
4. **Citations & Attribution:** The message response object includes `retrieved_files` (array of document filenames/IDs used in generation) and `retrieved_files_count`. Backboard does not generate inline sentence-level citation tags; these must be instructed via the system prompt and formatted by the backend.
5. **Architectural Evaluation:** A direct async REST client via `httpx.AsyncClient` is superior to installing `backboard-sdk` because it eliminates third-party dependency drift, allows exact connection pooling, and simplifies mock testing.

---

## 4. Recommended Architecture & Fit

The proposed architecture introduces three modular additions to the FastAPI backend:

```text
backend/app/services/backboard/
  ├── config.py         # Reads BACKBOARD_API_KEY, ASSISTANT_ID, TIMEOUT_SECONDS from .env
  ├── providers.py      # BackboardProvider Protocol, LiveBackboardProvider, MockBackboardProvider
  └── service.py        # BackboardService orchestrating sessions, rate-limits, and citation mapping
backend/app/api/
  ├── schemas/assistant.py     # Pydantic models (QueryRequest, QueryResponse, SourceCitation)
  └── endpoints/assistant.py   # Router registered in main.py (/api/assistant/threads, /query)
```

### Why this fits PahaarPulse
* Reuses existing [`SessionLocal`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/backend/app/database/base.py#L20) and dependency injection patterns.
* Mirrors the established `GemmaAnalysisService` protocol abstraction.
* Works seamlessly with Next.js [`apiFetch<T>`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/frontend/src/lib/api.ts#L27) and React Native [`apiClient`](file:///C:/Users/Swapnanil/Desktop/app2/landslide-app/src/services/api/client.ts).

---

## 5. Security and Privacy Assessment

| Security Dimension | Verified Finding | Action / Mitigation |
| :--- | :--- | :--- |
| **API Key Protection** | Secrets in `backend/.env` are shielded from client bundles. | Store `BACKBOARD_API_KEY` strictly in `backend/.env`. |
| **User Identity & Auth** | User authentication is **missing**; coordinator routes use shared key. | Implement HMAC-SHA256 signed session tokens embedding `thread_id`. |
| **Cross-User Thread Snooping** | Unchecked client UUIDs would allow thread hijacking. | Client never supplies raw `thread_id`; backend extracts it from signed token. |
| **Shared Assistant Fact Leak** | `memory: "Auto"` extracts facts into shared assistant context. | **Mandatory:** Configure `memory: "off"` on all message queries. |
| **Denial of Service** | Public assistant endpoint could exhaust API quota. | Add route-level rate limiting (10 queries/min per IP/session). |
| **Grounding & Prompt Injection** | Retrieved documents could contain adversarial text. | System prompt instructs model to treat documents strictly as passive facts. |

---

## 6. Knowledge-Base Readiness & Provenance

* **Tier 1 (Ready for Ingestion):**
  * 6 PahaarPulse scientific articles from `frontend/src/data/articles.ts`.
  * Official NDMA / SDMA Community Landslide Safety & Evacuation Guidelines.
* **Tier 2 (Pending Review):**
  * Internal Geological Hazard Identification SOPs and USGS technical primers.
* **Tier 3 (Rejected):**
  * Raw sensor telemetry logs, intermediate scraper CSVs, and operational emergency reports.
* **Ingestion Utility:** An idempotent CLI tool (`backend/scripts/ingest_knowledge_base.py`) will hash documents, check against `knowledge_base_manifest.json`, upload via `POST /api/assistants/{id}/documents`, and poll until `indexed`.

---

## 7. Proposed API Contracts

### `POST /api/assistant/threads`
* **Response `201 Created`:**
  ```json
  {
    "session_token": "eyJhbGciOiJIUzI1NiJ9.eyJzZXNzaW9uX2lkI...",
    "expires_at": "2026-10-24T14:00:00Z"
  }
  ```
  *(Also sets `pp_assistant_session` HttpOnly cookie for web browsers).*

### `POST /api/assistant/query`
* **Headers:** `Authorization: Bearer <session_token>` (or `Cookie: pp_assistant_session=<token>`).
* **Request Body:**
  ```json
  {
    "query": "What should residents do immediately if tension cracks appear on a slope?"
  }
  ```
* **Response `200 OK`:**
  ```json
  {
    "reply": "If tension cracks appear along a slope, residents should immediately evacuate the area...",
    "sources": [
      {
        "title": "Why Do Landslides Happen? Understanding Signals Before Failure",
        "document_id": "doc-uuid-1",
        "url_or_slug": "why-do-landslides-happen",
        "category": "LANDSLIDE SCIENCE"
      }
    ],
    "disclaimer": "PahaarPulse Assistant provides general educational and safety guidance based on documented landslide science. It does not replace real-time emergency orders from district authorities or on-site geotechnical engineering inspections.",
    "fallback_mode": false
  }
  ```

---

## 8. Test Plan Summary

1. **Default Offline Test Suite:** Uses `MockBackboardProvider` to test session token generation, signature tampering, timeout resilience, rate limiting, and citation parsing without network calls.
2. **Gated Live Smoke Test:** `backend/scripts/smoke_test_backboard.py --live` for developers with local keys.
3. **Regression Guarantee:** Guarantees zero breakage across the existing 273 backend tests and 17 mobile tests.

---

## 9. Key Decisions Requiring Approval

Detailed in [`BACKBOARD_PHASE_1_DECISIONS.md`](file:///C:/Users/Swapnanil/Desktop/app2/LRMSG/LRM/docs/backboard/BACKBOARD_PHASE_1_DECISIONS.md):
1. **Direct REST via `httpx`** instead of adding `backboard-sdk` dependency.
2. **Cryptographic HMAC session tokens** to secure conversations before user auth is implemented.
3. **Mandatory `memory="off"`** to prevent cross-user data leakage.
4. **Non-streaming JSON response** for initial Phase 2 MVP.
5. **Ingestion limited to Tier 1 Approved Corpus**.

---

## 10. Prioritized Phase 2 Implementation Plan

| Milestone | Scope & Deliverables | Review Gate |
| :--- | :--- | :--- |
| **M1: Dependencies & Provider Layer** | Add `httpx` to `backend/requirements.txt`; create `BackboardProvider` protocol and `MockBackboardProvider`. | 100% offline unit tests pass. |
| **M2: Service & Session Security** | Implement HMAC session token generator, session verification, and `BackboardService`. | Session tampering and expiry tests pass. |
| **M3: API Router & Schemas** | Implement `backend/app/api/endpoints/assistant.py` and register in `main.py` with rate limiting. | FastAPI endpoint integration tests pass. |
| **M4: Ingestion Tooling & Manifest** | Create `ingest_knowledge_base.py`; ingest Tier 1 articles into live Backboard assistant. | Verified all 7 docs report `status: "indexed"`. |
| **M5: Web Frontend UI** | Create Assistant Drawer / Floating Chat in Next.js using `apiFetch`; add sidebar navigation link. | E2E browser Q&A and citation rendering verified. |
| **M6: Mobile App Integration** | Add Knowledge Assistant entry in `LandslideSafetyGuideScreen.tsx` with offline fallback. | Mobile unit tests (17/17) pass. |

---

## 11. Codebase Invariance Statement

**No application source code, configuration files, environment variables, or database records were modified during this phase.**

All existing operational tables (`EmergencyRequest` = 90, `Shelter` = 11, `FieldReport` = 6) remain untouched, and the existing test suites remain passing:
* **Backend:** 273/273 tests passing (`Ran 273 tests in 2.045s, OK`).
* **Mobile:** 17/17 tests passing (`pass 17, fail 0`).
