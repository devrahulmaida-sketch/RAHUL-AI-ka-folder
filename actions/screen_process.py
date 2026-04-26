"""
screen_process.py — Cross-platform (Linux + Windows + macOS)
"""
import os, time, platform
from pathlib import Path

SYSTEM = platform.system().lower()


def screen_process(parameters: dict, player=None) -> str:
    angle = parameters.get("angle", "screen")
    text  = parameters.get("text", "What do you see?")

    img_path = _capture_camera() if angle == "camera" else _capture_screen()

    if not img_path or not Path(img_path).exists():
        if player: player.write_log("ERR: Screen capture failed.")
        return "Screen capture failed."

    if player:
        player.show_image(img_path)
        player.write_log("SYS: Screen captured — analyzing…")

    result = _analyze_openrouter(img_path, text) or _analyze_gemini(img_path, text)
    result = result or "Vision analysis failed — check OpenRouter/Gemini key in .env"

    if player:
        player.write_log(f"RAHUL: {result[:300]}")
    return result


def _capture_screen() -> str:
    ts = time.strftime("%Y%m%d_%H%M%S")

    if SYSTEM == "windows":
        path = os.path.join(os.environ.get("TEMP", "C:\\Temp"), f"screen_{ts}.png")
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(path)
            return path
        except Exception:
            # PowerShell fallback
            script = (
                f'Add-Type -AssemblyName System.Windows.Forms,System.Drawing; '
                f'$s=[System.Windows.Forms.Screen]::PrimaryScreen; '
                f'$b=New-Object System.Drawing.Bitmap($s.Bounds.Width,$s.Bounds.Height); '
                f'$g=[System.Drawing.Graphics]::FromImage($b); '
                f'$g.CopyFromScreen($s.Bounds.Location,[System.Drawing.Point]::Empty,$s.Bounds.Size); '
                f'$b.Save("{path}"); $g.Dispose(); $b.Dispose()'
            )
            os.system(f'powershell -Command "{script}"')
            return path if Path(path).exists() else ""

    elif SYSTEM == "darwin":
        path = f"/tmp/screen_{ts}.png"
        os.system(f"screencapture -x {path}")
        return path if Path(path).exists() else ""

    else:  # Linux
        path = f"/tmp/screen_{ts}.png"
        for tool in [f"scrot {path}", f"import -window root {path}",
                     f"gnome-screenshot -f {path}", f"maim {path}"]:
            if os.system(f"which {tool.split()[0]} > /dev/null 2>&1") == 0:
                os.system(tool)
                if Path(path).exists():
                    return path
        return ""


def _capture_camera() -> str:
    ts   = time.strftime("%Y%m%d_%H%M%S")
    path = (os.path.join(os.environ.get("TEMP","C:\\Temp"), f"cam_{ts}.jpg")
            if SYSTEM == "windows" else f"/tmp/camera_{ts}.jpg")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(path, frame)
                return path
    except ImportError:
        pass
    return ""


def _analyze_openrouter(img_path: str, prompt: str) -> str:
    try:
        import base64, requests, os
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("OPENROUTER_KEY", "")
        if not key:
            return ""
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        for model in ["meta-llama/llama-3.2-11b-vision-instruct:free",
                      "qwen/qwen2-vl-7b-instruct:free"]:
            try:
                resp = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}",
                             "Content-Type": "application/json"},
                    json={"model": model, "max_tokens": 512,
                          "messages": [{"role": "user", "content": [
                              {"type": "image_url",
                               "image_url": {"url": f"data:image/png;base64,{b64}"}},
                              {"type": "text", "text": prompt}
                          ]}]},
                    timeout=30,
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
            except Exception:
                continue
    except Exception:
        pass
    return ""


def _analyze_gemini(img_path: str, prompt: str) -> str:
    try:
        import base64, requests, os
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("GEMINI_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        if not key:
            return ""
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={key}",
            json={"contents": [{"parts": [
                {"inline_data": {"mime_type": "image/png", "data": b64}},
                {"text": prompt}
            ]}]},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass
    return ""
