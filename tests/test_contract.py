"""Contract smoke tests for Markery data surfaces.

Verifies that every contract surface defined in CONTRACT.md produces records
whose guaranteed-present fields are actually present, and that types and
constraints match what the document promises. Runs against the
`information-systems` project corpus.

Run conditions:
  - Requires data DBs via Git LFS: data/trademarks.duckdb, data/patents.duckdb,
    data/entities.duckdb
  - Library tests require library/index.jsonl and library/index.duckdb
  - JSONL and frontmatter tests run without DBs (file-based only)
  - Skip conditions match test_mvo.py — these tests belong in the CI mvo job.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb
import pytest

REPO_ROOT  = Path(__file__).resolve().parents[1]
DB_TM      = REPO_ROOT / "data" / "trademarks.duckdb"
DB_PAT     = REPO_ROOT / "data" / "patents.duckdb"
DB_ENT     = REPO_ROOT / "data" / "entities.duckdb"
DB_EMB     = REPO_ROOT / "library" / "index.duckdb"
LIB_INDEX  = REPO_ROOT / "library" / "index.jsonl"
MANIFEST   = REPO_ROOT / "MANIFEST.json"

PROJECT    = "information-systems"
PROJ_ROOT  = REPO_ROOT / "projects" / PROJECT

requires_dbs = pytest.mark.skipif(
    not DB_TM.exists() or not DB_PAT.exists() or not DB_ENT.exists(),
    reason="data DBs not present (run in mvo job with LFS)",
)

requires_library = pytest.mark.skipif(
    not LIB_INDEX.exists() or not DB_EMB.exists(),
    reason="library index.jsonl or index.duckdb not present",
)


# ---------------------------------------------------------------------------
# 1. patents.duckdb
# ---------------------------------------------------------------------------

@requires_dbs
class TestPatentsDB:
    PATENT_NO = "US1261167A"

    def test_patents_guaranteed_fields(self):
        conn = duckdb.connect(str(DB_PAT), read_only=True)
        row = conn.execute(
            "SELECT patent_no, title, grant_dt FROM patents WHERE patent_no = ?",
            [self.PATENT_NO],
        ).fetchone()
        conn.close()
        assert row is not None, f"{self.PATENT_NO} not found in patents"
        patent_no, title, grant_dt = row
        assert patent_no == self.PATENT_NO         # guaranteed-present
        assert title     is not None               # guaranteed-present
        assert grant_dt  is not None               # guaranteed-present (primary scoring date)

    def test_patent_classes_rows_exist(self):
        conn = duckdb.connect(str(DB_PAT), read_only=True)
        rows = conn.execute(
            "SELECT cpc_class FROM patent_classes WHERE patent_no = ?", [self.PATENT_NO]
        ).fetchall()
        conn.close()
        assert len(rows) >= 1
        for (cls,) in rows:
            if cls is not None:
                assert len(cls) >= 4, f"cpc_class {cls!r} shorter than 4 chars"


# ---------------------------------------------------------------------------
# 2. trademarks.duckdb
# ---------------------------------------------------------------------------

@requires_dbs
class TestTrademarksDB:
    SERIAL_INT = 71246709
    SERIAL_STR = "71246709"

    def test_case_file_serial_resolves(self):
        conn = duckdb.connect(str(DB_TM), read_only=True)
        row = conn.execute(
            "SELECT serial_no FROM case_file WHERE serial_no = ?", [self.SERIAL_INT]
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == self.SERIAL_INT   # serial_no is BIGINT in bulk tables

    def test_serial_no_type_split_cast_required(self):
        """Bulk serial_no is BIGINT; extended_marks serial_no is VARCHAR.
        Cross-layer join must use CAST(cf.serial_no AS VARCHAR)."""
        conn = duckdb.connect(str(DB_TM), read_only=True)
        row = conn.execute(
            "SELECT em.serial_no FROM extended_marks em "
            "JOIN case_file cf ON CAST(cf.serial_no AS VARCHAR) = em.serial_no "
            "WHERE em.serial_no = ?",
            [self.SERIAL_STR],
        ).fetchone()
        conn.close()
        assert row is not None, "Cross-layer join with CAST failed"
        assert row[0] == self.SERIAL_STR   # extended_marks serial_no is VARCHAR

    def test_extended_marks_structured_fields(self):
        conn = duckdb.connect(str(DB_TM), read_only=True)
        row = conn.execute(
            "SELECT serial_no, mark_text, status_cd, goods_desc FROM extended_marks "
            "WHERE serial_no = ?",
            [self.SERIAL_STR],
        ).fetchone()
        conn.close()
        assert row is not None
        serial_no, mark_text, status_cd, goods_desc = row
        assert serial_no  == self.SERIAL_STR   # VARCHAR (not BIGINT)
        assert mark_text  is not None          # non-figurative mark: text present
        assert status_cd  is not None          # guaranteed populated after reparse
        assert goods_desc is not None          # guaranteed populated after reparse

    def test_statement_text_accessible(self):
        conn = duckdb.connect(str(DB_TM), read_only=True)
        rows = conn.execute(
            "SELECT statement_text FROM statement WHERE serial_no = ?", [self.SERIAL_INT]
        ).fetchall()
        conn.close()
        assert len(rows) >= 1
        assert any(r[0] for r in rows if r[0]), "no non-empty statement_text found"


# ---------------------------------------------------------------------------
# 3. entities.duckdb
# ---------------------------------------------------------------------------

@requires_dbs
class TestEntitiesDB:
    def test_company_entity_guaranteed_fields(self):
        conn = duckdb.connect(str(DB_ENT), read_only=True)
        row = conn.execute(
            "SELECT entity_id, canonical_name FROM company_entity WHERE entity_id = 1"
        ).fetchone()
        conn.close()
        assert row is not None
        entity_id, canonical_name = row
        assert isinstance(entity_id, int)
        assert isinstance(canonical_name, str) and canonical_name   # NOT NULL

    def test_variant_source_values_are_valid_enum(self):
        valid = {"patent_assignee", "trademark_owner", "trademark_search"}
        conn = duckdb.connect(str(DB_ENT), read_only=True)
        rows = conn.execute("SELECT DISTINCT source FROM entity_name_variant").fetchall()
        conn.close()
        for (source,) in rows:
            assert source in valid, f"Unexpected source value: {source!r}"

    def test_variant_name_is_not_null(self):
        conn = duckdb.connect(str(DB_ENT), read_only=True)
        n_null = conn.execute(
            "SELECT count(*) FROM entity_name_variant WHERE variant_name IS NULL"
        ).fetchone()[0]
        conn.close()
        assert n_null == 0, f"{n_null} rows with NULL variant_name"


# ---------------------------------------------------------------------------
# 4. candidates.jsonl
# ---------------------------------------------------------------------------

class TestCandidatesJsonl:
    GUARANTEED = {
        "entity_id", "entity", "patent_no", "cpc_classes",
        "trademark_serial", "score",
        "title_name_hit", "abstract_name_hit",
        "goods_title_overlap", "goods_abstract_overlap",
    }

    def _records(self) -> list[dict]:
        path = PROJ_ROOT / "matches" / "candidates.jsonl"
        if not path.exists():
            pytest.skip("candidates.jsonl not present")
        recs = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        if not recs:
            pytest.skip("candidates.jsonl is empty")
        return recs

    def test_guaranteed_fields_present(self):
        for rec in self._records():
            for field in self.GUARANTEED:
                assert field in rec, f"guaranteed field {field!r} absent in candidates record"

    def test_cpc_classes_is_list(self):
        for rec in self._records():
            assert isinstance(rec["cpc_classes"], list)

    def test_trademark_serial_is_int(self):
        for rec in self._records():
            assert isinstance(rec["trademark_serial"], int)

    def test_score_in_valid_range(self):
        # Theoretical bounds: -0.4 (worst) to ~1.1 (all signals, same year)
        for rec in self._records():
            assert -0.5 <= rec["score"] <= 1.2, f"score {rec['score']} out of range"

    def test_signal_fields_types(self):
        for rec in self._records():
            assert isinstance(rec["title_name_hit"], bool)
            assert isinstance(rec["abstract_name_hit"], bool)
            assert isinstance(rec["goods_title_overlap"], (int, float))
            assert isinstance(rec["goods_abstract_overlap"], (int, float))


# ---------------------------------------------------------------------------
# 5. confirmed.jsonl
# ---------------------------------------------------------------------------

class TestConfirmedJsonl:
    GUARANTEED = {"patent_no", "trademark_serial", "entity_id", "entity", "type", "note"}

    def _records(self) -> list[dict]:
        path = PROJ_ROOT / "matches" / "confirmed.jsonl"
        if not path.exists():
            pytest.skip("confirmed.jsonl not present")
        recs = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        if not recs:
            pytest.skip("confirmed.jsonl is empty")
        return recs

    def test_guaranteed_fields_present(self):
        for rec in self._records():
            for field in self.GUARANTEED:
                assert field in rec, f"guaranteed field {field!r} absent in confirmed record"

    def test_trademark_serial_is_int(self):
        for rec in self._records():
            assert isinstance(rec["trademark_serial"], int)

    def test_type_field_is_non_empty_string(self):
        for rec in self._records():
            assert isinstance(rec["type"], str) and rec["type"]

    def test_note_field_is_string(self):
        for rec in self._records():
            assert isinstance(rec["note"], str)   # empty string "" is valid


# ---------------------------------------------------------------------------
# 7. Essay frontmatter
# ---------------------------------------------------------------------------

@requires_dbs
class TestEssayFrontmatter:
    SLUG = "soundex-us1261167a"
    ENFORCED = {
        "title", "trademark_serial", "trademark",
        "tm_filing_dt", "patent_no", "patent_grant_dt", "entity",
    }
    SCAFFOLD = {"tm_reg_no", "tm_owner", "patent_assignee", "date_gap"}

    def _fm(self) -> dict:
        essay = PROJ_ROOT / "content" / f"{self.SLUG}.md"
        if not essay.exists():
            pytest.skip(f"essay {self.SLUG}.md not found")
        text = essay.read_text()
        fm: dict = {}
        m = re.match(r'^---\n(.+?)\n---', text, re.DOTALL)
        if m:
            for line in m.group(1).splitlines():
                if ':' in line:
                    k, _, v = line.partition(':')
                    fm[k.strip()] = v.strip().strip('"')
        return fm

    def test_all_enforced_keys_present_and_non_empty(self):
        fm = self._fm()
        for key in self.ENFORCED:
            assert key in fm and fm[key], f"enforced key {key!r} missing or empty"

    def test_all_scaffold_keys_present(self):
        fm = self._fm()
        for key in self.SCAFFOLD:
            assert key in fm, f"scaffold key {key!r} missing"

    def test_slug_matches_convention(self):
        fm = self._fm()
        trademark = fm.get("trademark") or "figurative"
        tm_slug = re.sub(r'[^a-z0-9]+', '-', trademark.lower()).strip('-')
        expected = f"{tm_slug}-{fm['patent_no'].lower()}"
        assert self.SLUG == expected, \
            f"slug {self.SLUG!r} doesn't match convention {expected!r}"

    def test_patent_no_resolves_in_db(self):
        fm = self._fm()
        conn = duckdb.connect(str(DB_PAT), read_only=True)
        row = conn.execute(
            "SELECT patent_no FROM patents WHERE patent_no = ?", [fm["patent_no"].upper()]
        ).fetchone()
        conn.close()
        assert row is not None, f"patent_no {fm['patent_no']!r} not in patents.duckdb"

    def test_trademark_serial_resolves_in_db(self):
        fm = self._fm()
        conn = duckdb.connect(str(DB_TM), read_only=True)
        row = conn.execute(
            "SELECT serial_no FROM case_file WHERE serial_no = ?", [int(fm["trademark_serial"])]
        ).fetchone()
        conn.close()
        assert row is not None, \
            f"trademark_serial {fm['trademark_serial']!r} not in case_file"

    def test_patent_grant_dt_matches_db(self):
        fm = self._fm()
        conn = duckdb.connect(str(DB_PAT), read_only=True)
        row = conn.execute(
            "SELECT grant_dt FROM patents WHERE patent_no = ?", [fm["patent_no"].upper()]
        ).fetchone()
        conn.close()
        if row and row[0]:
            db_grant = str(row[0])[:10]
            fm_grant = fm.get("patent_grant_dt", "")[:10]
            assert db_grant == fm_grant, \
                f"patent_grant_dt mismatch: frontmatter={fm_grant!r} db={db_grant!r}"


# ---------------------------------------------------------------------------
# 8. library/index.jsonl
# ---------------------------------------------------------------------------

class TestLibraryIndexJsonl:
    GUARANTEED = {"work_slug", "section", "passage", "context", "indexed_at"}

    def _records(self) -> list[dict]:
        if not LIB_INDEX.exists():
            pytest.skip("library/index.jsonl not present")
        recs = [json.loads(l) for l in LIB_INDEX.read_text().splitlines() if l.strip()]
        if not recs:
            pytest.skip("library/index.jsonl is empty")
        return recs

    def test_guaranteed_fields_present(self):
        for rec in self._records():
            for field in self.GUARANTEED:
                assert field in rec, f"guaranteed field {field!r} absent in index.jsonl"

    def test_year_key_present_and_nullable(self):
        for rec in self._records():
            assert "year" in rec, "year key must always be present (even if null)"
            assert rec["year"] is None or isinstance(rec["year"], int)

    def test_work_slug_non_empty(self):
        for rec in self._records():
            assert isinstance(rec["work_slug"], str) and rec["work_slug"]

    def test_passage_non_empty(self):
        for rec in self._records():
            assert isinstance(rec["passage"], str) and rec["passage"]

    def test_indexed_at_is_iso8601(self):
        for rec in self._records():
            ts = rec["indexed_at"]
            assert "T" in ts, f"indexed_at {ts!r} is not ISO8601"


# ---------------------------------------------------------------------------
# 9. library/index.duckdb — passage_embeddings
# ---------------------------------------------------------------------------

@requires_library
class TestPassageEmbeddings:
    def test_passage_embeddings_fields(self):
        conn = duckdb.connect(str(DB_EMB), read_only=True)
        rows = conn.execute(
            "SELECT work_slug, passage_id, section, passage, embedding "
            "FROM passage_embeddings LIMIT 10"
        ).fetchall()
        conn.close()
        assert len(rows) > 0
        for work_slug, passage_id, section, passage, embedding in rows:
            assert isinstance(work_slug,  str)  and work_slug
            assert isinstance(passage_id, int)  and passage_id >= 0
            assert isinstance(passage,    str)  and passage
            assert isinstance(embedding,  list) and len(embedding) == 384, \
                f"embedding dim {len(embedding)} != 384 (all-MiniLM-L6-v2)"

    def test_passage_id_range_valid(self):
        # passage_id is the index position at the time the embedding was computed.
        # CONTRACT: "Stable until markery librarian index --rebuild."
        # We only verify the range is non-negative; work_slug cross-reference is
        # only valid immediately after index --embed, not across incremental adds.
        conn = duckdb.connect(str(DB_EMB), read_only=True)
        rows = conn.execute("SELECT passage_id FROM passage_embeddings").fetchall()
        conn.close()
        for (passage_id,) in rows:
            assert passage_id >= 0, f"negative passage_id: {passage_id}"


# ---------------------------------------------------------------------------
# MANIFEST.json
# ---------------------------------------------------------------------------

class TestManifest:
    def test_manifest_exists(self):
        assert MANIFEST.exists(), "MANIFEST.json not found at repo root"

    def test_contract_version_present(self):
        data = json.loads(MANIFEST.read_text())
        assert "contract_version" in data
        assert isinstance(data["contract_version"], str)
        assert data["contract_version"], "contract_version must be non-empty"

    def test_markery_version_present(self):
        data = json.loads(MANIFEST.read_text())
        assert "markery_version" in data
        assert isinstance(data["markery_version"], str)
        assert data["markery_version"], "markery_version must be non-empty"
