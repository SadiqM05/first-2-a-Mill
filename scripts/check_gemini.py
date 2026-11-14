"""Pre-demo Gemini connectivity check, using the app's own configuration and integration.

Usage:  python -m scripts.check_gemini

Makes exactly ONE request (no retry) through reslink.assistant.GeminiGenerator with the
app's real system instruction and JSON response schema, then validates the reply the same
way the app does. Prints the model name and result only; the API key is never printed.
Exit code 0 = ready, 1 = not configured or the check failed.
"""

from __future__ import annotations

import sys
import time

import reslink.assistant as assistant
from reslink.assistant import RESPONSE_SCHEMA, SYSTEM_INSTRUCTION, GeminiGenerator, parse_model_output
from reslink.config import load_env_file, load_settings

PROMPT = (
    'Evidence:\n<evidence id="connectivity-check">\nThis is a ResLink AI connectivity check.\n</evidence>\n\n'
    "Question: Confirm that the connectivity check worked."
)


def main() -> int:
    load_env_file()
    settings = load_settings()
    if not settings.gemini_configured:
        missing = [n for n, v in (("GEMINI_API_KEY", settings.gemini_api_key),
                                  ("GEMINI_MODEL", settings.gemini_model)) if not v]
        print(f"NOT CONFIGURED: set {', '.join(missing)} in .env (see .env.example)")
        return 1

    print(f"Checking Gemini model: {settings.gemini_model}")
    assistant.RETRIES = 0  # one request only: a rate limit should show up here, not be retried
    generator = GeminiGenerator(api_key=settings.gemini_api_key, model=settings.gemini_model)
    start = time.time()
    try:
        raw = generator.generate(SYSTEM_INSTRUCTION, PROMPT, RESPONSE_SCHEMA)
    except Exception as exc:
        code = getattr(exc, "code", None)
        hint = " (rate limit / quota: wait and retry)" if code == 429 else ""
        print(f"FAILED: {type(exc).__name__}" + (f" {code}" if isinstance(code, int) else "") + hint)
        return 1
    elapsed = time.time() - start
    try:
        sufficient, _answer, cited = parse_model_output(raw)
    except ValueError as exc:  # includes json.JSONDecodeError
        print(f"FAILED: reply did not match the app's JSON format ({type(exc).__name__})")
        return 1
    print(f"OK in {elapsed:.1f}s: structured reply parsed (sufficient={sufficient}, cited={cited})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
