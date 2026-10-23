# PahaarPulse — Backboard RAG Integration: Phase 1 Key Decisions

**Phase:** Phase 1 — Architectural Decision Records  
**Project:** PahaarPulse Landslide Knowledge Assistant  
**Date:** October 23, 2026  
**Status:** AWAITING PROJECT OWNER SIGN-OFF BEFORE PHASE 2 IMPLEMENTATION  

---

## Decision 1: Direct Async REST Client (`httpx`) vs. Adding `backboard-sdk` Dependency

* **Context:** Backboard offers an official `backboard-sdk` Python package. Alternatively, FastAPI can interact directly with Backboard's REST endpoints (`https://app.backboard.io/api`) via `httpx.AsyncClient`.
* **Options Considered:**
  1. *Install `backboard-sdk`:* Use high-level wrapper.
  2. *Direct REST with `httpx` (Recommended):* Implement a lean, asynchronous client protocol directly matching PahaarPulse's existing `GemmaAnalysisService` and `GemmaProviders` pattern.
* **Architect's Recommendation:** **Option 2 (Direct REST with `httpx`).**
  * *Rationale:* Avoids pinning an external SDK whose transitive dependencies or future breaking changes could disrupt backend stability. Provides precise control over timeouts, connection pools, and mock transports for offline unit tests.
* **Sign-Off Required:** `[APPROVED / REJECTED / PENDING]`

---

## Decision 2: Anonymous Session Security via Cryptographic HMAC Tokens

* **Context:** The application currently lacks user registration and session management. Allowing clients to supply an arbitrary `thread_id` would permit cross-user conversation snooping.
* **Options Considered:**
  1. *Client-supplied raw UUIDs (Insecure):* Rejected due to zero isolation.
  2. *Wait for complete User Authentication milestone:* Delays knowledge assistant launch indefinitely.
  3. *Cryptographic HMAC-SHA256 Session Tokens (Recommended):* The backend generates an unpredictable session token embedding `session_id` and `thread_id`, signed with `SESSION_SIGNING_KEY`. The client presents this token in an `HttpOnly` cookie or Bearer header; the backend extracts the bound `thread_id` only after verifying the signature.
* **Architect's Recommendation:** **Option 3.**
  * *Rationale:* Solves the conversation isolation and authorization problem immediately without blocking on user auth, while establishing an easy migration path once auth is implemented.
* **Sign-Off Required:** `[APPROVED / REJECTED / PENDING]`

---

## Decision 3: Mandatory Disabling of Assistant-Level Memory Extraction

* **Context:** Backboard provides automated memory extraction (`memory: "Auto"`), which extracts facts from chat messages and saves them to the assistant.
* **Risk:** In an assistant shared across multiple community members and responders, if User A mentions sensitive personal details (e.g. family location, medical condition), Backboard's memory could index that fact and inadvertently surface it in response to User B's query.
* **Options Considered:**
  1. *Enable Memory (`memory: "Auto"`):* Extreme privacy violation risk across shared users.
  2. *Disable Memory (`memory: "off"` - Recommended):* The assistant uses conversation history *only within the active thread* and searches the curated knowledge base without extracting or storing persistent cross-user facts.
* **Architect's Recommendation:** **Option 2 (`memory: "off"`).**
  * *Rationale:* Non-negotiable for multi-user safety and compliance.
* **Sign-Off Required:** `[APPROVED / REJECTED / PENDING]`

---

## Decision 4: Non-Streaming (`stream: false`) for Phase 2 MVP

* **Context:** Backboard supports Server-Sent Events (SSE) streaming and standard non-streaming JSON responses.
* **Options Considered:**
  1. *Non-Streaming (Recommended for MVP):* Request/response with structured Pydantic validation, deterministic JSON payloads, and simple frontend error boundaries.
  2. *Real-time Streaming:* Lower time-to-first-token, but requires FastAPI `StreamingResponse`, SSE stream parsing in React/Next.js, and SSE handling in React Native mobile.
* **Architect's Recommendation:** **Option 1 for Phase 2 MVP**, with streaming deferred to Phase 3.
  * *Rationale:* Ensures rock-solid reliability, simple citation parsing, and straightforward testing before adding streaming complexity.
* **Sign-Off Required:** `[APPROVED / REJECTED / PENDING]`

---

## Decision 5: Knowledge Base Ingestion Scope for Launch

* **Context:** Deciding which documents should be ingested into the Backboard assistant knowledge base for initial launch.
* **Options Considered:**
  1. *Ingest everything (including raw data & scrape manifests):* High hallucination risk.
  2. *Tier 1 Approved Corpus Only (Recommended):*
     - The 6 scientific articles from `frontend/src/data/articles.ts` (Why Landslides Happen, GIS Risk Mapping, ML Prediction, Rainfall & Soil Moisture, Satellites, Early Warning).
     - Official National Disaster Management Authority (NDMA) Community Landslide Safety & Evacuation Guidelines.
* **Architect's Recommendation:** **Option 2 (Tier 1 Only).**
  * *Rationale:* High-quality, verified, internal provenance with zero copyright uncertainty.
* **Sign-Off Required:** `[APPROVED / REJECTED / PENDING]`

---

## Decision 6: Rate Limiting & User Query Quotas

* **Context:** Protecting the Backboard API against quota exhaustion and Denial-of-Service attacks.
* **Recommended Policy:**
  * Thread initialization: Maximum 5 new threads per hour per IP.
  * Query submissions: Maximum 10 queries per minute per session / IP.
  * Maximum query length: 1,000 characters.
* **Sign-Off Required:** `[APPROVED / REJECTED / PENDING]`

---

## Decision 7: Geotechnical Disclaimer & Liability Framing

* **Context:** The AI assistant must never be construed as an official geotechnical slope certification or real-time evacuation order.
* **Mandatory Text Appended to Every Response:**
  > *"PahaarPulse Assistant provides general educational and safety guidance based on documented landslide science. It does not replace real-time emergency orders from district authorities or on-site geotechnical engineering inspections."*
* **Sign-Off Required:** `[APPROVED / REJECTED / PENDING]`
