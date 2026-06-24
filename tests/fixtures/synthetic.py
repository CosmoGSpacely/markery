"""Synthetic-fixture builder for hermetic Markery tests.

Builds a self-contained Markery repo under a tmp directory: minimal corpus DBs
(trademarks/patents/entities) holding a few invented rows, plus a synthetic
project with candidates/confirmed JSONL and one finished essay. The CLI is
pointed at it via the MARKERY_ROOT / MARKERY_DATA_DIR environment variables
(see markery.common.config).

No real `data/` or `projects/` is touched; everything here is invented and the
serial/patent numbers are deliberately outside any real corpus.

Usage in a test:

    from tests.fixtures.synthetic import build_synthetic_repo

    repo = build_synthetic_repo(tmp_path)
    out, rc = run_markery(repo, "historian", "card", repo.project, repo.cand_slug,
                          "--out", "-")
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import duckdb

PROJECT = "synth-project"

# --- Invented pairs (numbers chosen to be outside any real corpus) -----------
# Serials match the historian card's USPTO-serial regex \b7[01]\d{6}\b.
CAND_SERIAL = 71999001          # SYNTHEX — unreviewed candidate (card tests)
CONF_SERIAL = 71999002          # GAUGEX  — confirmed, has essay (validate tests)
SCAF_SERIAL = 71999003          # MEASUREX — confirmed, no essay (scaffold tests)

CAND_PATENT = "US1999001A"
CONF_PATENT = "US1999002A"
SCAF_PATENT = "US1999003A"

CAND_SLUG = "synthex-us1999001a"
CONF_SLUG = "gaugex-us1999002a"
SCAF_SLUG = "measurex-us1999003a"

ENTITY_ID = 1
ENTITY_CANON = "Synthex Manufacturing Company"
ENTITY_VARIANT = "SYNTHEX MFG CO"

# Annual-review fixture: a design mark filed in REVIEW_YEAR, plus a second project
# of type annual-review covering that year.
REVIEW_PROJECT = "synth-annual-review"
REVIEW_YEAR = 1935
REVIEW_SERIAL = 71950001

# A 1×1 transparent PNG — the smallest valid image, used for mark/figure blobs.
_PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6360000002000001a721be6f0000000049454e44ae"
    "426082"
)


@dataclass
class SyntheticRepo:
    root: Path
    data_dir: Path
    project: str = PROJECT
    cand_slug: str = CAND_SLUG
    conf_slug: str = CONF_SLUG
    scaf_slug: str = SCAF_SLUG
    cand_serial: int = CAND_SERIAL
    conf_serial: int = CONF_SERIAL
    cand_patent: str = CAND_PATENT
    conf_patent: str = CONF_PATENT
    review_project: str = REVIEW_PROJECT
    review_year: int = REVIEW_YEAR

    @property
    def env(self) -> dict[str, str]:
        e = dict(os.environ)
        e["MARKERY_ROOT"] = str(self.root)
        e["MARKERY_DATA_DIR"] = str(self.data_dir)
        return e

    @property
    def db_tm(self) -> Path:
        return self.data_dir / "trademarks.duckdb"

    @property
    def db_pat(self) -> Path:
        return self.data_dir / "patents.duckdb"

    @property
    def db_ent(self) -> Path:
        return self.data_dir / "entities.duckdb"


# ---------------------------------------------------------------------------
# Database builders — minimal schemas covering only what the historian
# card/digest/scaffold/validate commands query.
# ---------------------------------------------------------------------------

def _build_trademarks(path: Path) -> None:
    conn = duckdb.connect(str(path))
    conn.execute(
        "CREATE TABLE case_file (serial_no BIGINT, mark_id_char VARCHAR, "
        "filing_dt DATE, mark_draw_cd VARCHAR, registration_no VARCHAR, "
        "cfh_status_cd INTEGER)"
    )
    conn.execute(
        "CREATE TABLE statement "
        "(serial_no BIGINT, statement_type_cd VARCHAR, statement_text VARCHAR)"
    )
    conn.execute("CREATE TABLE intl_class (serial_no BIGINT, intl_class VARCHAR)")
    conn.execute(
        "CREATE TABLE owner "
        "(own_id BIGINT, serial_no BIGINT, own_name VARCHAR, own_type_cd VARCHAR, "
        "own_addr_city VARCHAR, own_addr_state_cd VARCHAR)"
    )
    conn.execute("CREATE TABLE classification (serial_no BIGINT, first_use_com_dt DATE)")
    conn.execute("CREATE TABLE mark_images (serial_no BIGINT, image_data BLOB)")
    conn.execute("CREATE TABLE design_search (serial_no BIGINT, design_search_cd VARCHAR)")

    meta = {
        CAND_SERIAL: ("SYNTHEX", "1935-03-15", "0331001"),
        CONF_SERIAL: ("GAUGEX", "1936-05-20", "0331002"),
        SCAF_SERIAL: ("MEASUREX", "1937-04-10", "0331003"),
    }
    own_id = 1
    for serial, (mark, filed, reg) in meta.items():
        # cfh_status_cd 700+ = dead (gates merch); use a live status here.
        # mark_draw_cd '4' = standard character (not a design mark).
        conn.execute(
            "INSERT INTO case_file VALUES (?, ?, ?, '4', ?, 630)",
            [serial, mark, filed, reg],
        )
        conn.execute(
            "INSERT INTO statement VALUES (?, 'GS0', ?)",
            [serial, "Synthetic precision measuring instruments for laboratory use."],
        )
        conn.execute("INSERT INTO intl_class VALUES (?, '009')", [serial])
        conn.execute(
            "INSERT INTO owner VALUES (?, ?, ?, '10', 'Athol', 'MA')",
            [own_id, serial, ENTITY_VARIANT],
        )
        conn.execute("INSERT INTO classification VALUES (?, ?)", [serial, filed])
        own_id += 1

    # A figurative design mark (mark_draw_cd '3%') for the annual-review path,
    # owned by an unrelated party so it stays out of the match-review project.
    conn.execute(
        "INSERT INTO case_file VALUES (?, ?, ?, '3', ?, 630)",
        [REVIEW_SERIAL, "STARBURST", f"{REVIEW_YEAR}-06-10", "0340001"],
    )
    conn.execute(
        "INSERT INTO owner VALUES (?, ?, 'ART DECO DESIGNS INC', '10', 'New York', 'NY')",
        [own_id, REVIEW_SERIAL],
    )
    conn.execute("INSERT INTO design_search VALUES (?, '260101')", [REVIEW_SERIAL])
    conn.execute("INSERT INTO design_search VALUES (?, '260102')", [CAND_SERIAL])
    conn.execute(
        "INSERT INTO statement VALUES (?, 'GS0', ?)",
        [REVIEW_SERIAL, "Decorative emblems and ornamental designs for packaging."],
    )

    # One mark carries an image so the image-write path is exercised.
    conn.execute("INSERT INTO mark_images VALUES (?, ?)", [CAND_SERIAL, _PNG_1PX])
    conn.close()


def _build_patents(path: Path) -> None:
    conn = duckdb.connect(str(path))
    conn.execute(
        "CREATE TABLE patents (patent_no VARCHAR, title VARCHAR, abstract VARCHAR, "
        "grant_dt DATE, assignee_name VARCHAR, app_dt DATE)"
    )
    conn.execute("CREATE TABLE patent_classes (patent_no VARCHAR, cpc_class VARCHAR)")
    conn.execute("CREATE TABLE patent_inventors (patent_no VARCHAR, inventor_name VARCHAR)")
    conn.execute("CREATE TABLE patent_figures (patent_no VARCHAR, figure_no INTEGER, figure_data BLOB)")
    rows = [
        (CAND_PATENT, "Synthetic Measuring Apparatus",
         "An apparatus for synthetic precision measurement employing a calibrated gauge.",
         "1935-01-08", ENTITY_VARIANT, "1933-06-01"),
        (CONF_PATENT, "Improved Gauge Mechanism",
         "A gauge mechanism providing improved repeatability over prior designs.",
         "1936-02-11", ENTITY_VARIANT, "1934-04-02"),
        (SCAF_PATENT, "Linear Measurement Instrument",
         "A linear measurement instrument with a vernier scale and locking screw.",
         "1937-03-09", ENTITY_VARIANT, "1935-07-15"),
    ]
    conn.executemany("INSERT INTO patents VALUES (?, ?, ?, ?, ?, ?)", rows)
    for pno in (CAND_PATENT, CONF_PATENT, SCAF_PATENT):
        conn.execute("INSERT INTO patent_classes VALUES (?, 'G01B0005')", [pno])
        conn.execute("INSERT INTO patent_inventors VALUES (?, 'Jane Synthex')", [pno])
    # One patent carries a figure so the figure-write path is exercised.
    conn.execute("INSERT INTO patent_figures VALUES (?, 1, ?)", [CAND_PATENT, _PNG_1PX])
    conn.close()


def _build_entities(path: Path) -> None:
    conn = duckdb.connect(str(path))
    conn.execute(
        "CREATE TABLE company_entity "
        "(entity_id INTEGER, canonical_name VARCHAR, entity_type VARCHAR, industry VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE entity_name_variant "
        "(entity_id INTEGER, variant_name VARCHAR, source VARCHAR)"
    )
    conn.execute(
        "INSERT INTO company_entity VALUES (?, ?, 'company', 'Precision instruments')",
        [ENTITY_ID, ENTITY_CANON],
    )
    # The publisher joins marks via 'trademark_owner' and patents via 'patent_assignee'.
    conn.execute(
        "INSERT INTO entity_name_variant VALUES (?, ?, 'trademark_owner')",
        [ENTITY_ID, ENTITY_VARIANT],
    )
    conn.execute(
        "INSERT INTO entity_name_variant VALUES (?, ?, 'patent_assignee')",
        [ENTITY_ID, ENTITY_VARIANT],
    )
    conn.close()


# ---------------------------------------------------------------------------
# Project builder
# ---------------------------------------------------------------------------

def _candidate(serial: int, patent: str, trademark: str, score: float) -> dict:
    return {
        "patent_no": patent,
        "trademark": trademark,
        "trademark_serial": serial,
        "tm_filing_dt": {
            CAND_SERIAL: "1935-03-15",
            CONF_SERIAL: "1936-05-20",
            SCAF_SERIAL: "1937-04-10",
        }[serial],
        "tm_reg_no": f"0{serial % 1000000 + 330000}",
        "tm_owner": ENTITY_VARIANT,
        "entity": ENTITY_CANON,
        "entity_id": ENTITY_ID,
        "cpc_classes": ["G01B"],
        "score": score,
        "title_name_hit": True,
        "abstract_name_hit": False,
        "goods_title_overlap": 0.25,
        "goods_abstract_overlap": 0.10,
    }


def _confirmed(serial: int, patent: str, trademark: str) -> dict:
    return {
        "patent_no": patent,
        "trademark": trademark,
        "trademark_serial": serial,
        "entity_id": ENTITY_ID,
        "entity": ENTITY_CANON,
        "type": "product_match",
        "note": "",
    }


CONF_ESSAY = f"""---
title: "GAUGEX — {CONF_PATENT}"
trademark_serial: {CONF_SERIAL}
trademark: "GAUGEX"
tm_filing_dt: "1936-05-20"
tm_reg_no: "0331002"
tm_owner: "{ENTITY_VARIANT}"
patent_no: "{CONF_PATENT}"
patent_grant_dt: "1936-02-11"
patent_assignee: "{ENTITY_VARIANT}"
entity: "{ENTITY_CANON}"
date_gap: "0.3 years"
---

## Primary Sources

- USPTO Trademark Serial No. {CONF_SERIAL} — GAUGEX, filed 1936-05.
- US Patent {CONF_PATENT} — Improved Gauge Mechanism, granted 1936-02.

## The Invention

The patent describes an improved gauge mechanism with better repeatability.

## The Mark

GAUGEX named the company's flagship precision gauge, filed in 1936-05.

## The Connection

The mark covered the very instrument the patent protected.

## Historical Context

A period of rapid growth in American precision-tool manufacturing.

## Significance

It illustrates how a single firm protected both an invention and its brand.
"""


def build_synthetic_repo(tmp_path: Path) -> SyntheticRepo:
    """Create a self-contained synthetic Markery repo under tmp_path."""
    root = tmp_path / "synth-repo"
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    # A pyproject.toml so any fallback root-walk still resolves inside the repo.
    (root / "pyproject.toml").write_text("[project]\nname = \"synth\"\n")

    _build_trademarks(data_dir / "trademarks.duckdb")
    _build_patents(data_dir / "patents.duckdb")
    _build_entities(data_dir / "entities.duckdb")

    proj = root / "projects" / PROJECT
    (proj / "matches").mkdir(parents=True)
    (proj / "content").mkdir(parents=True)
    (proj / "project.json").write_text(
        json.dumps({"type": "match-review-essay"}) + "\n"
    )
    (proj / "entities.txt").write_text(f"{ENTITY_ID}  # {ENTITY_CANON}\n")
    (proj / "entities.csv").write_text(
        "entity_id,canonical_name\n"
        f"{ENTITY_ID},{ENTITY_CANON}\n"
    )
    (proj / "variants.csv").write_text(
        "entity_id,variant_name,source\n"
        f"{ENTITY_ID},{ENTITY_VARIANT},trademark_owner\n"
        f"{ENTITY_ID},{ENTITY_VARIANT},patent_assignee\n"
    )

    candidates = [
        _candidate(CAND_SERIAL, CAND_PATENT, "SYNTHEX", 0.87),
        _candidate(CONF_SERIAL, CONF_PATENT, "GAUGEX", 0.81),
        _candidate(SCAF_SERIAL, SCAF_PATENT, "MEASUREX", 0.79),
    ]
    (proj / "matches" / "candidates.jsonl").write_text(
        "\n".join(json.dumps(c) for c in candidates) + "\n"
    )

    confirmed = [
        _confirmed(CONF_SERIAL, CONF_PATENT, "GAUGEX"),
        _confirmed(SCAF_SERIAL, SCAF_PATENT, "MEASUREX"),
    ]
    (proj / "matches" / "confirmed.jsonl").write_text(
        "\n".join(json.dumps(c) for c in confirmed) + "\n"
    )

    (proj / "content" / f"{CONF_SLUG}.md").write_text(CONF_ESSAY)

    # A second project of type annual-review, covering REVIEW_YEAR.
    review = root / "projects" / REVIEW_PROJECT
    review.mkdir(parents=True)
    (review / "project.json").write_text(
        json.dumps({"type": "annual-review", "review_years": [REVIEW_YEAR]}) + "\n"
    )

    return SyntheticRepo(root=root, data_dir=data_dir)


def run_markery(repo: SyntheticRepo, *args: str) -> tuple[str, int]:
    """Run `markery <args>` against the synthetic repo; return (output, rc)."""
    result = subprocess.run(
        ["markery", *args],
        capture_output=True,
        text=True,
        env=repo.env,
        cwd=str(repo.root),
    )
    return result.stdout + result.stderr, result.returncode
