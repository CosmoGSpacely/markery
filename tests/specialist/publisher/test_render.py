"""Unit tests for publisher render helpers."""

from __future__ import annotations

from markery.specialist.publisher.render import _esc, _render_markdown


def test_esc_empty_string():
    assert _esc("") == ""


def test_esc_none():
    assert _esc(None) == ""


def test_esc_html_chars():
    assert _esc('<b>me & "you"</b>') == "&lt;b&gt;me &amp; &quot;you&quot;&lt;/b&gt;"


def test_esc_plain_string():
    assert _esc("hello world") == "hello world"


def test_render_markdown_heading():
    result = _render_markdown("## Section Title\n\nParagraph.")
    assert "<h2>Section Title</h2>" in result
    assert "<p>" in result


def test_render_markdown_h1_becomes_h2():
    result = _render_markdown("# Top\n")
    assert "<h2>Top</h2>" in result


def test_render_markdown_paragraph():
    result = _render_markdown("Hello world")
    assert result.strip().startswith("<p>")
    assert "Hello world" in result


def test_render_markdown_bold():
    result = _render_markdown("This is **bold** text.")
    assert "<strong>bold</strong>" in result


def test_render_markdown_inline_code():
    result = _render_markdown("Use `markery status` to check.")
    assert "<code>markery status</code>" in result


def test_render_markdown_fenced_block():
    md = "```python\nprint('hi')\n```"
    result = _render_markdown(md)
    assert "<pre><code>" in result
    assert "print" in result


def test_render_markdown_empty():
    result = _render_markdown("")
    assert result.strip() == ""
