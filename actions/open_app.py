"""open_app.py — Cross-platform app launcher"""
import subprocess, shutil, os, platform

SYSTEM = platform.system().lower()

APP_ALIASES_LINUX = {
    "firefox": "firefox", "chrome": "google-chrome",
    "terminal": "x-terminal-emulator", "files": "nautilus",
    "calculator": "gnome-calculator", "vscode": "code",
    "notepad": "gedit", "vlc": "vlc",
    "whatsapp": "firefox --new-tab https://web.whatsapp.com",
    "youtube":  "firefox --new-tab https://youtube.com",
    "gmail":    "firefox --new-tab https://mail.google.com",
}

APP_ALIASES_WINDOWS = {
    "firefox":    "firefox",
    "chrome":     "chrome",
    "notepad":    "notepad",
    "calculator": "calc",
    "terminal":   "cmd",
    "powershell": "powershell",
    "explorer":   "explorer",
    "paint":      "mspaint",
    "vscode":     "code",
    "vlc":        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "spotify":    "spotify",
    "discord":    "discord",
    "task manager": "taskmgr",
    "whatsapp":   "start https://web.whatsapp.com",
    "youtube":    "start https://youtube.com",
    "gmail":      "start https://mail.google.com",
    "maps":       "start https://maps.google.com",
}


def open_app(parameters: dict, player=None) -> str:
    name = parameters.get("app_name", "").lower().strip()
    args = parameters.get("args", "")

    if SYSTEM == "windows":
        cmd = APP_ALIASES_WINDOWS.get(name, name)
        if args:
            cmd = f"{cmd} {args}"
        try:
            if cmd.startswith("start "):
                os.system(cmd)
            else:
                subprocess.Popen(cmd, shell=True,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            return f"Opened: {name}"
        except Exception as e:
            return f"Could not open {name}: {e}"
    else:
        cmd = APP_ALIASES_LINUX.get(name, name)
        if args:
            cmd = f"{cmd} {args}"
        try:
            subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return f"Opened: {name}"
        except Exception as e:
            return f"Could not open {name}: {e}"
