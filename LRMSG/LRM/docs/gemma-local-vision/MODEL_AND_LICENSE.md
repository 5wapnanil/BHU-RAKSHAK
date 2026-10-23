# Model and License Specification — Gemma Local Vision Inference

## Selected Primary Local Vision Model: Google Gemma 3 4B (`gemma3:4b`)

### 1. Model Overview & Identifier
- **Model Name:** Gemma 3 4B Instruction Tuned
- **Ollama Identifier:** `gemma3:4b`
- **Hugging Face Identifier:** `google/gemma-3-4b-it`
- **Publisher:** Google DeepMind
- **Release Date:** 2025/2026
- **Architecture:** Multimodal Auto-regressive Decoder with native SigLIP vision encoder and 128k token context window.

### 2. Vision and Structured JSON Support
- **Vision Modality:** Native multimodal architecture trained to accept interleaved text and high-resolution image inputs.
- **Image Input Handling in Ollama:** Passed via the `"images"` field in `/api/generate` or `/api/chat` as base64-encoded strings or image file paths.
- **Structured Output Support:** Compatible with Ollama's `"format": "json"` parameter, enabling schema-compliant extraction of `hazard_level`, `detected_hazards`, `confidence`, `summary`, and `limitations`.

### 3. Hardware & Storage Requirements
- **Parameter Count:** 4 Billion parameters.
- **Quantized Storage Footprint (Q4_K_M):** ~3.1 GB disk storage.
- **Runtime Memory / VRAM Footprint:** ~3.8 GB to 4.2 GB VRAM for 2048-token context.
- **Host Compatibility:**
  - Machine GPU: NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM).
  - VRAM Headroom: ~4.0 GB free VRAM remaining during inference.
  - Host RAM: 16 GB physical RAM.
  - Host Disk: 269 GB available on Drive C:.

### 4. License and Usage Terms
- **License:** Gemma Terms of Use (permissive open-weights license).
- **Commercial Use:** Permitted under the Gemma Terms of Use, provided users comply with Google's Prohibited Use Policy.
- **Open-Weight Verification:** Weights are publicly downloadable and runnable fully on-premises without cloud dependencies.
- **Redistribution:** Weights and fine-tunes may be redistributed in accordance with the Gemma license terms.

---

## Alternative Evaluated Vision Models

| Model Identifier | Publisher | Parameters | Quantized Size | VRAM Req. | Suitability Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`gemma3:4b`** | Google DeepMind | 4B | ~3.1 GB | ~4.0 GB | **Selected Primary:** Direct Gemma family member; native vision; fits easily in 8 GB VRAM. |
| **`llama3.2-vision:11b`** | Meta | 11B | ~7.9 GB | ~8.8 GB | Viable fallback; exceeds comfortable 8 GB VRAM threshold, requiring partial CPU offloading. |
| **`moondream:1.8b`** | Vikhyat | 1.8B | ~1.7 GB | ~2.2 GB | Ultra-lightweight fallback; lower nuance for specialized geotechnical categorization. |
| **`llava:7b`** | LLaVA Team | 7B | ~4.7 GB | ~5.5 GB | Well-supported open VLM; superseded by Gemma 3 for Gemma-aligned pipelines. |

---

## Current Environment Status & Live Verification

- **Ollama Runtime:** Installed at `C:\Users\Swapnanil\AppData\Local\Programs\Ollama\ollama.exe` (v0.40.8). Daemon active and bound to `http://127.0.0.1:11434`.
- **Model Status:** `gemma3:4b` downloaded (3.4 GB total across base and vision layers) and verified present.
- **Hardware Profile:**
  - Machine GPU: NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM), Driver 592.82, CUDA 13.1.
  - Active VRAM Footprint: 3,821 MiB / 8,188 MiB (~4.36 GB free headroom).
  - Process: `llama-server.exe` PID 32152.
- **Live Multimodal Verification:** Verified end-to-end on real 4.39 MB geotechnical landslide photograph with 2.98s warm GPU response time, schema validation, and PostgreSQL persistence.
