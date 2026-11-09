from pathlib import Path


WEB_DIR = Path(__file__).resolve().parent.parent / "tools" / "web"


def test_chat_loads_pinned_markdown_parser_and_sanitizer():
    page = (WEB_DIR / "chat.html").read_text(encoding="utf-8")

    assert "vendor/marked.umd.js" in page
    assert "vendor/purify.min.js" in page
    assert page.index("vendor/marked.umd.js") < page.index(
        "vendor/purify.min.js"
    ) < page.index("chat.js")


def test_assistant_markdown_is_sanitized_before_insertion():
    script = (WEB_DIR / "chat.js").read_text(encoding="utf-8")

    assert "window.marked.parse(content" in script
    assert "window.DOMPurify.sanitize(html" in script
    assert "RETURN_DOM_FRAGMENT: true" in script
    assert "ALLOW_DATA_ATTR: false" in script
    assert "message.textContent = content;" in script
