#!/usr/bin/env python3
"""
build_entities_db.py

Creates and populates entities.duckdb — a canonical company registry used to
cross-reference patent assignee names against trademark owner names.

Schema
------
company_entity       one row per organisation
entity_name_variant  all name spellings/variants per entity, tagged by source

Usage
-----
    python build_entities_db.py
"""

import duckdb

DB_PATH = "data/entities.duckdb"

DDL = """
CREATE TABLE IF NOT EXISTS company_entity (
    entity_id      INTEGER PRIMARY KEY,
    canonical_name VARCHAR NOT NULL,
    entity_type    VARCHAR,   -- 'manufacturer', 'publisher', 'individual', ...
    industry       VARCHAR,   -- 'office-systems', 'blank-books', ...
    notes          VARCHAR
);

CREATE TABLE IF NOT EXISTS entity_name_variant (
    variant_id   INTEGER PRIMARY KEY,
    entity_id    INTEGER NOT NULL REFERENCES company_entity(entity_id),
    variant_name VARCHAR NOT NULL,
    source       VARCHAR NOT NULL  -- 'patent_assignee' | 'trademark_owner' | 'canonical'
);
"""

# ── Seed data ─────────────────────────────────────────────────────────────────
# Each tuple: (entity_id, canonical_name, entity_type, industry, notes)
ENTITIES = [
    (
        1,
        "Remington Rand",
        "manufacturer",
        "office-systems",
        (
            "Formed 1927 by merger of Remington Typewriter Company and Rand Kardex Bureau. "
            "Major producer of visible card-index systems, filing cabinets, and loose-leaf "
            "binders through the 1930s. Merged into Sperry Rand in 1955."
        ),
    ),
    (
        2,
        "Wilson Jones",
        "manufacturer",
        "office-systems",
        (
            "Chicago manufacturer of loose-leaf binders, filing systems, and visible index "
            "products. One of the largest B42F patent filers in the 1900–1939 period. "
            "Known for the VI-DEX visible index line (1927) and REDIREF/HANDIREF quick-"
            "reference products. Still operates as a brand under ACCO Brands."
        ),
    ),
    (
        3,
        "Yawman & Erbe",
        "manufacturer",
        "office-systems",
        (
            "Rochester, NY manufacturer of filing cabinets, vertical files, and document "
            "guides. Acquired the Shannon lever-arch file brand (trademarked 1930). "
            "One of the early pioneers of vertical filing in American offices."
        ),
    ),
    (
        4,
        "Boorum & Pease",
        "manufacturer",
        "blank-books",
        (
            "New York manufacturer of blank books, account books, and loose-leaf devices. "
            "One of the dominant B42D filers in the 1900–1939 period. Trademarks include "
            "BULLDOG (1924) for fasteners and the descriptive mark STANDARD B&P BLANK "
            "BOOKS AND LOOSE LEAF DEVICES (1921). Later acquired by Esselte."
        ),
    ),
    (
        5,
        "Library Bureau",
        "manufacturer",
        "office-systems",
        (
            "Chicago/New York manufacturer of card-index systems, filing cabinets, and "
            "library furniture. Founded by Melvil Dewey in 1876 as a supply arm of the "
            "American Library Association; incorporated as Library Bureau in the 1880s. "
            "Holds the earliest B42F patent in the database (US664573A, 'File.', filed "
            "October 1896) — the progenitor filing-appliance entity. Absorbed by "
            "Remington Rand in the 1920s."
        ),
    ),
]

# Each tuple: (entity_id, variant_name, source)
VARIANTS = [
    # ── Remington Rand ─────────────────────────────────────────────────────
    (1, "Remington Typewriter Company",          "patent_assignee"),
    (1, "REMINGTON TYPEWRITER CO [US]",          "patent_assignee"),
    (1, "REMINGTON TYPEWRITER CO",               "patent_assignee"),
    (1, "REMINGTON RAND INC",                    "patent_assignee"),
    (1, "FIRM REMINGTON RAND INC",               "patent_assignee"),
    (1, "REMINGTON TYPEWRITER COMPANY, THE",     "trademark_owner"),
    (1, "REMINGTON RAND INC.",                   "trademark_owner"),
    (1, "REMINGTON RAND BUSINESS SERVICE, INC.", "trademark_owner"),
    (1, "Remington Rand Corporation",            "trademark_owner"),
    # Rand Kardex Bureau — pre-merger subsidiary that filed the SOUNDEX marks (1927)
    (1, "RAND KARDEX BUREAU, INC.",              "trademark_owner"),
    # Kardex Systems — post-merger successor that held SOUNDEX through expiration
    (1, "KARDEX SYSTEMS, INC.",                  "trademark_owner"),

    # ── Wilson Jones ───────────────────────────────────────────────────────
    (2, "WILSON JONES CO",                       "patent_assignee"),
    (2, "WILSON JONES LOOSE LEAF CO",            "patent_assignee"),
    (2, "WILSON JONES LOOSE LEAF CO [US]",       "patent_assignee"),
    (2, "WILSON JONES LOOSE LEAF COMPAN",        "patent_assignee"),
    (2, "WILSON JONES LOOSE LEAF COMPANY [US]",  "patent_assignee"),
    (2, "WILSON JONES COMPANY",                  "trademark_owner"),

    # ── Yawman & Erbe ──────────────────────────────────────────────────────
    (3, "YAWMAN & ERBE MFG CO",                  "patent_assignee"),
    (3, "YAWMAN & ERBE MFG CO [US]",             "patent_assignee"),
    (3, "YAWMAN AND ERBE MFG COMPANY [US]",      "patent_assignee"),
    (3, "YAWMAN AND ERBE MFG. CO.",              "trademark_owner"),

    # ── Boorum & Pease ─────────────────────────────────────────────────────
    (4, "BOORUM & PEASE COMPANY",                "patent_assignee"),
    (4, "BOORUM & PEASE LOOSE LEAF BOOK COMPANY [US]", "patent_assignee"),
    (4, "BOORUM AND PEASE COMPANY",              "patent_assignee"),
    (4, "BOORUM AND PEASE COMPANY [US]",         "patent_assignee"),
    (4, "BOORUM & PEASE CO.",                    "trademark_owner"),
    (4, "BOORUM & PEASE COMPANY",                "trademark_owner"),

    # ── Library Bureau ─────────────────────────────────────────────────────
    (5, "LIBRARY BUREAU [US]",                   "patent_assignee"),
    (5, "LIBRARY BUREAU",                        "patent_assignee"),
    (5, "Library Bureau",                        "trademark_owner"),
    (5, "LIBRARY BUREAU",                        "trademark_owner"),
    (5, "LIBRARY BUREAU, INC.",                  "trademark_owner"),
]


def build(db_path: str = DB_PATH) -> None:
    conn = duckdb.connect(db_path)
    conn.execute(DDL)

    # Insert entities
    added_entities = 0
    for row in ENTITIES:
        existing = conn.execute(
            "SELECT 1 FROM company_entity WHERE entity_id = ?", [row[0]]
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO company_entity VALUES (?, ?, ?, ?, ?)", list(row)
            )
            added_entities += 1

    # Insert variants (skip duplicates by entity_id + variant_name)
    added_variants = 0
    variant_id = (
        conn.execute("SELECT COALESCE(MAX(variant_id), 0) FROM entity_name_variant")
        .fetchone()[0]
        + 1
    )
    for entity_id, variant_name, source in VARIANTS:
        existing = conn.execute(
            "SELECT 1 FROM entity_name_variant WHERE entity_id=? AND variant_name=? AND source=?",
            [entity_id, variant_name, source],
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO entity_name_variant VALUES (?, ?, ?, ?)",
                [variant_id, entity_id, variant_name, source],
            )
            variant_id += 1
            added_variants += 1

    conn.close()
    print(f"Database: {db_path}")
    print(f"  {added_entities} entities added")
    print(f"  {added_variants} name variants added")


if __name__ == "__main__":
    build()
