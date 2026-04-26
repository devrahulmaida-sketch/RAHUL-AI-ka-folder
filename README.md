# 🤖 RAHUL Advanced AI v4.0
### Linux Edition | Swarm Architecture | 100% Free APIs

> **Gemini hatao, problems bhulao.** RAHUL ab OpenRouter + Nvidia + Groq pe chalta hai — teen free providers, auto-fallback, kabhi down nahi.

---

## 🏗️ Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────────┐
│  is_simple_query()?                 │
│   YES → Worker directly             │
│   NO  → Orchestrator (plans tasks)  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Orchestrator Agent (Manager)       │
│  • Breaks request into tasks        │
│  • Writes tasks.md checklist        │
│  • Uses large model for reasoning   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Worker Agent (Executor) × N tasks  │
│  • Reads ONE task at a time         │
│  • Calls tools to execute           │
│  • Marks task ✓ in tasks.md         │
│  • Uses fast model for speed        │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Dynamic API Router                 │
│  1. OpenRouter (primary)            │
│  2. Nvidia NIM (fallback)           │
│  3. Groq (tertiary + worker)        │
│  Auto-retry on 429/503              │
└─────────────────────────────────────┘
```

---

## ⚡ Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/RAHUL-AI.git
cd RAHUL-AI

# 2. Install
bash install.sh

# 3. Add your FREE API keys to .env
cp .env.example .env
nano .env

# 4. Run
python3 run.py
```

---

## 🔑 Free API Keys (All Have Free Tiers)

| Provider | URL | What it gives |
|---|---|---|
| **OpenRouter** | [openrouter.ai](https://openrouter.ai) | Llama 3.3 70B free |
| **Nvidia NIM** | [build.nvidia.com](https://build.nvidia.com) | 1000 free credits |
| **Groq** | [console.groq.com](https://console.groq.com) | Ultra-fast Llama free |

Add to `.env`:
```env
OPENROUTER_KEY=sk-or-...
NVIDIA_KEY=nvapi-...
GROQ_KEY=gsk_...
```

---

## 📁 Project Structure

```
RAHUL-AI/
├── run.py                    ← Main entry point
├── ui.py                     ← Advanced UI + AnimationOverlay
├── .env                      ← Your API keys (gitignored)
├── .env.example              ← Template
├── requirements.txt
├── install.sh
│
├── core/
│   ├── dynamic_router.py     ← OpenRouter→Nvidia→Groq fallback
│   ├── orchestrator.py       ← Manager: plans tasks
│   ├── worker_agent.py       ← Executor: runs tasks
│   └── memory_manager.py     ← File-based + JSON memory
│
├── astra_brain/              ← Token-safe file memory
│   ├── current_project.md    ← Active task context
│   ├── tasks.md              ← Swarm task checklist
│   └── sys_memory.json       ← System preferences
│
├── actions/                  ← 22+ tool implementations
│   ├── animation_engine.py
│   ├── web_search.py
│   ├── weather.py
│   ├── browser_control.py
│   ├── file_controller.py
│   ├── code_helper.py
│   ├── screen_process.py
│   ├── system_control.py
│   ├── youtube.py
│   └── ... (16 more)
│
├── memory/
│   └── memory.json           ← Permanent user facts
│
├── workspaces/               ← Generated files/artifacts
└── assets/
```

---

## 🧠 How Swarm Works

### Simple query (< 5 words, conversational):
```
"Kya haal hai?" → Worker directly → Response
```

### Complex task:
```
"Meri Python project ke liye ek README banao aur GitHub push karo"
    ↓
Orchestrator plans:
  [ ] Search best README templates
  [ ] Read existing project files
  [ ] Generate README.md content
  [ ] Write README.md to project folder
  [ ] Open terminal for git push instructions
    ↓
Worker executes each task → marks ✓ → next task
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `F4` | Toggle mic mute |
| `F5` | Cycle themes (Cyan/Gold/Purple) |
| `F11` | Fullscreen |
| `F2` | Conversation history |

---

## 🎨 Animation Types (shown on UI screen)

| Type | Example command |
|---|---|
| `list` | "Search Python tutorials" |
| `weather` | "Aaj ka weather Bhopal" |
| `steps` | "Python sikhna hai" |
| `news_ticker` | "Latest tech news" |
| `chart` | "CPU vs RAM usage dikha" |
| `comparison` | "React vs Vue compare karo" |
| `typewriter` | "Dramatic announcement" |
| `image` | "AI image banao sunset ki" |

---

## 📜 License
Personal and non-commercial use only. CC BY-NC 4.0
