"""Headless checks for the chat workflow controls."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


class _ElementIdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: dict[str, str] = {}

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        element_id = dict(attrs).get("id")
        if element_id:
            self.elements[element_id] = tag


def test_chat_workflow_controls_are_present() -> None:
    html_path = Path(__file__).resolve().parents[1] / "tools" / "web" / "chat.html"
    parser = _ElementIdParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    parser.close()

    expected_elements = {
        "analyze-document-button": "button",
        "workflow-path": "input",
        "workflow-type": "select",
    }
    assert all(
        parser.elements.get(element_id) == tag
        for element_id, tag in expected_elements.items()
    )
