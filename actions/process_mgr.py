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
        lines = [f"  {p[0]:6d}  {p[1][:22]:<24} CPU:{p[2]:.1f}%  MEM:{p[3]:.1f}%"
                 for p in sorted(procs, key=lambda x: -x[2])[:15]]
        return "Processes (top CPU):\n" + "\n".join(lines)

    elif action == "kill":
        if not name: return "Provide name or PID."
        killed = []
        for p in psutil.process_iter(["pid","name"]):
            try:
                if p.name().lower() == name.lower() or str(p.pid) == name:
                    p.terminate(); killed.append(f"{p.name()}({p.pid})")
            except Exception: pass
        return f"Terminated: {', '.join(killed)}" if killed else f"Not found: {name}"

    elif action in ("top_cpu","top_mem"):
        key = "cpu_percent" if action == "top_cpu" else "memory_percent"
        procs = sorted(psutil.process_iter(["pid","name",key]),
                       key=lambda p: p.info.get(key) or 0, reverse=True)
        lines = [f"  {p.pid:5d}  {p.name()[:26]:<28} {p.info.get(key,0):.1f}%" for p in procs[:10]]
        return f"Top {action.split('_')[1].upper()}:\n" + "\n".join(lines)

    elif action == "info":
        import datetime
        for p in psutil.process_iter(["pid","name","status","cpu_percent","memory_percent","create_time"]):
            if p.name().lower() == name.lower() or str(p.pid) == name:
                ct = datetime.datetime.fromtimestamp(p.info["create_time"]).strftime("%H:%M:%S")
                return (f"Process: {p.name()}\nPID: {p.pid}\nStatus: {p.info['status']}\n"
                        f"CPU: {p.info['cpu_percent']}%\nMem: {p.info['memory_percent']:.2f}%\nStarted: {ct}")
        return f"Not found: {name}"
    return f"Unknown: {action}"
