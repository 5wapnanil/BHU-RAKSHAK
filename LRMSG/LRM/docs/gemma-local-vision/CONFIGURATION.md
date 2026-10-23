# Configuration Guide — Gemma Local Vision Inference

## 1. Environment Variables Overview

All settings are configured in `backend/.env`. A template is provided in `backend/.env.example`.

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `GEMMA_PROVIDER` | string | `google` | Active AI provider (`google`, `ollama`, or `mock`). |
| `GEMINI_API_KEY` | string | *None* | Hosted Google AI Studio API key. |
| `GEMMA_MODEL` | string | `gemini-3.5-flash` | Hosted Google GenAI model identifier. |
| `OLLAMA_BASE_URL` | string | `http://localhost:11434` | Base URL of local or remote Ollama daemon. |
| `OLLAMA_MODEL` | string | `gemma3:4b` | Local vision model tag in Ollama. |
| `OLLAMA_TIMEOUT` | float | `60.0` | HTTP timeout (in seconds) for local VLM inference. |
| `GEMMA_ENABLE_FALLBACK` | bool | `false` | Explicitly enable automatic secondary fallback. |
| `GEMMA_FALLBACK_PROVIDER` | string | `ollama` | Provider to use if primary provider is unavailable. |
| `COORDINATOR_API_KEY` | string | *None* | Optional secret key for review/analyze endpoints. |

> [!CAUTION]
> **Secret Preservation Rule:** Never commit `backend/.env` containing real API keys or credentials. Ensure `backend/.env` is listed in `.gitignore`.

---

## 2. Choosing Hosted vs Local Inference

### Option A: Hosted Google AI (Current Default)
Best for cloud deployments with reliable internet connectivity:
```dotenv
GEMMA_PROVIDER=google
GEMMA_MODEL=gemini-3.5-flash
GEMINI_API_KEY="your_api_key_here"
```

### Option B: Local Ollama Gemma 3 Vision (Zero Cloud Dependence)
Best for offline, on-premises, or air-gapped field deployments with a dedicated GPU:
```dotenv
GEMMA_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT=60.0
```

### Option C: In-Memory Mock (Testing & Offline Development)
Best for running automated unit tests without network access or GPU requirements:
```dotenv
GEMMA_PROVIDER=mock
```

---

## 3. Local Ollama & Gemma 3 Installation Procedure

On this host workstation, Ollama 0.40.8 and `gemma3:4b` are already installed and verified:
- **Executable:** `C:\Users\Swapnanil\AppData\Local\Programs\Ollama\ollama.exe`
- **Installed Model:** `gemma3:4b` (3.4 GB)
- **Local Endpoint:** `http://127.0.0.1:11434`

To start the daemon and check availability:
```powershell
& "C:\Users\Swapnanil\AppData\Local\Programs\Ollama\ollama.exe" serve
curl http://127.0.0.1:11434/api/tags
```

---

## 4. Health Checks and Diagnostics

Check FastAPI backend health:
```powershell
curl http://localhost:8000/health
```

Run test screening on a specific report:
```powershell
curl -X POST http://localhost:8000/api/field-reports/<report-id>/analyze
```
