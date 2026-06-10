"""Unit tests for publisher render helpers."""

from __future__ import annotations

from markery.specialist.publisher.render import _esc, _page, _render_markdown, _year_from_dt


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


def test_page_no_og_tags():
    result = _page("Title", "<p>body</p>", {})
    assert 'property="og:' not in result


def test_page_with_og_tags():
    og = {"title": "T", "description": "D", "url": "https://example.com/page.html"}
    result = _page("Title", "<p>body</p>", {}, og=og)
    assert 'property="og:title"' in result
    assert 'content="T"' in result
    assert 'property="og:url"' in result
    assert 'content="https://example.com/page.html"' in result
    assert 'property="og:type"' in result
    assert 'content="article"' in result


# Group 2: list, blockquote, external link rendering

def test_render_markdown_unordered_list():
    result = _render_markdown("- Alpha\n- Beta\n- Gamma")
    assert "<ul>" in result
    assert "<li>Alpha</li>" in result
    assert "<li>Beta</li>" in result
    assert "</ul>" in result


def test_render_markdown_ordered_list():
    result = _render_markdown("1. First\n2. Second")
    assert "<ol>" in result
    assert "<li>First</li>" in result
    assert "</ol>" in result


def test_render_markdown_blockquote():
    result = _render_markdown("> Quoted text here.")
    assert "<blockquote>" in result
    assert "Quoted text here." in result
    assert "</blockquote>" in result


def test_render_markdown_external_link_https():
    result = _render_markdown("[USPTO](https://www.uspto.gov)")
    assert 'href="https://www.uspto.gov"' in result
    assert 'target="_blank"' in result
    assert 'rel="noopener"' in result
    assert ">USPTO<" in result


def test_render_markdown_external_link_rejects_javascript():
    result = _render_markdown("[Bad](javascript:alert(1))")
    assert "javascript:" not in result
    assert "Bad" in result


def test_render_markdown_list_closes_on_blank():
    result = _render_markdown("- Item\n\nParagraph after.")
    assert "</ul>" in result
    assert "<p>" in result


# Group 4: _year_from_dt helper

def test_year_from_dt_date_object():
    import datetime
    assert _year_from_dt(datetime.date(1930, 5, 1)) == 1930


def test_year_from_dt_string():
    assert _year_from_dt("1927-04-22") == 1927


def test_year_from_dt_none():
    assert _year_from_dt(None) is None
