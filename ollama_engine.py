"""
core/ollama_engine.py
━━━━━━━━━━━━━━━━━━━
Ollama local model engine.
No API key needed. No rate limits. Fully offline.
Supports: llama3, mistral, gemma2, phi3, qwen2, etc.
"""
from __future__ import annotations
import json, requests, threading
from typing import Callable

OLLAMA_BASE = "http://localhost:11434"


def is_running() -> bool:
    """Check if Ollama daemon is up."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def list_models() -> list[str]:
    """Return installed model names."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


def best_model() -> str:
    """Pick best available model by priority."""
    priority = [
        "llama3.1:8b", "llama3:8b", "llama3.1", "llama3",
        "mistral:7b", "mistral", "gemma2:9b", "gemma2",
        "qwen2.5:7b", "qwen2.5", "qwen2:7b", "qwen2",
        "phi3:medium", "phi3", "phi3.5",
        "deepseek-r1:8b", "deepseek-r1",
        "llama3.2:3b", "llama3.2",
    ]
    installed = list_models()
    for p in priority:
        for m in installed:
            if m.startswith(p):
                return m
    return installed[0] if installed else "llama3"


def chat(
    messages: list[dict],
    model: str | None = None,
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    stream_cb: Callable[[str], None] | None = None,
) -> dict:
    """
    Send chat request to Ollama.
    stream_cb: called with each token chunk if provided.
    Returns: {"content": str, "tool_calls": list}
    """
    mdl = model or best_model()

    # Build payload
    payload: dict = {
        "model":   mdl,
        "messages": messages,
        "options": {"temperature": temperature},
        "stream":  stream_cb is not None,
    }

    # Ollama supports tools for llama3.1+ models
    if tools:
        payload["tools"] = tools

    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/chat",
            json=payload,
            timeout=120,
            stream=stream_cb is not None,
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Ollama error {resp.status_code}: {resp.text[:200]}")

        # Streaming mode
        if stream_cb is not None:
            full_content = ""
            tool_calls   = []
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    delta = chunk.get("message", {}).get("content", "")
                    if delta:
                        full_content += delta
                        stream_cb(delta)
                    # Tool calls (llama3.1+ with tools)
                    tcs = chunk.get("message", {}).get("tool_calls", [])
                    if tcs:
                        tool_calls.extend(tcs)
                except json.JSONDecodeError:
                    continue
            return {"content": full_content, "tool_calls": tool_calls}

        # Non-streaming mode
        data = resp.json()
        msg  = data.get("message", {})
        return {
            "content":    msg.get("content", ""),
            "tool_calls": msg.get("tool_calls", []),
        }

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama not running! Start it with: ollama serve\n"
            "Install: https://ollama.ai"
        )


def pull_model(model: str, log_fn=None) -> bool:
    """Pull a model from Ollama registry."""
    try:
        if log_fn:
            log_fn(f"[Ollama] Pulling {model}… (this may take a few minutes)")
        resp = requests.post(
            f"{OLLAMA_BASE}/api/pull",
            json={"name": model},
            timeout=600,
            stream=True,
        )
        for line in resp.iter_lines():
            if line:
                try:
                    d = json.loads(line)
                    status = d.get("status", "")
                    if log_fn and status:
                        log_fn(f"[Ollama] {status}")
                except Exception:
                    pass
        return True
    except Exception as e:
        if log_fn:
            log_fn(f"[Ollama] Pull failed: {e}")
        return False
