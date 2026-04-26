"""
ui.py patch for v4.0 — _show_setup_ui updated for multi-provider .env
Drop-in replacement for v3.0 ui.py setup screen.
All other UI code stays identical.
"""

# ── Add this method to RahulUI class (replaces _show_setup_ui and _save_api) ─

SETUP_PATCH = '''
    def _show_setup_ui(self):
        """Multi-provider setup screen for v4.0"""
        self.setup_frame = tk.Frame(
            self.root, bg="#00080d",
            highlightbackground=T("PRI"), highlightthickness=2
        )
        self.setup_frame.place(relx=0.40, rely=0.5, anchor="center")

        tk.Label(self.setup_frame, text="◈  RAHUL  v4.0  SETUP",
                 fg=T("PRI"), bg="#00080d", font=("Courier",15,"bold")).pack(pady=(22,4))
        tk.Label(self.setup_frame,
                 text="Multi-Provider AI  •  OpenRouter + Nvidia + Groq",
                 fg=T("MID"), bg="#00080d", font=("Courier",9)).pack(pady=(0,18))

        fields = [
            ("OPENROUTER KEY (primary — free)",   "openrouter"),
            ("NVIDIA NIM KEY (fallback — free)",  "nvidia"),
            ("GROQ KEY (worker — ultra-fast free)","groq"),
        ]
        self._key_entries = {}
        for label, key in fields:
            tk.Label(self.setup_frame, text=label,
                     fg=T("DIM"), bg="#00080d", font=("Courier",8)).pack(pady=(4,2))
            e = tk.Entry(self.setup_frame, width=54, fg=T("TEXT"), bg="#000d12",
                         insertbackground=T("TEXT"), borderwidth=0,
                         font=("Courier",10), show="*")
            e.pack(pady=(0,6))
            self._key_entries[key] = e

        tk.Frame(self.setup_frame, bg=T("DIM"), height=1).pack(fill="x", padx=24, pady=(8,16))

        tk.Label(self.setup_frame,
                 text="★ At least ONE key required  •  More keys = better reliability",
                 fg=T("DIM"), bg="#00080d", font=("Courier",8)).pack(pady=(0,8))

        tk.Button(self.setup_frame, text="▸  START RAHUL v4.0",
                  command=self._save_api,
                  bg="#000000", fg=T("PRI"),
                  activebackground=T("DIM"), font=("Courier",12,"bold"),
                  borderwidth=0, pady=12, padx=30, cursor="hand2").pack(pady=(0,10))

        tk.Label(self.setup_frame,
                 text="Free keys: openrouter.ai  |  build.nvidia.com  |  console.groq.com",
                 fg=T("DIM"), bg="#00080d", font=("Courier",7)).pack(pady=(0,14))

    def _save_api(self):
        entries = self._key_entries
        or_key   = entries["openrouter"].get().strip()
        nv_key   = entries["nvidia"].get().strip()
        gr_key   = entries["groq"].get().strip()

        if not any([or_key, nv_key, gr_key]):
            for e in entries.values():
                e.configure(highlightthickness=1,
                            highlightbackground=T("RED"), highlightcolor=T("RED"))
            return

        import os
        os.makedirs(CONFIG_DIR, exist_ok=True)

        # Write .env file
        env_path = BASE_DIR / ".env"
        lines = []
        if or_key: lines.append(f"OPENROUTER_KEY={or_key}")
        if nv_key: lines.append(f"NVIDIA_KEY={nv_key}")
        if gr_key: lines.append(f"GROQ_KEY={gr_key}")
        lines.append("OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free")
        lines.append("NVIDIA_MODEL=meta/llama-3.3-70b-instruct")
        lines.append("GROQ_MODEL=llama-3.3-70b-versatile")
        lines.append("GROQ_WORKER_MODEL=llama-3.1-8b-instant")
        env_path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")

        # Also write legacy json for backward compat
        import json
        with open(API_FILE, "w") as f:
            json.dump({
                "gemini_api_key": "",
                "openrouter_key": or_key,
                "nvidia_key":     nv_key,
                "groq_key":       gr_key,
            }, f, indent=4)

        self.setup_frame.destroy()
        self._api_key_ready = True
        self.set_state("LISTENING")
        providers = []
        if or_key: providers.append("OpenRouter")
        if nv_key: providers.append("Nvidia")
        if gr_key: providers.append("Groq")
        self.write_log(f"SYS: RAHUL v4.0 online! Providers: {', '.join(providers)}")
        self.write_log("SYS: Swarm AI ready — type any command!")

    def _api_keys_exist(self):
        """Check .env OR legacy json for any valid key."""
        env_path = BASE_DIR / ".env"
        if env_path.exists():
            content = env_path.read_text()
            for key in ["OPENROUTER_KEY=", "NVIDIA_KEY=", "GROQ_KEY="]:
                if key in content:
                    val = [l.split("=",1)[1].strip()
                           for l in content.splitlines()
                           if l.startswith(key)]
                    if val and val[0] and val[0] != "your_openrouter_key_here":
                        return True
        if API_FILE.exists():
            try:
                import json
                d = json.loads(API_FILE.read_text())
                return bool(d.get("openrouter_key") or d.get("nvidia_key") or d.get("groq_key"))
            except Exception:
                pass
        return False
'''

# This file is a PATCH — see README for how to apply it to ui.py
# The full ui.py from v3.0 is unchanged except these 3 methods above.
print("UI patch v4.0 loaded — apply SETUP_PATCH methods to RahulUI in ui.py")
