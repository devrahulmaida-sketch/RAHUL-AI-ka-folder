"""clipboard_mgr.py"""
import subprocess, os


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
        return "Could not read clipboard. Install xclip: sudo apt install xclip"

    elif action == "write":
        if not text:
            return "No text to write."
        for cmd in tools_write:
            try:
                r = subprocess.run(cmd, shell=True, input=text,
                                   capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    return f"Copied to clipboard: {text[:50]}"
            except Exception:
                pass
        return "Could not write to clipboard."

    elif action == "clear":
        for cmd in tools_write:
            try:
                subprocess.run(cmd, shell=True, input="",
                               capture_output=True, text=True, timeout=5)
            except Exception:
                pass
        return "Clipboard cleared."

    return f"Unknown action: {action}"


# ─────────────────────────────────────────────────────────────────────────────

"""process_mgr.py"""


def process_mgr(parameters: dict, player=None) -> str:
    action = parameters.get("action", "list")
    name   = parameters.get("name", "")

    try:
        import psutil
    except ImportError:
        return "psutil not installed. Run: pip install psutil"

    if action == "list":
        procs = [(p.pid, p.name(), p.cpu_percent(), p.memory_percent())
                 for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"])
                 if p.info["name"]]
        lines = [f"  {p[0]:6d}  {p[1][:20]:<22} CPU:{p[2]:.1f}%  MEM:{p[3]:.1f}%"
                 for p in sorted(procs, key=lambda x: -x[2])[:15]]
        return "Running processes (top CPU):\n" + "\n".join(lines)

    elif action == "top_cpu":
        procs = sorted(psutil.process_iter(["pid","name","cpu_percent"]),
                       key=lambda p: p.info["cpu_percent"] or 0, reverse=True)
        lines = [f"  {p.pid:5d}  {p.name()[:25]:<26} {p.info['cpu_percent']:.1f}%" for p in procs[:10]]
        return "Top CPU:\n" + "\n".join(lines)

    elif action == "top_mem":
        procs = sorted(psutil.process_iter(["pid","name","memory_percent"]),
                       key=lambda p: p.info["memory_percent"] or 0, reverse=True)
        lines = [f"  {p.pid:5d}  {p.name()[:25]:<26} {p.info['memory_percent']:.2f}%" for p in procs[:10]]
        return "Top Memory:\n" + "\n".join(lines)

    elif action == "kill":
        if not name:
            return "Provide process name or PID."
        killed = []
        for p in psutil.process_iter(["pid","name"]):
            try:
                if p.name().lower() == name.lower() or str(p.pid) == name:
                    p.terminate()
                    killed.append(f"{p.name()} ({p.pid})")
            except Exception:
                pass
        return f"Terminated: {', '.join(killed)}" if killed else f"Process not found: {name}"

    elif action == "info":
        for p in psutil.process_iter(["pid","name","status","cpu_percent","memory_percent","create_time"]):
            if p.name().lower() == name.lower() or str(p.pid) == name:
                import datetime
                ct = datetime.datetime.fromtimestamp(p.info["create_time"]).strftime("%H:%M:%S")
                return (f"Process: {p.name()}\n"
                        f"PID:     {p.pid}\n"
                        f"Status:  {p.info['status']}\n"
                        f"CPU:     {p.info['cpu_percent']}%\n"
                        f"Memory:  {p.info['memory_percent']:.2f}%\n"
                        f"Started: {ct}")
        return f"Process not found: {name}"

    return f"Unknown action: {action}"


# ─────────────────────────────────────────────────────────────────────────────

"""network_info.py"""


def network_info(parameters: dict, player=None) -> str:
    action = parameters.get("action", "ip")
    host   = parameters.get("host", "8.8.8.8")

    import subprocess

    def run(cmd):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            return (r.stdout + r.stderr).strip()
        except Exception as e:
            return str(e)

    if action == "ip":
        local  = run("hostname -I | awk '{print $1}'")
        public = run("curl -s --max-time 5 https://api.ipify.org")
        return f"Local IP:  {local}\nPublic IP: {public}"

    elif action == "ping":
        result = run(f"ping -c 4 {host}")
        return f"Ping {host}:\n{result}"

    elif action == "wifi_list":
        result = run("nmcli dev wifi list 2>/dev/null || iwlist scan 2>/dev/null | grep ESSID")
        return f"WiFi networks:\n{result[:1000]}"

    elif action == "ports":
        result = run("ss -tlnp | head -20")
        return f"Open ports:\n{result}"

    elif action == "speedtest":
        result = run("speedtest-cli --simple 2>/dev/null || echo 'Install: pip install speedtest-cli'")
        return f"Speed test:\n{result}"

    return f"Unknown action: {action}"
