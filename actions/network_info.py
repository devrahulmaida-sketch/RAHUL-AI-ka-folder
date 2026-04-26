"""network_info.py"""
import subprocess


def _run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return str(e)


def network_info(parameters: dict, player=None) -> str:
    action = parameters.get("action", "ip")
    host   = parameters.get("host", "8.8.8.8")

    if action == "ip":
        local  = _run("hostname -I | awk '{print $1}'")
        public = _run("curl -s --max-time 5 https://api.ipify.org")
        return f"Local IP:  {local}\nPublic IP: {public}"
    elif action == "ping":
        return f"Ping {host}:\n{_run(f'ping -c 4 {host}')}"
    elif action == "wifi_list":
        return f"WiFi:\n{_run('nmcli dev wifi list 2>/dev/null')[:800]}"
    elif action == "ports":
        return f"Open ports:\n{_run('ss -tlnp | head -20')}"
    elif action == "speedtest":
        return f"Speed:\n{_run('speedtest-cli --simple 2>/dev/null || echo install: pip install speedtest-cli')}"
    return f"Unknown: {action}"
