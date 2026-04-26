"""code_helper.py — Write, edit, run, debug code on Linux"""
import os, subprocess, tempfile, threading
from pathlib import Path


LANG_EXT = {
    "python": ".py",  "py": ".py",
    "bash": ".sh",    "shell": ".sh",
    "javascript": ".js", "js": ".js",
    "typescript": ".ts", "ts": ".ts",
    "cpp": ".cpp",    "c++": ".cpp",
    "c": ".c",
    "rust": ".rs",
    "go": ".go",
    "java": ".java",
    "html": ".html",
    "css": ".css",
    "json": ".json",
}

LANG_RUN = {
    ".py":  "python3 {f}",
    ".sh":  "bash {f}",
    ".js":  "node {f}",
    ".rs":  "rustc {f} -o /tmp/rust_out && /tmp/rust_out",
    ".go":  "go run {f}",
    ".cpp": "g++ {f} -o /tmp/cpp_out && /tmp/cpp_out",
    ".c":   "gcc {f} -o /tmp/c_out && /tmp/c_out",
}


def code_helper(parameters: dict, player=None) -> str:
    action      = parameters.get("action", "write")
    description = parameters.get("description", "")
    language    = parameters.get("language", "python").lower()
    file_path   = parameters.get("file_path", "")
    code        = parameters.get("code", "")
    output_path = parameters.get("output_path", "")

    ext = LANG_EXT.get(language, ".py")

    if action == "write":
        if not code:
            return "No code provided to write."
        save_path = output_path or file_path or f"/tmp/rahul_code{ext}"
        os.makedirs(os.path.dirname(save_path) or "/tmp", exist_ok=True)
        with open(save_path, "w") as f:
            f.write(code)
        if ext == ".sh":
            os.chmod(save_path, 0o755)
        if player:
            player.write_log(f"SYS: Code written → {save_path}")
        return f"Code written to {save_path}"

    elif action == "run":
        target = file_path or output_path
        if not target and code:
            tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False, mode="w")
            tmp.write(code); tmp.close()
            target = tmp.name
        if not target:
            return "No file to run."

        ext_of = Path(target).suffix
        run_cmd = LANG_RUN.get(ext_of, f"python3 {target}")
        run_cmd = run_cmd.replace("{f}", target)

        # Open in terminal visibly
        terminal_cmds = [
            f"x-terminal-emulator -e 'bash -c \"{run_cmd}; echo; echo Press ENTER; read\"'",
            f"gnome-terminal -- bash -c '{run_cmd}; read'",
            f"xterm -e '{run_cmd}; read'",
        ]
        for tc in terminal_cmds:
            ret = os.system(tc + " &")
            if ret == 0:
                break

        # Also capture output
        try:
            result = subprocess.run(
                run_cmd, shell=True, capture_output=True,
                text=True, timeout=30
            )
            out = (result.stdout + result.stderr).strip()[:1000]
            return f"Ran: {target}\n{out}" if out else f"Ran: {target} (no output)"
        except subprocess.TimeoutExpired:
            return f"Running {target} (still executing in terminal)"

    elif action == "edit":
        if not file_path:
            return "file_path required for edit."
        editors = ["gedit", "kate", "xed", "nano", "vim"]
        for ed in editors:
            if os.system(f"which {ed} > /dev/null 2>&1") == 0:
                subprocess.Popen([ed, file_path])
                return f"Opened {file_path} in {ed}"
        return f"No editor found. File: {file_path}"

    elif action == "explain":
        if not file_path and not code:
            return "Provide file_path or code to explain."
        if file_path and os.path.isfile(file_path):
            with open(file_path) as f:
                code = f.read(4000)
        return f"Code to explain:\n```{language}\n{code[:2000]}\n```"

    elif action == "debug":
        target = file_path
        if not target:
            return "file_path required for debug."
        try:
            result = subprocess.run(
                ["python3", "-m", "py_compile", target],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return f"No syntax errors in {target}"
            return f"Syntax errors:\n{result.stderr}"
        except Exception as e:
            return f"Debug error: {e}"

    elif action == "auto":
        # Write + run in one shot
        if not code:
            return "No code provided."
        save = output_path or f"/tmp/rahul_auto{ext}"
        with open(save, "w") as f:
            f.write(code)
        if ext == ".sh":
            os.chmod(save, 0o755)
        ext_of  = Path(save).suffix
        run_cmd = LANG_RUN.get(ext_of, f"python3 {save}").replace("{f}", save)
        try:
            r = subprocess.run(run_cmd, shell=True, capture_output=True, text=True, timeout=20)
            out = (r.stdout + r.stderr).strip()[:1000]
            return f"✓ Ran {save}\n{out}" if out else f"✓ Ran {save}"
        except subprocess.TimeoutExpired:
            return f"Running {save}…"

    return f"Unknown action: {action}"
