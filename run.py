"""
run.py — RAHUL Advanced AI v4.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Architecture:
  • OpenRouter (primary) + Nvidia NIM (fallback) + Groq (tertiary)
  • Orchestrator (Manager)  — plans tasks
  • Worker Agent (Executor) — runs tasks with tools
  • File-based memory       — token-safe context
  • RAHUL UI                — Tkinter + AnimationOverlay
"""

import os, sys, json, threading, traceback
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# ── Core imports ──────────────────────────────────────────────────────────────
from core.memory_manager import (
    init_dirs, update_memory, load_memory, format_memory_for_prompt,
)
from core.dynamic_router import chat, extract_text, available_providers
from core.orchestrator   import plan, is_simple_query
from core.worker_agent   import WorkerAgent
from ui import RahulUI

# ── Action imports ─────────────────────────────────────────────────────────────
from actions.open_app        import open_app
from actions.web_search      import web_search as web_search_action
from actions.weather         import weather_action
from actions.browser_control import browser_control
from actions.file_controller import file_controller
from actions.code_helper     import code_helper
from actions.screen_process  import screen_process
from actions.reminder        import reminder_action
from actions.send_message    import send_message
from actions.system_control  import system_control
from actions.youtube         import youtube_action
from actions.news_reader     import news_reader
from actions.calculator      import calculator
from actions.translate       import translate_action
from actions.image_gen       import image_gen
from actions.pdf_reader      import pdf_reader
from actions.email_action    import email_action
from actions.clipboard_mgr   import clipboard_mgr
from actions.process_mgr     import process_mgr
from actions.network_info    import network_info
from actions.animation_engine import animation_engine

# ── Tool schema (OpenAI function-calling format) ───────────────────────────────
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open any application on Linux.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string"},
                    "args":     {"type": "string"},
                },
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web. Use for any current info, news, facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":          {"type": "string"},
                    "mode":           {"type": "string", "enum": ["search","news","images"]},
                    "show_on_screen": {"type": "boolean"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "weather_report",
            "description": "Get weather for any city. Shows animated card on UI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city":           {"type": "string"},
                    "show_animation": {"type": "boolean"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_control",
            "description": "Control Firefox browser: go_to, search, click, type, screenshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action":   {"type": "string"},
                    "url":      {"type": "string"},
                    "query":    {"type": "string"},
                    "text":     {"type": "string"},
                    "selector": {"type": "string"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_controller",
            "description": "Manage files: list, create, read, write, delete, move, find.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action":      {"type": "string"},
                    "path":        {"type": "string"},
                    "content":     {"type": "string"},
                    "destination": {"type": "string"},
                    "name":        {"type": "string"},
                    "new_name":    {"type": "string"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "code_helper",
            "description": "Write, run, debug code in any language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action":      {"type": "string"},
                    "language":    {"type": "string"},
                    "code":        {"type": "string"},
                    "file_path":   {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "screen_process",
            "description": "Capture and analyze screen or webcam with AI vision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "angle": {"type": "string", "enum": ["screen","camera"]},
                    "text":  {"type": "string"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_control",
            "description": "Control Linux: volume, brightness, wifi, screenshot, shutdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "value":  {"type": "string"},
                    "state":  {"type": "string"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "youtube",
            "description": "Search and play YouTube videos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "query":  {"type": "string"},
                    "url":    {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "news_reader",
            "description": "Get latest news. Shows scrolling ticker on UI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic":          {"type": "string"},
                    "count":          {"type": "integer"},
                    "show_animation": {"type": "boolean"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Math calculations, unit conversions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"},
                    "show_steps": {"type": "boolean"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate",
            "description": "Translate text between languages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text":        {"type": "string"},
                    "target_lang": {"type": "string"},
                    "source_lang": {"type": "string"},
                },
                "required": ["text", "target_lang"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "image_gen",
            "description": "Generate AI images (free, Pollinations.ai).",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "style":  {"type": "string"},
                    "size":   {"type": "string"},
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pdf_reader",
            "description": "Read, summarize, search PDF files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action":    {"type": "string"},
                    "file_path": {"type": "string"},
                    "query":     {"type": "string"},
                },
                "required": ["action", "file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "email_action",
            "description": "Open Gmail compose in browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to":      {"type": "string"},
                    "subject": {"type": "string"},
                    "body":    {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send Telegram or WhatsApp message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "receiver":     {"type": "string"},
                    "message_text": {"type": "string"},
                    "platform":     {"type": "string"},
                },
                "required": ["receiver", "message_text", "platform"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder",
            "description": "Set a timed reminder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time":    {"type": "string"},
                    "date":    {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["time", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clipboard_mgr",
            "description": "Read or write clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "text":   {"type": "string"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_mgr",
            "description": "List, kill, or info about Linux processes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "name":   {"type": "string"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "network_info",
            "description": "Network info: IP, ping, speed, wifi list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "host":   {"type": "string"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "animation_engine",
            "description": (
                "Show animated content on RAHUL's UI screen. "
                "Types: card, list, chart, steps, news_ticker, comparison, "
                "weather, typewriter, countdown, image. "
                "ALWAYS use this to visually present information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "type":       {"type": "string"},
                    "title":      {"type": "string"},
                    "content":    {"type": "string"},
                    "color":      {"type": "string"},
                    "duration":   {"type": "integer"},
                    "image_path": {"type": "string"},
                },
                "required": ["type", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Silently save user facts to permanent memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "key":      {"type": "string"},
                    "value":    {"type": "string"},
                },
                "required": ["category", "key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_rahul",
            "description": "Shutdown RAHUL when user says goodbye/exit/band karo.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────
def _execute_tool(name: str, args: dict, ui: RahulUI) -> str:
    print(f"[RAHUL] ⚡ Tool: {name}  args={str(args)[:80]}")
    try:
        if name == "save_memory":
            cat = args.get("category", "notes")
            key = args.get("key", "")
            val = args.get("value", "")
            if key and val:
                update_memory({cat: {key: {"value": val}}})
            return "Memory saved."

        elif name == "shutdown_rahul":
            ui.write_log("SYS: RAHUL shutting down…")
            def _bye():
                import time, os; time.sleep(1.2); os._exit(0)
            threading.Thread(target=_bye, daemon=True).start()
            return "Goodbye!"

        elif name == "screen_process":
            threading.Thread(
                target=screen_process,
                kwargs={"parameters": args, "player": ui},
                daemon=True,
            ).start()
            return "Vision activated."

        dispatch = {
            "open_app":         lambda: open_app(args, ui),
            "web_search":       lambda: web_search_action(args, ui),
            "weather_report":   lambda: weather_action(args, ui),
            "browser_control":  lambda: browser_control(args, ui),
            "file_controller":  lambda: file_controller(args, ui),
            "code_helper":      lambda: code_helper(args, ui),
            "reminder":         lambda: reminder_action(args, ui),
            "send_message":     lambda: send_message(args, ui),
            "system_control":   lambda: system_control(args, ui),
            "youtube":          lambda: youtube_action(args, ui),
            "news_reader":      lambda: news_reader(args, ui),
            "calculator":       lambda: calculator(args, ui),
            "translate":        lambda: translate_action(args, ui),
            "image_gen":        lambda: image_gen(args, ui),
            "pdf_reader":       lambda: pdf_reader(args, ui),
            "email_action":     lambda: email_action(args, ui),
            "clipboard_mgr":    lambda: clipboard_mgr(args, ui),
            "process_mgr":      lambda: process_mgr(args, ui),
            "network_info":     lambda: network_info(args, ui),
            "animation_engine": lambda: animation_engine(args, ui),
        }

        if name in dispatch:
            return str(dispatch[name]())
        return f"Unknown tool: {name}"

    except Exception as e:
        traceback.print_exc()
        return f"Tool error ({name}): {e}"


# ── Conversational fallback (no task decomposition needed) ────────────────────
CHAT_SYSTEM = """You are RAHUL — a friendly, proactive AI assistant for Linux.
Personality: Hinglish mix, enthusiastic, helpful.
Phrases: "Sir, ye dekho!", "Bas ek second!", "Ho gaya!"
For simple questions, answer directly and warmly.
Keep answers SHORT (2-4 sentences max for chat).
Always use animation_engine to visually show interesting info."""


def _simple_chat(user_input: str, ui: RahulUI, worker: WorkerAgent):
    """Handle conversational turns via worker (no orchestrator needed)."""
    worker.run_single(user_input)


# ── Main app class ─────────────────────────────────────────────────────────────
class RAHULApp:
    def __init__(self, ui: RahulUI):
        self.ui = ui
        self.worker = WorkerAgent(
            ui=ui,
            tools_schema=TOOLS_SCHEMA,
            tool_executor=lambda name, args: _execute_tool(name, args, ui),
        )
        ui.on_text_command = self._handle_input

    def _handle_input(self, text: str):
        """Route: simple chat → Worker directly. Complex → Orchestrator → Worker."""
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _process(self, text: str):
        self.ui.set_state("THINKING")

        if is_simple_query(text):
            # Direct to worker — no planning overhead
            self.ui.write_log("SYS: [Direct mode]")
            self.worker.run_single(text)
            return

        # Complex request — plan first
        self.ui.write_log("SYS: [Swarm mode] Planning…")
        try:
            tasks = plan(
                text,
                log_fn=lambda m: self.ui.write_log(f"SYS: {m}"),
            )
        except Exception as e:
            self.ui.write_log(f"ERR: Planning failed — {e}")
            self.worker.run_single(text)
            return

        if not tasks:
            self.worker.run_single(text)
            return

        if len(tasks) == 1:
            self.ui.write_log(f"SYS: 1 task → executing…")
        else:
            self.ui.write_log(f"SYS: {len(tasks)} tasks planned → executing swarm…")
            # Show task list on UI
            try:
                import json as _j
                animation_engine({
                    "type":     "steps",
                    "title":    "Task Plan",
                    "content":  _j.dumps([{"step": str(i+1), "description": t[:55]}
                                          for i, t in enumerate(tasks)]),
                    "color":    "#00d4ff",
                    "duration": 10,
                }, self.ui)
            except Exception:
                pass

        self.worker.run_all_tasks(tasks)

    def start(self):
        init_dirs()
        providers = available_providers()
        if not providers:
            self.ui.write_log("ERR: No API keys found in .env file!")
            self.ui.write_log("SYS: Add OPENROUTER_KEY or NVIDIA_KEY or GROQ_KEY to .env")
        else:
            self.ui.write_log(f"SYS: ✓ RAHUL v4.0 online — Providers: {', '.join(providers)}")
            self.ui.write_log("SYS: Swarm engine ready. Type your command!")
        self.ui.set_state("LISTENING")


def main():
    ui = RahulUI()

    def runner():
        ui.wait_for_api_key()
        app = RAHULApp(ui)
        app.start()

    threading.Thread(target=runner, daemon=True).start()
    ui.root.mainloop()


if __name__ == "__main__":
    main()
