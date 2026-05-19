"""Convert Markery markdown essays to MediaWiki wikitext.

Handles the subset of markdown that the historian produces:
  - ATX headings (# ## ###) → == Section == / === Sub ===
  - **bold** → '''bold'''
  - _italic_ / *italic* → ''italic''
  - [text](url) → [url text]
  - [[internal]] cross-links → plain text (wikilinks need manual review)
  - Fenced code blocks → <syntaxhighlight> (rare; included for completeness)
  - Plain paragraphs preserved as-is
  - Frontmatter (---) stripped
"""

from __future__ import annotations

import re


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4:].lstrip("\n")


def markdown_to_wikitext(text: str) -> str:
    """Convert a markdown string to MediaWiki wikitext."""
    text = _strip_frontmatter(text)

    # Fenced code blocks → <syntaxhighlight>
    def _code_block(m: re.Match) -> str:
        lang = m.group(1).strip() or "text"
        return f"<syntaxhighlight lang=\"{lang}\">\n{m.group(2)}</syntaxhighlight>"

    text = re.sub(r'```(\w*)\n(.*?)```', _code_block, text, flags=re.DOTALL)

    lines: list[str] = []
    for line in text.split("\n"):
        # ATX headings
        if line.startswith("#### "):
            line = f"==== {line[5:].rstrip()} ===="
        elif line.startswith("### "):
            line = f"=== {line[4:].rstrip()} ==="
        elif line.startswith("## "):
            line = f"== {line[3:].rstrip()} =="
        elif line.startswith("# "):
            line = f"== {line[2:].rstrip()} =="
        else:
            # Bold and italic (order matters: bold first)
            line = re.sub(r'\*\*(.+?)\*\*', r"'''\1'''", line)
            line = re.sub(r'\*(.+?)\*',     r"''\1''",   line)
            line = re.sub(r'_(.+?)_',       r"''\1''",   line)

            # Markdown links [text](url) → [url text]
            line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\2 \1]', line)

            # [[cross-links]] — leave as wikilinks for manual review
            # (a link index isn't available here; the researcher adjusts targets)

            # Inline code → <code>...</code>
            line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)

        lines.append(line)

    return "\n".join(lines)


def build_draft_wikitext(
    essay_text: str,
    trademark: str,
    patent_no: str,
    trademark_serial: str,
    entity: str,
    filing_dt: str,
    grant_dt: str,
    goods_desc: str = "",
) -> str:
    """Build a complete draft wikitext article for a confirmed pair."""
    body = markdown_to_wikitext(essay_text)

    refs = [
        f"<ref>United States Patent and Trademark Office. "
        f"Trademark Serial No. {trademark_serial}. "
        f"Mark: {trademark}. Filed: {filing_dt}. "
        f"{{{{cite web|url=https://tsdr.uspto.gov/#caseNumber={trademark_serial}&caseType=SERIAL_NO&searchType=statusSearch"
        f"|title=TSDR Serial No. {trademark_serial}|publisher=USPTO}}}}}}</ref>",
        f"<ref>{{{{US patent|{patent_no}}}}} Granted {grant_dt}. "
        f"Assignee: {entity}.</ref>",
    ]

    sources_section = (
        "\n\n== Sources ==\n"
        "<references />\n"
        "\n"
        "=== Primary sources ===\n"
        f"* USPTO Trademark Serial No. {trademark_serial} ({trademark}, filed {filing_dt})\n"
        f"* {patent_no} (granted {grant_dt}, assignee: {entity})\n"
    )

    categories = (
        "\n[[Category:Trademarks]]\n"
        "[[Category:United States patents]]\n"
        f"[[Category:{entity}]]\n"
    )

    return body + sources_section + categories
