"""reminder.py — Set reminders using Linux 'at' command or notify-send"""
import os, subprocess, threading, time


def reminder_action(parameters: dict, player=None) -> str:
    msg      = parameters.get("message", "Reminder!")
    rem_time = parameters.get("time", "")
    rem_date = parameters.get("date", "")

    if not rem_time:
        return "Please provide a time for the reminder."

    # Build 'at' command time string
    at_time = rem_time
    if rem_date:
        at_time = f"{rem_time} {rem_date}"

    # Check if 'at' is available
    if os.system("which at > /dev/null 2>&1") == 0:
        at_cmd = f'echo "notify-send \\"RAHUL Reminder\\" \\"{msg}\\"" | at {at_time} 2>/dev/null'
        result = os.system(at_cmd)
        if result == 0:
            return f"Reminder set for {at_time}: {msg}"

    # Fallback: background thread timer
    def _parse_seconds():
        """Simple time parser — handles HH:MM format for today."""
        try:
            from datetime import datetime
            now = datetime.now()
            h, m = map(int, rem_time.split(":"))
            target = now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (target - now).total_seconds()
            return max(0, diff)
        except Exception:
            return 60  # default 1 minute

    def _remind():
        secs = _parse_seconds()
        time.sleep(secs)
        # Try notify-send
        os.system(f'notify-send "RAHUL Reminder" "{msg}" --icon=dialog-information')
        if player:
            player.write_log(f"SYS: ⏰ REMINDER: {msg}")

    threading.Thread(target=_remind, daemon=True).start()
    return f"Reminder scheduled for {rem_time}: {msg}"
