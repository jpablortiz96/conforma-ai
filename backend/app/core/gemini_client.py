"""Centralized Gemini access for Conforma-AI."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class GeminiClientError(RuntimeError):
    """Raised when Gemini cannot be reached or returns unusable output."""


@dataclass(slots=True)
class GeminiProbeResult:
    """Model access result used by the probe script."""

    model: str
    ok: bool
    message: str


def _get_sdk_client() -> Any:
    """Create a Google GenAI SDK client or raise a descriptive error."""

    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiClientError("GEMINI_API_KEY is not configured.")

    try:
        genai = import_module("google.genai")
    except ImportError as exc:
        raise GeminiClientError(
            "google-genai is not installed. Install backend requirements first."
        ) from exc

    try:
        return genai.Client(api_key=settings.gemini_api_key)
    except Exception as exc:  # pragma: no cover - SDK-dependent
        raise GeminiClientError(f"Failed to initialize Gemini client: {exc}") from exc


def _build_generation_config(
    *,
    temperature: float,
    response_mime_type: str | None,
) -> Any:
    """Build a config object if the SDK types are available."""

    try:
        types = import_module("google.genai.types")
    except ImportError:
        config: dict[str, Any] = {"temperature": temperature}
        if response_mime_type:
            config["response_mime_type"] = response_mime_type
        return config

    kwargs: dict[str, Any] = {"temperature": temperature}
    if response_mime_type:
        kwargs["response_mime_type"] = response_mime_type
    return types.GenerateContentConfig(**kwargs)


def _extract_text_from_response(response: Any) -> str:
    """Extract textual content from a Gemini SDK response object."""

    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    parts: list[str] = []
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        if content is None:
            continue
        for part in getattr(content, "parts", None) or []:
            part_text = getattr(part, "text", None)
            if isinstance(part_text, str) and part_text.strip():
                parts.append(part_text.strip())

    if parts:
        return "\n".join(parts)

    raise GeminiClientError("Gemini returned no text content.")


def _strip_code_fences(payload: str) -> str:
    """Remove markdown code fences when the model ignores JSON-only instructions."""

    text = payload.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def _generate_text_sync(
    *,
    model: str,
    prompt: str,
    temperature: float,
    response_mime_type: str | None,
) -> str:
    """Call Gemini synchronously and return the plain text response."""

    client = _get_sdk_client()
    config = _build_generation_config(
        temperature=temperature,
        response_mime_type=response_mime_type,
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
    except Exception as exc:  # pragma: no cover - SDK-dependent
        raise GeminiClientError(f"Gemini model call failed for {model}: {exc}") from exc

    return _extract_text_from_response(response)


async def generate_text(
    *,
    model: str,
    prompt: str,
    temperature: float = 0.1,
    response_mime_type: str | None = None,
) -> str:
    """Generate text from Gemini using the configured API key."""

    return await asyncio.to_thread(
        _generate_text_sync,
        model=model,
        prompt=prompt,
        temperature=temperature,
        response_mime_type=response_mime_type,
    )


async def generate_json(
    *,
    model: str,
    prompt: str,
    temperature: float = 0.1,
) -> dict[str, Any]:
    """Generate and parse a strict JSON response from Gemini with one retry."""

    attempts = (
        prompt,
        (
            f"{prompt}\n\n"
            "Return strict JSON only. Do not include markdown fences, prose, or commentary."
        ),
    )
    last_error: Exception | None = None

    for attempt in attempts:
        try:
            text = await generate_text(
                model=model,
                prompt=attempt,
                temperature=temperature,
                response_mime_type="application/json",
            )
            return json.loads(_strip_code_fences(text))
        except (GeminiClientError, json.JSONDecodeError) as exc:
            last_error = exc
            logger.warning("Gemini JSON generation retry triggered: %s", exc)

    raise GeminiClientError(f"Gemini JSON generation failed: {last_error}")


async def call_pro_json(prompt: str, temperature: float = 0.1) -> dict[str, Any]:
    """Call the configured Pro Gemini model and parse JSON output."""

    settings = get_settings()
    return await generate_json(
        model=settings.gemini_pro_model,
        prompt=prompt,
        temperature=temperature,
    )


async def call_flash_json(prompt: str, temperature: float = 0.1) -> dict[str, Any]:
    """Call the configured Flash Gemini model and parse JSON output."""

    settings = get_settings()
    return await generate_json(
        model=settings.gemini_flash_model,
        prompt=prompt,
        temperature=temperature,
    )


async def probe_models(models: list[str]) -> list[GeminiProbeResult]:
    """Probe a list of Gemini models and report access diagnostics."""

    results: list[GeminiProbeResult] = []
    probe_prompt = 'Return exactly this JSON: {"status":"ok"}'

    for model in models:
        try:
            payload = await generate_json(model=model, prompt=probe_prompt, temperature=0.0)
            if payload.get("status") == "ok":
                results.append(
                    GeminiProbeResult(
                        model=model,
                        ok=True,
                        message="Model responded successfully.",
                    )
                )
            else:
                results.append(
                    GeminiProbeResult(
                        model=model,
                        ok=False,
                        message=f"Unexpected payload: {payload}",
                    )
                )
        except Exception as exc:
            results.append(
                GeminiProbeResult(
                    model=model,
                    ok=False,
                    message=str(exc),
                )
            )

    return results
