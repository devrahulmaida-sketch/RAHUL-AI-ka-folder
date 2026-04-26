"""pdf_reader.py"""
import os


def pdf_reader(parameters: dict, player=None) -> str:
    action    = parameters.get("action", "read")
    file_path = parameters.get("file_path", "")
    query     = parameters.get("query", "")
    pages     = parameters.get("pages", "all")

    if not file_path or not os.path.exists(file_path):
        return f"PDF not found: {file_path}"

    try:
        import pypdf
    except ImportError:
        try:
            from PyPDF2 import PdfReader
            pypdf = None
        except ImportError:
            return "pypdf not installed. Run: pip install pypdf"

    try:
        if pypdf:
            reader = pypdf.PdfReader(file_path)
        else:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)

        total_pages = len(reader.pages)

        if pages == "all":
            page_range = range(total_pages)
        else:
            try:
                start, end = pages.split("-")
                page_range = range(int(start)-1, min(int(end), total_pages))
            except Exception:
                page_range = range(min(5, total_pages))

        text = ""
        for i in page_range:
            text += reader.pages[i].extract_text() or ""
            if len(text) > 8000:
                break

        if action == "read":
            return f"PDF ({total_pages} pages):\n{text[:3000]}"

        elif action == "summarize":
            words = text.split()
            first = " ".join(words[:300])
            return (f"PDF Summary ({total_pages} pages, ~{len(words)} words):\n"
                    f"{first}…\n\n[Full text available — ask me to read specific pages]")

        elif action == "search":
            if not query:
                return "Provide a query for search."
            lines   = text.split("\n")
            matches = [l.strip() for l in lines if query.lower() in l.lower() and l.strip()]
            if matches:
                return f"Found {len(matches)} matches for '{query}':\n" + "\n".join(matches[:15])
            return f"No matches found for '{query}'"

        elif action == "extract_text":
            path_out = file_path.replace(".pdf", "_extracted.txt")
            with open(path_out, "w", encoding="utf-8") as f:
                f.write(text)
            return f"Text extracted to: {path_out}"

        return f"Unknown action: {action}"

    except Exception as e:
        return f"PDF error: {e}"
