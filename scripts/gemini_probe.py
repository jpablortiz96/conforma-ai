"""Probe configured Gemini preview model access for the D1 baseline."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.gemini_client import probe_models  # noqa: E402


async def main() -> int:
    """Run the Gemini access probe and print clear diagnostics."""

    settings = get_settings()
    models = ["gemini-3.1-pro-preview", "gemini-3-flash-preview"]

    print("Conforma-AI Gemini probe")
    print(f"Preview models under test: {', '.join(models)}")
    print(
        "Configured runtime models: "
        f"{settings.gemini_pro_model}, {settings.gemini_flash_model}"
    )

    if not settings.gemini_api_key:
        print("Status: GEMINI_API_KEY is missing.")
        print("Result: backend will operate in deterministic fallback mode.")
        print("Suggestions:")
        print("- Add GEMINI_API_KEY to backend/.env.")
        print("- Keep GEMINI_PRO_MODEL and GEMINI_FLASH_MODEL aligned with your AI Studio access.")
        return 0

    results = await probe_models(models)
    failed = [result for result in results if not result.ok]

    for result in results:
        state = "OK" if result.ok else "FAIL"
        print(f"[{state}] {result.model}: {result.message}")

    if failed:
        print("Diagnostic: one or more preview models are unavailable to the configured API key.")
        print("Fallback suggestions:")
        print("- Verify the key comes from Google AI Studio and has active quota/billing.")
        print("- If preview access is restricted, switch the env vars to a Pro and Flash Gemini model available in your project.")
        print("- Re-run this script after updating backend/.env.")
    else:
        print("Diagnostic: both configured preview models are reachable.")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
