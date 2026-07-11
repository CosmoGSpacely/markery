"""Entity registry for MATCHMAKER specialist.

Owns entities.duckdb: company_entity and entity_name_variant tables.
Entity data lives in per-project CSV files (entities.csv, variants.csv).
Running `markery matchmaker build --data-dir <project-dir>` reads those files
and inserts any new rows.

Entry points:
    open_db(db_path)              Open entities.duckdb and ensure schema exists.
    build(data_dir, db_path)      Idempotent seed insert from CSV; returns counts.
    list_entities(conn)           Return all entities ordered by entity_id.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import duckdb

from markery.common.config import DB
from markery.common.dbutil import scalar as _scalar, next_id as _next_id

DDL = """
CREATE TABLE IF NOT EXISTS company_entity (
    entity_id      INTEGER PRIMARY KEY,  -- contract: INTEGER, NOT NULL
    canonical_name VARCHAR NOT NULL,     -- contract: VARCHAR, NOT NULL — human-readable name, e.g. 'Remington Rand'
    entity_type    VARCHAR,
    industry       VARCHAR,
    slug           VARCHAR,               -- stored, immutable identity slug (never re-derived at render)
    founded        VARCHAR,               -- optional ISO year/date the firm was founded
    dissolved      VARCHAR                -- optional ISO year/date the firm was dissolved
);

CREATE TABLE IF NOT EXISTS entity_name_variant (
    variant_id   INTEGER PRIMARY KEY,
    entity_id    INTEGER NOT NULL REFERENCES company_entity(entity_id),  -- contract: INTEGER, NOT NULL
    variant_name VARCHAR NOT NULL,  -- contract: VARCHAR, NOT NULL — uppercase string used in assignee/owner searches
    source       VARCHAR NOT NULL   -- contract: VARCHAR, NOT NULL — one of: patent_assignee | trademark_owner | trademark_search
);

-- Succession / M&A between DISTINCT real firms (Decision 1). A historical fact,
-- never a merge: Westinghouse Electric & Mfg Co --renamed_to--> Westinghouse
-- Electric Corporation (1945). Both may earn their own entity focus.
CREATE TABLE IF NOT EXISTS entity_relation (
    from_entity    INTEGER NOT NULL REFERENCES company_entity(entity_id),
    to_entity      INTEGER NOT NULL REFERENCES company_entity(entity_id),
    kind           VARCHAR NOT NULL,   -- renamed_to | merged_into | acquired_by | succeeded_by | subsidiary_of
    effective_date VARCHAR,            -- optional ISO date the relation took effect
    source         VARCHAR
);

-- Dedup merge (Decision 1). Records that were ALWAYS the same real firm collapse
-- to one survivor id; the retired id/slug redirects so URLs and cross-links keep
-- resolving. Not a historical event — distinct from entity_relation.
CREATE TABLE IF NOT EXISTS entity_alias (
    retired_id   INTEGER NOT NULL,
    retired_slug VARCHAR,             -- retained so [[entity:<retired_slug>]] redirects even if the row is deleted
    survivor_id  INTEGER NOT NULL REFERENCES company_entity(entity_id)
);

-- People as first-class data-layer entities (Phase 28 P2 — data-model half of D072).
-- Inventors (from patent_inventors) and notable founders, deduplicated to a stable
-- identity with a stable slug. Narrative/rendering (essays, People nav) stays in D072.
CREATE TABLE IF NOT EXISTS person_entity (
    person_id      INTEGER PRIMARY KEY,
    canonical_name VARCHAR NOT NULL,
    slug           VARCHAR NOT NULL UNIQUE,  -- stable URL/identity slug
    kind           VARCHAR                   -- 'inventor' | 'founder' | …
);

CREATE TABLE IF NOT EXISTS person_name_variant (
    variant_id   INTEGER PRIMARY KEY,
    person_id    INTEGER NOT NULL REFERENCES person_entity(person_id),
    variant_name VARCHAR NOT NULL,           -- raw corpus string (e.g. patent_inventors.inventor_name)
    source       VARCHAR NOT NULL            -- 'patent_inventor' | 'founder'
);

-- Person dedup merge — same discipline as entity_alias.
CREATE TABLE IF NOT EXISTS person_alias (
    retired_id   INTEGER NOT NULL,
    retired_slug VARCHAR,
    survivor_id  INTEGER NOT NULL REFERENCES person_entity(person_id)
);
"""


def _migrate_drop_notes(conn: duckdb.DuckDBPyConnection) -> None:
    """One-time migration: remove the notes column from company_entity.

    The FK on entity_name_variant blocks ALTER TABLE DROP COLUMN, so we rebuild
    both tables: save rows, drop both, recreate without notes, re-insert.
    """
    try:
        cols = {r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'company_entity'"
        ).fetchall()}
        if "notes" not in cols:
            return

        entities = conn.execute(
            "SELECT entity_id, canonical_name, entity_type, industry FROM company_entity"
        ).fetchall()
        variants = conn.execute(
            "SELECT variant_id, entity_id, variant_name, source FROM entity_name_variant"
        ).fetchall()

        conn.execute("DROP TABLE entity_name_variant")
        conn.execute("DROP TABLE company_entity")
        conn.execute(DDL)

        for row in entities:
            conn.execute(
                "INSERT INTO company_entity "
                "(entity_id, canonical_name, entity_type, industry) VALUES (?, ?, ?, ?)",
                list(row),
            )
        for row in variants:
            conn.execute(
                "INSERT INTO entity_name_variant VALUES (?, ?, ?, ?)", list(row)
            )
        conn.commit()
    except Exception:
        pass


def _migrate_add_registry_columns(conn: duckdb.DuckDBPyConnection) -> None:
    """Add slug/founded/dissolved to a legacy company_entity and backfill slugs.

    Idempotent: ALTER ... ADD COLUMN only runs when the column is absent; slug
    backfill only touches rows whose slug is NULL. Runs after DDL so the columns
    are created for fresh DBs and added for pre-Phase-34 ones.
    """
    from markery.specialist.matchmaker.autoregister import slugify

    cols = {r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'company_entity'"
    ).fetchall()}
    for col in ("slug", "founded", "dissolved"):
        if col not in cols:
            conn.execute(f"ALTER TABLE company_entity ADD COLUMN {col} VARCHAR")

    missing = conn.execute(
        "SELECT entity_id, canonical_name FROM company_entity "
        "WHERE slug IS NULL OR slug = '' ORDER BY entity_id"
    ).fetchall()
    if missing:
        taken = {
            r[0] for r in conn.execute(
                "SELECT slug FROM company_entity WHERE slug IS NOT NULL AND slug <> ''"
            ).fetchall()
        }
        for eid, name in missing:
            slug = _unique_slug(slugify(name or f"entity-{eid}"), taken)
            taken.add(slug)
            conn.execute(
                "UPDATE company_entity SET slug = ? WHERE entity_id = ?", [slug, eid]
            )
    conn.commit()


def _unique_slug(base: str, taken: set[str]) -> str:
    """Return base, or base-2/base-3/... — the first not already in taken."""
    base = base or "entity"
    if base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"


def open_db(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open entities.duckdb and ensure schema exists."""
    path = str(db_path or DB["entities"])
    conn = duckdb.connect(path)
    # Migration must run before DDL: DuckDB 1.5.x registers REFERENCES clauses from
    # CREATE TABLE IF NOT EXISTS even when the table already exists, which would make
    # the subsequent DROP TABLE fail with a dependency error.
    _migrate_drop_notes(conn)
    conn.execute(DDL)
    _migrate_add_registry_columns(conn)
    return conn


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build(data_dir: str | Path, db_path: str | Path | None = None) -> dict[str, int]:
    """Insert entities and variants from CSV files in data_dir. Idempotent.

    Reads entities.csv (entity_id, canonical_name, entity_type, industry) and
    variants.csv (entity_id, variant_name, source). Skips existing rows.
    Returns {"entities": n_added, "variants": n_added}.
    """
    data_dir = Path(data_dir)
    entities = _read_csv(data_dir / "entities.csv")
    variants = _read_csv(data_dir / "variants.csv")

    from markery.specialist.matchmaker.autoregister import slugify

    conn = open_db(db_path)

    taken_slugs = {
        r[0] for r in conn.execute(
            "SELECT slug FROM company_entity WHERE slug IS NOT NULL AND slug <> ''"
        ).fetchall()
    }

    added_entities = 0
    for row in entities:
        eid = int(row["entity_id"])
        existing = conn.execute(
            "SELECT canonical_name FROM company_entity WHERE entity_id = ?", [eid]
        ).fetchone()
        if existing:
            if existing[0] != row["canonical_name"]:
                conn.close()
                raise ValueError(
                    f"entity_id {eid} is already registered as '{existing[0]}' — "
                    f"cannot overwrite with '{row['canonical_name']}'. "
                    f"Assign a different entity_id in {Path(data_dir) / 'entities.csv'}."
                )
            # Same name — idempotent skip
        else:
            slug = _unique_slug(
                (row.get("slug") or "").strip() or slugify(row["canonical_name"]),
                taken_slugs,
            )
            taken_slugs.add(slug)
            conn.execute(
                "INSERT INTO company_entity "
                "(entity_id, canonical_name, entity_type, industry, slug, founded, dissolved) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [eid, row["canonical_name"], row.get("entity_type"), row.get("industry"),
                 slug, (row.get("founded") or None), (row.get("dissolved") or None)],
            )
            added_entities += 1

    _VALID_SOURCES = {"patent_assignee", "trademark_owner", "trademark_search"}
    for i, row in enumerate(variants, start=2):
        source = row.get("source", "")
        if source not in _VALID_SOURCES:
            conn.close()
            print(
                f"ERROR: variants.csv row {i}: source={source!r} is not in "
                f"{sorted(_VALID_SOURCES)}. "
                f"If variant_name contains a comma, quote the field.",
                file=sys.stderr,
            )
            sys.exit(1)

    added_variants = 0
    next_id = _next_id(conn, "entity_name_variant", "variant_id")
    for row in variants:
        eid = int(row["entity_id"])
        vname = row["variant_name"]
        source = row["source"]
        if not conn.execute(
            """SELECT 1 FROM entity_name_variant
               WHERE entity_id = ? AND variant_name = ? AND source = ?""",
            [eid, vname, source],
        ).fetchone():
            conn.execute(
                "INSERT INTO entity_name_variant VALUES (?, ?, ?, ?)",
                [next_id, eid, vname, source],
            )
            next_id += 1
            added_variants += 1

    conn.commit()
    export_registry(conn)
    conn.close()
    return {"entities": added_entities, "variants": added_variants}


def clear(
    data_dir: str | Path,
    db_path: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Delete company_entity and entity_name_variant rows for entity IDs in entities.csv.

    Reads entity_id values from data_dir/entities.csv.
    Returns {"entities": n, "variants": n} — rows deleted (or that would be deleted on dry_run).
    The FK constraint on entity_name_variant requires variants to be deleted before entities.
    """
    data_dir = Path(data_dir)
    entities_csv = data_dir / "entities.csv"
    if not entities_csv.exists():
        raise FileNotFoundError(f"entities.csv not found at {entities_csv}")

    entity_ids = [int(r["entity_id"]) for r in _read_csv(entities_csv)]
    if not entity_ids:
        return {"entities": 0, "variants": 0}

    conn = open_db(db_path)
    placeholders = ",".join("?" * len(entity_ids))

    n_variants = _scalar(conn,
        f"SELECT count(*) FROM entity_name_variant WHERE entity_id IN ({placeholders})",
        entity_ids)
    n_entities = _scalar(conn,
        f"SELECT count(*) FROM company_entity WHERE entity_id IN ({placeholders})",
        entity_ids)

    if not dry_run:
        conn.execute(
            f"DELETE FROM entity_name_variant WHERE entity_id IN ({placeholders})",
            entity_ids,
        )
        conn.execute(
            f"DELETE FROM company_entity WHERE entity_id IN ({placeholders})",
            entity_ids,
        )
        conn.commit()
        export_registry(conn)

    conn.close()
    return {"entities": n_entities, "variants": n_variants}


# ---------------------------------------------------------------------------
# Dedup merge vs. succession/M&A (Phase 35) — kept strictly separate
# ---------------------------------------------------------------------------

# entity_relation.kind — genuine history between DISTINCT firms. Never a merge.
VALID_RELATION_KINDS = {
    "renamed_to", "merged_into", "acquired_by", "succeeded_by", "subsidiary_of",
}


def next_entity_id(conn: duckdb.DuckDBPyConnection) -> int:
    """Next free company entity id, never reusing a retired (aliased) id.

    A retired id is permanently burned: entity_alias references it for URL redirects,
    so handing it to a *different* firm would conflate the two. Reserve past every id
    that has ever existed by taking MAX over live rows and retired aliases.
    """
    live = _scalar(conn, "SELECT COALESCE(MAX(entity_id), 0) FROM company_entity")
    retired = _scalar(conn, "SELECT COALESCE(MAX(retired_id), 0) FROM entity_alias")
    return max(live, retired) + 1


def next_person_id(conn: duckdb.DuckDBPyConnection) -> int:
    """Next free person id, never reusing a retired (aliased) id. See next_entity_id."""
    live = _scalar(conn, "SELECT COALESCE(MAX(person_id), 0) FROM person_entity")
    retired = _scalar(conn, "SELECT COALESCE(MAX(retired_id), 0) FROM person_alias")
    return max(live, retired) + 1


def _entity_row(conn: duckdb.DuckDBPyConnection, eid: int) -> tuple | None:
    return conn.execute(
        "SELECT entity_id, canonical_name, slug FROM company_entity WHERE entity_id = ?",
        [eid],
    ).fetchone()


def merge_entities(
    conn: duckdb.DuckDBPyConnection,
    retired_id: int,
    survivor_id: int,
    dry_run: bool = False,
) -> dict:
    """Dedup-merge retired_id into survivor_id (records that were ALWAYS the same firm).

    Moves the retired entity's variants onto the survivor (skipping duplicates),
    records an entity_alias (retired_id, retired_slug, survivor_id) so the retired
    slug keeps resolving, re-points any dangling references, then deletes the retired
    row. This is NOT a historical event — use add_relation() for succession/M&A.

    Returns a mapping report. On dry_run, computes the report without writing.
    Raises ValueError on unknown/identical ids.
    """
    if retired_id == survivor_id:
        raise ValueError("retired and survivor entity ids are identical")
    retired = _entity_row(conn, retired_id)
    survivor = _entity_row(conn, survivor_id)
    if retired is None:
        raise ValueError(f"retired entity_id {retired_id} not found")
    if survivor is None:
        raise ValueError(f"survivor entity_id {survivor_id} not found")

    retired_slug = retired[2]
    existing = {
        (r[0], r[1]) for r in conn.execute(
            "SELECT variant_name, source FROM entity_name_variant WHERE entity_id = ?",
            [survivor_id],
        ).fetchall()
    }
    retired_variants = conn.execute(
        "SELECT variant_id, variant_name, source FROM entity_name_variant "
        "WHERE entity_id = ? ORDER BY variant_id", [retired_id],
    ).fetchall()
    to_move = [v for v in retired_variants if (v[1], v[2]) not in existing]
    to_drop = [v for v in retired_variants if (v[1], v[2]) in existing]

    report = {
        "retired_id": retired_id,
        "retired_name": retired[1],
        "retired_slug": retired_slug,
        "survivor_id": survivor_id,
        "survivor_name": survivor[1],
        "variants_moved": len(to_move),
        "variants_deduped": len(to_drop),
    }
    if dry_run:
        return report

    for vid, _, _ in to_move:
        conn.execute(
            "UPDATE entity_name_variant SET entity_id = ? WHERE variant_id = ?",
            [survivor_id, vid],
        )
    for vid, _, _ in to_drop:
        conn.execute("DELETE FROM entity_name_variant WHERE variant_id = ?", [vid])

    # Re-point references that named the retired id, so nothing dangles on delete.
    conn.execute(
        "UPDATE entity_alias SET survivor_id = ? WHERE survivor_id = ?",
        [survivor_id, retired_id],
    )
    conn.execute(
        "UPDATE entity_relation SET from_entity = ? WHERE from_entity = ?",
        [survivor_id, retired_id],
    )
    conn.execute(
        "UPDATE entity_relation SET to_entity = ? WHERE to_entity = ?",
        [survivor_id, retired_id],
    )
    conn.execute(
        "INSERT INTO entity_alias (retired_id, retired_slug, survivor_id) VALUES (?, ?, ?)",
        [retired_id, retired_slug, survivor_id],
    )
    conn.execute("DELETE FROM company_entity WHERE entity_id = ?", [retired_id])
    conn.commit()
    export_registry(conn)
    return report


def add_relation(
    conn: duckdb.DuckDBPyConnection,
    from_entity: int,
    to_entity: int,
    kind: str,
    effective_date: str | None = None,
    source: str | None = None,
) -> dict:
    """Record a succession / M&A relation between two DISTINCT firms (never a merge).

    Both ids must exist and differ; kind must be in VALID_RELATION_KINDS. Idempotent
    on (from, to, kind). Returns {created: bool, ...}.
    """
    if kind not in VALID_RELATION_KINDS:
        raise ValueError(
            f"relation kind {kind!r} not in {sorted(VALID_RELATION_KINDS)}"
        )
    if from_entity == to_entity:
        raise ValueError("a firm cannot have a succession relation to itself")
    if _entity_row(conn, from_entity) is None:
        raise ValueError(f"from_entity {from_entity} not found")
    if _entity_row(conn, to_entity) is None:
        raise ValueError(f"to_entity {to_entity} not found")

    dup = conn.execute(
        "SELECT 1 FROM entity_relation WHERE from_entity = ? AND to_entity = ? AND kind = ?",
        [from_entity, to_entity, kind],
    ).fetchone()
    if not dup:
        conn.execute(
            "INSERT INTO entity_relation (from_entity, to_entity, kind, effective_date, source) "
            "VALUES (?, ?, ?, ?, ?)",
            [from_entity, to_entity, kind, effective_date, source],
        )
        conn.commit()
        export_registry(conn)
    return {"created": not dup, "from_entity": from_entity, "to_entity": to_entity,
            "kind": kind, "effective_date": effective_date}


# ---------------------------------------------------------------------------
# Deterministic git-tracked export (Decision 1 durability artifact)
# ---------------------------------------------------------------------------

# (filename, ORDER BY, SELECT) for each registry table. Column order and row
# order are fixed so the export diffs cleanly under git.
_EXPORT_TABLES = [
    ("entities.csv",
     "entity_id, canonical_name, entity_type, industry, slug, founded, dissolved",
     "entity_id"),
    ("entity_variants.csv",
     "variant_id, entity_id, variant_name, source",
     "variant_id"),
    ("entity_relations.csv",
     "from_entity, to_entity, kind, effective_date, source",
     "from_entity, to_entity, kind"),
    ("entity_aliases.csv",
     "retired_id, retired_slug, survivor_id",
     "retired_id"),
    ("persons.csv",
     "person_id, canonical_name, slug, kind",
     "person_id"),
    ("person_variants.csv",
     "variant_id, person_id, variant_name, source",
     "variant_id"),
    ("person_aliases.csv",
     "retired_id, retired_slug, survivor_id",
     "retired_id"),
]

_EXPORT_TABLE_NAMES = {
    "entities.csv": "company_entity",
    "entity_variants.csv": "entity_name_variant",
    "entity_relations.csv": "entity_relation",
    "entity_aliases.csv": "entity_alias",
    "persons.csv": "person_entity",
    "person_variants.csv": "person_name_variant",
    "person_aliases.csv": "person_alias",
}


def _registry_dir_for(conn: duckdb.DuckDBPyConnection) -> Path:
    """Where this connection's export belongs — derived from the DB file, not a global.

    Deriving from the connection (rather than the import-time config REGISTRY_DIR)
    keeps the export co-located with the DB it snapshots: the real registry
    (``<root>/data/entities.duckdb``) exports to ``<root>/registry``, while a
    tmp-path test DB exports beside itself — so hermetic tests never write the repo.
    """
    db_file = None
    for row in conn.execute("PRAGMA database_list").fetchall():
        # (seq, name, file); the attached registry is 'entities' or DuckDB's 'main'.
        if row[1] in ("entities", "main") and row[2]:
            db_file = Path(row[2]).resolve()
            break
    if db_file is None:                       # in-memory or unnamed → fall back to config
        from markery.common.config import REGISTRY_DIR
        return REGISTRY_DIR
    parent = db_file.parent
    root = parent.parent if parent.name == "data" else parent
    return root / "registry"


def export_registry(
    conn: duckdb.DuckDBPyConnection,
    out_dir: str | Path | None = None,
) -> Path:
    """Write a deterministic CSV snapshot of the registry to out_dir.

    Regenerated in full on every registry write so the git-tracked export always
    matches the canonical DuckDB. Column and row order are fixed for clean diffs.
    When out_dir is None the directory is derived from the connection's DB file
    (see _registry_dir_for) so the export stays co-located and test-isolated.
    Returns the export directory.
    """
    out = Path(out_dir) if out_dir is not None else _registry_dir_for(conn)
    out.mkdir(parents=True, exist_ok=True)
    for fname, cols, order in _EXPORT_TABLES:
        table = _EXPORT_TABLE_NAMES[fname]
        target = out / fname
        # COPY ... TO writes a deterministic, header-first CSV. ORDER BY fixes row order.
        conn.execute(
            f"COPY (SELECT {cols} FROM {table} ORDER BY {order}) "
            f"TO '{target}' (HEADER, DELIMITER ',')"
        )
    return out


def list_entities(conn: duckdb.DuckDBPyConnection) -> list[dict]:
    """Return all entities ordered by entity_id."""
    rows = conn.execute(
        "SELECT entity_id, canonical_name, entity_type, industry, slug, founded, dissolved "
        "FROM company_entity ORDER BY entity_id"
    ).fetchall()
    return [
        {
            "entity_id":      r[0],
            "canonical_name": r[1],
            "entity_type":    r[2],
            "industry":       r[3],
            "slug":           r[4],
            "founded":        r[5],
            "dissolved":      r[6],
        }
        for r in rows
    ]
