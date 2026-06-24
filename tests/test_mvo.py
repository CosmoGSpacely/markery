"""MVO (Minimum Viable Output) contract tests for historian CLI commands.

Validates that card, digest, validate, and scaffold produce the required fields
and structure defined in tests/benchmarks/mvo.md. All checks are deterministic;
no LLM inference is required.

Hermetic by construction: the historian contract tests build a self-contained
synthetic repo (temp corpus DBs + a synthetic project) under tmp_path and point
the `markery` CLI at it via MARKERY_ROOT / MARKERY_DATA_DIR (see
tests/fixtures/synthetic.py). They never read the real data/ or projects/.

Real-corpus checks (trademark inspect against the live Mack bulldog, librarian
against the committed library) are marked `@pytest.mark.dataqa` and skip when
the real data is absent — they belong to the optional data-QA lane, not the
gating hermetic suite.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.fixtures.synthetic import build_synthetic_repo, run_markery

REPO_ROOT    = Path(__file__).resolve().parents[1]
DB_TM        = REPO_ROOT / "data" / "trademarks.duckdb"
DB_PAT       = REPO_ROOT / "data" / "patents.duckdb"
LIBRARY_DIR  = REPO_ROOT / "library"
LIBRARY_IDX  = LIBRARY_DIR / "index.jsonl"


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    """A self-contained synthetic Markery repo, built once per module."""
    return build_synthetic_repo(tmp_path_factory.mktemp("mvo"))


# ---------------------------------------------------------------------------
# card  (hermetic)
# ---------------------------------------------------------------------------

class TestCard:
    def _card(self, repo, slug: str | None = None) -> str:
        slug = slug or repo.cand_slug
        out, rc = run_markery(repo, "historian", "card", repo.project, slug, "--out", "-")
        assert rc == 0, f"card exited {rc}:\n{out}"
        return out

    def test_header_format(self, repo):
        out = self._card(repo)
        assert re.search(r"^## CARD: \S+  \[", out, re.MULTILINE), \
            "header line missing or malformed"

    def test_status_in_header(self, repo):
        out = self._card(repo)
        header = out.splitlines()[0]
        assert "candidate" in header or "confirmed" in header

    def test_score_in_header(self, repo):
        out = self._card(repo)
        m = re.search(r"\[\S+\s+([\d.]+)\s+", out.splitlines()[0])
        assert m, "score not found in header"
        score = float(m.group(1))
        assert 0.0 < score <= 1.0

    def test_gap_in_header(self, repo):
        out = self._card(repo)
        assert re.search(r"gap=[\d.]+y", out.splitlines()[0])

    @pytest.mark.parametrize("field", [
        "mark:", "filed:", "owner:", "goods:", "entity:",
        "patent:", "title:", "grant:", "assignee:", "cpc:", "abstract:",
        "signals:", "essay:",
    ])
    def test_required_fields_present(self, repo, field):
        out = self._card(repo)
        assert any(line.startswith(field) for line in out.splitlines()), \
            f"field '{field}' missing from card output"

    def test_serial_in_mark_line(self, repo):
        out = self._card(repo)
        mark_line = next(l for l in out.splitlines() if l.startswith("mark:"))
        serials = re.findall(r"\b7[01]\d{6}\b", mark_line)
        assert serials, "no USPTO serial number in mark: line"

    def test_patent_format(self, repo):
        out = self._card(repo)
        pat_line = next(l for l in out.splitlines() if l.startswith("patent:"))
        assert re.search(r"US\d+[A-Z]", pat_line), "patent number format invalid"

    def test_signals_has_gt_ga(self, repo):
        out = self._card(repo)
        sig_line = next(l for l in out.splitlines() if l.startswith("signals:"))
        assert "gt=" in sig_line and "ga=" in sig_line

    def test_essay_field_value(self, repo):
        out_cand = self._card(repo)
        essay_line = next(l for l in out_cand.splitlines() if l.startswith("essay:"))
        assert essay_line.strip().endswith("absent") or essay_line.strip().endswith("present")

    def test_serial_resolves_in_db(self, repo):
        import duckdb
        out = self._card(repo)
        mark_line = next(l for l in out.splitlines() if l.startswith("mark:"))
        serial = re.search(r"\b(7[01]\d{6})\b", mark_line).group(1)
        conn = duckdb.connect(str(repo.db_tm), read_only=True)
        row = conn.execute("SELECT 1 FROM case_file WHERE serial_no = ?", [int(serial)]).fetchone()
        conn.close()
        assert row is not None, f"serial {serial} not found in synthetic trademarks DB"

    def test_patent_resolves_in_db(self, repo):
        import duckdb
        out = self._card(repo)
        pat_line = next(l for l in out.splitlines() if l.startswith("patent:"))
        pat_no = re.search(r"(US\d+[A-Z])", pat_line).group(1)
        conn = duckdb.connect(str(repo.db_pat), read_only=True)
        row = conn.execute("SELECT 1 FROM patents WHERE patent_no = ?", [pat_no]).fetchone()
        conn.close()
        assert row is not None, f"patent {pat_no} not found in synthetic patents DB"


# ---------------------------------------------------------------------------
# digest  (hermetic)
# ---------------------------------------------------------------------------

class TestDigest:
    def _digest(self, repo) -> str:
        out, rc = run_markery(repo, "historian", "digest", repo.project)
        assert rc == 0, f"digest exited {rc}:\n{out}"
        return out

    def test_header_format(self, repo):
        out = self._digest(repo)
        assert re.search(r"^## DIGEST: \S+  \[", out, re.MULTILINE)

    def test_queue_line_present(self, repo):
        out = self._digest(repo)
        queue_line = next((l for l in out.splitlines() if l.startswith("queue:")), None)
        assert queue_line is not None, "queue: line missing"

    def test_queue_fields(self, repo):
        out = self._digest(repo)
        queue_line = next(l for l in out.splitlines() if l.startswith("queue:"))
        for field in ("confirmed=", "rejected=", "unreviewed≥", "total_candidates="):
            assert field in queue_line, f"'{field}' missing from queue: line"

    def test_queue_counts_are_integers(self, repo):
        out = self._digest(repo)
        queue_line = next(l for l in out.splitlines() if l.startswith("queue:"))
        counts = re.findall(r"=(\d+)", queue_line)
        assert len(counts) == 4, "expected 4 integer counts in queue: line"
        assert all(int(c) >= 0 for c in counts)

    def test_next_review_present_when_unreviewed(self, repo):
        out = self._digest(repo)
        queue_line = next(l for l in out.splitlines() if l.startswith("queue:"))
        m = re.search(r"unreviewed≥[\d.]+?=(\d+)", queue_line)
        unreviewed = int(m.group(1)) if m else 0
        if unreviewed > 0:
            assert "next_review" in out, "next_review section missing despite unreviewed > 0"

    def test_enrichment_line_present(self, repo):
        out = self._digest(repo)
        assert any("enrichment:" in l for l in out.splitlines())

    def test_preflight_line_present(self, repo):
        out = self._digest(repo)
        assert any("preflight:" in l for l in out.splitlines())


# ---------------------------------------------------------------------------
# validate  (hermetic)
# ---------------------------------------------------------------------------

class TestValidate:
    EXPECTED_CHECKS = {
        "title_present",
        "trademark_present",
        "serial_resolves",
        "patent_resolves",
        "grant_date_matches",
        "filing_date_in_body",
        "entity_recognised",
        "no_cross_contamination",
    }

    def _validate(self, repo) -> tuple[str, int]:
        return run_markery(repo, "historian", "validate", repo.project, repo.conf_slug)

    def test_exit_zero_on_all_pass(self, repo):
        _, rc = self._validate(repo)
        assert rc == 0

    def test_eight_check_lines(self, repo):
        out, _ = self._validate(repo)
        check_lines = [l for l in out.splitlines() if re.match(r"\s+(PASS|FAIL)\s+\w", l)]
        assert len(check_lines) == 8, f"expected 8 check lines, got {len(check_lines)}"

    def test_all_check_names_present(self, repo):
        out, _ = self._validate(repo)
        for name in self.EXPECTED_CHECKS:
            assert name in out, f"check '{name}' not found in validate output"

    def test_all_pass_message(self, repo):
        out, _ = self._validate(repo)
        assert "All checks passed." in out

    def test_no_fail_lines(self, repo):
        out, _ = self._validate(repo)
        fail_lines = [l for l in out.splitlines() if re.match(r"\s+FAIL\s+", l)]
        assert fail_lines == [], f"unexpected FAIL lines: {fail_lines}"


# ---------------------------------------------------------------------------
# scaffold  (hermetic)
# ---------------------------------------------------------------------------

REQUIRED_FRONTMATTER_KEYS = [
    "title", "trademark_serial", "trademark", "tm_filing_dt",
    "patent_no", "patent_grant_dt", "entity",
]

REQUIRED_SECTIONS = [
    "## Primary Sources",
    "## The Invention",
    "## The Mark",
    "## The Connection",
    "## Historical Context",
    "## Significance",
]


class TestScaffold:
    """Scaffold a confirmed pair that has no essay yet (writes a fresh file)."""

    def _scaffold(self, repo) -> tuple[str, int]:
        return run_markery(repo, "historian", "scaffold", repo.project, repo.scaf_slug, "--force")

    def _essay_path(self, repo) -> Path:
        return repo.root / "projects" / repo.project / "content" / f"{repo.scaf_slug}.md"

    def test_exit_zero(self, repo):
        _, rc = self._scaffold(repo)
        assert rc == 0

    def test_stdout_written_message(self, repo):
        out, _ = self._scaffold(repo)
        assert "Scaffold written →" in out

    def test_file_created(self, repo):
        self._scaffold(repo)
        assert self._essay_path(repo).exists(), "essay file not created"

    def test_frontmatter_block(self, repo):
        self._scaffold(repo)
        text = self._essay_path(repo).read_text(encoding="utf-8")
        assert text.startswith("---"), "file does not begin with frontmatter block"
        assert "---\n" in text[3:], "frontmatter block not closed"

    @pytest.mark.parametrize("key", REQUIRED_FRONTMATTER_KEYS)
    def test_frontmatter_key_present(self, repo, key):
        self._scaffold(repo)
        text = self._essay_path(repo).read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
        assert fm_match, "could not parse frontmatter"
        fm_text = fm_match.group(1)
        assert re.search(rf"^{key}:", fm_text, re.MULTILINE), \
            f"frontmatter key '{key}' missing"

    def test_trademark_serial_is_digits(self, repo):
        self._scaffold(repo)
        text = self._essay_path(repo).read_text(encoding="utf-8")
        m = re.search(r"^trademark_serial:\s*(\d+)", text, re.MULTILINE)
        assert m, "trademark_serial is not a bare integer"

    def test_patent_no_format(self, repo):
        self._scaffold(repo)
        text = self._essay_path(repo).read_text(encoding="utf-8")
        m = re.search(r'^patent_no:\s*"?(US\d+[A-Z])"?', text, re.MULTILINE)
        assert m, "patent_no format invalid or missing"

    def test_filing_date_format(self, repo):
        self._scaffold(repo)
        text = self._essay_path(repo).read_text(encoding="utf-8")
        m = re.search(r'^tm_filing_dt:\s*"?(\d{4}-\d{2}-\d{2})"?', text, re.MULTILINE)
        assert m, "tm_filing_dt date format invalid"

    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_section_header_present(self, repo, section):
        self._scaffold(repo)
        text = self._essay_path(repo).read_text(encoding="utf-8")
        assert section in text, f"section '{section}' missing from scaffold"


# ---------------------------------------------------------------------------
# design_codes.describe — pure, no DB required (hermetic)
# ---------------------------------------------------------------------------

class TestDesignCodeDescribe:
    def test_known_section(self):
        from markery.specialist.trademark.design_codes import describe
        d = describe("030108")
        assert "Animals" in d and "bulldog" in d.lower()

    def test_category_decomposition(self):
        from markery.specialist.trademark.design_codes import describe
        d = describe("260103")  # geometric figures, unknown section
        assert "Geometric" in d
        assert "division 01" in d and "section 03" in d

    def test_bad_format(self):
        from markery.specialist.trademark.design_codes import describe
        assert "unrecognised" in describe("03A1")


# ===========================================================================
# Data-QA lane — real-corpus checks. Marked @pytest.mark.dataqa; skip when the
# committed data/ or library/ is absent. Not part of the gating hermetic suite.
# ===========================================================================

requires_dbs = pytest.mark.skipif(
    not DB_TM.exists() or not DB_PAT.exists(),
    reason="data DBs not present",
)

_library_works = LIBRARY_DIR / "works"
requires_library = pytest.mark.skipif(
    not _library_works.exists() or not any(_library_works.iterdir()),
    reason="library/works not present or empty",
)

requires_library_index = pytest.mark.skipif(
    not LIBRARY_IDX.exists(),
    reason="library/index.jsonl absent; run: markery librarian index",
)


def _run(*args: str) -> tuple[str, int]:
    import subprocess
    result = subprocess.run(list(args), capture_output=True, text=True)
    return result.stdout + result.stderr, result.returncode


@pytest.mark.dataqa
@requires_library
class TestLibrarian:
    """MVO contracts for librarian commands against the real library (mvo.md §librarian)."""

    SEARCH_QUERY = "trademark"

    def test_index_exits_0(self):
        out, rc = _run("markery", "librarian", "index")
        assert rc == 0, f"librarian index exited {rc}:\n{out}"

    def test_index_output_contains_work_count(self):
        out, rc = _run("markery", "librarian", "index")
        assert rc == 0
        assert re.search(r"Indexed \d+ work\(s\)", out), \
            "output does not contain 'Indexed N work(s)' line"

    def test_list_exits_0(self):
        out, rc = _run("markery", "librarian", "list")
        assert rc == 0, f"librarian list exited {rc}:\n{out}"

    def test_list_output_contains_slug(self):
        out, rc = _run("markery", "librarian", "list")
        assert rc == 0
        works_dir = LIBRARY_DIR / "works"
        known_slug = next(p.name for p in works_dir.iterdir() if p.is_dir())
        assert known_slug in out, f"slug '{known_slug}' not found in list output"

    @requires_library_index
    def test_search_exits_0(self):
        out, rc = _run("markery", "librarian", "search", self.SEARCH_QUERY)
        assert rc == 0, f"librarian search exited {rc}:\n{out}"

    @requires_library_index
    def test_search_output_has_header_line(self):
        out, rc = _run("markery", "librarian", "search", self.SEARCH_QUERY)
        assert rc == 0
        assert "AUTHOR" in out and "SECTION" in out, \
            "search output header line missing expected columns"

    @requires_library_index
    def test_card_exits_0(self):
        out, rc = _run(
            "markery", "librarian", "card", self.SEARCH_QUERY,
            "--out", "-", "--mode", "keyword",
        )
        assert rc == 0, f"librarian card exited {rc}:\n{out}"

    @requires_library_index
    def test_card_output_contains_header(self):
        out, rc = _run(
            "markery", "librarian", "card", self.SEARCH_QUERY,
            "--out", "-", "--mode", "keyword",
        )
        assert rc == 0
        assert "# Library card:" in out, "card output missing '# Library card:' header"

    @requires_library_index
    def test_card_output_contains_passage(self):
        out, rc = _run(
            "markery", "librarian", "card", self.SEARCH_QUERY,
            "--out", "-", "--mode", "keyword",
        )
        assert rc == 0
        assert '"' in out, "card output contains no quoted passage lines"


@pytest.mark.dataqa
@requires_dbs
class TestTrademarkInspect:
    """MVO contract for `markery trademark inspect <serial>` against real data.

    Fixture: the Mack bulldog, serial 71247861 — a purely figurative mark with
    design search code 030108, mark image present, owner MACK TRUCKS, INC.
    """
    BULLDOG = "71247861"

    def _inspect(self, serial: str) -> tuple[str, int]:
        return _run("markery", "trademark", "inspect", serial)

    def test_exit_zero(self):
        _out, rc = self._inspect(self.BULLDOG)
        assert rc == 0

    def test_header_and_core_fields(self):
        out, _ = self._inspect(self.BULLDOG)
        assert out.startswith(f"## TRADEMARK {self.BULLDOG}")
        for field in ("mark:", "filed:", "registration:", "owner:", "goods:", "image:"):
            assert field in out, f"missing field line: {field}"

    def test_figurative_marked(self):
        out, _ = self._inspect(self.BULLDOG)
        assert "(figurative" in out  # null mark text → figurative label

    def test_image_available(self):
        out, _ = self._inspect(self.BULLDOG)
        assert "image:         available" in out

    def test_design_code_described(self):
        out, _ = self._inspect(self.BULLDOG)
        assert "030108" in out
        assert "bulldog" in out.lower()  # human-readable gloss, not just the code

    def test_missing_serial_exits_nonzero(self):
        _out, rc = self._inspect("99999999")
        assert rc != 0
