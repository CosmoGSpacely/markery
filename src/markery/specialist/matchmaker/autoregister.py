"""Auto entity registration from the corpus (Phase 28 P2).

Derives `company_entity` + `entity_name_variant` from corpus owner/assignee
strings, and `person_entity` + `person_name_variant` from `patent_inventors`,
so projects no longer require hand-written entities.csv / variants.csv. The
spawning pipeline (Phase 32) calls these; a human-confirm gate stays at the CLI.

Pure proposal functions (read-only, return dicts) are separated from the commit
functions (write to entities.duckdb) so callers can show a proposal before it
lands.
"""

from __future__ import annotations

import re

import duckdb

# ---------------------------------------------------------------------------
# Name normalisation + variant ranking (shared with suggest-variants)
# ---------------------------------------------------------------------------

_ABBREV = {
    r"\bINCORPORATED\b": "INC",
    r"\bCORPORATION\b":  "CORP",
    r"\bCOMPANY\b":      "CO",
    r"\bLIMITED\b":      "LTD",
    r"\bMANUFACTURING\b": "MFG",
    r"\bBROTHERS\b":     "BROS",
}
_STRIP = re.compile(r"\b(INC\.?|CORP\.?|CO\.?|LTD\.?|MFG\.?|THE)\b|[,.]", re.I)


def normalise_name(s: str) -> str:
    s = s.upper()
    for pat, repl in _ABBREV.items():
        s = re.sub(pat, repl, s)
    s = _STRIP.sub(" ", s)
    return " ".join(s.split())


def score_names(query_tokens: set[str], candidate: str) -> float:
    cand_tokens = set(normalise_name(candidate).split())
    if not cand_tokens or not query_tokens:
        return 0.0
    overlap = query_tokens & cand_tokens
    return len(overlap) / len(query_tokens | cand_tokens)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

def _rank(query_tokens: set[str], rows: list[tuple], min_score: float, top: int) -> list[dict]:
    scored = [
        {"name": name, "count": count, "score": score_names(query_tokens, name)}
        for name, count in rows
    ]
    return sorted(
        [r for r in scored if r["score"] >= min_score],
        key=lambda r: (-r["score"], -r["count"]),
    )[:top]


def propose_company(
    conn_pat: duckdb.DuckDBPyConnection,
    conn_tm: duckdb.DuckDBPyConnection,
    canonical: str,
    min_score: float = 0.3,
    top: int = 10,
) -> dict:
    """Propose a company_entity + variants for ``canonical`` from corpus strings.

    Read-only: returns {canonical, variants:[{name, source, count, score}]}.
    No entity_id is assigned until commit_company."""
    query_tokens = set(normalise_name(canonical).split())

    pat_rows = conn_pat.execute(
        "SELECT assignee_name, COUNT(*) AS n FROM patents "
        "WHERE assignee_name IS NOT NULL AND assignee_name != '' "
        "GROUP BY assignee_name ORDER BY n DESC"
    ).fetchall()
    tm_rows = conn_tm.execute(
        "SELECT own_name, COUNT(*) AS n FROM owner "
        "WHERE own_name IS NOT NULL AND own_name != '' "
        "GROUP BY own_name ORDER BY n DESC"
    ).fetchall()

    variants: list[dict] = []
    for r in _rank(query_tokens, pat_rows, min_score, top):
        variants.append({**r, "source": "patent_assignee"})
    for r in _rank(query_tokens, tm_rows, min_score, top):
        variants.append({**r, "source": "trademark_owner"})
    return {"canonical": canonical, "variants": variants}


def commit_company(
    conn_ent: duckdb.DuckDBPyConnection,
    proposal: dict,
    entity_type: str | None = None,
    industry: str | None = None,
) -> dict:
    """Write a proposed company_entity + its variants. Idempotent.

    If a company with the same canonical_name exists, variants are added to it;
    otherwise a new entity_id (MAX+1) is assigned. Returns
    {entity_id, created, variants_added}."""
    canonical = proposal["canonical"]
    existing = conn_ent.execute(
        "SELECT entity_id FROM company_entity WHERE canonical_name = ?", [canonical]
    ).fetchone()
    if existing:
        eid, created = existing[0], False
    else:
        eid = (conn_ent.execute(
            "SELECT COALESCE(MAX(entity_id), 0) FROM company_entity"
        ).fetchone()[0]) + 1
        conn_ent.execute(
            "INSERT INTO company_entity (entity_id, canonical_name, entity_type, industry) "
            "VALUES (?, ?, ?, ?)", [eid, canonical, entity_type, industry],
        )
        created = True

    next_vid = (conn_ent.execute(
        "SELECT COALESCE(MAX(variant_id), 0) FROM entity_name_variant"
    ).fetchone()[0]) + 1
    added = 0
    for v in proposal["variants"]:
        name, source = v["name"], v["source"]
        if conn_ent.execute(
            "SELECT 1 FROM entity_name_variant WHERE entity_id=? AND variant_name=? AND source=?",
            [eid, name, source],
        ).fetchone():
            continue
        conn_ent.execute(
            "INSERT INTO entity_name_variant VALUES (?, ?, ?, ?)",
            [next_vid, eid, name, source],
        )
        next_vid += 1
        added += 1
    conn_ent.commit()
    return {"entity_id": eid, "created": created, "variants_added": added}


# ---------------------------------------------------------------------------
# People (inventors)
# ---------------------------------------------------------------------------

def _canonical_person(raw: str) -> str:
    """Human-readable canonical from a raw inventor string.

    Corpus inventor names arrive in mixed forms; we keep the surface form but
    collapse whitespace. (Fuzzy cross-spelling clustering is left to a later pass.)"""
    return " ".join(raw.split())


def propose_people_from_inventors(
    conn_ent: duckdb.DuckDBPyConnection,
    conn_pat: duckdb.DuckDBPyConnection,
    min_patents: int = 1,
    limit: int | None = None,
) -> list[dict]:
    """Propose person_entity rows from patent_inventors.

    Read-only: returns [{canonical, slug, patent_count, variants:[raw_name]}],
    skipping inventors already registered (by variant_name) and assigning
    collision-free stable slugs. No rows are written."""
    rows = conn_pat.execute(
        "SELECT inventor_name, COUNT(DISTINCT patent_no) AS n FROM patent_inventors "
        "WHERE inventor_name IS NOT NULL AND inventor_name != '' "
        "GROUP BY inventor_name HAVING n >= ? ORDER BY n DESC, inventor_name",
        [min_patents],
    ).fetchall()

    existing_variants = {
        r[0] for r in conn_ent.execute(
            "SELECT variant_name FROM person_name_variant"
        ).fetchall()
    }
    used_slugs = {
        r[0] for r in conn_ent.execute("SELECT slug FROM person_entity").fetchall()
    }

    proposals: list[dict] = []
    for raw, n in rows:
        if raw in existing_variants:
            continue
        canonical = _canonical_person(raw)
        base = slugify(canonical) or "person"
        slug, i = base, 2
        while slug in used_slugs:
            slug = f"{base}-{i}"
            i += 1
        used_slugs.add(slug)
        proposals.append({
            "canonical": canonical, "slug": slug,
            "patent_count": n, "variants": [raw],
        })
        if limit is not None and len(proposals) >= limit:
            break
    return proposals


def commit_people(conn_ent: duckdb.DuckDBPyConnection, proposals: list[dict],
                  kind: str = "inventor") -> dict:
    """Write proposed person_entity + person_name_variant rows. Returns counts."""
    next_pid = (conn_ent.execute(
        "SELECT COALESCE(MAX(person_id), 0) FROM person_entity"
    ).fetchone()[0]) + 1
    next_vid = (conn_ent.execute(
        "SELECT COALESCE(MAX(variant_id), 0) FROM person_name_variant"
    ).fetchone()[0]) + 1
    people = variants = 0
    for p in proposals:
        conn_ent.execute(
            "INSERT INTO person_entity (person_id, canonical_name, slug, kind) "
            "VALUES (?, ?, ?, ?)", [next_pid, p["canonical"], p["slug"], kind],
        )
        people += 1
        for vname in p["variants"]:
            conn_ent.execute(
                "INSERT INTO person_name_variant VALUES (?, ?, ?, ?)",
                [next_vid, next_pid, vname, f"patent_{kind}" if kind == "inventor" else kind],
            )
            next_vid += 1
            variants += 1
        next_pid += 1
    conn_ent.commit()
    return {"people_added": people, "variants_added": variants}
