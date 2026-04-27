"""
RAHUL Advanced UI v3.0 — Linux Edition
Features:
  • Typing-first (no mic required)
  • Animation engine with in-UI content rendering
  • 3 Themes  •  System stats  •  Tool feed  •  History
  • Particle system  •  Smooth waveform  •  Glassmorphism panels
"""

import os, json, time, math, random, threading, platform
import tkinter as tk
from tkinter import font as tkfont
from collections import deque
from PIL import Image, ImageTk, ImageDraw
import sys
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

BASE_DIR   = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
API_FILE   = CONFIG_DIR / "api_keys.json"

SYSTEM_NAME = "RAHUL"
VERSION     = "v5.0 Ollama"

# ── THEMES ──────────────────────────────────────────────────────────────────
THEMES = {
    "CYAN": dict(
        BG="#000000", PRI="#00d4ff", MID="#007a99", DIM="#003344",
        DIMMER="#001520", ACC="#ff6600", ACC2="#ffcc00",
        TEXT="#8ffcff", PANEL="#010c10", GREEN="#00ff88",
        RED="#ff3333", MUTED="#ff3366",
    ),
    "GOLD": dict(
        BG="#000000", PRI="#ffd700", MID="#997a00", DIM="#443300",
        DIMMER="#1a1200", ACC="#ff6600", ACC2="#ff9900",
        TEXT="#ffe87c", PANEL="#0d0900", GREEN="#88ff44",
        RED="#ff3333", MUTED="#ff3366",
    ),
    "PURPLE": dict(
        BG="#000000", PRI="#bf5fff", MID="#6a2299", DIM="#2d0d44",
        DIMMER="#110520", ACC="#ff4488", ACC2="#ff88cc",
        TEXT="#e5b3ff", PANEL="#0a0212", GREEN="#44ff99",
        RED="#ff3333", MUTED="#ff3366",
    ),
}
_THEME = "CYAN"
def T(k): return THEMES[_THEME][k]


class Particle:
    def __init__(self, cx, cy, speaking=False):
        self.x  = cx + random.uniform(-70, 70)
        self.y  = cy + random.uniform(-70, 70)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-2.8, -0.4) if speaking else random.uniform(-1.2, -0.2)
        self.life  = 1.0
        self.decay = random.uniform(0.010, 0.026) if speaking else random.uniform(0.005, 0.012)
        self.size  = random.uniform(1.5, 3.8) if speaking else random.uniform(0.8, 2.0)

    def step(self):
        self.x += self.vx; self.y += self.vy
        self.vy *= 0.98;   self.vx *= 0.99
        self.life -= self.decay
        return self.life > 0


# ── AnimationOverlay — renders rich content inside the UI ───────────────────
class AnimationOverlay:
    """Renders rich content animations on a SEPARATE top-layer canvas.
    Uses a dedicated canvas placed on top of main bg canvas — 
    so c.delete('all') on bg never wipes animations."""

    def __init__(self, root_widget, W: int, H: int):
        self.root   = root_widget
        self._items: list[dict] = []
        self._lock  = threading.Lock()

        # Dedicated overlay canvas — transparent bg, on top of main canvas
        self.c = tk.Canvas(
            root_widget, bg="",
            highlightthickness=0,
        )
        self.c.place(x=0, y=0, width=W, height=H)
        # Ensure it stays on top but allows click-through on empty areas
        self.c.lift()
        self._W, self._H = W, H

    def resize(self, W: int, H: int):
        self._W, self._H = W, H
        self.c.place(x=0, y=0, width=W, height=H)

    def show(self, anim_type: str, title: str, content: str = "",
             color: str = "", duration: int = 8, image_path: str = ""):
        import json as _json
        col = color or T("PRI")
        try:
            data = _json.loads(content) if content.strip().startswith(("{","[")) else {}
        except Exception:
            data = {"body": content}

        entry = {
            "type": anim_type, "title": title, "data": data,
            "color": col, "duration": duration, "image_path": image_path,
            "start": time.time(), "alpha": 0.0, "done": False,
            "scroll_x": 0, "step_idx": 0,
        }
        with self._lock:
            self._items = [i for i in self._items if not i["done"]]
            self._items.append(entry)

    def draw_all(self, W, H, tick):
        """Called every animation frame — clears and redraws overlay canvas."""
        self.c.delete("all")   # clear ONLY the overlay canvas
        now = time.time()
        with self._lock:
            active = [i for i in self._items if not i["done"]]

        if not active:
            return

        item    = active[-1]
        elapsed = now - item["start"]
        fade_in  = min(1.0, elapsed / 0.6)
        fade_out = 1.0 if elapsed < item["duration"] - 1.0 else max(0.0, item["duration"] - elapsed)
        alpha    = int(min(fade_in, fade_out) * 255)

        if elapsed >= item["duration"]:
            item["done"] = True
            return

        t = item["type"]
        dispatch = {
            "card":        self._draw_card,
            "list":        self._draw_list,
            "chart":       self._draw_chart,
            "steps":       self._draw_steps,
            "news_ticker": self._draw_ticker,
            "comparison":  self._draw_comparison,
            "weather":     self._draw_weather,
            "typewriter":  self._draw_typewriter,
            "countdown":   self._draw_countdown,
            "image":       self._draw_image,
        }
        fn = dispatch.get(t, self._draw_card)
        fn(item, W, H, alpha, tick)

    def _ac(self, r, g, b, a):
        f = a / 255.0
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

    def _hex_rgba(self, hex_col, a):
        h = hex_col.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return self._ac(r, g, b, a)

    # ── card ──────────────────────────────────────────────────────────────────
    def _draw_card(self, item, W, H, alpha, tick):
        c = self.c
        cx, cy = int(W * 0.42), int(H * 0.54)
        w, h = min(480, int(W * 0.55)), 180
        x0, y0 = cx - w//2, cy

        border = self._hex_rgba(item["color"], alpha)
        bg     = self._hex_rgba("#001a22", int(alpha * 0.85))
        c.create_rectangle(x0, y0, x0+w, y0+h, fill="#001a22", outline=border, width=2)

        # Icon pulse
        pulse = 1 + 0.06 * math.sin(tick * 0.12)
        icon  = item["data"].get("icon", "◈")
        c.create_text(x0 + 36, y0 + h//2, text=icon,
                      fill=border, font=("Courier", 22, "bold"))

        c.create_text(cx, y0 + 22, text=item["title"].upper(),
                      fill=border, font=("Courier", 12, "bold"))

        body = item["data"].get("body", "")
        if body:
            c.create_text(cx, y0 + h//2 + 10, text=body,
                          fill=T("TEXT"), font=("Courier", 10), width=w - 80)

    # ── list ──────────────────────────────────────────────────────────────────
    def _draw_list(self, item, W, H, alpha, tick):
        c = self.c
        cx, cy = int(W * 0.42), int(H * 0.50)
        items  = item["data"] if isinstance(item["data"], list) else []
        h      = 40 + len(items) * 32 + 20
        w      = min(520, int(W * 0.60))
        x0, y0 = cx - w//2, cy - h//2

        border = self._hex_rgba(item["color"], alpha)
        c.create_rectangle(x0, y0, x0+w, y0+h, fill="#001520", outline=border, width=2)
        c.create_text(cx, y0 + 20, text=f"◈  {item['title'].upper()}",
                      fill=border, font=("Courier", 11, "bold"))

        elapsed = time.time() - item["start"]
        visible = min(len(items), max(1, int(elapsed * 2.5)))

        for i, entry in enumerate(items[:visible]):
            ey   = y0 + 44 + i * 32
            row_a = min(alpha, int(alpha * (i + 1) / max(1, visible)))
            col  = self._hex_rgba(item["color"], row_a)
            txt  = entry["text"] if isinstance(entry, dict) else str(entry)
            ico  = entry.get("icon", "▸") if isinstance(entry, dict) else "▸"
            c.create_text(x0 + 24, ey, text=ico, fill=col,
                          font=("Courier", 11), anchor="w")
            c.create_text(x0 + 52, ey, text=txt, fill=T("TEXT"),
                          font=("Courier", 10), anchor="w")

    # ── chart ─────────────────────────────────────────────────────────────────
    def _draw_chart(self, item, W, H, alpha, tick):
        c = self.c
        cx, cy = int(W * 0.42), int(H * 0.50)
        w, h   = min(540, int(W * 0.62)), 200
        x0, y0 = cx - w//2, cy - h//2

        border  = self._hex_rgba(item["color"], alpha)
        labels  = item["data"].get("labels", [])
        values  = item["data"].get("values", [])
        ctype   = item["data"].get("chart_type", "bar")

        c.create_rectangle(x0, y0, x0+w, y0+h, fill="#001520", outline=border, width=2)
        c.create_text(cx, y0 + 18, text=f"◈  {item['title'].upper()}",
                      fill=border, font=("Courier", 10, "bold"))

        if not values: return
        elapsed = time.time() - item["start"]
        progress = min(1.0, elapsed / 1.5)

        if ctype in ("bar", "bar"):
            bw   = max(8, (w - 60) // max(1, len(values)) - 6)
            maxv = max(values) or 1
            chart_h = h - 70
            bx0  = x0 + 30
            for i, (lbl, val) in enumerate(zip(labels, values)):
                bx  = bx0 + i * (bw + 6)
                bh  = int(chart_h * (val / maxv) * progress)
                by  = y0 + h - 28 - bh
                hue = int(200 + i * 30) % 360
                col = border if i == 0 else T("ACC2")
                c.create_rectangle(bx, by, bx+bw, y0+h-28, fill=col, outline="")
                c.create_text(bx + bw//2, y0+h-18, text=str(lbl)[:6],
                              fill=T("DIM"), font=("Courier", 7))
                if bh > 14:
                    c.create_text(bx+bw//2, by+4, text=str(int(val)),
                                  fill=T("TEXT"), font=("Courier", 7))

    # ── steps ─────────────────────────────────────────────────────────────────
    def _draw_steps(self, item, W, H, alpha, tick):
        c = self.c
        cx, cy  = int(W * 0.42), int(H * 0.50)
        steps   = item["data"] if isinstance(item["data"], list) else []
        h       = 50 + len(steps) * 38 + 20
        w       = min(520, int(W * 0.60))
        x0, y0  = cx - w//2, cy - h//2

        border  = self._hex_rgba(item["color"], alpha)
        elapsed = time.time() - item["start"]
        current = min(len(steps) - 1, int(elapsed * 0.9))

        c.create_rectangle(x0, y0, x0+w, y0+h, fill="#001520", outline=border, width=2)
        c.create_text(cx, y0 + 22, text=f"◈  {item['title'].upper()}",
                      fill=border, font=("Courier", 11, "bold"))

        for i, step in enumerate(steps):
            sy     = y0 + 48 + i * 38
            done   = i < current
            active = i == current
            num_col = T("GREEN") if done else (border if active else T("DIM"))
            txt_col = T("TEXT") if done or active else T("DIM")
            stext  = step.get("step", str(i+1)) if isinstance(step, dict) else str(i+1)
            desc   = step.get("description", "") if isinstance(step, dict) else str(step)
            prefix = "✓" if done else (f"▶ {stext}" if active else f"  {stext}")
            c.create_text(x0 + 30, sy, text=prefix, fill=num_col,
                          font=("Courier", 10, "bold"), anchor="w")
            c.create_text(x0 + 80, sy, text=desc[:55], fill=txt_col,
                          font=("Courier", 9), anchor="w")

    # ── news ticker ───────────────────────────────────────────────────────────
    def _draw_ticker(self, item, W, H, alpha, tick):
        c   = self.c
        y   = int(H * 0.78)
        col = self._hex_rgba(item["color"], alpha)
        c.create_rectangle(0, y-2, W, y+30, fill="#001520", outline="")
        c.create_line(0, y-2, W, y-2, fill=col, width=1)

        headlines = item["data"] if isinstance(item["data"], list) else []
        if not headlines: return
        full_text = "  ◆  ".join(
            (h.get("text", str(h)) if isinstance(h, dict) else str(h)) for h in headlines
        )
        item["scroll_x"] = item.get("scroll_x", W) - 2
        if item["scroll_x"] < -len(full_text) * 8:
            item["scroll_x"] = W
        c.create_text(item["scroll_x"], y + 12, text=full_text,
                      fill=col, font=("Courier", 10), anchor="w")

    # ── comparison ────────────────────────────────────────────────────────────
    def _draw_comparison(self, item, W, H, alpha, tick):
        c = self.c
        cx, cy = int(W * 0.42), int(H * 0.50)
        hdrs   = item["data"].get("headers", [])
        rows   = item["data"].get("rows", [])
        cols_n = max(len(hdrs), 2)
        row_h  = 26
        h      = 48 + (len(rows) + 1) * row_h + 16
        w      = min(560, int(W * 0.65))
        x0, y0 = cx - w//2, cy - h//2
        cw     = (w - 20) // cols_n

        border = self._hex_rgba(item["color"], alpha)
        c.create_rectangle(x0, y0, x0+w, y0+h, fill="#001520", outline=border, width=2)
        c.create_text(cx, y0 + 18, text=f"◈  {item['title'].upper()}",
                      fill=border, font=("Courier", 10, "bold"))

        hy = y0 + 36
        for ci, hdr in enumerate(hdrs):
            hx = x0 + 10 + ci * cw + cw // 2
            c.create_text(hx, hy, text=str(hdr).upper(),
                          fill=border, font=("Courier", 9, "bold"))
        c.create_line(x0+10, hy+12, x0+w-10, hy+12, fill=T("DIM"))

        for ri, row in enumerate(rows):
            ry = hy + 18 + ri * row_h
            bg = "#001a22" if ri % 2 == 0 else "#000d15"
            c.create_rectangle(x0+10, ry-8, x0+w-10, ry+16, fill=bg, outline="")
            for ci, cell in enumerate(row[:cols_n]):
                rx = x0 + 10 + ci * cw + cw // 2
                c.create_text(rx, ry, text=str(cell)[:18],
                               fill=T("TEXT"), font=("Courier", 9))

    # ── weather ───────────────────────────────────────────────────────────────
    def _draw_weather(self, item, W, H, alpha, tick):
        c = self.c
        cx, cy = int(W * 0.42), int(H * 0.54)
        w, h   = 420, 160
        x0, y0 = cx - w//2, cy

        border  = self._hex_rgba(item["color"], alpha)
        d       = item["data"]
        temp    = d.get("temp", "?")
        cond    = d.get("condition", "Clear")
        city    = d.get("city", item["title"])
        humidity= d.get("humidity", "")
        icon    = {"Clear":"☀️","Clouds":"☁️","Rain":"🌧️",
                   "Snow":"❄️","Thunderstorm":"⛈️"}.get(cond, "🌤️")

        c.create_rectangle(x0, y0, x0+w, y0+h, fill="#001520", outline=border, width=2)

        pulse = 1 + 0.08 * math.sin(tick * 0.10)
        fs    = int(28 * pulse)
        c.create_text(x0 + 55, y0 + h//2, text=icon,
                      fill=border, font=("Courier", fs))
        c.create_text(x0 + 140, y0 + 40, text=city.upper(),
                      fill=border, font=("Courier", 11, "bold"), anchor="w")
        c.create_text(x0 + 140, y0 + 70,
                      text=f"{temp}°C  —  {cond}",
                      fill=T("TEXT"), font=("Courier", 14, "bold"), anchor="w")
        if humidity:
            c.create_text(x0 + 140, y0 + 98,
                          text=f"Humidity: {humidity}%",
                          fill=T("DIM"), font=("Courier", 9), anchor="w")

    # ── typewriter ────────────────────────────────────────────────────────────
    def _draw_typewriter(self, item, W, H, alpha, tick):
        c    = self.c
        cx   = int(W * 0.42)
        cy   = int(H * 0.60)
        body = item["data"].get("body", item["title"])
        elapsed = time.time() - item["start"]
        chars   = min(len(body), int(elapsed * 28))
        shown   = body[:chars]
        cursor  = "█" if tick % 30 < 15 else ""
        col     = self._hex_rgba(item["color"], alpha)

        c.create_rectangle(cx - 260, cy - 50, cx + 260, cy + 50,
                           fill="#001520", outline=col, width=1)
        c.create_text(cx, cy - 30, text=f"◈  {item['title'].upper()}",
                      fill=col, font=("Courier", 10, "bold"))
        c.create_text(cx, cy + 8,
                      text=shown + cursor,
                      fill=T("TEXT"), font=("Courier", 10), width=480)

    # ── countdown ────────────────────────────────────────────────────────────
    def _draw_countdown(self, item, W, H, alpha, tick):
        c = self.c
        cx, cy = int(W * 0.42), int(H * 0.57)
        remaining = max(0, item["data"].get("seconds", 10) - int(time.time() - item["start"]))
        col = self._hex_rgba(item["color"], alpha)
        pulse = 1 + 0.12 * math.sin(tick * 0.2)
        fs = int(36 * pulse)
        c.create_text(cx, cy - 20, text=item["title"].upper(),
                      fill=col, font=("Courier", 11, "bold"))
        c.create_text(cx, cy + 20, text=f"{remaining:02d}",
                      fill=col, font=("Courier", fs, "bold"))

    # ── image ─────────────────────────────────────────────────────────────────
    def _draw_image(self, item, W, H, alpha):
        path = item.get("image_path", "")
        if not path or not Path(path).exists():
            return
        try:
            img  = Image.open(path).convert("RGBA")
            iw, ih = 300, 220
            img  = img.resize((iw, ih), Image.LANCZOS)
            cx, cy = int(W * 0.42), int(H * 0.54)
            if not hasattr(item, "_tk_img") or item.get("_img_path") != path:
                item["_tk_img"]   = ImageTk.PhotoImage(img)
                item["_img_path"] = path
            self.c.create_image(cx, cy, image=item["_tk_img"])
            col = self._hex_rgba(item["color"], alpha)
            self.c.create_text(cx, cy + ih//2 + 12, text=item["title"],
                                fill=col, font=("Courier", 9))
        except Exception as e:
            print(f"[AnimOverlay] image error: {e}")


# ── Main UI ──────────────────────────────────────────────────────────────────
class RahulUI:
    def __init__(self):
        global _THEME
        self.root = tk.Tk()
        self.root.title(f"RAHUL  {VERSION}")
        self.root.resizable(True, True)
        self._is_fullscreen = False

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        W  = min(sw, 1140)
        H  = min(sh, 840)
        self.root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.root.configure(bg="#000000")
        self.W, self.H = W, H

        # Core state
        self.speaking, self.muted  = False, False
        self.scale, self.target_scale = 1.0, 1.0
        self.halo_a, self.target_halo = 60.0, 60.0
        self.last_t  = time.time()
        self.tick    = 0
        self.scan_angle   = 0.0
        self.scan2_angle  = 180.0
        self.rings_spin   = [0.0, 120.0, 240.0]
        self.pulse_r      = [0.0]
        self.status_text  = "INITIALISING"
        self.status_blink = True
        self._jarvis_state = "INITIALISING"
        self.on_text_command = None
        self.on_voice_toggle = None  # callback(bool) for voice on/off

        # Advanced
        self.particles      = []
        self._tool_feed     = deque(maxlen=10)
        self._convo_history = []
        self._waveform      = [0.0] * 52
        self._waveform_tgt  = [0.0] * 52
        self._sys_cpu       = 0.0
        self._sys_ram       = 0.0
        self._sys_net_up    = 0
        self._sys_net_dn    = 0
        self._last_net      = (0, 0)
        self._session_start = time.time()
        self._msg_count     = 0
        self._active_tool   = None
        self._active_tool_t = 0
        self._current_theme = "CYAN"
        self._show_history  = False
        self._hist_overlay  = None

        # Image
        self._img_frame     = None
        self._original_img  = None
        self._image_scale   = 0.5

        # Geometry
        self.FACE_SZ = min(int(H * 0.44), 340)
        self.FCX     = int(W * 0.40)
        self.FCY     = int(H * 0.14) + self.FACE_SZ // 2

        # Face image (optional)
        self._face_pil   = None
        self._has_face   = False
        self._face_cache = None
        self._try_load_face()

        # Canvas
        self.bg = tk.Canvas(self.root, width=W, height=H, bg="#000000", highlightthickness=0)
        self.bg.place(x=0, y=0)

        # Animation overlay — separate canvas on top of bg
        self.anim = AnimationOverlay(self.root, W, H)

        # Panels
        self._build_right_panel()

        # Log
        LW   = int(W * 0.52)
        LH   = 100
        LOG_Y = H - LH - 82
        self._lw, self._log_y = LW, LOG_Y
        self.log_frame = tk.Frame(self.root, bg="#010c10",
                                   highlightbackground="#003344", highlightthickness=1)
        self.log_frame.place(x=self.FCX - LW//2, y=LOG_Y, width=LW, height=LH)
        self.log_text = tk.Text(
            self.log_frame, fg="#8ffcff", bg="#010c10",
            insertbackground="#8ffcff", borderwidth=0,
            wrap="word", font=("Courier", 9), padx=8, pady=5,
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        for tag, col in [("you","#e8e8e8"),("ai","#00d4ff"),("sys","#ffcc00"),
                         ("err","#ff3333"),("tool","#ff6600")]:
            self.log_text.tag_config(tag, foreground=col)

        self.typing_queue = deque()
        self.is_typing    = False

        INPUT_Y = LOG_Y - 50
        self._build_input_bar(LW, INPUT_Y)
        self._build_mute_button()
        self._build_bottom_bar()

        self.root.bind("<Configure>", self._on_resize)
        self.root.bind("<F4>",  lambda e: self._toggle_mute())
        self.root.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self._exit_fullscreen())
        self.root.bind("<F2>",  lambda e: self._toggle_history())
        self.root.bind("<F5>",  lambda e: self._cycle_theme())

        self._api_key_ready = self._api_keys_exist()
        if not self._api_key_ready:
            self._show_setup_ui()

        self._start_sys_monitor()
        self._start_waveform()
        self._animate()
        self.root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))

    # ── Right panel ───────────────────────────────────────────────────────────
    def _build_right_panel(self):
        PX = int(self.W * 0.77)
        PW = self.W - PX - 10
        self._hud_x, self._hud_w = PX, PW

        # System stats
        self._stats = tk.Frame(self.root, bg="#010c10",
                                highlightbackground="#003344", highlightthickness=1)
        self._stats.place(x=PX, y=68, width=PW, height=170)
        tk.Label(self._stats, text="◈  SYS STATUS", bg="#010c10", fg="#007a99",
                  font=("Courier", 8, "bold")).pack(pady=(8,4))
        self._cpu_v = tk.StringVar(value="CPU  ░░░░░░░░░░  0%")
        self._ram_v = tk.StringVar(value="RAM  ░░░░░░░░░░  0%")
        self._net_v = tk.StringVar(value="NET  ↑0   ↓0 KB/s")
        self._upt_v = tk.StringVar(value="UPT  00:00:00")
        for v in [self._cpu_v, self._ram_v, self._net_v, self._upt_v]:
            tk.Label(self._stats, textvariable=v, bg="#010c10", fg="#8ffcff",
                      font=("Courier", 8), anchor="w", padx=10).pack(fill="x", pady=1)

        # Tool feed
        self._feed_f = tk.Frame(self.root, bg="#010c10",
                                 highlightbackground="#003344", highlightthickness=1)
        self._feed_f.place(x=PX, y=248, width=PW, height=240)
        tk.Label(self._feed_f, text="◈  TOOL FEED", bg="#010c10", fg="#007a99",
                  font=("Courier", 8, "bold")).pack(pady=(8,4))
        self._feed_c = tk.Canvas(self._feed_f, bg="#010c10", highlightthickness=0, height=200)
        self._feed_c.pack(fill="both", expand=True, padx=6)

        # Session
        self._sess_f = tk.Frame(self.root, bg="#010c10",
                                 highlightbackground="#003344", highlightthickness=1)
        self._sess_f.place(x=PX, y=498, width=PW, height=90)
        tk.Label(self._sess_f, text="◈  SESSION", bg="#010c10", fg="#007a99",
                  font=("Courier", 8, "bold")).pack(pady=(8,4))
        self._sess_v = tk.StringVar(value="Messages: 0\nUptime:  00:00:00")
        tk.Label(self._sess_f, textvariable=self._sess_v, bg="#010c10", fg="#8ffcff",
                  font=("Courier", 8), justify="left", padx=10).pack(fill="x")

        # Buttons row
        btn_f = tk.Frame(self.root, bg="#000000")
        btn_f.place(x=PX, y=598, width=PW, height=60)

        tk.Button(btn_f, text="📋 F2: History", command=self._toggle_history,
                   bg="#010c10", fg="#007a99", font=("Courier", 7), borderwidth=0,
                   cursor="hand2", activebackground="#001a22",
                   activeforeground="#00d4ff").pack(fill="x", padx=2, pady=2)

        tk.Button(btn_f, text="🎨 F5: Theme", command=self._cycle_theme,
                   bg="#010c10", fg="#007a99", font=("Courier", 7), borderwidth=0,
                   cursor="hand2", activebackground="#001a22",
                   activeforeground="#00d4ff").pack(fill="x", padx=2, pady=2)

    # ── Conversation history ──────────────────────────────────────────────────
    def _toggle_history(self):
        self._show_history = not self._show_history
        if self._show_history:
            self._build_hist()
        elif self._hist_overlay:
            self._hist_overlay.destroy()
            self._hist_overlay = None

    def _build_hist(self):
        if self._hist_overlay:
            self._hist_overlay.destroy()
        self._hist_overlay = tk.Frame(self.root, bg="#00080d",
                                        highlightbackground=T("PRI"), highlightthickness=1)
        x0 = int(self.W * 0.04)
        self._hist_overlay.place(x=x0, y=72, width=int(self.W*0.58), height=self.H-180)

        hdr = tk.Frame(self._hist_overlay, bg="#001520")
        hdr.pack(fill="x")
        tk.Label(hdr, text="  ◈  CONVERSATION HISTORY", bg="#001520", fg=T("PRI"),
                  font=("Courier", 10, "bold")).pack(side="left", pady=6)
        tk.Button(hdr, text="✕", command=self._toggle_history,
                   bg="#001520", fg=T("RED"), font=("Courier", 10, "bold"),
                   borderwidth=0, cursor="hand2").pack(side="right", padx=8)

        frm = tk.Frame(self._hist_overlay, bg="#00080d")
        frm.pack(fill="both", expand=True, padx=8, pady=8)
        sb  = tk.Scrollbar(frm)
        sb.pack(side="right", fill="y")
        txt = tk.Text(frm, bg="#00080d", fg=T("TEXT"), font=("Courier", 9),
                       wrap="word", borderwidth=0, yscrollcommand=sb.set)
        txt.pack(fill="both", expand=True)
        sb.config(command=txt.yview)
        txt.tag_config("you", foreground="#e8e8e8", font=("Courier", 9, "bold"))
        txt.tag_config("ai",  foreground=T("PRI"))
        txt.tag_config("ts",  foreground=T("DIM"), font=("Courier", 7))
        txt.configure(state="normal")
        if not self._convo_history:
            txt.insert(tk.END, "  No history yet.\n", "ts")
        for e in self._convo_history:
            txt.insert(tk.END, f"  [{e['time']}] ", "ts")
            if e["role"] == "you":
                txt.insert(tk.END, f"YOU: {e['text']}\n", "you")
            else:
                txt.insert(tk.END, f"AI:  {e['text']}\n", "ai")
        txt.see(tk.END)
        txt.configure(state="disabled")

    # ── Theme ─────────────────────────────────────────────────────────────────
    def _cycle_theme(self):
        global _THEME
        order = ["CYAN", "GOLD", "PURPLE"]
        idx = order.index(_THEME)
        _THEME = order[(idx + 1) % len(order)]
        self._current_theme = _THEME
        self.write_log(f"SYS: Theme → {_THEME}")

    # ── Mute ──────────────────────────────────────────────────────────────────
    def _build_mute_button(self):
        self._mute_c = tk.Canvas(self.root, width=130, height=32, bg="#000000",
                                  highlightthickness=0, cursor="hand2")
        self._mute_c.place(x=14, y=self.H - 66)
        self._mute_c.bind("<Button-1>", lambda e: self._toggle_mute())
        self._draw_mute()

        # Voice input toggle button (next to mute)
        self._voice_active = False
        self._voice_c = tk.Canvas(self.root, width=130, height=32, bg="#000000",
                                   highlightthickness=0, cursor="hand2")
        self._voice_c.place(x=150, y=self.H - 66)
        self._voice_c.bind("<Button-1>", lambda e: self._toggle_voice())
        self._draw_voice_btn()

        # TTS toggle button
        self._tts_active = True
        self._tts_c = tk.Canvas(self.root, width=100, height=32, bg="#000000",
                                 highlightthickness=0, cursor="hand2")
        self._tts_c.place(x=286, y=self.H - 66)
        self._tts_c.bind("<Button-1>", lambda e: self._toggle_tts())
        self._draw_tts_btn()

    def _draw_voice_btn(self):
        c = self._voice_c
        c.delete("all")
        if self._voice_active:
            bd, fl, ic, lb, fg = T("GREEN"), "#001a0a", "🎤", " ON", T("GREEN")
        else:
            bd, fl, ic, lb, fg = T("DIM"), T("PANEL"), "🎤", " OFF", T("DIM")
        c.create_rectangle(0, 0, 130, 32, outline=bd, fill=fl, width=1)
        c.create_text(65, 16, text=f"VOICE{ic}{lb}", fill=fg, font=("Courier", 9, "bold"))

    def _draw_tts_btn(self):
        c = self._tts_c
        c.delete("all")
        if self._tts_active:
            bd, fl, lb, fg = T("ACC2"), "#1a1400", "🔊 ON", T("ACC2")
        else:
            bd, fl, lb, fg = T("DIM"), T("PANEL"), "🔇 OFF", T("DIM")
        c.create_rectangle(0, 0, 100, 32, outline=bd, fill=fl, width=1)
        c.create_text(50, 16, text=lb, fill=fg, font=("Courier", 9, "bold"))

    def _toggle_voice(self):
        self._voice_active = not self._voice_active
        self._draw_voice_btn()
        if self._voice_active:
            self.write_log("SYS: Voice input ON — bol ke command do!")
            if self.on_voice_toggle:
                self.on_voice_toggle(True)
        else:
            self.write_log("SYS: Voice input OFF.")
            if self.on_voice_toggle:
                self.on_voice_toggle(False)

    def _toggle_tts(self):
        self._tts_active = not self._tts_active
        self._draw_tts_btn()
        self.write_log(f"SYS: TTS {'ON' if self._tts_active else 'OFF'}")

    def _draw_mute(self):
        c = self._mute_c
        c.delete("all")
        if self.muted:
            bd, fl, ic, lb, fg = T("MUTED"), "#1a0008", "🔇", " MUTED", T("MUTED")
        else:
            bd, fl, ic, lb, fg = T("MID"), T("PANEL"), "🎙", " LIVE", T("GREEN")
        c.create_rectangle(0,0,130,32, outline=bd, fill=fl, width=1)
        c.create_text(65, 16, text=f"{ic}{lb}", fill=fg, font=("Courier",10,"bold"))

    def _toggle_mute(self):
        self.muted = not self.muted
        self._draw_mute()
        if self.muted:
            self.set_state("MUTED")
            self.write_log("SYS: Mic muted.")
        else:
            self.set_state("LISTENING")
            self.write_log("SYS: Mic active.")

    def _stream_token(self, token: str):
        """Called during streaming — shows tokens as they arrive in log."""
        # Accumulate tokens, flush on sentence end or punctuation
        if not hasattr(self, "_stream_buf"):
            self._stream_buf = ""
        self._stream_buf += token
        # Flush on sentence boundaries
        if any(c in token for c in ".!?\n") or len(self._stream_buf) > 60:
            buf = self._stream_buf.strip()
            if buf:
                self.log_text.configure(state="normal")
                self.log_text.insert(tk.END, buf + " ", "ai")
                self.log_text.see(tk.END)
                self.log_text.configure(state="disabled")
            self._stream_buf = ""

    # ── Input bar ─────────────────────────────────────────────────────────────
    def _build_input_bar(self, lw, y):
        x0    = self.FCX - lw//2
        BTN_W = 75
        INP_W = lw - BTN_W - 4

        self._input_var = tk.StringVar()
        self._input_entry = tk.Entry(
            self.root, textvariable=self._input_var,
            fg=T("TEXT"), bg="#000d12", insertbackground=T("TEXT"),
            borderwidth=0, font=("Courier", 10),
            highlightthickness=1,
            highlightbackground=T("DIM"), highlightcolor=T("PRI"),
        )
        self._input_entry.place(x=x0, y=y, width=INP_W, height=30)
        self._input_entry.bind("<Return>",   self._submit)
        self._input_entry.bind("<KP_Enter>", self._submit)

        self._send_btn = tk.Button(
            self.root, text="SEND ▸", command=self._submit,
            fg=T("PRI"), bg=T("PANEL"),
            activeforeground="#000000", activebackground=T("PRI"),
            font=("Courier", 9, "bold"), borderwidth=0, cursor="hand2",
        )
        self._send_btn.place(x=x0+INP_W+4, y=y, width=BTN_W, height=30)

    def _submit(self, event=None):
        text = self._input_var.get().strip()
        if not text:
            return
        self._input_var.set("")
        self.write_log(f"You: {text}")
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

    def _build_bottom_bar(self):
        pass  # drawn on canvas in _draw()

    # ── State ─────────────────────────────────────────────────────────────────
    def set_state(self, state: str):
        self._jarvis_state = state
        m = {"MUTED":(False,"MUTED"),"SPEAKING":(True,"SPEAKING"),
             "THINKING":(False,"THINKING"),"LISTENING":(False,"LISTENING"),
             "PROCESSING":(False,"PROCESSING")}
        self.speaking, self.status_text = m.get(state, (False,"ONLINE"))

    # ── Tool notification ─────────────────────────────────────────────────────
    def notify_tool(self, name: str, status: str = "running"):
        icons = {
            "open_app":"🚀","web_search":"🔍","browser_control":"🌐",
            "file_controller":"📁","code_helper":"💻","screen_process":"👁",
            "system_control":"⚙️","youtube":"▶️","news_reader":"📰",
            "calculator":"🧮","translate":"🌐","image_gen":"🎨",
            "pdf_reader":"📄","email_action":"📧","clipboard_mgr":"📋",
            "process_mgr":"⚡","network_info":"📡","animation_engine":"✨",
            "weather_report":"🌤️","reminder":"⏰","send_message":"💬",
        }
        icon = icons.get(name, "⚡")
        ts   = time.strftime("%H:%M:%S")
        self._tool_feed.appendleft({"ts":ts,"name":name,"icon":icon,"status":status})
        self._active_tool   = name
        self._active_tool_t = 80
        self._refresh_feed()

    def _refresh_feed(self):
        c = self._feed_c
        c.delete("all")
        y = 4
        for i, item in enumerate(self._tool_feed):
            col = T("PRI") if i==0 else T("MID") if i<3 else T("DIM")
            c.create_text(6, y, anchor="nw",
                          text=f"{item['icon']} {item['name'][:17]:<17} {item['ts']}",
                          fill=col, font=("Courier",7))
            y += 20
            if y > 195: break

    # ── Sys monitor ───────────────────────────────────────────────────────────
    def _start_sys_monitor(self):
        def _loop():
            while True:
                try:
                    if HAS_PSUTIL:
                        self._sys_cpu = psutil.cpu_percent(interval=1)
                        self._sys_ram = psutil.virtual_memory().percent
                        net  = psutil.net_io_counters()
                        up   = max(0, (net.bytes_sent - self._last_net[0]) // 1024)
                        dn   = max(0, (net.bytes_recv - self._last_net[1]) // 1024)
                        self._last_net = (net.bytes_sent, net.bytes_recv)
                        self._sys_net_up, self._sys_net_dn = up, dn
                    uptime = int(time.time() - self._session_start)
                    h, m, s = uptime//3600, (uptime%3600)//60, uptime%60
                    def bar(v): f=int(v/10); return "█"*f + "░"*(10-f)
                    self._cpu_v.set(f"CPU  {bar(self._sys_cpu)} {self._sys_cpu:4.0f}%")
                    self._ram_v.set(f"RAM  {bar(self._sys_ram)} {self._sys_ram:4.0f}%")
                    self._net_v.set(f"NET  ↑{self._sys_net_up:4d} ↓{self._sys_net_dn:4d} KB/s")
                    self._upt_v.set(f"UPT  {h:02d}:{m:02d}:{s:02d}")
                    self._sess_v.set(f"Messages: {self._msg_count}\nUptime:  {h:02d}:{m:02d}:{s:02d}")
                except Exception:
                    pass
                time.sleep(2)
        threading.Thread(target=_loop, daemon=True).start()

    def _start_waveform(self):
        def _loop():
            while True:
                for i in range(52):
                    if self.speaking:
                        self._waveform_tgt[i] = random.uniform(5, 22)
                    elif self._jarvis_state == "THINKING":
                        self._waveform_tgt[i] = 3 + 2*math.sin(time.time()*3 + i*0.5)
                    elif self._jarvis_state == "PROCESSING":
                        self._waveform_tgt[i] = 2 + 5*abs(math.sin(time.time()*5 + i*0.4))
                    else:
                        self._waveform_tgt[i] = 1.5 + math.sin(time.time()*0.8 + i*0.3)
                time.sleep(0.04)
        threading.Thread(target=_loop, daemon=True).start()

    # ── Face ──────────────────────────────────────────────────────────────────
    def _try_load_face(self):
        for name in ["face.png","face.jpg","assets/face.png"]:
            p = BASE_DIR / name
            if p.exists():
                try:
                    FW  = self.FACE_SZ
                    img = Image.open(str(p)).convert("RGBA").resize((FW,FW), Image.LANCZOS)
                    msk = Image.new("L",(FW,FW),0)
                    ImageDraw.Draw(msk).ellipse((2,2,FW-2,FW-2), fill=255)
                    img.putalpha(msk)
                    self._face_pil  = img
                    self._has_face  = True
                    return
                except Exception:
                    pass
        self._has_face = False

    @staticmethod
    def _ac(r,g,b,a):
        f = a/255.0
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

    def _hex_rgb(self, h):
        h = h.lstrip("#")
        return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)

    # ── Resize ────────────────────────────────────────────────────────────────
    def _on_resize(self, e):
        if hasattr(self,"_rb"): return
        self._rb = True
        try:
            nw, nh = self.root.winfo_width(), self.root.winfo_height()
            if abs(nw-self.W)>10 or abs(nh-self.H)>10:
                self.W, self.H = nw, nh
                self.FCX = int(nw*0.40)
                self.FCY = int(nh*0.14) + self.FACE_SZ//2
                self.bg.configure(width=nw, height=nh)
                LW = int(nw*0.52)
                LOG_Y = nh - 100 - 82
                x0 = self.FCX - LW//2
                self.log_frame.place(x=x0, y=LOG_Y, width=LW)
                INP_Y = LOG_Y - 50
                self._input_entry.place(x=x0, y=INP_Y, width=LW-79)
                self._send_btn.place(x=x0+LW-75, y=INP_Y, width=75)
                self._mute_c.place(y=nh-66)
        finally:
            del self._rb

    def _toggle_fullscreen(self):
        if self._is_fullscreen: self._exit_fullscreen()
        else:
            self._is_fullscreen = True
            self.root.attributes("-fullscreen", True)

    def _exit_fullscreen(self):
        self._is_fullscreen = False
        self.root.attributes("-fullscreen", False)

    # ── Image display ──────────────────────────────────────────────────────────
    def show_image(self, path: str):
        try:
            if self._img_frame:
                self._img_frame.destroy()
            self._original_img = Image.open(path)
            self._image_scale  = 0.5
            PX = int(self.W * 0.77)
            PW = self.W - PX - 10
            self._img_frame = tk.Frame(self.root, bg=T("PANEL"),
                                        highlightbackground=T("PRI"), highlightthickness=2)
            self._img_frame.place(x=PX, y=self.H-280, width=PW, height=240)
            tk.Label(self._img_frame, text="IMAGE", bg=T("PANEL"), fg=T("PRI"),
                      font=("Courier",9,"bold")).pack(pady=4)
            self._ic = tk.Canvas(self._img_frame, bg="#000000", highlightthickness=0)
            self._ic.pack(fill=tk.BOTH, expand=True, padx=4)
            cf = tk.Frame(self._img_frame, bg=T("PANEL"))
            cf.pack(fill=tk.X, pady=4)
            tk.Button(cf, text="-", bg="#000000", fg=T("PRI"), width=3,
                       command=self._img_sm).pack(side=tk.LEFT, padx=4)
            self._size_lbl = tk.Label(cf, text="50%", bg=T("PANEL"),
                                       fg=T("TEXT"), font=("Courier",8))
            self._size_lbl.pack(side=tk.LEFT)
            tk.Button(cf, text="+", bg="#000000", fg=T("PRI"), width=3,
                       command=self._img_bg).pack(side=tk.LEFT, padx=4)
            tk.Button(cf, text="✕", bg=T("RED"), fg="white", width=3,
                       command=self._hide_img).pack(side=tk.RIGHT, padx=4)
            self._upd_img()
        except Exception as e:
            print(f"[UI] img: {e}")

    def _upd_img(self):
        if not self._original_img: return
        w = int(self._original_img.width  * self._image_scale)
        h = int(self._original_img.height * self._image_scale)
        r = self._original_img.resize((w,h), Image.LANCZOS)
        self._disp_img = ImageTk.PhotoImage(r)
        self._ic.delete("all")
        self._ic.create_image(w//2, h//2, image=self._disp_img)
        self._size_lbl.config(text=f"{int(self._image_scale*100)}%")

    def _img_bg(self): self._image_scale = min(1.5, self._image_scale+0.1); self._upd_img()
    def _img_sm(self): self._image_scale = max(0.2, self._image_scale-0.1); self._upd_img()
    def _hide_img(self):
        if self._img_frame: self._img_frame.destroy(); self._img_frame = None

    def set_feature_status(self, f, v): pass

    # ── Animation ─────────────────────────────────────────────────────────────
    def _animate(self):
        self.tick += 1
        t, now = self.tick, time.time()

        if now - self.last_t > (0.06 if self.speaking else 0.30):
            if self.speaking:
                self.target_scale = random.uniform(1.08, 1.22)
                self.target_halo  = random.uniform(185, 248)
            elif self.muted:
                self.target_scale = random.uniform(0.997, 1.001)
                self.target_halo  = random.uniform(16, 28)
            else:
                self.target_scale = random.uniform(1.001, 1.008)
                self.target_halo  = random.uniform(48, 72)
            self.last_t = now

        sp = 0.52 if self.speaking else 0.20
        self.scale  += (self.target_scale - self.scale)  * sp
        self.halo_a += (self.target_halo  - self.halo_a) * sp

        for i, spd in enumerate([2.5,-1.8,3.2] if self.speaking else [0.8,-0.5,1.2]):
            self.rings_spin[i] = (self.rings_spin[i] + spd) % 360

        self.scan_angle  = (self.scan_angle  + (5.2 if self.speaking else 2.0)) % 360
        self.scan2_angle = (self.scan2_angle + (-3.1 if self.speaking else -1.2)) % 360

        pspd  = 7 if self.speaking else 3
        limit = self.FACE_SZ * 0.78
        new_p = [r+pspd for r in self.pulse_r if r+pspd < limit]
        if len(new_p) < 3 and random.random() < (0.09 if self.speaking else 0.025):
            new_p.append(0.0)
        self.pulse_r = new_p

        if self.speaking and random.random() < 0.4:
            self.particles.append(Particle(self.FCX, self.FCY, True))
        elif random.random() < 0.04:
            self.particles.append(Particle(self.FCX, self.FCY, False))
        self.particles = [p for p in self.particles if p.step()]
        if len(self.particles) > 90: self.particles = self.particles[-90:]

        for i in range(52):
            self._waveform[i] += (self._waveform_tgt[i] - self._waveform[i]) * 0.38

        if t % 40 == 0: self.status_blink = not self.status_blink
        if self._active_tool_t > 0: self._active_tool_t -= 1

        self._draw()
        self.anim.draw_all(self.W, self.H, t)  # overlay on top
        self.root.after(16, self._animate)

    # ── Draw ──────────────────────────────────────────────────────────────────
    def _draw(self):
        c = self.bg
        W, H   = self.W, self.H
        t      = self.tick
        FCX, FCY = self.FCX, self.FCY
        FW     = self.FACE_SZ
        pr     = self._hex_rgb(T("PRI"))
        c.delete("all")

        # Grid
        for x in range(0, W, 44):
            for y in range(0, H, 44):
                c.create_rectangle(x,y,x+1,y+1, fill=T("DIMMER"), outline="")

        # Scan line
        sl_y = (t*2) % H
        c.create_line(0, sl_y, W, sl_y, fill=T("DIMMER"), width=1)

        # Halo
        for r in range(int(FW*0.58), int(FW*0.28), -22):
            frac = 1.0 - (r - FW*0.28) / (FW*0.30)
            ga   = max(0, min(255, int(self.halo_a * 0.09 * frac)))
            if self.muted:
                c.create_oval(FCX-r,FCY-r,FCX+r,FCY+r, outline=self._ac(255,0,30,ga), width=2)
            else:
                c.create_oval(FCX-r,FCY-r,FCX+r,FCY+r, outline=self._ac(*pr,ga), width=2)

        # Pulse rings
        for pr2 in self.pulse_r:
            pa = max(0, int(210*(1-pr2/(FW*0.78))))
            col= self._ac(255,30,80,pa) if self.muted else self._ac(*pr,pa)
            c.create_oval(FCX-pr2,FCY-pr2,FCX+pr2,FCY+pr2, outline=col, width=2)

        # Spinning arcs
        for idx,(rf,ww,al,gp) in enumerate([(0.48,3,120,80),(0.40,2,80,55),(0.32,1,55,38)]):
            rr = int(FW*rf)
            ba = self.rings_spin[idx]
            av = max(0,min(255,int(self.halo_a*(1.0-idx*0.18))))
            cl = self._ac(255,30,80,av) if self.muted else self._ac(*pr,av)
            for s in range(360//(al+gp)):
                st = (ba + s*(al+gp)) % 360
                c.create_arc(FCX-rr,FCY-rr,FCX+rr,FCY+rr, start=st, extent=al,
                              outline=cl, width=ww, style="arc")

        # Scanner
        sr  = int(FW*0.50)
        sa  = min(255,int(self.halo_a*1.5))
        ae  = 82 if self.speaking else 46
        sc  = self._ac(255,30,80,sa) if self.muted else self._ac(*pr,sa)
        c.create_arc(FCX-sr,FCY-sr,FCX+sr,FCY+sr, start=self.scan_angle,  extent=ae, outline=sc, width=3, style="arc")
        c.create_arc(FCX-sr,FCY-sr,FCX+sr,FCY+sr, start=self.scan2_angle, extent=ae, outline=self._ac(255,100,0,sa//2), width=2, style="arc")

        # Tick marks
        t_o, t_i = int(FW*0.505), int(FW*0.480)
        am = self._ac(*pr, 140)
        for deg in range(0,360,10):
            rad = math.radians(deg)
            inn = t_i if deg%30==0 else t_i+6
            c.create_line(FCX+t_o*math.cos(rad), FCY-t_o*math.sin(rad),
                           FCX+inn*math.cos(rad), FCY-inn*math.sin(rad),
                           fill=am, width=2 if deg%90==0 else 1)

        # Crosshairs
        ch_r, gap = int(FW*0.52), int(FW*0.14)
        cha = self._ac(*pr, int(self.halo_a*0.5))
        for x1,y1,x2,y2 in [(FCX-ch_r,FCY,FCX-gap,FCY),(FCX+gap,FCY,FCX+ch_r,FCY),
                              (FCX,FCY-ch_r,FCX,FCY-gap),(FCX,FCY+gap,FCX,FCY+ch_r)]:
            c.create_line(x1,y1,x2,y2, fill=cha, width=1)

        # Corner brackets
        bl = 28; bc = self._ac(*pr,200)
        for bx,by,dx,dy in [(FCX-FW//2,FCY-FW//2,1,1),(FCX+FW//2,FCY-FW//2,-1,1),
                              (FCX-FW//2,FCY+FW//2,1,-1),(FCX+FW//2,FCY+FW//2,-1,-1)]:
            c.create_line(bx,by,bx+dx*bl,by, fill=bc, width=2)
            c.create_line(bx,by,bx,by+dy*bl, fill=bc, width=2)

        # Particles
        for p in self.particles:
            al = int(p.life*200)
            col= self._ac(*pr,al) if not self.muted else self._ac(255,50,100,al)
            r2 = max(1,int(p.size*p.life))
            c.create_oval(p.x-r2,p.y-r2,p.x+r2,p.y+r2, fill=col, outline="")

        # Face / Orb
        if self._has_face:
            fw = int(FW*self.scale)
            if self._face_cache is None or abs(self._face_cache[0]-self.scale)>0.004:
                sc2 = self._face_pil.resize((fw,fw), Image.BILINEAR)
                tk_i= ImageTk.PhotoImage(sc2)
                self._face_cache = (self.scale, tk_i)
            c.create_image(FCX, FCY, image=self._face_cache[1])
        else:
            orb = int(FW*0.27*self.scale)
            rgb = (255,30,80) if self.muted else pr
            for i in range(9,0,-1):
                r2 = int(orb*i/9); frac=i/9
                ga = max(0,min(255,int(self.halo_a*1.1*frac)))
                c.create_oval(FCX-r2,FCY-r2,FCX+r2,FCY+r2,
                               fill=self._ac(int(rgb[0]*frac),int(rgb[1]*frac),int(rgb[2]*frac),ga),
                               outline="")
            c.create_text(FCX,FCY, text=SYSTEM_NAME,
                           fill=self._ac(*pr,min(255,int(self.halo_a*2))),
                           font=("Courier",14,"bold"))

        # (Animation overlay draws itself on its own canvas)

        # Header
        c.create_rectangle(0,0,W,60, fill="#00080d", outline="")
        c.create_line(0,60,W,60, fill=T("MID"), width=1)
        c.create_text(FCX, 20, text=SYSTEM_NAME, fill=T("PRI"), font=("Courier",18,"bold"))
        c.create_text(FCX, 42, text="Advanced Personal AI — Linux Edition",
                       fill=T("MID"), font=("Courier",8))
        c.create_text(16, 30, text=f"◈ {MODEL_BADGE if 'MODEL_BADGE' in dir() else 'MK-37'}",
                       fill=T("DIM"), font=("Courier",8), anchor="w")
        c.create_text(int(W*0.74)-16, 30, text=time.strftime("%H:%M:%S"),
                       fill=T("PRI"), font=("Courier",14,"bold"), anchor="e")

        # Status
        sy = FCY + FW//2 + 38
        if self.muted:
            stat, sc3 = "⊘ MUTED", T("MUTED")
        elif self.speaking:
            stat, sc3 = "● SPEAKING", T("ACC")
        elif self._jarvis_state == "THINKING":
            s = "◈" if self.status_blink else "◇"
            stat, sc3 = f"{s} THINKING", T("ACC2")
        elif self._jarvis_state == "PROCESSING":
            s = "▷" if self.status_blink else "▶"
            stat, sc3 = f"{s} PROCESSING", T("ACC2")
        elif self._jarvis_state == "LISTENING":
            s = "●" if self.status_blink else "○"
            stat, sc3 = f"{s} LISTENING", T("GREEN")
        else:
            s = "●" if self.status_blink else "○"
            stat, sc3 = f"{s} {self.status_text}", T("PRI")
        c.create_text(FCX, sy, text=stat, fill=sc3, font=("Courier",12,"bold"))

        # Active tool badge
        if self._active_tool and self._active_tool_t > 0:
            al2 = min(255, self._active_tool_t*3)
            c.create_rectangle(FCX-100, sy+18, FCX+100, sy+34, fill="#001a22", outline=T("DIM"))
            c.create_text(FCX, sy+26, text=f"⚡ {self._active_tool}",
                           fill=self._ac(*pr,al2), font=("Courier",8))

        # Waveform
        wy  = sy + 44
        N   = 52; bw = 6; total = N*bw; wx0 = FCX - total//2
        for i in range(N):
            if self.muted:
                hb, cl = 2, T("MUTED")
            else:
                hb = max(2, int(self._waveform[i]))
                cl = T("PRI") if hb>14 else T("MID") if hb>7 else T("DIM")
            bx = wx0 + i*bw
            c.create_rectangle(bx, wy+24-hb, bx+bw-2, wy+24, fill=cl, outline="")

        # Footer
        c.create_rectangle(0,H-24,W,H, fill="#00080d", outline="")
        c.create_line(0,H-24,W,H-24, fill=T("DIM"), width=1)
        c.create_text(W-14,H-12, fill=T("DIM"), font=("Courier",7), anchor="e",
                       text="[F4]MUTE  [F11]FULLSCREEN  [F2]HISTORY  [F5]THEME")
        c.create_text(W//2, H-12, fill=T("DIM"), font=("Courier",7),
                       text=f"RAHUL {VERSION}  Theme:{self._current_theme}")

    # ── Log ───────────────────────────────────────────────────────────────────
    def write_log(self, text: str):
        self.typing_queue.append(text)
        ts = time.strftime("%H:%M")
        tl = text.lower()
        if tl.startswith("you:"):
            self._msg_count += 1
            self._convo_history.append({"time":ts,"role":"you","text":text[4:].strip()})
            self.set_state("PROCESSING")
        elif tl.startswith("rahul:") or tl.startswith("ai:"):
            pfx = "rahul:" if tl.startswith("rahul:") else "ai:"
            self._convo_history.append({"time":ts,"role":"ai","text":text[len(pfx):].strip()})
            self.set_state("SPEAKING")
        if len(self._convo_history) > 300:
            self._convo_history = self._convo_history[-300:]
        if not self.is_typing:
            self._start_typing()

    def _start_typing(self):
        if not self.typing_queue:
            self.is_typing = False
            if not self.speaking and not self.muted:
                self.set_state("LISTENING")
            return
        self.is_typing = True
        text = self.typing_queue.popleft()
        tl   = text.lower()
        tag  = ("you" if tl.startswith("you:") else
                "ai"  if (tl.startswith("rahul:") or tl.startswith("ai:")) else
                "tool" if "tool" in tl else
                "err"  if ("err" in tl or "error" in tl or "failed" in tl) else "sys")
        self.log_text.configure(state="normal")
        self._type_char(text, 0, tag)

    def _type_char(self, text, i, tag):
        if i < len(text):
            self.log_text.insert(tk.END, text[i], tag)
            self.log_text.see(tk.END)
            self.root.after(7, self._type_char, text, i+1, tag)
        else:
            self.log_text.insert(tk.END, "\n")
            self.log_text.configure(state="disabled")
            self.root.after(18, self._start_typing)

    def start_speaking(self):  self.set_state("SPEAKING")
    def stop_speaking(self):
        if not self.muted: self.set_state("LISTENING")

    # ── API / Setup (v5.0 — Ollama local) ────────────────────────────────────
    def _api_keys_exist(self):
        """v5: Just check if Ollama is running."""
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def wait_for_api_key(self):
        while not self._api_key_ready:
            time.sleep(0.2)

    def _show_setup_ui(self):
        """v5.0 Setup — Ollama local model selection."""
        self.setup_frame = tk.Frame(
            self.root, bg="#00080d",
            highlightbackground=T("PRI"), highlightthickness=2,
        )
        self.setup_frame.place(relx=0.40, rely=0.5, anchor="center")

        tk.Label(self.setup_frame, text="◈  RAHUL  v5.0  SETUP",
                 fg=T("PRI"), bg="#00080d",
                 font=("Courier", 15, "bold")).pack(pady=(22, 4))
        tk.Label(self.setup_frame,
                 text="Local AI  •  Ollama  •  No API Key Needed",
                 fg=T("MID"), bg="#00080d",
                 font=("Courier", 9)).pack(pady=(0, 16))

        # Status
        self._status_var = tk.StringVar(value="Checking Ollama…")
        tk.Label(self.setup_frame, textvariable=self._status_var,
                 fg=T("ACC2"), bg="#00080d",
                 font=("Courier", 9)).pack(pady=(0, 12))

        # Model list
        tk.Label(self.setup_frame, text="SELECT MODEL",
                 fg=T("DIM"), bg="#00080d",
                 font=("Courier", 8)).pack(pady=(0, 4))

        self._model_var = tk.StringVar(value="llama3")
        self._model_entry = tk.Entry(
            self.setup_frame, textvariable=self._model_var,
            fg=T("TEXT"), bg="#000d12",
            insertbackground=T("TEXT"), borderwidth=0,
            font=("Courier", 11), width=30,
        )
        self._model_entry.pack(pady=(0, 8))

        self._models_frame = tk.Frame(self.setup_frame, bg="#00080d")
        self._models_frame.pack(pady=(0, 16))
        tk.Label(self._models_frame, text="Available models loading…",
                 fg=T("DIM"), bg="#00080d",
                 font=("Courier", 8)).pack()

        tk.Frame(self.setup_frame, bg=T("DIM"), height=1).pack(fill="x", padx=24, pady=(0, 14))

        tk.Button(
            self.setup_frame, text="▸  START RAHUL v5.0",
            command=self._save_api,
            bg="#000000", fg=T("PRI"),
            activebackground=T("DIM"),
            font=("Courier", 12, "bold"),
            borderwidth=0, pady=12, padx=30, cursor="hand2",
        ).pack(pady=(0, 8))

        tk.Label(self.setup_frame,
                 text="Ollama not installed? → ollama.ai",
                 fg=T("DIM"), bg="#00080d",
                 font=("Courier", 7)).pack(pady=(0, 14))

        # Check Ollama in background
        threading.Thread(target=self._check_ollama_setup, daemon=True).start()

    def _check_ollama_setup(self):
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if models:
                    self._status_var.set(f"✓ Ollama running — {len(models)} models")
                    # Show model buttons
                    for w in self._models_frame.winfo_children():
                        w.destroy()
                    for m in models[:6]:
                        tk.Button(
                            self._models_frame, text=m[:35],
                            command=lambda mn=m: self._model_var.set(mn),
                            bg="#001520", fg=T("PRI"),
                            font=("Courier", 8), borderwidth=0,
                            cursor="hand2", padx=6, pady=3,
                        ).pack(side="left", padx=2)
                    self._model_var.set(models[0])
                else:
                    self._status_var.set("⚠ Ollama running but no models!")
            else:
                self._status_var.set("✗ Ollama not running — start with: ollama serve")
        except Exception:
            self._status_var.set("✗ Ollama not found — install: ollama.ai")

    def _save_api(self):
        model = self._model_var.get().strip()
        if not model:
            return

        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(API_FILE, "w") as f:
            json.dump({"ollama_model": model, "tts": True}, f, indent=4)

        self.setup_frame.destroy()
        self._api_key_ready = True
        self.set_state("LISTENING")
        self.write_log(f"SYS: RAHUL v5.0 online! Model: {model}")
        self.write_log("SYS: Local AI ready — type ya bol ke command do!")

MODEL_BADGE = "OLLAMA LOCAL"
