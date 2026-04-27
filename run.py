"""
run.py — RAHUL Advanced AI v5.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ollama local models  •  No API key  •  No rate limits
Indian male TTS      •  Voice input  •  Text input
Fast chat            •  Animation fixed
"""
import sys, json, threading, traceback, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from ui import RahulUI
from core.ollama_engine import is_running, best_model, list_models
from core.brain         import RAHULBrain
from core.memory_manager import init_dirs, update_memory
from core.tts_engine    import speak, stop as tts_stop
from core import voice_input

# ── Actions ───────────────────────────────────────────────────────────────────
from actions.open_app         import open_app
from actions.web_search       import web_search as web_search_action
from actions.weather          import weather_action
from actions.browser_control  import browser_control
from actions.file_controller  import file_controller
from actions.code_helper      import code_helper
from actions.screen_process   import screen_process
from actions.reminder         import reminder_action
from actions.send_message     import send_message
from actions.system_control   import system_control
from actions.youtube          import youtube_action
from actions.news_reader      import news_reader
from actions.calculator       import calculator
from actions.translate        import translate_action
from actions.image_gen        import image_gen
from actions.pdf_reader       import pdf_reader
from actions.email_action     import email_action
from actions.clipboard_mgr    import clipboard_mgr
from actions.process_mgr      import process_mgr
from actions.network_info     import network_info
from actions.animation_engine import animation_engine

# ── Tool schema for Ollama (OpenAI-compatible format) ─────────────────────────
TOOLS = [
    {"type":"function","function":{"name":"open_app","description":"Open any application.",
     "parameters":{"type":"object","properties":{"app_name":{"type":"string"},"args":{"type":"string"}},"required":["app_name"]}}},
    {"type":"function","function":{"name":"web_search","description":"Search the web for any information.",
     "parameters":{"type":"object","properties":{"query":{"type":"string"},"mode":{"type":"string"},"show_on_screen":{"type":"boolean"}},"required":["query"]}}},
    {"type":"function","function":{"name":"weather_report","description":"Get weather for a city. Shows animated card.",
     "parameters":{"type":"object","properties":{"city":{"type":"string"},"show_animation":{"type":"boolean"}},"required":["city"]}}},
    {"type":"function","function":{"name":"browser_control","description":"Control browser: go_to, search, click, screenshot.",
     "parameters":{"type":"object","properties":{"action":{"type":"string"},"url":{"type":"string"},"query":{"type":"string"},"text":{"type":"string"}},"required":["action"]}}},
    {"type":"function","function":{"name":"file_controller","description":"Manage files: list, read, write, create, delete.",
     "parameters":{"type":"object","properties":{"action":{"type":"string"},"path":{"type":"string"},"content":{"type":"string"},"name":{"type":"string"}},"required":["action"]}}},
    {"type":"function","function":{"name":"code_helper","description":"Write, run, debug code.",
     "parameters":{"type":"object","properties":{"action":{"type":"string"},"language":{"type":"string"},"code":{"type":"string"},"file_path":{"type":"string"}},"required":["action"]}}},
    {"type":"function","function":{"name":"screen_process","description":"Capture and analyze screen with AI vision.",
     "parameters":{"type":"object","properties":{"angle":{"type":"string"},"text":{"type":"string"}},"required":["text"]}}},
    {"type":"function","function":{"name":"system_control","description":"Control system: volume, brightness, screenshot, wifi.",
     "parameters":{"type":"object","properties":{"action":{"type":"string"},"value":{"type":"string"},"state":{"type":"string"}},"required":["action"]}}},
    {"type":"function","function":{"name":"youtube","description":"Search and play YouTube videos.",
     "parameters":{"type":"object","properties":{"action":{"type":"string"},"query":{"type":"string"},"url":{"type":"string"}}}}},
    {"type":"function","function":{"name":"news_reader","description":"Get latest news with animated ticker.",
     "parameters":{"type":"object","properties":{"topic":{"type":"string"},"count":{"type":"integer"},"show_animation":{"type":"boolean"}},"required":["topic"]}}},
    {"type":"function","function":{"name":"calculator","description":"Math calculations and unit conversions.",
     "parameters":{"type":"object","properties":{"expression":{"type":"string"},"show_steps":{"type":"boolean"}},"required":["expression"]}}},
    {"type":"function","function":{"name":"translate","description":"Translate text between languages.",
     "parameters":{"type":"object","properties":{"text":{"type":"string"},"target_lang":{"type":"string"}},"required":["text","target_lang"]}}},
    {"type":"function","function":{"name":"image_gen","description":"Generate AI image (free, Pollinations).",
     "parameters":{"type":"object","properties":{"prompt":{"type":"string"},"style":{"type":"string"}},"required":["prompt"]}}},
    {"type":"function","function":{"name":"pdf_reader","description":"Read and summarize PDF files.",
     "parameters":{"type":"object","properties":{"action":{"type":"string"},"file_path":{"type":"string"},"query":{"type":"string"}},"required":["action","file_path"]}}},
    {"type":"function","function":{"name":"email_action","description":"Open Gmail compose in browser.",
     "parameters":{"type":"object","properties":{"to":{"type":"string"},"subject":{"type":"string"},"body":{"type":"string"}},"required":["to","subject","body"]}}},
    {"type":"function","function":{"name":"send_message","description":"Send Telegram or WhatsApp message.",
     "parameters":{"type":"object","properties":{"receiver":{"type":"string"},"message_text":{"type":"string"},"platform":{"type":"string"}},"required":["receiver","message_text","platform"]}}},
    {"type":"function","function":{"name":"reminder","description":"Set a timed reminder.",
     "parameters":{"type":"object","properties":{"time":{"type":"string"},"message":{"type":"string"}},"required":["time","message"]}}},
    {"type":"function","function":{"name":"clipboard_mgr","description":"Read or write clipboard.",
     "parameters":{"type":"object","properties":{"action":{"type":"string"},"text":{"type":"string"}},"required":["action"]}}},
    {"type":"function","function":{"name":"process_mgr","description":"List or kill Linux processes.",
     "parameters":{"type":"object","properties":{"action":{"type":"string"},"name":{"type":"string"}},"required":["action"]}}},
    {"type":"function","function":{"name":"network_info","description":"Network: IP, ping, speed, wifi.",
     "parameters":{"type":"object","properties":{"action":{"type":"string"},"host":{"type":"string"}},"required":["action"]}}},
    {"type":"function","function":{"name":"animation_engine",
     "description":"Show animated content ON SCREEN: card, list, chart, steps, news_ticker, comparison, weather, typewriter, countdown, image. ALWAYS use to visually present information.",
     "parameters":{"type":"object","properties":{"type":{"type":"string"},"title":{"type":"string"},"content":{"type":"string"},"color":{"type":"string"},"duration":{"type":"integer"},"image_path":{"type":"string"}},"required":["type","title"]}}},
    {"type":"function","function":{"name":"save_memory","description":"Save user facts permanently. Call silently.",
     "parameters":{"type":"object","properties":{"category":{"type":"string"},"key":{"type":"string"},"value":{"type":"string"}},"required":["category","key","value"]}}},
    {"type":"function","function":{"name":"shutdown_rahul","description":"Shutdown RAHUL when user says bye/exit.",
     "parameters":{"type":"object","properties":{}}}},
]


# ── Tool executor ─────────────────────────────────────────────────────────────
def execute_tool(name: str, args: dict, ui: RahulUI) -> str:
    print(f"[RAHUL] ⚡ {name}  {str(args)[:60]}")
    try:
        if name == "save_memory":
            cat, key, val = args.get("category","notes"), args.get("key",""), args.get("value","")
            if key and val:
                update_memory({cat: {key: {"value": val}}})
            return "Saved."

        elif name == "shutdown_rahul":
            ui.write_log("SYS: Shutting down RAHUL…")
            def _bye():
                import time; time.sleep(1); os._exit(0)
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
        return f"Error: {e}"


# ── Main app ──────────────────────────────────────────────────────────────────
class RAHULApp:
    def __init__(self, ui: RahulUI):
        self.ui = ui
        self.brain = RAHULBrain(
            ui=ui,
            tool_executor=lambda n, a: execute_tool(n, a, ui),
            tools_schema=TOOLS,
        )
        ui.on_text_command = self._on_text
        ui.on_voice_toggle = self._on_voice_toggle

    def _on_text(self, text: str):
        # Stop any ongoing TTS
        tts_stop()
        threading.Thread(target=self.brain.process, args=(text,), daemon=True).start()

    def _on_voice_toggle(self, active: bool):
        if active:
            voice_input.start_listening(
                on_text=self._on_text,
                ui=self.ui,
            )
        else:
            voice_input.stop_listening()

    def start(self):
        init_dirs()

        if not is_running():
            self.ui.write_log("ERR: Ollama not running!")
            self.ui.write_log("SYS: Start with: ollama serve")
            self.ui.write_log("SYS: Install:    https://ollama.ai")
            self.ui.set_state("INITIALISING")
            return

        model = best_model()
        models = list_models()
        self.ui.write_log(f"SYS: ✓ RAHUL v5.0 online!")
        self.ui.write_log(f"SYS: Model: {model}")
        self.ui.write_log(f"SYS: Available: {', '.join(models[:4])}")
        self.ui.write_log("SYS: Type karo ya VOICE button dabao!")
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
