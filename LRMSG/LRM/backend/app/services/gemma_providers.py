"""Provider-independent Gemma AI inference boundary.

Supports Google GenAI SDK (multimodal Gemini/Gemma), local Ollama (Gemma2/PaliGemma),
and deterministic mock providers for testing and local development.
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Optional, Protocol, Tuple

from dotenv import load_dotenv

from backend.app.api.schemas.gemma_analysis import GemmaHazardOutput

# Ensure backend/.env is loaded following project conventions
_backend_dir = Path(__file__).resolve().parents[2]
load_dotenv(_backend_dir / ".env")

logger = logging.getLogger(__name__)


class GemmaProviderError(Exception):
    """Base exception for AI provider inference failures."""
    pass


class GemmaProviderUnavailableError(GemmaProviderError):
    """Raised when the configured provider runtime or credentials are not available."""
    pass


class GemmaTimeoutError(GemmaProviderError):
    """Raised when model inference times out."""
    pass


class GemmaRateLimitError(GemmaProviderError):
    """Raised when inference request is rate limited (HTTP 429)."""
    pass


class GemmaTemporaryUnavailableError(GemmaProviderError):
    """Raised when the provider is temporarily unavailable or overloaded (HTTP 503 / high demand spikes)."""
    pass


class GemmaMalformedOutputError(GemmaProviderError):
    """Raised when model response cannot be parsed into the expected schema."""
    pass


class AnalysisProvider(Protocol):
    """Abstract protocol for Gemma AI hazard analysis."""

    @property
    def provider_name(self) -> str:
        """Name of the inference provider."""
        ...

    def is_available(self) -> bool:
        """Check whether credentials and runtime are available."""
        ...

    async def analyze(
        self,
        notes: Optional[str],
        location_name: Optional[str],
        photo_bytes: Optional[bytes] = None,
        photo_mime: Optional[str] = None,
    ) -> GemmaHazardOutput:
        """Perform multimodal or text-only geotechnical hazard screening."""
        ...


SYSTEM_PROMPT = (
    "You are PahaarPulse Geotechnical Screening Assistant, an AI triage system designed to "
    "screen ground field reports for landslide indicators in mountainous terrain. "
    "Analyze the provided field observation notes and optional photograph for visible geotechnical indicators.\n\n"
    "OBSERVABLE GEOTECHNICAL HAZARD INDICATORS:\n"
    "- tension_cracks: Visible fissures or tension cracks in soil, rock mass, or asphalt pavement.\n"
    "- slope_displacement: Visible downslope slippage, scarps, shear failures, or offset terrain.\n"
    "- toe_erosion: Stream cutting, gully erosion, or destabilized toe of slope.\n"
    "- rockfall_debris: Boulders, rock fragments, or talus fallen from cliffs or slopes.\n"
    "- road_blockage: Embankment collapse, road obstruction, or road surface sloughing.\n"
    "- structural_damage: Fractured retaining walls, bent guardrails, distressed culverts, or damaged buildings.\n"
    "- mudflow: Saturated debris slurry, mud tracks, or active washouts.\n"
    "- water_seepage: Active groundwater bubbling, slope saturated weep points, or ponding.\n\n"
    "You must return ONLY a JSON object with this exact structure:\n"
    "{\n"
    '  "hazard_level": "low" | "moderate" | "high" | "critical" | "indeterminate",\n'
    '  "detected_hazards": ["string"],\n'
    '  "confidence": float (between 0.0 and 1.0 representing uncalibrated observational clarity),\n'
    '  "summary": "concise description of visible geotechnical features and observer reports",\n'
    '  "limitations": "explicit caveats, image quality constraints, or observational uncertainty"\n'
    "}\n\n"
    "CRITICAL GEOTECHNICAL SCREENING RULES:\n"
    "1. SEPARATION OF EVIDENCE: Differentiate directly visible features in the photograph from assertions in observer notes. "
    "Only include indicators in 'detected_hazards' that are visibly supported by the image (or described in text if text-only). "
    "Do NOT treat an observer's written claims as physical visual confirmation.\n"
    "2. UNCERTAINTY & INDETERMINATE: If image quality, lighting, perspective, distance, or vegetation obscures the slope, "
    "or if evidence is insufficient to assess stability, classify 'hazard_level' as 'indeterminate'. Never default an uncertain report to 'low'.\n"
    "3. NO SAFETY CLEARANCES: Never state or imply that a slope or location is safe, stable, or cleared for occupancy. "
    "This analysis is strictly a preliminary triage screening and is NOT a substitute for an on-site geotechnical engineering inspection.\n"
    "4. UNCALIBRATED CONFIDENCE: The confidence score is a subjective model-reported clarity index, not a statistically calibrated probability.\n"
    "5. Return strictly valid JSON with no markdown formatting or prose outside the JSON."
)


def parse_gemma_json(raw_text: str) -> GemmaHazardOutput:
    """Safely extracts and parses JSON output from models, handling markdown fences and whitespace."""
    if not raw_text or not raw_text.strip():
        raise GemmaMalformedOutputError("Model returned empty response text.")

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise GemmaMalformedOutputError(
            f"Failed to parse model JSON: {e}. Raw response snippet: {cleaned[:200]}"
        ) from e

    try:
        return GemmaHazardOutput.model_validate(data)
    except Exception as e:
        raise GemmaMalformedOutputError(f"Output schema validation failed: {e}") from e


class MockGemmaProvider:
    """Deterministic provider for testing, offline verification, and demos."""

    def __init__(
        self,
        *,
        simulate_error: Optional[str] = None,
        simulate_timeout: bool = False,
        simulate_rate_limit: bool = False,
        simulate_unavailable: bool = False,
        simulate_malformed: bool = False,
        simulate_missing_model: bool = False,
        simulate_connection_error: bool = False,
        simulate_markdown_json: bool = False,
        custom_output: Optional[GemmaHazardOutput] = None,
    ):
        self.simulate_error = simulate_error
        self.simulate_timeout = simulate_timeout
        self.simulate_rate_limit = simulate_rate_limit
        self.simulate_unavailable = simulate_unavailable
        self.simulate_malformed = simulate_malformed
        self.simulate_missing_model = simulate_missing_model
        self.simulate_connection_error = simulate_connection_error
        self.simulate_markdown_json = simulate_markdown_json
        self.custom_output = custom_output

        # Provenance and inspection tracking for test verification
        self.last_received_notes: Optional[str] = None
        self.last_received_location: Optional[str] = None
        self.last_received_photo_bytes: Optional[bytes] = None
        self.last_received_photo_mime: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return "mock_gemma"

    def is_available(self) -> bool:
        return True

    async def analyze(
        self,
        notes: Optional[str],
        location_name: Optional[str],
        photo_bytes: Optional[bytes] = None,
        photo_mime: Optional[str] = None,
    ) -> GemmaHazardOutput:
        self.last_received_notes = notes
        self.last_received_location = location_name
        self.last_received_photo_bytes = photo_bytes
        self.last_received_photo_mime = photo_mime

        if self.simulate_connection_error:
            raise GemmaProviderUnavailableError("Cannot connect to Ollama daemon at http://localhost:11434")
        if self.simulate_missing_model:
            raise GemmaProviderUnavailableError(
                "Ollama model 'gemma3:4b' is not pulled. Run 'ollama pull gemma3:4b' on the host."
            )
        if self.simulate_unavailable:
            raise GemmaTemporaryUnavailableError("Mock provider temporarily unavailable (HTTP 503).")
        if self.simulate_timeout:
            raise GemmaTimeoutError("Mock inference timed out after 30 seconds.")
        if self.simulate_rate_limit:
            raise GemmaRateLimitError("Mock provider rate limit exceeded (HTTP 429).")
        if self.simulate_error:
            raise GemmaProviderError(self.simulate_error)
        if self.simulate_malformed:
            raise GemmaMalformedOutputError("Model returned non-JSON unstructured output: 'I cannot answer this.'")
        if self.simulate_markdown_json:
            mock_markdown = '```json\n{"hazard_level": "moderate", "detected_hazards": ["tension_cracks"], "confidence": 0.8, "summary": "Markdown wrapped", "limitations": "None"}\n```'
            return parse_gemma_json(mock_markdown)
        if self.custom_output:
            return self.custom_output

        text_content = (notes or "").lower()
        has_photo = photo_bytes is not None and len(photo_bytes) > 0

        # Deterministic keyword heuristic for testing
        detected: list[str] = []
        hazard_level = "indeterminate"
        confidence = 0.50

        if any(w in text_content for w in ("critical", "massive", "washed away", "blocked", "debris flow", "catastrophic")):
            hazard_level = "critical"
            detected = ["slope_displacement", "road_blockage", "rockfall_debris"]
            confidence = 0.90 if has_photo else 0.75
        elif any(w in text_content for w in ("high", "major crack", "active movement", "mudflow")):
            hazard_level = "high"
            detected = ["tension_cracks", "slope_displacement"]
            confidence = 0.85 if has_photo else 0.70
        elif any(w in text_content for w in ("moderate", "crack", "fissure", "slump", "erosion")):
            hazard_level = "moderate"
            detected = ["tension_cracks", "toe_erosion"]
            confidence = 0.80 if has_photo else 0.65
        elif any(w in text_content for w in ("low", "minor", "stable", "seepage")):
            hazard_level = "low"
            detected = ["water_seepage"]
            confidence = 0.75 if has_photo else 0.60
        elif has_photo:
            # Photo provided without strong keywords -> moderate screening baseline
            hazard_level = "moderate"
            detected = ["surface_disturbance"]
            confidence = 0.65
        else:
            hazard_level = "indeterminate"
            detected = []
            confidence = 0.40

        loc_desc = f" near {location_name}" if location_name else ""
        if has_photo:
            summary = (
                f"Multimodal screening of field photograph and notes{loc_desc} identified "
                f"{', '.join(detected) if detected else 'unresolved features'}. Preliminary classification: {hazard_level}."
            )
            limitations = "Visual assessment limited by camera angle, lighting, and lack of ground-truth scale."
        else:
            summary = (
                f"Text-only screening of observer notes{loc_desc}. "
                f"Reported indicators: {', '.join(detected) if detected else 'unspecified movement'}. "
                f"Preliminary classification: {hazard_level}."
            )
            limitations = "No field photograph attached. Physical visual confirmation is completely absent."

        return GemmaHazardOutput(
            hazard_level=hazard_level,  # type: ignore[arg-type]
            detected_hazards=detected,
            confidence=confidence,
            summary=summary,
            limitations=limitations,
        )


class GoogleGenAIGemmaProvider:
    """Cloud inference provider utilizing Google GenAI SDK (Gemini / Gemma multimodal)."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_GENAI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        self.model_name = model_name or os.environ.get("GEMMA_MODEL", "gemini-2.5-flash")

    @property
    def provider_name(self) -> str:
        return f"google_genai:{self.model_name}"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def analyze(
        self,
        notes: Optional[str],
        location_name: Optional[str],
        photo_bytes: Optional[bytes] = None,
        photo_mime: Optional[str] = None,
    ) -> GemmaHazardOutput:
        if not self.is_available():
            raise GemmaProviderUnavailableError(
                "Google GenAI API key is missing. Configure GEMINI_API_KEY or GOOGLE_GENAI_API_KEY."
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise GemmaProviderUnavailableError(f"google-genai SDK not installed: {e}")

        client = genai.Client(api_key=self.api_key)

        prompt_parts: list = [
            SYSTEM_PROMPT,
            f"\n\n--- OBSERVATION DATA ---\n"
            f"Location: {location_name or 'Unspecified coordinates'}\n"
            f"Observer Notes: {notes or 'No written notes provided.'}\n"
        ]

        if photo_bytes:
            clean_mime = photo_mime or "image/jpeg"
            prompt_parts.append(
                types.Part.from_bytes(data=photo_bytes, mime_type=clean_mime)
            )
            prompt_parts.append("\nAnalyze the attached field photograph in conjunction with the observer notes.")
        else:
            prompt_parts.append(
                "\nNOTE: No field photograph was attached. Perform text-based analysis of notes only."
            )

        try:
            # Execute generation with JSON mode
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt_parts,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            return parse_gemma_json(response.text)

        except GemmaMalformedOutputError:
            raise
        except Exception as e:
            err_str = str(e)
            err_lower = err_str.lower()
            code = getattr(e, "code", None) or getattr(e, "status_code", None)

            # Temporary provider capacity / unavailability (HTTP 503 / UNAVAILABLE / high demand spikes)
            if (
                code == 503
                or "503" in err_str
                or "unavailable" in err_lower
                or "high demand" in err_lower
                or "temporarily unavailable" in err_lower
            ):
                raise GemmaTemporaryUnavailableError(
                    "AI screening temporarily unavailable due to high provider demand. Please try again later."
                ) from e

            # Rate limiting / Quota exceeded (HTTP 429)
            if (
                code == 429
                or "429" in err_str
                or "quota" in err_lower
                or "rate limit" in err_lower
                or "resource_exhausted" in err_lower
            ):
                raise GemmaRateLimitError(
                    "AI screening rate limit exceeded. Please try again later."
                ) from e

            # Timeout / Deadline exceeded
            if "deadline" in err_lower or "timeout" in err_lower:
                raise GemmaTimeoutError(
                    "AI screening request timed out. Please try again later."
                ) from e

            raise GemmaProviderError(f"Google GenAI inference error: {e}") from e


class OllamaGemmaProvider:
    """Local inference provider utilizing an Ollama instance (Gemma 3 Vision, PaliGemma, or compatible VLM)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model_name = model_name or os.environ.get("OLLAMA_MODEL", "gemma3:4b")
        raw_timeout = os.environ.get("OLLAMA_TIMEOUT", "60.0")
        try:
            self.timeout = timeout if timeout is not None else float(raw_timeout)
        except ValueError:
            self.timeout = 60.0

    @property
    def provider_name(self) -> str:
        return f"ollama:{self.model_name}"

    def is_available(self) -> bool:
        # Check if Ollama host is configured or explicitly selected
        return bool(
            self.base_url
            or os.environ.get("OLLAMA_BASE_URL")
            or os.environ.get("OLLAMA_HOST")
            or os.environ.get("GEMMA_PROVIDER", "").lower().strip() == "ollama"
        )

    async def analyze(
        self,
        notes: Optional[str],
        location_name: Optional[str],
        photo_bytes: Optional[bytes] = None,
        photo_mime: Optional[str] = None,
    ) -> GemmaHazardOutput:
        import httpx

        url = f"{self.base_url}/api/generate"
        prompt_parts = [
            SYSTEM_PROMPT,
            f"\n\n--- OBSERVATION DATA ---\n"
            f"Location: {location_name or 'Unspecified coordinates'}\n"
            f"Observer Notes: {notes or 'No written notes provided.'}\n",
        ]

        if photo_bytes:
            prompt_parts.append(
                "Analyze the attached field photograph in conjunction with the observer notes. "
                "Base geotechnical indicators strictly on visible evidence."
            )
        else:
            prompt_parts.append(
                "NOTE: No field photograph was attached. Perform text-based screening of notes only."
            )

        body: dict = {
            "model": self.model_name,
            "prompt": "\n".join(prompt_parts),
            "stream": False,
            "format": "json",
        }

        if photo_bytes:
            body["images"] = [base64.b64encode(photo_bytes).decode("utf-8")]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=body)

                if res.status_code == 429:
                    raise GemmaRateLimitError("Ollama concurrency limit reached. Please try again later.")
                if res.status_code == 503:
                    raise GemmaTemporaryUnavailableError(
                        "Ollama service temporarily unavailable. Please try again later."
                    )
                if res.status_code == 404:
                    err_text = res.text
                    if "model" in err_text.lower() and "not found" in err_text.lower():
                        raise GemmaProviderUnavailableError(
                            f"Ollama model '{self.model_name}' is not pulled. Run 'ollama pull {self.model_name}' on the host."
                        )
                    raise GemmaProviderUnavailableError(f"Ollama endpoint not found (HTTP 404): {err_text}")

                if res.status_code != 200:
                    err_text = res.text
                    if "does not support images" in err_text.lower():
                        raise GemmaProviderError(
                            f"Configured Ollama model '{self.model_name}' does not support multimodal image input. "
                            f"Please configure a vision-capable model (e.g. OLLAMA_MODEL=gemma3:4b)."
                        )
                    raise GemmaProviderError(f"Ollama returned HTTP {res.status_code}: {err_text}")

                res_json = res.json()
                raw_response = res_json.get("response", "")
                return parse_gemma_json(raw_response)

        except httpx.TimeoutException:
            raise GemmaTimeoutError(f"Ollama local inference timed out after {self.timeout}s.")
        except httpx.ConnectError as e:
            raise GemmaProviderUnavailableError(
                f"Cannot connect to Ollama daemon at {self.base_url}: {e}. Ensure Ollama is running."
            )
        except httpx.RequestError as e:
            raise GemmaProviderUnavailableError(f"Ollama network communication error at {self.base_url}: {e}")


class FallbackGemmaProvider:
    """Explicitly configured wrapper providing secondary fallback if primary inference fails."""

    def __init__(self, primary: AnalysisProvider, fallback: AnalysisProvider):
        self.primary = primary
        self.fallback = fallback

    @property
    def provider_name(self) -> str:
        return f"{self.primary.provider_name}[fallback:{self.fallback.provider_name}]"

    def is_available(self) -> bool:
        return self.primary.is_available() or self.fallback.is_available()

    async def analyze(
        self,
        notes: Optional[str],
        location_name: Optional[str],
        photo_bytes: Optional[bytes] = None,
        photo_mime: Optional[str] = None,
    ) -> GemmaHazardOutput:
        try:
            logger.info(f"Attempting primary AI inference via {self.primary.provider_name}...")
            result = await self.primary.analyze(notes, location_name, photo_bytes, photo_mime)
            if result.summary and "[Inference Provider:" not in result.summary:
                result.summary = f"{result.summary}\n[Inference Provider: {self.primary.provider_name}]"
            return result
        except (
            GemmaProviderUnavailableError,
            GemmaTemporaryUnavailableError,
            GemmaRateLimitError,
            GemmaTimeoutError,
        ) as primary_err:
            logger.warning(
                f"Primary provider {self.primary.provider_name} unavailable ({primary_err}). "
                f"Failing over to configured fallback provider {self.fallback.provider_name}..."
            )
            result = await self.fallback.analyze(notes, location_name, photo_bytes, photo_mime)
            if result.summary and "[Inference Provider:" not in result.summary:
                result.summary = f"{result.summary}\n[Inference Provider: {self.fallback.provider_name} (fallback)]"
            return result


class UnconfiguredGemmaProvider:
    """Null provider returned when no Gemma credentials or local runtimes are present."""

    @property
    def provider_name(self) -> str:
        return "unconfigured"

    def is_available(self) -> bool:
        return False

    async def analyze(
        self,
        notes: Optional[str],
        location_name: Optional[str],
        photo_bytes: Optional[bytes] = None,
        photo_mime: Optional[str] = None,
    ) -> GemmaHazardOutput:
        raise GemmaProviderUnavailableError(
            "No Gemma AI inference provider is configured. "
            "Please configure GEMINI_API_KEY (for Google GenAI) or OLLAMA_BASE_URL (for local Ollama)."
        )


def _resolve_base_provider(provider_type: str) -> AnalysisProvider:
    """Helper to instantiate a concrete provider by name."""
    if provider_type == "mock":
        return MockGemmaProvider()
    if provider_type == "google":
        return GoogleGenAIGemmaProvider()
    if provider_type == "ollama":
        return OllamaGemmaProvider()

    # Autodetection
    google_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_GENAI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if google_key and google_key.strip():
        return GoogleGenAIGemmaProvider()

    if os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST"):
        return OllamaGemmaProvider()

    return UnconfiguredGemmaProvider()


def get_gemma_provider() -> AnalysisProvider:
    """Factory selecting the active analysis provider according to environment configuration.
    
    If GEMMA_ENABLE_FALLBACK=true, wraps the primary provider with a secondary fallback provider.
    """
    primary_type = os.environ.get("GEMMA_PROVIDER", "").lower().strip()
    primary_provider = _resolve_base_provider(primary_type)

    enable_fallback = os.environ.get("GEMMA_ENABLE_FALLBACK", "").lower().strip() in ("true", "1", "yes")
    if not enable_fallback:
        return primary_provider

    # Fallback target resolution
    fallback_type = os.environ.get("GEMMA_FALLBACK_PROVIDER", "").lower().strip()
    if not fallback_type:
        fallback_type = "ollama" if isinstance(primary_provider, GoogleGenAIGemmaProvider) else "google"

    secondary_provider = _resolve_base_provider(fallback_type)
    logger.info(
        f"Configuring fallback pipeline: Primary={primary_provider.provider_name}, Fallback={secondary_provider.provider_name}"
    )
    return FallbackGemmaProvider(primary=primary_provider, fallback=secondary_provider)
