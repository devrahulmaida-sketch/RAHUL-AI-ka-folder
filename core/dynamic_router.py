"""
core/dynamic_router.py
━━━━━━━━━━━━━━━━━━━━━
Multi-provider REST router.
Priority: OpenRouter → Nvidia NIM → Groq
Auto-retries on 429/503 without user intervention.
100% free tier on all three providers.
"""

from __future__ import annotations
import os, json, time, requests
from typing import Any
from dotenv import load_dotenv

load_dotenv()

# ── Provider configs ──────────────────────────────────────────────────────────
PROVIDERS = [
    {
        "name":    "OpenRouter",
        "url":     "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_KEY",
        "model":   os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
        "headers_extra": {
            "HTTP-Referer": "https://github.com/RAHUL-AI",
            "X-Title":      "RAHUL Advanced AI",
        },
    },
    {
        "name":    "Nvidia NIM",
        "url":     "https://integrate.api.nvidia.com/v1/chat/completions",
        "key_env": "NVIDIA_KEY",
        "model":   os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"),
        "headers_extra": {},
    },
    {
        "name":    "Groq",
        "url":     "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_KEY",
        "model":   os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "headers_extra": {},
    },
]

# Dedicated fast model for worker tasks (speed priority)
# These are verified working free models as of 2025
WORKER_PROVIDERS = [
    {
        "name":    "Groq-Worker",
        "url":     "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_KEY",
        "model":   os.getenv("GROQ_WORKER_MODEL", "llama-3.1-8b-instant"),
        "headers_extra": {},
    },
    {
        # Fallback 1: Use main OpenRouter model (70B — slower but works)
        "name":    "OpenRouter-Worker",
        "url":     "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_KEY",
        "model":   os.getenv("OPENROUTER_MODEL",
                             "meta-llama/llama-3.3-70b-instruct:free"),
        "headers_extra": {
            "HTTP-Referer": "https://github.com/RAHUL-AI",
            "X-Title":      "RAHUL Advanced AI",
        },
    },
    {
        # Fallback 2: Nvidia NIM (free credits)
        "name":    "Nvidia-Worker",
        "url":     "https://integrate.api.nvidia.com/v1/chat/completions",
        "key_env": "NVIDIA_KEY",
        "model":   os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"),
        "headers_extra": {},
    },
]


class RouterError(Exception):
    """All providers exhausted."""


def _build_headers(provider: dict) -> dict:
    key = os.getenv(provider["key_env"], "")
    h = {
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
    }
    h.update(provider.get("headers_extra", {}))
    return h


def _call_provider(
    provider: dict,
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 60,
) -> dict:
    """Single provider call — raises on failure."""
    payload: dict[str, Any] = {
        "model":       provider["model"],
        "messages":    messages,
        "temperature": temperature,
        "max_tokens":  max_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    resp = requests.post(
        provider["url"],
        headers=_build_headers(provider),
        json=payload,
        timeout=timeout,
    )

    if resp.status_code in (429, 503, 529):
        raise requests.HTTPError(f"{provider['name']} rate-limited ({resp.status_code})")

    if resp.status_code != 200:
        raise requests.HTTPError(
            f"{provider['name']} error {resp.status_code}: {resp.text[:200]}"
        )

    return resp.json()


def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    worker_mode: bool = False,
    log_fn=None,
) -> dict:
    """
    Try providers in order. Returns raw OpenAI-compatible response dict.
    worker_mode=True uses faster/smaller models.
    """
    pool = WORKER_PROVIDERS if worker_mode else PROVIDERS
    last_err = None

    for provider in pool:
        key = os.getenv(provider["key_env"], "")
        if not key:
            continue   # skip unconfigured providers silently

        try:
            if log_fn:
                log_fn(f"[Router] Trying {provider['name']} ({provider['model'][:35]})…")
            result = _call_provider(
                provider, messages, tools, temperature, max_tokens
            )
            if log_fn:
                log_fn(f"[Router] ✓ {provider['name']} responded.")
            return result

        except requests.HTTPError as e:
            last_err = e
            if log_fn:
                log_fn(f"[Router] ✗ {provider['name']}: {e} — trying fallback…")
            time.sleep(0.5)
            continue

        except requests.exceptions.Timeout:
            last_err = TimeoutError(f"{provider['name']} timed out")
            if log_fn:
                log_fn(f"[Router] ✗ {provider['name']}: timeout — trying fallback…")
            continue

        except Exception as e:
            last_err = e
            if log_fn:
                log_fn(f"[Router] ✗ {provider['name']}: {e}")
            continue

    raise RouterError(
        f"All providers failed. Last error: {last_err}"
    )


def extract_text(response: dict) -> str:
    """Pull assistant text from OpenAI-compatible response."""
    try:
        return response["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError):
        return ""


def extract_tool_calls(response: dict) -> list[dict]:
    """Pull tool_calls list from response (may be empty)."""
    try:
        return response["choices"][0]["message"].get("tool_calls") or []
    except (KeyError, IndexError):
        return []


def available_providers() -> list[str]:
    """Return list of configured provider names."""
    names = []
    for p in PROVIDERS:
        if os.getenv(p["key_env"]):
            names.append(p["name"])
    return names
