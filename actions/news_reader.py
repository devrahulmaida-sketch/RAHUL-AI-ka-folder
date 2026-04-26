"""news_reader.py"""
import json, threading


def news_reader(parameters: dict, player=None) -> str:
    topic      = parameters.get("topic", "general")
    count      = int(parameters.get("count", 5))
    show_anim  = parameters.get("show_animation", True)

    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddg:
            results = list(ddg.news(topic, max_results=count))
    except Exception as e:
        return f"News error: {e}"

    if not results:
        return "No news found."

    headlines = [{"text": r.get("title",""), "icon": "📰"} for r in results]
    summary   = "\n".join([f"• {r['text']}" for r in headlines])

    if show_anim and player and hasattr(player, "anim"):
        def _show():
            player.anim.show(
                anim_type="news_ticker",
                title=f"News: {topic}",
                content=json.dumps(headlines),
                color="#ffcc00",
                duration=15,
            )
        threading.Thread(target=_show, daemon=True).start()

    return f"Latest news — {topic}:\n{summary}"
