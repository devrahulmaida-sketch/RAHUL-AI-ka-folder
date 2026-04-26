"""youtube.py"""
import os, subprocess


def youtube_action(parameters: dict, player=None) -> str:
    action = parameters.get("action", "play")
    query  = parameters.get("query", "")
    url    = parameters.get("url", "")
    region = parameters.get("region", "IN")

    if action == "play":
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}" if query else url
        os.system(f"xdg-open '{search_url}' &")
        return f"Opening YouTube: {query or url}"

    elif action == "search":
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddg:
                results = list(ddg.text(f"youtube {query}", max_results=5))
            lines = [f"• {r.get('title','')} — {r.get('href','')}" for r in results[:5]]
            return "YouTube results:\n" + "\n".join(lines)
        except Exception as e:
            return f"Search error: {e}"

    elif action == "transcript":
        if not url:
            return "URL required for transcript."
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            vid_id = url.split("v=")[-1].split("&")[0]
            transcript = YouTubeTranscriptApi.get_transcript(vid_id)
            text = " ".join([t["text"] for t in transcript[:50]])
            return f"Transcript (first 50 segments):\n{text[:2000]}"
        except Exception as e:
            return f"Transcript error: {e}"

    elif action == "trending":
        os.system(f"xdg-open 'https://www.youtube.com/feed/trending' &")
        return "Opened YouTube trending."

    return f"Unknown YouTube action: {action}"
