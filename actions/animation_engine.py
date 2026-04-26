"""
animation_engine.py — Renders rich animated content on the RAHUL UI
Types: card, list, chart, steps, news_ticker, comparison, weather,
       typewriter, countdown, mindmap, image
"""
import json
import threading
import time


def animation_engine(parameters: dict, player) -> str:
    anim_type  = parameters.get("type", "card")
    title      = parameters.get("title", "")
    content    = parameters.get("content", "")
    color      = parameters.get("color", "")
    duration   = int(parameters.get("duration", 8))
    image_path = parameters.get("image_path", "")

    # Validate content JSON
    if content:
        try:
            json.loads(content)
        except Exception:
            # wrap plain text as card body
            content = json.dumps({"body": content})

    def _show():
        player.anim.show(
            anim_type=anim_type,
            title=title,
            content=content,
            color=color,
            duration=duration,
            image_path=image_path,
        )
        player.write_log(f"SYS: Showing {anim_type} — {title}")

    threading.Thread(target=_show, daemon=True).start()
    return f"Animation '{anim_type}' displayed: {title}"
