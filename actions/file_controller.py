"""file_controller.py — Full file/folder management for Linux"""
import os, shutil, glob, json
from pathlib import Path


def file_controller(parameters: dict, player=None) -> str:
    action = parameters.get("action", "list")
    path   = parameters.get("path", str(Path.home()))
    dest   = parameters.get("destination", "")
    name   = parameters.get("name", "")
    new_name = parameters.get("new_name", "")
    content  = parameters.get("content", "")

    path = os.path.expanduser(path)

    try:
        if action == "list":
            target = path if os.path.isdir(path) else str(Path(path).parent)
            items  = os.listdir(target)
            dirs   = sorted([i for i in items if os.path.isdir(os.path.join(target, i))])
            files  = sorted([i for i in items if os.path.isfile(os.path.join(target, i))])
            result = f"📁 {target}\n"
            result += "\n".join([f"  📂 {d}" for d in dirs[:20]])
            result += "\n"
            result += "\n".join([f"  📄 {f}" for f in files[:20]])
            if len(items) > 40:
                result += f"\n  … and {len(items)-40} more"
            return result

        elif action == "create_file":
            fp = os.path.join(path, name) if name else path
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content or "")
            return f"Created file: {fp}"

        elif action == "create_folder":
            fp = os.path.join(path, name) if name else path
            os.makedirs(fp, exist_ok=True)
            return f"Created folder: {fp}"

        elif action == "delete":
            if os.path.isfile(path):
                os.remove(path)
                return f"Deleted file: {path}"
            elif os.path.isdir(path):
                shutil.rmtree(path)
                return f"Deleted folder: {path}"
            return f"Not found: {path}"

        elif action == "move":
            shutil.move(path, dest)
            return f"Moved {path} → {dest}"

        elif action == "copy":
            if os.path.isdir(path):
                shutil.copytree(path, dest)
            else:
                shutil.copy2(path, dest)
            return f"Copied {path} → {dest}"

        elif action == "rename":
            parent  = str(Path(path).parent)
            new_path = os.path.join(parent, new_name)
            os.rename(path, new_path)
            return f"Renamed to: {new_name}"

        elif action == "read":
            if not os.path.isfile(path):
                return f"File not found: {path}"
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read(8000)
            return text

        elif action == "write":
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Written to: {path}"

        elif action == "find":
            pattern = os.path.join(path, "**", f"*{name}*")
            matches = glob.glob(pattern, recursive=True)[:20]
            if not matches:
                return f"No files matching '{name}' found."
            return "\n".join(matches)

        elif action == "disk_usage":
            total, used, free = shutil.disk_usage("/")
            gb = 1024**3
            return (f"Disk Usage:\n"
                    f"  Total: {total/gb:.1f} GB\n"
                    f"  Used:  {used/gb:.1f} GB\n"
                    f"  Free:  {free/gb:.1f} GB")

        elif action == "largest":
            target = path if os.path.isdir(path) else str(Path.home())
            files  = []
            for root, _, fnames in os.walk(target):
                for fn in fnames:
                    fp = os.path.join(root, fn)
                    try:
                        files.append((os.path.getsize(fp), fp))
                    except Exception:
                        pass
            files.sort(reverse=True)
            lines = [f"  {sz//1024:>8} KB  {fp}" for sz, fp in files[:10]]
            return "Largest files:\n" + "\n".join(lines)

        else:
            return f"Unknown action: {action}"

    except PermissionError:
        return f"Permission denied: {path}"
    except Exception as e:
        return f"File error: {e}"
