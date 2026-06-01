"""Unit and MVO tests for the LIBRARIAN specialist.

Unit tests use tmp_path fixtures with synthetic library content (3 works,
5 passages each). Claude API and sentence-transformers are mocked — no network
calls required.

MVO tests run the actual CLI against the committed library/ data.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LIBRARY = REPO_ROOT / "library"

# ---------------------------------------------------------------------------
# Synthetic library fixture
# ---------------------------------------------------------------------------

_META = {
    "work-a": {
        "source": "ia", "slug": "work-a",
        "title": "Filing Systems and Their Management",
        "author": "Smith, John", "year": 1920,
        "ia_identifier": "filesys00smit", "ia_access": "open",
        "gutenberg_id": None, "acquired_at": "2026-06-01T00:00:00+00:00",
    },
    "work-b": {
        "source": "gutenberg", "slug": "work-b",
        "title": "Office Methods and Card Indexing",
        "author": "Brown, Alice", "year": 1915,
        "ia_identifier": None, "ia_access": None,
        "gutenberg_id": "12345", "acquired_at": "2026-06-01T00:00:00+00:00",
    },
    "work-c": {
        "source": "manual", "slug": "work-c",
        "title": "Card Index Practice",
        "author": "Jones, Robert", "year": 1922,
        "ia_identifier": None, "ia_access": None,
        "gutenberg_id": None, "acquired_at": "2026-06-01T00:00:00+00:00",
    },
}

_PASSAGES = {
    "work-a": [
        ("Card index overview", "A card index is a systematic method of filing information.", "p. 10"),
        ("Vertical filing practice", "The vertical file cabinet became standard in American offices by 1910.", "p. 25"),
        ("Cross-reference systems", "Cross-reference cards allow retrieval by multiple access points.", "p. 42"),
        ("Remington Rand visible card", "The Remington Rand visible card tray allowed rapid scanning of records.", "p. 67"),
        ("Filing efficiency", "Efficient filing requires consistent alphabetical arrangement of all items.", "p. 88"),
    ],
    "work-b": [
        ("Scientific management of offices", "Scientific management transformed clerical operations in large firms.", "p. 5"),
        ("Record keeping standards", "Every record must be filed within 24 hours of receipt to maintain order.", "p. 18"),
        ("Card catalog evolution", "The card catalog system evolved directly from library practice.", "p. 33"),
        ("Filing cabinet design", "Steel filing cabinets replaced wooden boxes in offices after 1900.", "p. 51"),
        ("Index card dimensions", "The standard index card measures three by five inches for uniformity.", "p. 70"),
    ],
    "work-c": [
        ("Fundamentals of card indexing", "Card indexing provides flexible reorganization of business records.", "p. 1"),
        ("Visible record system design", "Visible systems expose the top edge of each card for instant scanning.", "p. 15"),
        ("Phonetic indexing method", "Phonetic codes group names with similar sounds together in one place.", "p. 28"),
        ("Rotary card file systems", "Rotary files allow 360-degree access without walking the filing aisle.", "p. 44"),
        ("Color coding for categories", "Color tabs identify record categories at a glance without reading.", "p. 59"),
    ],
}


def _make_excerpts(title: str, passages: list[tuple[str, str, str]]) -> str:
    lines = [f"# Excerpts — {title}\n\n## Passages"]
    for section, passage, page in passages:
        lines.append(
            f"\n### {section}\n\n"
            f'> "{passage}" ({page})\n\n'
            f"Context note: Relevant to research on office filing systems.\n"
        )
    return "\n".join(lines)


@pytest.fixture()
def lib(tmp_path, monkeypatch):
    """Synthetic library in tmp_path; patches _LIBRARY in the index module."""
    lib_dir = tmp_path / "library"
    (lib_dir / "works").mkdir(parents=True)

    for slug, meta in _META.items():
        work_dir = lib_dir / "works" / slug
        work_dir.mkdir()
        (work_dir / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        (work_dir / "excerpts.md").write_text(
            _make_excerpts(meta["title"], _PASSAGES[slug]), encoding="utf-8"
        )

    import markery.specialist.librarian.index as idx
    monkeypatch.setattr(idx, "_LIBRARY", lib_dir)
    monkeypatch.setattr(idx, "_INDEX_PATH", lib_dir / "index.jsonl")
    monkeypatch.setattr(idx, "_EMBED_DB", lib_dir / "index.duckdb")

    return lib_dir


# ---------------------------------------------------------------------------
# TestIndexWorks
# ---------------------------------------------------------------------------

class TestIndexWorks:
    def test_returns_correct_counts(self, lib):
        from markery.specialist.librarian.index import index_works
        indexed, skipped = index_works()
        assert indexed == 3
        assert skipped == 0

    def test_creates_index_jsonl(self, lib):
        from markery.specialist.librarian.index import index_works
        index_works()
        idx_path = lib / "index.jsonl"
        assert idx_path.exists()

    def test_record_count(self, lib):
        from markery.specialist.librarian.index import index_works
        index_works()
        records = [
            json.loads(l)
            for l in (lib / "index.jsonl").read_text().splitlines()
            if l.strip()
        ]
        assert len(records) == 15  # 3 works × 5 passages

    def test_record_fields(self, lib):
        from markery.specialist.librarian.index import index_works
        index_works()
        records = [
            json.loads(l)
            for l in (lib / "index.jsonl").read_text().splitlines()
            if l.strip()
        ]
        required = {"work_slug", "author", "title", "year", "section", "passage", "page", "context", "indexed_at"}
        for rec in records:
            assert required <= rec.keys(), f"missing fields in record: {rec}"

    def test_author_propagated(self, lib):
        from markery.specialist.librarian.index import index_works
        index_works()
        records = [
            json.loads(l)
            for l in (lib / "index.jsonl").read_text().splitlines()
            if l.strip()
        ]
        a_recs = [r for r in records if r["work_slug"] == "work-a"]
        assert all(r["author"] == "Smith, John" for r in a_recs)

    def test_incremental_skips_unchanged(self, lib):
        from markery.specialist.librarian.index import index_works
        index_works()
        _, skipped = index_works()
        assert skipped == 3  # all 3 synthetic works have passages → all skipped

    def test_rebuild_reindexes_all(self, lib):
        from markery.specialist.librarian.index import index_works
        index_works()
        indexed, skipped = index_works(rebuild=True)
        assert indexed == 3
        assert skipped == 0


# ---------------------------------------------------------------------------
# TestKeywordSearch
# ---------------------------------------------------------------------------

class TestKeywordSearch:
    def test_returns_passage_for_exact_term(self, lib):
        from markery.specialist.librarian.index import index_works, search_keyword
        index_works()
        results = search_keyword("Remington Rand")
        assert len(results) >= 1
        assert any("Remington Rand" in r["passage"] for r in results)

    def test_all_terms_must_match(self, lib):
        from markery.specialist.librarian.index import index_works, search_keyword
        index_works()
        # "xyzzy" is not in any passage
        results = search_keyword("card xyzzy_nonexistent")
        assert results == []

    def test_multi_word_query(self, lib):
        from markery.specialist.librarian.index import index_works, search_keyword
        index_works()
        results = search_keyword("phonetic indexing")
        assert len(results) >= 1
        assert any("Phonetic" in r["section"] or "phonetic" in r["passage"] for r in results)

    def test_case_insensitive(self, lib):
        from markery.specialist.librarian.index import index_works, search_keyword
        index_works()
        upper = search_keyword("CARD INDEX")
        lower = search_keyword("card index")
        assert len(upper) == len(lower)

    def test_top_n_respected(self, lib):
        from markery.specialist.librarian.index import index_works, search_keyword
        index_works()
        results = search_keyword("card", top=3)
        assert len(results) <= 3

    def test_result_contains_required_fields(self, lib):
        from markery.specialist.librarian.index import index_works, search_keyword
        index_works()
        results = search_keyword("filing")
        assert results
        for r in results:
            assert "work_slug" in r
            assert "author" in r
            assert "passage" in r
            assert "page" in r
            assert "section" in r


# ---------------------------------------------------------------------------
# TestSemanticSearch  (sentence-transformers mocked)
# ---------------------------------------------------------------------------

class _FakeModel:
    """Deterministic fake embedder — same text always gets the same vector."""
    def encode(self, texts, show_progress_bar=False):
        import numpy as np
        vecs = []
        for text in texts:
            vec = np.zeros(384, dtype=np.float32)
            for i, c in enumerate(text):
                vec[i % 384] += ord(c) / 256.0
            norm = np.linalg.norm(vec) + 1e-10
            vecs.append(vec / norm)
        return np.array(vecs)


class TestSemanticSearch:
    def _patch_model(self, monkeypatch):
        import markery.specialist.librarian.index as idx
        monkeypatch.setattr(idx, "_get_model", lambda: _FakeModel())

    def test_embedding_index_created(self, lib, monkeypatch):
        from markery.specialist.librarian.index import index_works, index_embeddings
        self._patch_model(monkeypatch)
        index_works()
        embedded, skipped = index_embeddings()
        assert embedded == 15
        assert skipped == 0
        assert (lib / "index.duckdb").exists()

    def test_passage_embeddings_table_exists(self, lib, monkeypatch):
        import duckdb
        from markery.specialist.librarian.index import index_works, index_embeddings
        self._patch_model(monkeypatch)
        index_works()
        index_embeddings()
        con = duckdb.connect(str(lib / "index.duckdb"), read_only=True)
        rows = con.execute("SELECT count(*) FROM passage_embeddings").fetchone()
        con.close()
        assert rows[0] == 15

    def test_incremental_embedding_skips_existing(self, lib, monkeypatch):
        from markery.specialist.librarian.index import index_works, index_embeddings
        self._patch_model(monkeypatch)
        index_works()
        index_embeddings()
        embedded, skipped = index_embeddings()
        assert embedded == 0
        assert skipped == 15

    def test_semantic_search_returns_results(self, lib, monkeypatch):
        from markery.specialist.librarian.index import index_works, index_embeddings, search_semantic
        self._patch_model(monkeypatch)
        index_works()
        index_embeddings()
        results = search_semantic("card index systems", top=5)
        assert len(results) >= 1

    def test_semantic_search_result_fields(self, lib, monkeypatch):
        from markery.specialist.librarian.index import index_works, index_embeddings, search_semantic
        self._patch_model(monkeypatch)
        index_works()
        index_embeddings()
        results = search_semantic("filing cabinets", top=3)
        assert results
        for r in results:
            assert "work_slug" in r
            assert "passage" in r

    def test_semantic_falls_back_when_no_db(self, lib, monkeypatch):
        from markery.specialist.librarian.index import index_works, search_semantic
        self._patch_model(monkeypatch)
        index_works()
        # No index_embeddings() called — index.duckdb absent
        results = search_semantic("card index")
        assert results == []


# ---------------------------------------------------------------------------
# TestListWorks
# ---------------------------------------------------------------------------

class TestListWorks:
    def test_returns_all_works(self, lib):
        from markery.specialist.librarian.index import index_works, list_works
        index_works()
        summaries = list_works()
        slugs = {s["slug"] for s in summaries}
        assert slugs == {"work-a", "work-b", "work-c"}

    def test_excerpt_count_correct(self, lib):
        from markery.specialist.librarian.index import index_works, list_works
        index_works()
        summaries = list_works()
        for s in summaries:
            assert s["excerpt_count"] == 5

    def test_metadata_fields_present(self, lib):
        from markery.specialist.librarian.index import index_works, list_works
        index_works()
        summaries = list_works()
        for s in summaries:
            assert "author" in s
            assert "year" in s
            assert "source" in s
            assert "has_raw_text" in s

    def test_raw_text_absent_for_synthetic(self, lib):
        from markery.specialist.librarian.index import index_works, list_works
        index_works()
        summaries = list_works()
        assert all(not s["has_raw_text"] for s in summaries)


# ---------------------------------------------------------------------------
# TestCard
# ---------------------------------------------------------------------------

class TestCard:
    def _make_card(self, lib, monkeypatch, query: str, mode: str = "keyword") -> str:
        """Build a card and return its text content via --out -."""
        import markery.specialist.librarian.cli as cli_mod
        import markery.specialist.librarian.index as idx

        monkeypatch.setattr(idx, "_LIBRARY", lib)
        monkeypatch.setattr(idx, "_INDEX_PATH", lib / "index.jsonl")
        monkeypatch.setattr(idx, "_EMBED_DB", lib / "index.duckdb")
        monkeypatch.setattr(cli_mod, "_LIBRARY", lib)
        monkeypatch.setattr(cli_mod, "_CARDS_DIR", lib / "cards")

        from markery.specialist.librarian.index import index_works
        index_works()

        import argparse, io, sys
        from markery.specialist.librarian.cli import cmd_card

        args = argparse.Namespace(
            query=query,
            top=5,
            mode=mode,
            out="-",
            tokens=False,
        )
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            cmd_card(args)
        finally:
            sys.stdout = old_stdout
        return buf.getvalue()

    def test_output_contains_citation_brackets(self, lib, monkeypatch):
        content = self._make_card(lib, monkeypatch, "card index")
        assert re.search(r"\[\w+.*?\(\d{4}\)\]", content), \
            "no [Author (Year)] citation bracket found"

    def test_token_estimate_under_300(self, lib, monkeypatch):
        content = self._make_card(lib, monkeypatch, "card index filing")
        token_est = len(content) // 4
        assert token_est <= 300, f"card too large: ~{token_est} tokens"

    def test_header_line_present(self, lib, monkeypatch):
        content = self._make_card(lib, monkeypatch, "filing systems")
        assert content.startswith("# Library card:"), "header line missing"

    def test_saves_to_cards_dir(self, lib, monkeypatch):
        import markery.specialist.librarian.cli as cli_mod
        import markery.specialist.librarian.index as idx

        monkeypatch.setattr(idx, "_LIBRARY", lib)
        monkeypatch.setattr(idx, "_INDEX_PATH", lib / "index.jsonl")
        monkeypatch.setattr(idx, "_EMBED_DB", lib / "index.duckdb")
        monkeypatch.setattr(cli_mod, "_LIBRARY", lib)
        monkeypatch.setattr(cli_mod, "_CARDS_DIR", lib / "cards")

        from markery.specialist.librarian.index import index_works
        index_works()

        import argparse
        from markery.specialist.librarian.cli import cmd_card
        args = argparse.Namespace(
            query="card index",
            top=3,
            mode="keyword",
            out=None,
            tokens=False,
        )
        cmd_card(args)
        card_file = lib / "cards" / "card-index.md"
        assert card_file.exists()
        content = card_file.read_text()
        assert "# Library card:" in content


# ---------------------------------------------------------------------------
# TestExtract  (Claude API mocked)
# ---------------------------------------------------------------------------

class TestExtract:
    def _mock_response(self, passage: str = "The card index is the primary tool.", page: str = "p. 5", context: str = "Directly relevant.") -> MagicMock:
        resp = MagicMock()
        resp.content = [MagicMock()]
        resp.content[0].text = (
            f"PASSAGE: {passage}\nPAGE: {page}\nCONTEXT: {context}\n---\n"
        )
        resp.usage = MagicMock(input_tokens=500, output_tokens=50)
        return resp

    def test_extract_calls_claude_with_topics(self, tmp_path, monkeypatch):
        work_dir = tmp_path / "library" / "works" / "test-work"
        work_dir.mkdir(parents=True)
        (work_dir / "raw_text.txt").write_text("A card index is the primary tool for systematic filing." * 20)
        (work_dir / "metadata.json").write_text(json.dumps({"title": "Test Work", "author": "Author, A."}))

        import markery.specialist.librarian.extract as ext
        import markery.common.config as cfg_mod
        monkeypatch.setattr(cfg_mod, "ROOT", tmp_path)
        # Re-bind _LIBRARY in extract module
        monkeypatch.setattr(ext, "_LIBRARY", tmp_path / "library")

        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._mock_response()
        monkeypatch.setattr(ext, "_get_client", lambda: mock_client)

        out_path = ext.extract("test-work", topics=["card index"], max_passages=5)
        assert out_path.exists()
        assert mock_client.messages.create.called

        # Verify topics appear in the prompt
        call_kwargs = mock_client.messages.create.call_args
        prompt_text = call_kwargs[1]["messages"][0]["content"]
        assert "card index" in prompt_text

    def test_extract_writes_candidates_md(self, tmp_path, monkeypatch):
        work_dir = tmp_path / "library" / "works" / "test-work"
        work_dir.mkdir(parents=True)
        (work_dir / "raw_text.txt").write_text(
            "The card index provides efficient access to records.\n\n" * 30
        )
        (work_dir / "metadata.json").write_text(json.dumps({"title": "Test Work"}))

        import markery.specialist.librarian.extract as ext
        monkeypatch.setattr(ext, "_LIBRARY", tmp_path / "library")
        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._mock_response()
        monkeypatch.setattr(ext, "_get_client", lambda: mock_client)

        out_path = ext.extract("test-work", topics=["card index"], max_passages=5)
        assert out_path.name == "candidates.md"
        content = out_path.read_text()
        assert "<!-- status: pending -->" in content

    def test_extract_auto_accept_writes_excerpts(self, tmp_path, monkeypatch):
        work_dir = tmp_path / "library" / "works" / "test-work"
        work_dir.mkdir(parents=True)
        (work_dir / "raw_text.txt").write_text(
            "The card index provides efficient access to records.\n\n" * 30
        )
        (work_dir / "metadata.json").write_text(json.dumps({"title": "Test Work"}))

        import markery.specialist.librarian.extract as ext
        monkeypatch.setattr(ext, "_LIBRARY", tmp_path / "library")
        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._mock_response()
        monkeypatch.setattr(ext, "_get_client", lambda: mock_client)

        out_path = ext.extract("test-work", topics=["card index"], max_passages=5, auto_accept=True)
        assert out_path.name == "excerpts.md"
        content = out_path.read_text()
        assert "## Passages" in content


# ---------------------------------------------------------------------------
# TestAcquireStructure  (HTTP mocked)
# ---------------------------------------------------------------------------

class TestAcquireStructure:
    def test_acquire_ia_creates_directory(self, tmp_path, monkeypatch):
        """acquire from IA creates metadata.json in library/works/<slug>/."""
        work_dir_root = tmp_path / "library" / "works"
        work_dir_root.mkdir(parents=True)

        import markery.specialist.librarian.sources.ia as ia_mod

        fake_meta = {
            "metadata": {
                "identifier": "filesys00smit",
                "title": "Filing Systems",
                "creator": "Smith, John",
                "date": "1920",
                "mediatype": "texts",
                "access-restricted-item": False,
            },
            "files": [{"name": "filesys00smit_djvu.txt", "format": "DjVuTXT"}],
        }

        import markery.specialist.librarian.cli as cli_mod
        import markery.specialist.librarian.sources.common as common_mod

        monkeypatch.setattr(cli_mod, "_LIBRARY", tmp_path / "library")
        monkeypatch.setattr(cli_mod, "_WANTS", tmp_path / "library" / "wants.jsonl")

        monkeypatch.setattr(ia_mod, "fetch_metadata", lambda ident: fake_meta)
        monkeypatch.setattr(ia_mod, "download_text", lambda ident, out_dir: out_dir / "raw_text.txt")

        import argparse
        args = argparse.Namespace(identifier="filesys00smit", source="ia")
        cli_mod.cmd_acquire(args)

        expected_slug = "smith-filing-systems"
        work_dir = tmp_path / "library" / "works" / expected_slug
        assert work_dir.exists(), f"Expected work dir at {work_dir}"
        meta_file = work_dir / "metadata.json"
        assert meta_file.exists()
        meta = json.loads(meta_file.read_text())
        assert meta["source"] == "ia"
        assert meta["slug"] == expected_slug
        assert meta["title"] == "Filing Systems"

    def test_acquire_borrow_only_registers_metadata_only(self, tmp_path, monkeypatch):
        """Borrow-only IA items register metadata but download_text raises PermissionError."""
        import markery.specialist.librarian.sources.ia as ia_mod
        import markery.specialist.librarian.cli as cli_mod

        monkeypatch.setattr(cli_mod, "_LIBRARY", tmp_path / "library")
        monkeypatch.setattr(cli_mod, "_WANTS", tmp_path / "library" / "wants.jsonl")
        (tmp_path / "library" / "works").mkdir(parents=True)

        fake_meta = {
            "metadata": {
                "identifier": "borrowonly00auth",
                "title": "Borrow Only Work",
                "creator": "Author, Test",
                "date": "1930",
                "access-restricted-item": True,
            },
            "files": [],
        }
        monkeypatch.setattr(ia_mod, "fetch_metadata", lambda ident: fake_meta)
        monkeypatch.setattr(
            ia_mod, "download_text",
            lambda ident, out_dir: (_ for _ in ()).throw(PermissionError("borrow-only"))
        )

        import argparse
        args = argparse.Namespace(identifier="borrowonly00auth", source="ia")
        cli_mod.cmd_acquire(args)

        work_dir = tmp_path / "library" / "works" / "author-borrow-only-work"
        assert work_dir.exists()
        assert (work_dir / "metadata.json").exists()
        assert not (work_dir / "raw_text.txt").exists()


# ---------------------------------------------------------------------------
# MVO tests — real library/, CLI subprocess
# ---------------------------------------------------------------------------

requires_library = pytest.mark.skipif(
    not (LIBRARY / "index.jsonl").exists(),
    reason="library/index.jsonl not present",
)


def _cli(*args: str) -> tuple[str, int]:
    result = subprocess.run(
        ["python", "-m", "markery.cli", *args],
        capture_output=True, text=True,
        cwd=str(REPO_ROOT),
    )
    return result.stdout + result.stderr, result.returncode


@requires_library
class TestMVOLibrarian:
    def test_index_exit_zero(self):
        _, rc = _cli("librarian", "index")
        assert rc == 0

    def test_index_produces_valid_jsonl(self):
        idx_path = LIBRARY / "index.jsonl"
        assert idx_path.exists()
        lines = [l for l in idx_path.read_text().splitlines() if l.strip()]
        assert lines, "index.jsonl is empty"
        for line in lines:
            rec = json.loads(line)
            assert "work_slug" in rec
            assert "passage" in rec
            assert "section" in rec

    def test_search_keyword_returns_results(self):
        out, rc = _cli("librarian", "search", "card index", "--mode", "keyword")
        assert rc == 0
        assert re.search(r"AUTHOR.*SECTION.*PASSAGE", out), "header row missing"
        assert re.search(r"\d{4}", out), "no year found in results"

    def test_search_keyword_no_match_exits_zero(self):
        out, rc = _cli("librarian", "search", "xyzzy_definitely_not_found")
        assert rc == 0
        assert "No matches" in out

    def test_list_shows_all_works(self):
        out, rc = _cli("librarian", "list")
        assert rc == 0
        assert re.search(r"SLUG.*AUTHOR.*YEAR", out), "list header missing"
        assert "galloway" in out.lower()
        assert "leffingwell" in out.lower()

    def test_list_shows_excerpt_counts(self):
        out, rc = _cli("librarian", "list")
        assert rc == 0
        # At least one work should show a non-zero excerpt count
        assert re.search(r"\s[1-9]\d*\s", out), "no non-zero excerpt count found"

    def test_card_citation_brackets(self):
        out, rc = _cli("librarian", "card", "card index filing", "--mode", "keyword", "--out", "-")
        assert rc == 0
        assert re.search(r"\[\w.*?\(\d{4}\)\]", out), "no [Author (Year)] bracket found"

    def test_card_token_estimate(self):
        out, rc = _cli("librarian", "card", "filing system", "--mode", "keyword", "--out", "-")
        assert rc == 0
        token_est = len(out) // 4
        assert token_est <= 300, f"card output too large: ~{token_est} tokens"

    def test_wants_exit_zero(self):
        _, rc = _cli("librarian", "wants")
        assert rc == 0

    def test_list_verbose(self):
        out, rc = _cli("librarian", "list", "--verbose")
        assert rc == 0
        assert "galloway" in out.lower() or "Galloway" in out
