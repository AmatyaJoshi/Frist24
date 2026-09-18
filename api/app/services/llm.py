"""Ollama HTTP client. Local only. JSON mode, temperature 0, fallback model, explicit timeouts."""
from __future__ import annotations

import json
import logging
import time

import httpx

from app.config import get_settings

log = logging.getLogger("frist24.llm")


class LlmUnavailable(RuntimeError):
    pass


class LlmBadOutput(ValueError):
    pass


def available_models(timeout: float = 3.0) -> list[str]:
    s = get_settings()
    try:
        r = httpx.get(f"{s.ollama_url}/api/tags", timeout=timeout)
        r.raise_for_status()
        return [m.get("name", "") for m in r.json().get("models", [])]
    except httpx.HTTPError as e:
        raise LlmUnavailable(f"ollama not reachable at {s.ollama_url}: {type(e).__name__}") from e


def pick_model() -> str:
    """Configured model if pulled, else fallback, else the first pulled model."""
    s = get_settings()
    models = available_models()
    names = {m.split(":")[0] for m in models} | set(models)
    for candidate in (s.ollama_model, s.ollama_fallback_model):
        if candidate in models or candidate.split(":")[0] in names:
            return candidate
    if models:
        log.warning("neither %s nor %s pulled; using %s", s.ollama_model, s.ollama_fallback_model, models[0])
        return models[0]
    raise LlmUnavailable("ollama has no models pulled yet (ollama-pull still running?)")


def generate_json(prompt: str, model: str, timeout: float = 300.0, num_predict: int = 2048) -> tuple[dict, dict]:
    """Call /api/generate with format=json. Returns (parsed_json, meta)."""
    s = get_settings()
    body = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0, "num_predict": num_predict, "num_ctx": 8192},
    }
    t = time.perf_counter()
    try:
        r = httpx.post(f"{s.ollama_url}/api/generate", json=body, timeout=timeout)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise LlmUnavailable(f"ollama generate failed: {type(e).__name__}: {e}") from e
    data = r.json()
    text = data.get("response", "")
    meta = {
        "model": data.get("model", model),
        "seconds": round(time.perf_counter() - t, 1),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
        "done_reason": data.get("done_reason"),
    }
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        raise LlmBadOutput(f"model returned non-JSON ({e}): {text[:200]!r}") from e
    if not isinstance(parsed, dict):
        raise LlmBadOutput("model returned JSON that is not an object")
    return parsed, meta
