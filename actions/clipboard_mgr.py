"""clipboard_mgr.py"""
import subprocess


def clipboard_mgr(parameters: dict, player=None) -> str:
    action = parameters.get("action", "read")
    text   = parameters.get("text", "")

    tools_read  = ["xclip -o -selection clipboard", "xsel --clipboard --output", "wl-paste"]
    tools_write = ["xclip -selection clipboard", "xsel --clipboard --input", "wl-copy"]

    if action == "read":
        for cmd in tools_read:
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if r.returncode == 0 and r.stdout:
                    return f"Clipboard: {r.stdout[:500]}"
            except Exception:
                pass
        return "Could not read clipboard. Install: sudo apt install xclip"

    elif action == "write":
        if not text:
            return "No text to write."
        for cmd in tools_write:
            try:
                r = subprocess.run(cmd, shell=True, input=text, capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    return f"Copied to clipboard: {text[:50]}"
            except Exception:
                pass
        return "Could not write to clipboard."

    elif action == "clear":
        for cmd in tools_write:
            try:
                subprocess.run(cmd, shell=True, input="", capture_output=True, text=True, timeout=5)
            except Exception:
                pass
        return "Clipboard cleared."
    return f"Unknown action: {action}"
