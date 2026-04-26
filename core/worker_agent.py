"""
core/worker_agent.py
━━━━━━━━━━━━━━━━━━━
Worker Agent — execution only.
Reads ONE task at a time from tasks.md.
Calls tools → marks task done → exits thread.
Uses fast/small model (Groq llama-3.1-8b or similar).
"""

from __future__ import annotations
import json, threading, traceback
from datetime import datetime
from core.dynamic_router import chat, extract_text, extract_tool_calls
from core.memory_manager import (
    get_next_task, mark_task_done, tasks_remaining,
    build_context_snippet, update_memory, load_memory,
    format_memory_for_prompt,
)

WORKER_SYSTEM = """You are RAHUL's Worker Agent — a friendly, execution-focused AI assistant.

PERSONALITY: Warm, Hinglish mix, enthusiastic.
Phrases: "Sir, ho gaya!", "Bas ek second!", "Ye raha!", "Kya baat hai!"

STRICT RULES:
1. For GREETINGS (hi, hello, hy, hey, namaste, kya haal, etc.) → JUST REPLY WARMLY, no tools at all
2. For SIMPLE QUESTIONS (what time, how are you, thanks, ok, bye) → ANSWER DIRECTLY, no tools
3. Only call tools when the task ACTUALLY needs it (search, open app, create file, weather, etc.)
4. NEVER call send_message just because the user said "hi" or a short message
5. Keep replies SHORT for chat (2-3 lines max), detailed for tasks

TOOL USAGE GUIDE:
- "Search for X" → use web_search
- "Weather in X" → use weather_report  
- "Open X" → use open_app
- "Show me X" → use animation_engine
- "Create file X" → use file_controller
- Greetings/thanks/bye → NO TOOLS, just reply

Always save important user facts (name, city, etc.) using save_memory silently."""


class WorkerAgent:
    def __init__(self, ui, tools_schema: list[dict], tool_executor):
        """
        ui           — RahulUI instance for logging
        tools_schema — OpenAI-format tool definitions
        tool_executor— callable(name, args) → str result
        """
        self.ui            = ui
        self.tools_schema  = tools_schema
        self.tool_executor = tool_executor
        self._lock         = threading.Lock()

    def execute_task(self, task: str) -> str:
        """
        Execute a single task. Called in a background thread.
        Returns final response text.
        """
        now     = datetime.now().strftime("%A, %d %B %Y — %I:%M %p")
        ctx     = build_context_snippet()
        mem_str = format_memory_for_prompt(load_memory())

        system_parts = [WORKER_SYSTEM, f"[TIME] {now}"]
        if mem_str:
            system_parts.append(mem_str)
        if ctx:
            system_parts.append(f"[CONTEXT]\n{ctx}")

        messages = [
            {"role": "system", "content": "\n\n".join(system_parts)},
            {"role": "user",   "content": f"Execute this task: {task}"},
        ]

        max_rounds = 6   # prevent infinite tool loops
        final_text = ""

        for round_num in range(max_rounds):
            try:
                response = chat(
                    messages=messages,
                    tools=self.tools_schema,
                    temperature=0.5,
                    max_tokens=1024,
                    worker_mode=True,
                    log_fn=lambda m: self.ui.write_log(f"SYS: {m}"),
                )
            except Exception as e:
                err = f"Worker API error: {e}"
                self.ui.write_log(f"ERR: {err}")
                return err

            text       = extract_text(response)
            tool_calls = extract_tool_calls(response)

            # Collect assistant message
            assistant_msg: dict = {"role": "assistant", "content": text or None}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

            if text and not tool_calls:
                # Final answer — done
                final_text = text
                break

            if not tool_calls:
                # No tools, no text — shouldn't happen
                final_text = text or "Task completed."
                break

            # Execute all tool calls
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                try:
                    tool_args = json.loads(tc["function"].get("arguments", "{}"))
                except json.JSONDecodeError:
                    tool_args = {}

                self.ui.set_state("THINKING")
                self.ui.notify_tool(tool_name)
                self.ui.write_log(f"SYS: ⚡ {tool_name}…")

                try:
                    result = self.tool_executor(tool_name, tool_args)
                except Exception as e:
                    result = f"Tool error: {e}"
                    traceback.print_exc()

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.get("id", f"call_{tool_name}"),
                    "name":         tool_name,
                    "content":      str(result)[:2000],
                })

        # Mark task done in tasks.md
        mark_task_done(task)
        remaining = tasks_remaining()
        if remaining > 0:
            self.ui.write_log(f"SYS: Task done. {remaining} remaining.")

        return final_text

    def run_all_tasks(self, tasks: list[str]):
        """Execute tasks sequentially in a background thread."""
        def _run():
            for task in tasks:
                self.ui.set_state("THINKING")
                result = self.execute_task(task)
                if result:
                    self.ui.write_log(f"RAHUL: {result}")
                self.ui.set_state("LISTENING")

        threading.Thread(target=_run, daemon=True).start()

    def run_single(self, task: str):
        """Execute one task in a background thread."""
        def _run():
            self.ui.set_state("THINKING")
            result = self.execute_task(task)
            if result:
                self.ui.write_log(f"RAHUL: {result}")
            self.ui.set_state("LISTENING")

        threading.Thread(target=_run, daemon=True).start()
