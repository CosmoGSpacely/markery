"""Scaffold builds a resolvable Google Patents link (full doc id, not bare number)."""

from __future__ import annotations

from tests.fixtures.synthetic import build_synthetic_repo, run_markery, PROJECT, SCAF_PATENT


def test_scaffold_patent_url_is_full_doc_id(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    out, rc = run_markery(repo, "historian", "scaffold", PROJECT, "measurex-us1999003a")
    assert rc == 0, out
    scaffold = repo.root / "projects" / PROJECT / "content" / "measurex-us1999003a.md"
    body = scaffold.read_text(encoding="utf-8")
    # Full document id (US1999003A) → resolves on Google Patents…
    assert f"patents.google.com/patent/{SCAF_PATENT}" in body
    # …not the bare number (US1389147A→1389147 style), which 404s.
    assert "patents.google.com/patent/1999003" not in body
