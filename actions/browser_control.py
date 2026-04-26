"""browser_control.py — Control Firefox/Chromium on Linux via Playwright"""
import subprocess, time, threading


_browsers = {}   # browser_name → playwright page


def browser_control(parameters: dict, player=None) -> str:
    action  = parameters.get("action", "go_to")
    url     = parameters.get("url", "")
    query   = parameters.get("query", "")
    text    = parameters.get("text", "")
    selector= parameters.get("selector", "")
    browser = parameters.get("browser", "firefox")
    engine  = parameters.get("engine", "google")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "playwright not installed. Run: pip install playwright && playwright install"

    global _browsers
    key = browser

    def _get_or_create():
        if key not in _browsers or _browsers[key]["closed"]:
            pw  = sync_playwright().start()
            br  = pw.firefox.launch(headless=False) if browser == "firefox" else pw.chromium.launch(headless=False)
            ctx = br.new_context()
            pg  = ctx.new_page()
            _browsers[key] = {"pw": pw, "br": br, "ctx": ctx, "page": pg, "closed": False}
        return _browsers[key]["page"]

    try:
        if action == "go_to":
            page = _get_or_create()
            page.goto(url, timeout=20000)
            return f"Navigated to {url}"

        elif action == "search":
            page = _get_or_create()
            engines = {
                "google": f"https://www.google.com/search?q={query}",
                "bing":   f"https://www.bing.com/search?q={query}",
                "duckduckgo": f"https://duckduckgo.com/?q={query}",
            }
            page.goto(engines.get(engine, engines["google"]))
            return f"Searched for: {query}"

        elif action == "new_tab":
            if key in _browsers and not _browsers[key]["closed"]:
                pg = _browsers[key]["ctx"].new_page()
                if url: pg.goto(url)
                _browsers[key]["page"] = pg
                return f"New tab opened: {url or 'blank'}"
            return "No browser open. Use go_to first."

        elif action == "click":
            page = _browsers.get(key, {}).get("page")
            if not page: return "No browser open."
            if selector:
                page.click(selector)
            elif text:
                page.get_by_text(text).first.click()
            return "Clicked."

        elif action == "type":
            page = _browsers.get(key, {}).get("page")
            if not page: return "No browser open."
            if selector:
                page.fill(selector, text)
            else:
                page.keyboard.type(text)
            return f"Typed: {text}"

        elif action == "scroll":
            page = _browsers.get(key, {}).get("page")
            if not page: return "No browser open."
            direction = parameters.get("direction", "down")
            amount    = int(parameters.get("amount", 500))
            dy = amount if direction == "down" else -amount
            page.evaluate(f"window.scrollBy(0, {dy})")
            return f"Scrolled {direction} {amount}px"

        elif action == "screenshot":
            page = _browsers.get(key, {}).get("page")
            if not page: return "No browser open."
            path = parameters.get("path", "/tmp/screenshot.png")
            page.screenshot(path=path)
            if player: player.show_image(path)
            return f"Screenshot saved: {path}"

        elif action == "back":
            page = _browsers.get(key, {}).get("page")
            if page: page.go_back()
            return "Went back."

        elif action == "forward":
            page = _browsers.get(key, {}).get("page")
            if page: page.go_forward()
            return "Went forward."

        elif action == "reload":
            page = _browsers.get(key, {}).get("page")
            if page: page.reload()
            return "Reloaded."

        elif action == "close":
            if key in _browsers:
                try: _browsers[key]["br"].close(); _browsers[key]["pw"].stop()
                except: pass
                _browsers[key]["closed"] = True
            return "Browser closed."

        elif action == "get_url":
            page = _browsers.get(key, {}).get("page")
            return page.url if page else "No browser open."

        elif action == "get_text":
            page = _browsers.get(key, {}).get("page")
            if not page: return "No browser open."
            return page.inner_text("body")[:2000]

        else:
            return f"Unknown action: {action}"

    except Exception as e:
        return f"Browser error: {e}"
