"""Claude-assisted passage extraction for LIBRARIAN specialist.

extract()    — chunks raw_text.txt, calls Claude, writes candidates.md
review()     — interactive accept/reject loop over candidates.md
"""

from __future__ import annotations

import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from markery.common.config import ROOT, DEFAULT_MODEL as _DEFAULT_MODEL
from markery.common.tokens import TokenRecord, emit as emit_tokens

_LIBRARY = ROOT / "library"

# ~8 000 chars ≈ 2 000 tokens; 800-char overlap ≈ 200 tokens
_CHUNK_CHARS = 8_000
_OVERLAP_CHARS = 800


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Collapse extra whitespace produced by djvu OCR."""
    # Collapse multiple spaces within a line; preserve newlines
    lines = [re.sub(r"  +", " ", ln) for ln in text.splitlines()]
    return "\n".join(lines)


def chunk_text(text: str,
               chunk_chars: int = _CHUNK_CHARS,
               overlap_chars: int = _OVERLAP_CHARS) -> list[str]:
    """Split text into overlapping chunks, breaking at paragraph boundaries."""
    text = _normalize(text)
    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_chars, length)
        if end < length:
            # Try to break at a paragraph boundary (double newline)
            para_break = text.rfind("\n\n", start, end)
            if para_break > start + chunk_chars // 2:
                end = para_break
            else:
                # Fall back to sentence end (period + space)
                sent_break = text.rfind(". ", start, end)
                if sent_break > start + chunk_chars // 2:
                    end = sent_break + 1
        chunks.append(text[start:end].strip())
        if end >= length:
            break
        start = max(start + 1, end - overlap_chars)

    return [c for c in chunks if c]


# ---------------------------------------------------------------------------
# Claude API call — system prompt (cached)
# ---------------------------------------------------------------------------

# Load librarian identity at module init; append detailed extraction task to
# push the combined prompt above the 1024-token minimum for Anthropic caching.
_PERSONA_DIR = Path(__file__).parent / "persona"
_LIBRARIAN_IDENTITY: str = (
    (_PERSONA_DIR / "identity.md").read_text(encoding="utf-8")
    if (_PERSONA_DIR / "identity.md").exists() else ""
)

_EXTRACT_TASK = """\
---

## Your Task: Extracting Verbatim Passages from Historical Texts

You receive one chunk of text at a time from a digitized historical work — a business \
history, trade journal, industrial catalog, advertising treatise, or government survey \
typically published between 1870 and 1950. Your task is to identify verbatim quotations \
directly relevant to the research topics specified in the user message.

### What Makes a Passage Worth Extracting

A passage is extractable when it is:

**Verbatim and quotable.** The exact words from the source — not paraphrased, summarised, \
or corrected. OCR artifacts (broken hyphens from line breaks, spacing irregularities, \
ligature failures such as "ﬁ" for "fi") should be preserved as they appear. \
Faithfulness to the source text is more important than readability.

**Substantive and specific.** A passage should state a specific fact, name a specific \
product, company, date, or describe a specific commercial activity. Generic observations \
("business was important in this era") are not extractable. Named evidence \
("The SOUNDEX filing system, introduced by Rand Kardex Bureau in 1927, employed a \
phonetic coding scheme derived from Odell's 1918 patent") is extractable.

**Directly relevant to the stated topics.** The passage must address the research topics \
in a way that contributes to a historical analysis. A keyword appearing in passing within \
an otherwise unrelated sentence does not qualify. Evaluate whether a historian studying \
this topic would want to quote this passage.

**Self-contained or contextualizable.** The passage should be comprehensible with only \
the CONTEXT note for support. If it requires three paragraphs of surrounding text to \
make sense, it is not suitable for extraction.

### Handling OCR Artifacts

Djvu and microfilm OCR sources produce predictable artifacts. Preserve these in extracted \
passages rather than correcting them, so the extracted text remains verifiably verbatim:
- Broken hyphens from line wraps: "manu-\\nfacturing" should be read as "manufacturing" \
  but extracted with the break preserved
- Merged words: "filingsystem" appears — extract as found
- Extra spacing: "the  card  index" — extract as found
- Character substitutions: "1" for "l" and vice versa

When an artifact would confuse the reader, note it in the CONTEXT line.

### Estimating Page Numbers

Page numbers in djvu OCR often appear as isolated numerals at the top or bottom of a \
page break — a line containing only "42" or "PAGE 42". Roman numerals indicate front \
matter (e.g. "xiv"). Use format "p. 42" for a single page, "pp. 42-43" when a passage \
visibly spans a break, and "?" when no page marker is apparent near the passage.

### Output Format

For each relevant passage, use exactly this format:

PASSAGE: <exact verbatim text, as it appears in the source>
PAGE: <p. N, pp. N-M, or ?>
CONTEXT: <one sentence explaining why this passage is relevant to the research topics>
---

Extract up to 3 passages per chunk. If no relevant passages exist in this excerpt, \
respond with exactly: NO_PASSAGES

Do not add commentary outside the PASSAGE/PAGE/CONTEXT blocks. If fewer than 3 passages \
qualify, that is the correct result — do not pad with weak extractions.\
"""

_SYSTEM = (_LIBRARIAN_IDENTITY + "\n\n" + _EXTRACT_TASK).strip()

_USER_TMPL = """\
From the following passage, extract up to 3 verbatim quotations relevant to: {topics}.

For each quotation use exactly this format:

PASSAGE: <exact verbatim text, as it appears in the source>
PAGE: <estimated page number, e.g. "p. 42" or "pp. 42-43", or "?" if unclear>
CONTEXT: <one sentence explaining why this passage is relevant to the research topics>
---

If no relevant passages exist in this excerpt, respond with exactly: NO_PASSAGES

Text:
{chunk}"""



def _call_claude(chunk: str, topics: list[str], client, model: str) -> tuple[list[dict], int, int, int, int]:
    """Call Claude for one chunk.

    Returns (candidates, prompt_tokens, completion_tokens, cache_read, cache_creation).
    The system prompt is sent as an ephemeral cache block; on the second+ chunk in a
    session cache_read is > 0 only if the prefix meets the model-dependent minimum.
    That minimum is 4096 tokens on Haiku 4.5 (the default model), 2048 on Sonnet 4.6,
    1024 on older Sonnet — see common/llm.py. If the system prompt is below the
    active model's threshold, caching silently does not activate (cache_read = 0).
    """
    user_msg = _USER_TMPL.format(
        topics=", ".join(f'"{t}"' for t in topics),
        chunk=chunk,
    )
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=[{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()
    prompt_tok     = resp.usage.input_tokens
    completion_tok = resp.usage.output_tokens
    cache_read     = getattr(resp.usage, "cache_read_input_tokens",   0) or 0
    cache_create   = getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
    candidates = _parse_response(text)
    return candidates, prompt_tok, completion_tok, cache_read, cache_create


def _parse_response(text: str) -> list[dict]:
    """Parse PASSAGE/PAGE/CONTEXT blocks from Claude response."""
    if "NO_PASSAGES" in text:
        return []

    candidates: list[dict] = []
    # Split on --- separators
    blocks = re.split(r"\n---+\n?", text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        passage_m = re.search(r"PASSAGE:\s*(.+?)(?=\nPAGE:|\nCONTEXT:|$)", block,
                               re.DOTALL | re.IGNORECASE)
        page_m    = re.search(r"PAGE:\s*(.+?)(?=\nCONTEXT:|$)", block,
                               re.DOTALL | re.IGNORECASE)
        context_m = re.search(r"CONTEXT:\s*(.+?)$", block,
                               re.DOTALL | re.IGNORECASE)
        if not passage_m:
            continue
        passage = passage_m.group(1).strip().strip('"')
        page    = page_m.group(1).strip() if page_m else "?"
        context = context_m.group(1).strip() if context_m else ""
        if len(passage) < 20:
            continue
        candidates.append({"passage": passage, "page": page, "context": context})
    return candidates


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _word_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def _deduplicate(candidates: list[dict], threshold: float = 0.6) -> list[dict]:
    """Remove near-duplicates; keep the candidate with the longer context."""
    kept: list[dict] = []
    for cand in candidates:
        ws = _word_set(cand["passage"])
        is_dup = False
        for i, existing in enumerate(kept):
            ews = _word_set(existing["passage"])
            union = ws | ews
            if not union:
                continue
            overlap = len(ws & ews) / len(union)
            if overlap >= threshold:
                # Keep the one with the longer context note
                if len(cand["context"]) > len(existing["context"]):
                    kept[i] = cand
                is_dup = True
                break
        if not is_dup:
            kept.append(cand)
    return kept


# ---------------------------------------------------------------------------
# Heading derivation
# ---------------------------------------------------------------------------

def _make_heading(context: str, passage: str) -> str:
    """Derive a short topic heading from the context sentence."""
    # Strip leading "This passage..." or "The passage..."
    text = re.sub(r"^(this|the)\s+passage\s+\w+\s+", "", context.lower())
    words = re.findall(r"[a-z]+", text)
    stop = {"a", "an", "the", "of", "in", "and", "for", "to", "its", "is",
            "are", "was", "were", "that", "this", "by", "as", "with"}
    sig = [w for w in words if w not in stop][:6]
    if sig:
        heading = " ".join(sig).title()
    else:
        # Fall back to first 6 words of passage
        pwords = passage.split()[:6]
        heading = " ".join(pwords).rstrip(".,;:") + "…"
    return heading


# ---------------------------------------------------------------------------
# candidates.md formatting
# ---------------------------------------------------------------------------

_CANDIDATES_HEADER = """\
# Candidates — {title}

*Generated by `markery librarian extract`*
*Topics: {topics}*
*Date: {date}*
*Source: {slug}*

---
"""

_CANDIDATE_BLOCK = """\
### {heading}

> "{passage}" ({page})

Context: {context}

<!-- status: pending -->

---
"""


def _write_candidates(path: Path, slug: str, title: str,
                      topics: list[str], candidates: list[dict]) -> None:
    header = _CANDIDATES_HEADER.format(
        title=title,
        topics=", ".join(topics),
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        slug=slug,
    )
    blocks = []
    for c in candidates:
        heading = _make_heading(c["context"], c["passage"])
        blocks.append(_CANDIDATE_BLOCK.format(
            heading=heading,
            passage=c["passage"],
            page=c["page"],
            context=c["context"],
        ))
    path.write_text(header + "\n".join(blocks), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract(
    slug: str,
    topics: list[str],
    max_passages: int = 10,
    auto_accept: bool = False,
    tokens_flag: bool = False,
    batch: bool = False,
) -> Path:
    """Extract passages from raw_text.txt and write candidates.md (or excerpts.md
    if --auto-accept). Returns path to the written file."""
    t0 = time.monotonic()
    work_dir = _LIBRARY / "works" / slug
    raw_text_path = work_dir / "raw_text.txt"

    if not raw_text_path.exists():
        print(
            f"No raw_text.txt for '{slug}'.\n"
            f"Run: markery librarian acquire <identifier>",
            file=sys.stderr,
        )
        sys.exit(1)

    # Read metadata for title
    meta_path = work_dir / "metadata.json"
    title = slug
    if meta_path.exists():
        import json
        meta = json.loads(meta_path.read_text())
        title = meta.get("title", slug)

    model = os.environ.get("MARKERY_MODEL", _DEFAULT_MODEL)

    text = raw_text_path.read_text(encoding="utf-8", errors="replace")
    chunks = chunk_text(text)
    total_chunks = len(chunks)

    from markery.common.llm import get_client
    client = get_client()
    if client is None:
        print(
            "ANTHROPIC_API_KEY not set or anthropic package not installed.\n"
            "Set ANTHROPIC_API_KEY in .env and run: pip install anthropic",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Extracting from '{slug}' ({total_chunks} chunks, topics: {', '.join(topics)})",
          flush=True)

    all_candidates: list[dict] = []
    total_prompt = 0
    total_completion = 0
    total_cache_read = 0
    total_cache_create = 0
    errors = 0

    if batch:
        # All chunks are independent and not latency-sensitive — submit as one
        # Batch API job (50% price). No early-stop; the whole book is processed.
        from markery.common.llm import call_batch
        items = [
            (f"chunk-{i}", _USER_TMPL.format(
                topics=", ".join(f'"{t}"' for t in topics), chunk=chunk))
            for i, chunk in enumerate(chunks, 1)
        ]
        print(f"  submitting {len(items)} chunks as one batch (50% price)…", flush=True)
        results = call_batch(model, _SYSTEM, items, max_tokens=1024)
        for cid, r in results.items():
            if "error" in r:
                errors += 1
                print(f"\n  {cid} error: {r['error']}", file=sys.stderr)
                continue
            all_candidates.extend(_parse_response(r["text"]))
            total_prompt += r["prompt_tokens"]
            total_completion += r["completion_tokens"]
            total_cache_read += r["cache_read_tokens"]
            total_cache_create += r["cache_creation_tokens"]
    else:
        for i, chunk in enumerate(chunks, 1):
            print(f"  chunk {i}/{total_chunks}…", end="\r", flush=True)
            try:
                cands, ptok, ctok, cread, ccreate = _call_claude(chunk, topics, client, model)
                all_candidates.extend(cands)
                total_prompt += ptok
                total_completion += ctok
                total_cache_read += cread
                total_cache_create += ccreate
                # Stop early if we already have plenty of candidates
                if len(all_candidates) >= max_passages * 3:
                    print(f"\n  stopping early ({len(all_candidates)} candidates found)")
                    break
            except Exception as exc:
                errors += 1
                print(f"\n  chunk {i} error: {exc}", file=sys.stderr)

    print(f"  {len(all_candidates)} raw candidates from {total_chunks - errors} chunks")

    deduped = _deduplicate(all_candidates)[:max_passages]
    print(f"  {len(deduped)} after deduplication")

    wall_ms = int((time.monotonic() - t0) * 1000)

    if tokens_flag or os.environ.get("MARKERY_TOKEN_LOG"):
        record = TokenRecord(
            model=model,
            prompt_tokens=total_prompt,
            completion_tokens=total_completion,
            cache_read_tokens=total_cache_read,
            cache_creation_tokens=total_cache_create,
            wall_ms=wall_ms,
            batch=batch,
        )
        emit_tokens(record, specialist="librarian", command="extract",
                    tokens_flag=tokens_flag, n_calls=total_chunks - errors)

    if not deduped:
        print("No relevant passages found.", file=sys.stderr)
        sys.exit(0)

    if auto_accept:
        out_path = _append_to_excerpts(work_dir, deduped)
        print(f"  {len(deduped)} passage(s) appended to {out_path}")
        return out_path
    else:
        out_path = work_dir / "candidates.md"
        _write_candidates(out_path, slug, title, topics, deduped)
        print(f"  candidates written to {out_path}")
        print("  Run: markery librarian review " + slug)
        return out_path


def _append_to_excerpts(work_dir: Path, candidates: list[dict]) -> Path:
    """Append accepted candidates to excerpts.md."""
    excerpts_path = work_dir / "excerpts.md"
    existing = excerpts_path.read_text(encoding="utf-8") if excerpts_path.exists() else ""

    # Ensure there's a Passages section
    if "## Passages" not in existing:
        existing = existing.rstrip() + "\n\n## Passages\n"

    new_blocks = []
    for c in candidates:
        heading = _make_heading(c["context"], c["passage"])
        new_blocks.append(
            f"\n### {heading}\n\n"
            f"> \"{c['passage']}\" ({c['page']})\n\n"
            f"Context note: {c['context']}\n"
        )
    excerpts_path.write_text(existing + "\n".join(new_blocks), encoding="utf-8")
    return excerpts_path


# ---------------------------------------------------------------------------
# Interactive review
# ---------------------------------------------------------------------------

def review(slug: str, auto_accept: bool = False) -> None:
    """Review candidates.md, appending accepted passages to excerpts.md.

    With auto_accept=True, accepts all pending candidates without prompting.
    Without it, opens the interactive accept/reject/skip/quit loop.
    """
    work_dir = _LIBRARY / "works" / slug
    candidates_path = work_dir / "candidates.md"

    if not candidates_path.exists():
        print(f"No candidates.md for '{slug}'.\n"
              f"Run: markery librarian extract {slug} --topics <topic>",
              file=sys.stderr)
        sys.exit(1)

    raw = candidates_path.read_text(encoding="utf-8")
    blocks = _split_candidate_blocks(raw)

    pending = [b for b in blocks if _get_status(b) == "pending"]
    if not pending:
        print("No pending candidates to review.")
        return

    if auto_accept:
        accepted_count = 0
        for block in pending:
            heading, passage, page, context = _parse_block(block)
            if passage:
                _append_to_excerpts(work_dir, [{"passage": passage, "page": page,
                                                "context": context}])
                raw = raw.replace(
                    block,
                    block.replace("<!-- status: pending -->", "<!-- status: accepted -->"),
                    1,
                )
                accepted_count += 1
        candidates_path.write_text(raw, encoding="utf-8")
        print(f"Auto-accepted {accepted_count} of {len(pending)} pending passage(s).")
        return

    print(f"Reviewing {len(pending)} candidate(s) for '{slug}'.")
    print("Keys: [a]ccept  [r]eject  [s]kip  [q]uit\n")

    accepted_count = 0
    for idx, block in enumerate(pending, 1):
        heading, passage, page, context = _parse_block(block)
        print(f"--- [{idx}/{len(pending)}] {heading} ---")
        print(f'  > "{passage}" ({page})')
        print(f"  Context: {context}")
        print()

        while True:
            choice = input("  [a/r/s/q] ").strip().lower()
            if choice in ("a", "r", "s", "q"):
                break
            print("  Enter a, r, s, or q.")

        if choice == "q":
            print("Review paused.")
            break
        elif choice == "a":
            _append_to_excerpts(work_dir, [{"passage": passage, "page": page, "context": context}])
            raw = raw.replace(block, block.replace(
                "<!-- status: pending -->", "<!-- status: accepted -->"), 1)
            accepted_count += 1
            print("  Accepted.\n")
        elif choice == "r":
            raw = raw.replace(block, block.replace(
                "<!-- status: pending -->", "<!-- status: rejected -->"), 1)
            print("  Rejected.\n")
        else:
            print("  Skipped.\n")

    candidates_path.write_text(raw, encoding="utf-8")
    print(f"Review complete. {accepted_count} passage(s) accepted.")


def _split_candidate_blocks(text: str) -> list[str]:
    """Split candidates.md into individual passage blocks."""
    # Each block starts with ### and ends at the next --- or end of file
    pattern = re.compile(r"(### .+?(?=\n### |\Z))", re.DOTALL)
    return [m.group(1).strip() for m in pattern.finditer(text)]


def _get_status(block: str) -> str:
    m = re.search(r"<!-- status: (\w+) -->", block)
    return m.group(1) if m else "pending"


def _parse_block(block: str) -> tuple[str, str, str, str]:
    """Return (heading, passage, page, context) from a candidate block."""
    heading_m = re.match(r"### (.+)", block)
    heading = heading_m.group(1).strip() if heading_m else "Untitled"

    quote_m = re.search(r'>\s+"(.+?)"\s+\(([^)]+)\)', block, re.DOTALL)
    if quote_m:
        passage = quote_m.group(1).strip()
        page = quote_m.group(2).strip()
    else:
        # Try without quotes
        quote_m2 = re.search(r">\s+(.+?)\s+\(([^)]+)\)", block, re.DOTALL)
        passage = quote_m2.group(1).strip() if quote_m2 else ""
        page = quote_m2.group(2).strip() if quote_m2 else "?"

    context_m = re.search(r"Context:\s+(.+?)(?=\n|$)", block, re.IGNORECASE)
    context = context_m.group(1).strip() if context_m else ""

    return heading, passage, page, context
