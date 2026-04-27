"""
core/brain.py
━━━━━━━━━━━━
RAHUL's main AI brain using Ollama local models.
Simple, fast, direct — no orchestrator overhead for simple chat.
Uses tool-calling for actions.
"""
from __future__ import annotations
import json, threading, traceback, re
from datetime import datetime
from core.ollama_engine import chat as ollama_chat, best_model, is_running
from core.memory_manager import (
    load_memory, format_memory_for_prompt, update_memory,
    build_context_snippet,
)

SYSTEM_PROMPT = """Tum ho RAHUL — ek advanced personal AI assistant jo user ke computer pe locally chalta hai.

PERSONALITY:
- Hinglish mein baat karo naturally (Hindi + English mix)
- Warm aur friendly raho, jaise ek close friend
- Excited raho jab kuch interesting dikhao: "Sir, ye dekho!", "Kya baat hai!", "Ho gaya!"
- Short aur snappy replies chat ke liye, detailed replies tasks ke liye

CRITICAL RULES:
1. Greetings (hi, hy, hello, namaste) pe SIRF warmly reply karo — koi tool mat chalao
2. Simple questions pe DIRECT answer do — tools sirf action ke liye
3. HAMESHA animation_engine use karo jab kuch visually dikhana ho
4. User ke important facts (naam, city, preferences) save_memory se save karo silently
5. Koi bhi task ke liye REAL tool call karo — simulate mat karo

TOOL USE GUIDE:
- Kuch search karna → web_search
- Weather → weather_report + animation dikhao
- App kholna → open_app  
- Files → file_controller
- Code → code_helper
- News → news_reader + animation dikhao
- Screen dekho → screen_process
- Kuch visually dikhana → animation_engine (HAMESHA use karo)
- System control → system_control
- Calculator → calculator

OUTPUT FORMAT:
- Chat: 1-3 lines max, Hinglish
- Tasks: Tools use karo, phir short summary do
- Never say "As an AI I can't..." — tum kar sakte ho!"""


def _load_system(ui=None) -> str:
    from core.memory_manager import load_memory, format_memory_for_prompt
    now     = datetime.now().strftime("%A, %d %B %Y — %I:%M %p")
    mem_str = format_memory_for_prompt(load_memory())
    parts   = [SYSTEM_PROMPT, f"\n[ABHI KA SAMAY] {now}"]
    if mem_str:
        parts.append(mem_str)
    return "\n".join(parts)


class RAHULBrain:
    def __init__(self, ui, tool_executor, tools_schema: list[dict]):
        self.ui            = ui
        self.tool_executor = tool_executor
        self.tools_schema  = tools_schema
        self._history: list[dict] = []
        self._lock = threading.Lock()

    def process(self, user_text: str):
        """Process user input — called in background thread."""
        self.ui.set_state("THINKING")

        with self._lock:
            self._history.append({"role": "user", "content": user_text})

        # Keep history compact (last 10 turns = 20 messages)
        with self._lock:
            if len(self._history) > 20:
                self._history = self._history[-20:]

        system = _load_system(self.ui)

        # Build messages for Ollama
        messages = [{"role": "system", "content": system}] + self._history

        # Agentic loop
        max_rounds = 5
        for round_num in range(max_rounds):
            try:
                # Streaming response — show tokens as they come
                streamed_text = []

                def _on_token(tok: str):
                    streamed_text.append(tok)
                    # Update UI incrementally
                    if hasattr(self.ui, "_stream_token"):
                        self.ui._stream_token(tok)

                # Check if model supports tools (llama3.1+ does)
                model = best_model()
                supports_tools = any(
                    k in model for k in ["llama3.1", "llama3.2", "qwen2.5", "mistral-nemo"]
                )

                result = ollama_chat(
                    messages=messages,
                    tools=self.tools_schema if supports_tools else None,
                    temperature=0.7,
                    stream_cb=_on_token,
                )

            except RuntimeError as e:
                self.ui.write_log(f"ERR: {e}")
                self.ui.set_state("LISTENING")
                return
            except Exception as e:
                self.ui.write_log(f"ERR: Ollama error — {e}")
                traceback.print_exc()
                self.ui.set_state("LISTENING")
                return

            content    = result.get("content", "").strip()
            tool_calls = result.get("tool_calls", [])

            # If model doesn't support tools natively, parse tool calls from text
            if not supports_tools and content:
                tool_calls = _parse_tool_calls_from_text(content)
                if tool_calls:
                    content = ""  # clear text if tools were extracted

            # Add assistant response to history
            with self._lock:
                self._history.append({"role": "assistant", "content": content or ""})

            # Show text response
            if content and not tool_calls:
                # Final text answer — write to log and speak
                self.ui.write_log(f"RAHUL: {content}")
                from core.tts_engine import speak
                threading.Thread(
                    target=speak, args=(content,), daemon=True
                ).start()
                break

            # Execute tool calls
            if tool_calls:
                tool_results = []
                for tc in tool_calls:
                    # Handle both dict formats (Ollama tool response)
                    if isinstance(tc, dict):
                        fn   = tc.get("function", tc)
                        name = fn.get("name", "")
                        args_raw = fn.get("arguments", fn.get("parameters", {}))
                        if isinstance(args_raw, str):
                            try:
                                args = json.loads(args_raw)
                            except Exception:
                                args = {}
                        else:
                            args = args_raw or {}
                    else:
                        continue

                    if not name:
                        continue

                    self.ui.set_state("THINKING")
                    self.ui.notify_tool(name)
                    self.ui.write_log(f"SYS: ⚡ {name}…")

                    try:
                        res = self.tool_executor(name, args)
                    except Exception as e:
                        res = f"Tool error: {e}"
                        traceback.print_exc()

                    tool_results.append({
                        "role":    "tool",
                        "name":    name,
                        "content": str(res)[:1500],
                    })

                # Add tool results to history and continue loop
                with self._lock:
                    self._history.extend(tool_results)
                messages = [{"role": "system", "content": system}] + self._history
                continue

            # No content and no tool calls — done
            break

        self.ui.set_state("LISTENING")


def _parse_tool_calls_from_text(text: str) -> list[dict]:
    """
    For models that don't natively support tool calling,
    parse JSON tool calls from text output.
    Models are prompted to output: <tool>{"name":"...","arguments":{...}}</tool>
    """
    tool_calls = []
    pattern = re.findall(r'<tool>(.*?)</tool>', text, re.DOTALL)
    for match in pattern:
        try:
            data = json.loads(match.strip())
            tool_calls.append({"function": data})
        except Exception:
            pass

    # Also try plain JSON blocks
    if not tool_calls:
        json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        for block in json_blocks:
            try:
                data = json.loads(block)
                if "name" in data:
                    tool_calls.append({"function": data})
            except Exception:
                pass

    return tool_calls
