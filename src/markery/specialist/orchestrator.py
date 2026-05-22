"""Cross-specialist operation dispatch.

Policy (G5): any call that crosses a specialist boundary routes through this
module.  Callers import from here; they do not import from other specialists
directly.  This gives a single auditable place to:

  - see every operation that crosses a specialist boundary
  - apply rate limiting, retry logic, or permission checks in the future
  - keep specialist internal APIs from leaking into unrelated callers

All imports from other specialists are deferred (inside each function) so that
importing this module does not pull in every specialist's dependencies.

Current operations
------------------
project_type              common              → return the declared ProjectType for a project root
enrich_signal_fields      patent specialist   → add text signals to candidates.jsonl (MATCH_REVIEW_ESSAY only)
fetch_patent              patent specialist   → fetch one patent from EPO; upsert patents.duckdb
fetch_patent_citations    patent specialist   → fetch backward citations; pull new patents from EPO
fetch_trademark           trademark specialist → fetch one mark from TSDR; upsert extended_marks
entity_forward_report     matchmaker (cross)  → list post-1939 extended marks for a named entity
"""

from __future__ import annotations

from pathlib import Path


def project_type(path: Path):
    """Return the declared ProjectType for the project at path.

    Delegates to load_project(). Raises FileNotFoundError if project.json is
    absent — run 'markery project adopt <name>' to declare the project type.
    """
    from markery.common.project import load_project
    return load_project(path).type


def fetch_patent(patent_no: str) -> bool:
    """Fetch a single patent from EPO OPS and upsert into patents.duckdb.

    Returns True if the patent was found and stored, False if EPO returned 404.
    """
    from markery.specialist.patent.build import open_db
    from markery.specialist.patent.fetch import fetch_patent_record
    from markery.specialist.patent.epo_client import EPOClient
    from markery.common.auth import load_epo_credentials
    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)
    conn   = open_db()
    try:
        return fetch_patent_record(patent_no, client, conn)
    finally:
        conn.close()


def fetch_patent_citations(patent_no: str) -> int:
    """Fetch backward citations for a patent and pull any new cited patents into patents.duckdb.

    Returns count of new patents added.
    """
    from markery.specialist.patent.build import open_db
    from markery.specialist.patent.fetch import fetch_citation_chain
    from markery.specialist.patent.epo_client import EPOClient
    from markery.common.auth import load_epo_credentials
    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)
    conn   = open_db()
    try:
        return fetch_citation_chain(patent_no, client, conn)
    finally:
        conn.close()


def fetch_trademark(serial_no: str, force: bool = False) -> bool:
    """Fetch a single trademark from TSDR and upsert into extended_marks.

    Returns True if stored, False if TSDR returned 404 or record already exists
    (pass force=True to re-fetch existing records).
    """
    from markery.specialist.trademark.build import open_db
    from markery.specialist.trademark.fetch import fetch_mark_record
    from markery.specialist.trademark.tsdr_client import TSDRClient
    from markery.common.auth import load_tsdr_key
    client = TSDRClient(load_tsdr_key())
    conn   = open_db()
    try:
        return fetch_mark_record(serial_no, client, conn, force=force)
    finally:
        conn.close()


def entity_forward_report(entity_name: str, after_year: int = 1939) -> list[dict]:
    """Return extended marks for a named entity filed after after_year.

    Joins entity_name_variant with extended_marks via cross-specialist ATTACH.
    Returns [] if no matches found.
    """
    from markery.specialist.matchmaker.link import entity_forward_report as _report
    return _report(entity_name, after_year)


def enrich_signal_fields(candidates_path: Path) -> int:
    """Enrich candidates.jsonl with text-match signals via the patent specialist.

    Adds title_name_hit, abstract_name_hit, goods_title_overlap,
    goods_abstract_overlap to each candidate row by reading patents.duckdb
    and trademarks.duckdb through the patent specialist's published API.

    Requires a MATCH_REVIEW_ESSAY project. Raises TypeError if the project
    type is set and differs. Raises FileNotFoundError if project.json is absent.

    Returns the count of candidates enriched.
    """
    from markery.common.project import ProjectType, load_project
    project_root = candidates_path.parent.parent
    proj = load_project(project_root)
    if proj.type != ProjectType.MATCH_REVIEW_ESSAY:
        raise TypeError(
            f"enrich_signal_fields requires a match-review-essay project; "
            f"'{project_root.name}' declares type '{proj.type.value}'. "
            f"Check {project_root / 'project.json'}."
        )
    from markery.specialist.patent.signals import enrich_candidates
    return enrich_candidates(candidates_path)
