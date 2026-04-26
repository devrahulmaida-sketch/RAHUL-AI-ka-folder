"""
core/orchestrator.py
━━━━━━━━━━━━━━━━━━━
Manager Agent — reasoning & planning ONLY.
Reads user prompt → breaks into tasks → writes tasks.md.
Does NOT execute anything itself.
Uses larger model for better reasoning quality.
"""

from __future__ import annotations
import re, json, time
from datetime import datetime
from core.dynamic_router import chat, extract_text
from core.memory_manager import (
    set_project, set_tasks, get_project,
    format_memory_for_prompt, load_memory,
    build_context_snippet,
)

ORCHESTRATOR_SYSTEM = """You are RAHUL's Orchestrator — a planning-only agent.

Your ONLY job:
1. Understand the user's request
2. Break it into 3-8 clear, concrete, executable tasks
3. Output ONLY a JSON array of task strings — nothing else

CRITICAL RULES:
- For GREETINGS (hi, hello, hy, hey, namaste, kya haal) → output ["Reply to greeting warmly in Hinglish"]
- For SIMPLE QUESTIONS → output ["Answer: <the answer>"]
- For REAL TASKS → break into atomic steps, ordered by dependency
- Each task must be a single, atomic action
- Be specific: "Search web for X" not "do research"
- Output ONLY valid JSON array, no markdown, no explanation

Example outputs:
["Reply to greeting warmly in Hinglish"]
["Search web for latest Python tutorials", "Create file workspace/notes.md with search results"]
["Get weather for Bhopal", "Show weather animation on screen"]
"""


def plan(user_input: str, log_fn=None) -> list[str]:
    """
    Convert user input into an ordered task list.
    Returns list of task strings and writes to tasks.md.
    """
    now     = datetime.now().strftime("%A, %d %B %Y — %I:%M %p")
    mem_str = format_memory_for_prompt(load_memory())
    context = build_context_snippet()

    system_parts = [ORCHESTRATOR_SYSTEM]
    if mem_str:
        system_parts.append(mem_str)
    system_parts.append(f"[CURRENT TIME] {now}")

    messages = [
        {"role": "system", "content": "\n\n".join(system_parts)},
        {"role": "user",   "content": user_input},
    ]

    if log_fn:
        log_fn("[Orchestrator] Planning tasks…")

    try:
        response = chat(
            messages=messages,
            temperature=0.3,
            max_tokens=512,
            worker_mode=False,
            log_fn=log_fn,
        )
        raw = extract_text(response).strip()

        # Try 1: Extract JSON array
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            try:
                tasks = json.loads(match.group())
                if isinstance(tasks, list) and tasks:
                    tasks = [str(t).strip() for t in tasks if str(t).strip()]
                    set_project(f"## User Request\n\n{user_input}")
                    set_tasks(tasks)
                    if log_fn:
                        log_fn(f"[Orchestrator] ✓ {len(tasks)} tasks planned.")
                    return tasks
            except json.JSONDecodeError:
                pass

        # Try 2: Parse numbered list  "1. Do X\n2. Do Y"
        numbered = re.findall(r'^\s*\d+[\.\)]\s*(.+)$', raw, re.MULTILINE)
        if numbered:
            tasks = [t.strip() for t in numbered if t.strip()]
            set_project(f"## User Request\n\n{user_input}")
            set_tasks(tasks)
            if log_fn:
                log_fn(f"[Orchestrator] ✓ {len(tasks)} tasks (from numbered list).")
            return tasks

        # Try 3: Parse bullet list  "- Do X\n• Do Y"
        bulleted = re.findall(r'^\s*[-•*]\s*(.+)$', raw, re.MULTILINE)
        if bulleted:
            tasks = [t.strip() for t in bulleted if t.strip()]
            set_project(f"## User Request\n\n{user_input}")
            set_tasks(tasks)
            if log_fn:
                log_fn(f"[Orchestrator] ✓ {len(tasks)} tasks (from bullet list).")
            return tasks

    except Exception as e:
        if log_fn:
            log_fn(f"[Orchestrator] Planning error: {e}")

    # Fallback — treat whole input as single task
    fallback = [user_input]
    set_tasks(fallback)
    return fallback


def is_simple_query(user_input: str) -> bool:
    """
    Detect if input is a simple conversational query
    that doesn't need task decomposition.
    """
    simple_patterns = [
        # Greetings (including typos like 'hy')
        r"^(hi|hy|hii|hiii|hello|hey|helo|hola|namaste|namaskar|salaam|salam)",
        r"^(kya haal|kaise ho|kaisa ho|kya chal|sup|wassup|what'?s up)",
        # Time
        r"^(what time|kitne baje|time kya|abhi kitne|time batao)",
        # Thanks
        r"^(thanks|thnx|thx|shukriya|thank you|dhanyawad|shukriya|wah|bahut achha|great|nice|good)",
        # Goodbye
        r"^(bye|goodbye|alvida|band karo|close|exit|quit|chal|theek hai bye)",
        # Simple yes/no
        r"^(ok|okay|theek|haan|nahi|yes|no|sure|hmm|aha|ohhh?|acha|achha)",
        # Just punctuation / empty-ish
        r"^[?.!]{1,3}$",
    ]
    low = user_input.lower().strip()

    for pat in simple_patterns:
        if re.match(pat, low, re.IGNORECASE):
            return True

    # Very short input (≤ 3 words) with no action verbs → conversational
    words = low.split()
    action_verbs = {
        # English
        "search","find","open","create","make","write","show","tell",
        "play","send","download","install","run","execute","generate",
        "translate","explain","analyze","check","calculate","set","get",
        "list","delete","move","copy","read","launch","start","stop",
        "news","weather","screenshot","image","video","music","file",
        # Hindi/Hinglish
        "kholo","banao","dikhao","dhundho","chalao","likho","batao",
        "nikalo","lao","bhejo","karo","dekho","sunao","search",
        "dikha","dhoondho","chala","bana","likh","khol","band",
    }
    if len(words) <= 3 and not any(w in action_verbs for w in words):
        return True

    return False
