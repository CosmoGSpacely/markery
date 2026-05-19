"""Tests for wikitext.py markdown → MediaWiki converter."""

from __future__ import annotations

from markery.specialist.wikipedia.wikitext import markdown_to_wikitext, build_draft_wikitext


# ---------------------------------------------------------------------------
# markdown_to_wikitext
# ---------------------------------------------------------------------------

def test_h2_becomes_wiki_section():
    result = markdown_to_wikitext("## Background")
    assert "== Background ==" in result


def test_h3_becomes_wiki_subsection():
    result = markdown_to_wikitext("### Details")
    assert "=== Details ===" in result


def test_h1_becomes_h2_section():
    result = markdown_to_wikitext("# Title")
    assert "== Title ==" in result


def test_bold_converted():
    result = markdown_to_wikitext("This is **bold** text.")
    assert "'''bold'''" in result


def test_italic_asterisks_converted():
    result = markdown_to_wikitext("This is *italic* text.")
    assert "''italic''" in result


def test_italic_underscores_converted():
    result = markdown_to_wikitext("This is _italic_ text.")
    assert "''italic''" in result


def test_markdown_link_converted():
    result = markdown_to_wikitext("[USPTO](https://www.uspto.gov)")
    assert "[https://www.uspto.gov USPTO]" in result


def test_inline_code_converted():
    result = markdown_to_wikitext("Run `markery status`.")
    assert "<code>markery status</code>" in result


def test_fenced_code_block_converted():
    md = "```python\nprint('hello')\n```"
    result = markdown_to_wikitext(md)
    assert "<syntaxhighlight" in result
    assert "print" in result


def test_cross_links_preserved_as_wikilinks():
    result = markdown_to_wikitext("See [[SOUNDEX]] article.")
    assert "[[SOUNDEX]]" in result


def test_frontmatter_stripped():
    md = "---\nkey: value\n---\n\nBody text."
    result = markdown_to_wikitext(md)
    assert "key: value" not in result
    assert "Body text." in result


def test_plain_paragraph_unchanged():
    result = markdown_to_wikitext("Plain prose paragraph here.")
    assert "Plain prose paragraph here." in result


# ---------------------------------------------------------------------------
# build_draft_wikitext
# ---------------------------------------------------------------------------

def test_build_draft_contains_sources_section():
    result = build_draft_wikitext(
        essay_text="## Background\n\nThis mark was filed in 1927.",
        trademark="VI-DEX",
        patent_no="US1527374A",
        trademark_serial="71297261",
        entity="Wilson Jones Company",
        filing_dt="1926-09-17",
        grant_dt="1924-02-19",
    )
    assert "== Sources ==" in result
    assert "71297261" in result
    assert "US1527374A" in result


def test_build_draft_contains_categories():
    result = build_draft_wikitext(
        essay_text="Body.",
        trademark="VI-DEX",
        patent_no="US1527374A",
        trademark_serial="71297261",
        entity="Wilson Jones",
        filing_dt="1926-09-17",
        grant_dt="1924-02-19",
    )
    assert "[[Category:" in result


def test_build_draft_contains_converted_essay():
    result = build_draft_wikitext(
        essay_text="## Section\n\nBody with **bold** text.",
        trademark="SOUNDEX",
        patent_no="US1261167A",
        trademark_serial="71246709",
        entity="Remington Rand",
        filing_dt="1921-06-07",
        grant_dt="1918-04-02",
    )
    assert "== Section ==" in result
    assert "'''bold'''" in result
