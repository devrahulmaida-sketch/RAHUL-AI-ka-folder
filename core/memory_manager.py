"""
core/memory_manager.py
━━━━━━━━━━━━━━━━━━━━━
Hybrid memory system:
  • astra_brain/current_project.md  — active task context (Markdown)
  • astra_brain/tasks.md            — swarm task checklist (Markdown)
  • memory/memory.json              — persistent user facts (JSON)
  • astra_brain/sys_memory.json     — system preferences

Token-safe: context window per request stays minimal because
AI reads only what it needs, not a growing history array.
"""

from __future__ import annotations
import json, os, re, time
from pathlib import Path
from typing import Optional

BASE_DIR    = Path(__file__).resolve().parent.parent
BRAIN_DIR   = BASE_DIR / "astra_brain"
MEMORY_DIR  = BASE_DIR / "memory"

PROJECT_FILE = BRAIN_DIR / "current_project.md"
TASKS_FILE   = BRAIN_DIR / "tasks.md"
SYS_FILE     = BRAIN_DIR / "sys_memory.json"
USER_MEM     = MEMORY_DIR / "memory.json"

# ── Init dirs ─────────────────────────────────────────────────────────────────
def init_dirs():
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "workspaces").mkdir(parents=True, exist_ok=True)

    if not PROJECT_FILE.exists():
        PROJECT_FILE.write_text(
            "# Current Project\n\n_No active project._\n", encoding="utf-8"
        )
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text(
            "# Task Checklist\n\n_No tasks yet._\n", encoding="utf-8"
        )
    if not SYS_FILE.exists():
        SYS_FILE.write_text(
            json.dumps({"user_name": "", "city": "", "preferences": {}}, indent=2),
            encoding="utf-8",
        )


# ── Project context ───────────────────────────────────────────────────────────
def set_project(context: str):
    PROJECT_FILE.write_text(
        f"# Current Project\n\n{context}\n\n_Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}_\n",
        encoding="utf-8",
    )


def get_project() -> str:
    if PROJECT_FILE.exists():
        return PROJECT_FILE.read_text(encoding="utf-8")
    return "No active project."


# ── Task checklist (swarm) ────────────────────────────────────────────────────
def set_tasks(task_list: list[str]):
    """Write a fresh task checklist from the orchestrator."""
    lines = ["# Task Checklist\n",
             f"_Created: {time.strftime('%Y-%m-%d %H:%M:%S')}_\n"]
    for t in task_list:
        lines.append(f"- [ ] {t}")
    TASKS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_next_task() -> Optional[str]:
    """Return the first unchecked task, or None if all done."""
    if not TASKS_FILE.exists():
        return None
    for line in TASKS_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- [ ]"):
            return line.strip()[6:].strip()
    return None


def mark_task_done(task_text: str):
    """Mark a task as complete by matching text."""
    if not TASKS_FILE.exists():
        return
    content = TASKS_FILE.read_text(encoding="utf-8")
    escaped = re.escape(task_text)
    content = re.sub(
        rf"- \[ \] {escaped}",
        f"- [x] {task_text}",
        content,
    )
    TASKS_FILE.write_text(content, encoding="utf-8")


def get_all_tasks() -> str:
    if TASKS_FILE.exists():
        return TASKS_FILE.read_text(encoding="utf-8")
    return "No tasks."


def tasks_remaining() -> int:
    if not TASKS_FILE.exists():
        return 0
    return sum(
        1 for l in TASKS_FILE.read_text(encoding="utf-8").splitlines()
        if l.strip().startswith("- [ ]")
    )


def clear_tasks():
    TASKS_FILE.write_text("# Task Checklist\n\n_No tasks yet._\n", encoding="utf-8")


# ── User memory (JSON) ────────────────────────────────────────────────────────
def load_memory() -> dict:
    if USER_MEM.exists():
        try:
            return json.loads(USER_MEM.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def update_memory(updates: dict):
    mem = load_memory()
    for cat, data in updates.items():
        if cat not in mem:
            mem[cat] = {}
        if isinstance(data, dict):
            mem[cat].update(data)
        else:
            mem[cat] = data
    mem["_last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    USER_MEM.parent.mkdir(parents=True, exist_ok=True)
    USER_MEM.write_text(json.dumps(mem, indent=2, ensure_ascii=False), encoding="utf-8")


def format_memory_for_prompt(memory: dict) -> str:
    if not memory:
        return ""
    lines = ["[USER MEMORY]"]
    skip = {"_last_updated"}
    for cat, data in memory.items():
        if cat in skip:
            continue
        if isinstance(data, dict):
            for k, v in data.items():
                val = v.get("value", v) if isinstance(v, dict) else v
                lines.append(f"  • {cat}/{k}: {val}")
        else:
            lines.append(f"  • {cat}: {data}")
    return "\n".join(lines) + "\n" if len(lines) > 1 else ""


# ── System prefs ──────────────────────────────────────────────────────────────
def get_sys_memory() -> dict:
    if SYS_FILE.exists():
        try:
            return json.loads(SYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def set_sys_memory(data: dict):
    SYS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── Compact context builder (token-safe) ──────────────────────────────────────
def build_context_snippet() -> str:
    """
    Build a minimal context string for each API call.
    Includes: project goal + pending tasks + key user facts.
    Does NOT include full conversation history.
    """
    parts = []

    # Project
    proj = get_project()
    if "_No active project_" not in proj:
        # Only first 400 chars
        parts.append(proj[:400])

    # Next task only
    nxt = get_next_task()
    if nxt:
        remaining = tasks_remaining()
        parts.append(f"[CURRENT TASK] {nxt}  ({remaining} tasks remaining)")

    # User memory (compact)
    mem_str = format_memory_for_prompt(load_memory())
    if mem_str:
        parts.append(mem_str[:300])

    return "\n\n".join(parts)
