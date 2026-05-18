"""Enrich candidates.jsonl with text-matching signals.

New fields added to each candidate row:
  title_name_hit        bool   mark name words appear in patent title
  abstract_name_hit     bool   mark name words appear in abstract
  goods_title_overlap   float  Jaccard(goods tokens, title tokens)
  goods_abstract_overlap float Jaccard(goods tokens, abstract tokens)

Modifies candidates.jsonl in-place (rewrites the file).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb

from markery.common.config import DB

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "to", "for", "on",
    "with", "by", "from", "at", "as", "is", "be", "are", "was",
    "were", "has", "have", "had", "not", "this", "that", "it",
    "its", "such", "used", "use", "using", "which", "more", "than",
    "other", "any", "all", "also", "their", "may", "can", "been",
}


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    return {
        w for w in re.findall(r"[a-zA-Z]+", text.lower())
        if len(w) > 2 and w not in STOPWORDS
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return round(len(a & b) / len(a | b), 4)


def _name_hit(text: str | None, mark: str) -> bool:
    if not text:
        return False
    mark_words = _tokens(mark)
    significant = {w for w in mark_words if len(w) > 3}
    if not significant:
        significant = mark_words
    text_lower = text.lower()
    return any(w in text_lower for w in significant)


def _fetch_goods(conn_tm: duckdb.DuckDBPyConnection, serial_no: str) -> str | None:
    row = conn_tm.execute(
        "SELECT statement_text FROM statement WHERE serial_no = ? LIMIT 1", [serial_no]
    ).fetchone()
    if row and row[0]:
        return row[0]
    row = conn_tm.execute(
        "SELECT goods_desc FROM mark_case_status WHERE serial_no = ? LIMIT 1", [serial_no]
    ).fetchone()
    return row[0] if row else None


def _fetch_patent_texts(
    conn_pat: duckdb.DuckDBPyConnection,
    patent_no: str,
) -> tuple[str | None, str | None]:
    row = conn_pat.execute(
        "SELECT title, abstract FROM patents WHERE patent_no = ?", [patent_no]
    ).fetchone()
    return (row[0], row[1]) if row else (None, None)


def enrich_candidates(
    candidates_path: Path,
    patents_db: Path | None = None,
    trademarks_db: Path | None = None,
) -> int:
    """Enrich candidates_path in-place with text signals. Returns count enriched."""
    patents_db    = patents_db    or DB["patents"]
    trademarks_db = trademarks_db or DB["trademarks"]

    if not candidates_path.exists():
        print(f"No candidates file at {candidates_path}")
        return 0

    lines      = [l for l in candidates_path.read_text().splitlines() if l.strip()]
    candidates = [json.loads(l) for l in lines]

    conn_pat = duckdb.connect(str(patents_db),    read_only=True)
    conn_tm  = duckdb.connect(str(trademarks_db), read_only=True)

    _pat_cache: dict[str, tuple] = {}
    _tm_cache:  dict[str, str | None] = {}

    enriched = 0
    for c in candidates:
        pno  = c["patent_no"]
        sno  = str(c["trademark_serial"])
        mark = c["trademark"]

        if pno not in _pat_cache:
            _pat_cache[pno] = _fetch_patent_texts(conn_pat, pno)
        title, abstract = _pat_cache[pno]

        if sno not in _tm_cache:
            _tm_cache[sno] = _fetch_goods(conn_tm, sno)
        goods = _tm_cache[sno]

        goods_tok    = _tokens(goods)
        title_tok    = _tokens(title)
        abstract_tok = _tokens(abstract)

        c["title_name_hit"]         = _name_hit(title, mark)
        c["abstract_name_hit"]      = _name_hit(abstract, mark)
        c["goods_title_overlap"]    = _jaccard(goods_tok, title_tok)
        c["goods_abstract_overlap"] = _jaccard(goods_tok, abstract_tok)
        enriched += 1

    conn_pat.close()
    conn_tm.close()

    with open(candidates_path, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")

    return enriched
