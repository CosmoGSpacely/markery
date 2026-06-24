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
    conn.execute("CREATE TABLE case_file (serial_no BIGINT)")
    conn.execute(
        "CREATE TABLE statement "
        "(serial_no BIGINT, statement_type_cd VARCHAR, statement_text VARCHAR)"
    )
    conn.execute("CREATE TABLE intl_class (serial_no BIGINT, intl_class VARCHAR)")
    conn.execute(
        "CREATE TABLE owner "
        "(serial_no BIGINT, own_name VARCHAR, own_type_cd VARCHAR)"
    )

    for serial in (CAND_SERIAL, CONF_SERIAL, SCAF_SERIAL):
        conn.execute("INSERT INTO case_file VALUES (?)", [serial])
        conn.execute(
            "INSERT INTO statement VALUES (?, 'GS0', ?)",
            [serial, "Synthetic precision measuring instruments for laboratory use."],
        )
        conn.execute("INSERT INTO intl_class VALUES (?, '009')", [serial])
        conn.execute(
            "INSERT INTO owner VALUES (?, ?, '10')", [serial, ENTITY_VARIANT]
        )
    conn.close()


def _build_patents(path: Path) -> None:
    conn = duckdb.connect(str(path))
    conn.execute(
        "CREATE TABLE patents (patent_no VARCHAR, title VARCHAR, abstract VARCHAR, "
        "grant_dt DATE, assignee_name VARCHAR, app_dt DATE)"
    )
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
    conn.executemany(
        "INSERT INTO patents VALUES (?, ?, ?, ?, ?, ?)", rows
    )
    conn.close()


def _build_entities(path: Path) -> None:
    conn = duckdb.connect(str(path))
    conn.execute(
        "CREATE TABLE company_entity (entity_id INTEGER, canonical_name VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE entity_name_variant "
        "(entity_id INTEGER, variant_name VARCHAR, source VARCHAR)"
    )
    conn.execute(
        "INSERT INTO company_entity VALUES (?, ?)", [ENTITY_ID, ENTITY_CANON]
    )
    conn.execute(
        "INSERT INTO entity_name_variant VALUES (?, ?, 'trademark_owner')",
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
