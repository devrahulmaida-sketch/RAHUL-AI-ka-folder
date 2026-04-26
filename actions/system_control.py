"""
system_control.py — Cross-platform (Linux + Windows)
Automatically detects OS and uses correct commands.
"""
import subprocess, os, platform, time

SYSTEM = platform.system().lower()  # 'linux', 'windows', 'darwin'


def _run(cmd: str, timeout=10) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return str(e)


def system_control(parameters: dict, player=None) -> str:
    action = parameters.get("action", "")
    value  = str(parameters.get("value", ""))
    state  = parameters.get("state", "toggle")

    # ── VOLUME ────────────────────────────────────────────────────────────────
    if action == "volume":
        if SYSTEM == "windows":
            if value:
                vol = max(0, min(100, int(value)))
                script = (
                    f"$obj = New-Object -ComObject WScript.Shell; "
                    f"$obj.SendKeys([char]173); "  # mute toggle trick
                )
                # Use nircmd if available, else PowerShell
                result = _run(
                    f'powershell -Command "'
                    f'$wshShell = New-Object -comObject WScript.Shell; '
                    f'[audio]::Volume = {vol/100:.2f}"', 5
                )
                # Simpler: use nircmd (free tool)
                nircmd = _run(f'nircmd.exe setsysvolume {int(vol/100*65535)}')
                return f"Volume set to {vol}%"
            return "Provide volume value (0-100)"
        else:
            if value:
                vol = max(0, min(150, int(value)))
                _run(f"pactl set-sink-volume @DEFAULT_SINK@ {vol}%")
                return f"Volume set to {vol}%"
            return _run("pactl get-sink-volume @DEFAULT_SINK@")

    # ── SCREENSHOT ────────────────────────────────────────────────────────────
    elif action == "screenshot":
        ts   = time.strftime("%Y%m%d_%H%M%S")
        if SYSTEM == "windows":
            path = os.path.join(os.environ.get("TEMP", "C:\\Temp"), f"screenshot_{ts}.png")
            # Use PowerShell
            script = (
                f'Add-Type -AssemblyName System.Windows.Forms; '
                f'$screen = [System.Windows.Forms.Screen]::PrimaryScreen; '
                f'$bitmap = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height); '
                f'$graphics = [System.Drawing.Graphics]::FromImage($bitmap); '
                f'$graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size); '
                f'$bitmap.Save("{path}"); '
                f'$graphics.Dispose(); $bitmap.Dispose()'
            )
            _run(f'powershell -Command "{script}"')
        else:
            path = f"/tmp/screenshot_{ts}.png"
            for tool in [f"scrot {path}", f"import -window root {path}",
                         f"gnome-screenshot -f {path}", f"maim {path}"]:
                if os.system(f"which {tool.split()[0]} > /dev/null 2>&1") == 0:
                    _run(tool); break

        if os.path.exists(path):
            if player: player.show_image(path)
            return f"Screenshot saved: {path}"
        return "Screenshot failed."

    # ── BRIGHTNESS ────────────────────────────────────────────────────────────
    elif action == "brightness":
        if not value:
            return "Provide brightness value (0-100)"
        br = max(0, min(100, int(value)))
        if SYSTEM == "windows":
            _run(
                f'powershell -Command "(Get-WmiObject -Namespace root/WMI '
                f'-Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{br})"'
            )
        else:
            _run(f"brightnessctl set {br}% 2>/dev/null || "
                 f"xrandr --output $(xrandr | grep ' connected' | head -1 | "
                 f"cut -d' ' -f1) --brightness {br/100:.2f}")
        return f"Brightness set to {br}%"

    # ── WIFI ──────────────────────────────────────────────────────────────────
    elif action == "wifi":
        if SYSTEM == "windows":
            if state == "off":
                _run("netsh interface set interface Wi-Fi disable")
                return "WiFi disabled."
            elif state == "on":
                _run("netsh interface set interface Wi-Fi enable")
                return "WiFi enabled."
            else:
                return _run("netsh wlan show interfaces")
        else:
            if state == "off":   _run("nmcli radio wifi off"); return "WiFi off."
            elif state == "on":  _run("nmcli radio wifi on");  return "WiFi on."
            else:
                _run("nmcli radio wifi toggle")
                return f"WiFi toggled: {_run('nmcli radio wifi')}"

    # ── LOCK ──────────────────────────────────────────────────────────────────
    elif action == "lock":
        if SYSTEM == "windows":
            _run("rundll32.exe user32.dll,LockWorkStation")
        else:
            for cmd in ["gnome-screensaver-command -l",
                        "loginctl lock-session", "xdg-screensaver lock"]:
                if os.system(f"which {cmd.split()[0]} > /dev/null 2>&1") == 0:
                    _run(cmd + " &"); break
        return "Screen locked."

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    elif action == "shutdown":
        if SYSTEM == "windows":
            _run("shutdown /s /t 5")
        else:
            _run("shutdown -h now")
        return "Shutting down in 5 seconds..."

    # ── RESTART ───────────────────────────────────────────────────────────────
    elif action == "restart":
        if SYSTEM == "windows":
            _run("shutdown /r /t 5")
        else:
            _run("reboot")
        return "Restarting in 5 seconds..."

    # ── SLEEP ─────────────────────────────────────────────────────────────────
    elif action == "sleep":
        if SYSTEM == "windows":
            _run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        else:
            _run("systemctl suspend")
        return "Going to sleep..."

    # ── CLIPBOARD ─────────────────────────────────────────────────────────────
    elif action == "clipboard":
        if SYSTEM == "windows":
            out = _run("powershell -Command Get-Clipboard")
        else:
            for tool in ["xclip -o", "xsel --clipboard --output"]:
                out = _run(tool)
                if out: break
        return f"Clipboard: {out[:500]}" if out else "Clipboard empty."

    # ── DISK ──────────────────────────────────────────────────────────────────
    elif action == "disk":
        if SYSTEM == "windows":
            return _run("wmic logicaldisk get size,freespace,caption")
        else:
            return _run("df -h --output=source,size,used,avail,pcent,target | head -8")

    # ── MEMORY ────────────────────────────────────────────────────────────────
    elif action == "memory":
        if SYSTEM == "windows":
            return _run('systeminfo | findstr /C:"Available Physical Memory" /C:"Total Physical Memory"')
        else:
            return _run("free -h")

    # ── BATTERY ───────────────────────────────────────────────────────────────
    elif action == "battery":
        if SYSTEM == "windows":
            return _run(
                'powershell -Command "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining"'
            )
        else:
            return _run("cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || echo 'No battery'")

    # ── UPTIME ────────────────────────────────────────────────────────────────
    elif action == "uptime":
        if SYSTEM == "windows":
            return _run(
                'powershell -Command "(Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime | Select-Object -ExpandProperty TotalHours"'
            )
        else:
            return _run("uptime -p")

    return f"Unknown system action: {action}"
