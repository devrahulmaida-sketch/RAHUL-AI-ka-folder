"""web_search.py — Search the web using DuckDuckGo (free, no API key)"""
import json
import threading


def web_search(parameters: dict, player=None) -> str:
    query      = parameters.get("query", "")
    mode       = parameters.get("mode", "search")
    show_anim  = parameters.get("show_on_screen", True)

    if not query:
        return "No query provided."

    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "duckduckgo-search not installed. Run: pip install duckduckgo-search"

    results = []
    try:
        with DDGS() as ddg:
            if mode == "news":
                raw = list(ddg.news(query, max_results=6))
                results = [{"text": r.get("title",""), "icon": "📰",
                             "url": r.get("url","")} for r in raw]
            else:
                raw = list(ddg.text(query, max_results=6))
                results = [{"text": r.get("title",""), "icon": "🔍",
                             "body": r.get("body",""), "url": r.get("href","")} for r in raw]
    except Exception as e:
        return f"Search error: {e}"

    if not results:
        return "No results found."

    # Build summary
    summary_lines = []
    for i, r in enumerate(results[:5], 1):
        summary_lines.append(f"{i}. {r['text']}")
    summary = "\n".join(summary_lines)

    # Show on UI as animated list
    if show_anim and player and hasattr(player, "anim"):
        list_data = json.dumps([{"text": r["text"][:60], "icon": r.get("icon","🔍")}
                                  for r in results[:6]])
        def _show():
            player.anim.show(
                anim_type="list",
                title=f"Search: {query[:40]}",
                content=list_data,
                color="#00d4ff",
                duration=12,
            )
        threading.Thread(target=_show, daemon=True).start()

    return f"Search results for '{query}':\n{summary}"
