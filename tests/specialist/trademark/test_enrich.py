"""Unit tests for trademark BLOB storage and enrichment."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from markery.specialist.trademark.build import open_db
from markery.specialist.trademark.enrich import (
    store_mark_image,
    store_case_status,
    enrich_project,
    backfill_structured_fields,
    _collect_serial_nos,
    _collect_serials_from_variants,
)
from contextlib import contextmanager
from unittest.mock import patch as _patch

from markery.common.project import Project


_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


@contextmanager
def _patch_root(tmp_path: Path):
    """Patch ROOT in both config and project modules so Project.root resolves correctly."""
    with _patch("markery.common.config.ROOT", tmp_path), \
         _patch("markery.common.project.ROOT", tmp_path):
        yield


@pytest.fixture(autouse=True)
def _assets(tmp_path, monkeypatch):
    """Keep externalized mark-image files inside the test's tmp dir."""
    import markery.common.config as cfg
    monkeypatch.setattr(cfg, "ASSETS_DIR", tmp_path / "assets")


def _in_memory_db():
    return open_db(":memory:")


_PARSED_STATUS = {
    "serial_no":          "71165547",
    "mark_text":          "VI-DEX",
    "filing_dt":          "1927-01-15",
    "registration_no":    "0212345",
    "registration_dt":    "1928-03-10",
    "status_cd":          "700",
    "goods_desc":         "Card filing systems",
    "intl_class":         "16",
    "first_use_dt":       "1926-01-01",
    "first_use_comm_dt":  "1926-06-01",
    "raw_json":           None,
}


# ---------------------------------------------------------------------------
# store_mark_image
# ---------------------------------------------------------------------------

def test_store_mark_image_inserts_new():
    conn   = _in_memory_db()
    client = MagicMock()
    client.fetch_mark_image.return_value = _PNG_BYTES

    result = store_mark_image("71165547", client, conn)
    assert result is True

    from markery.common.assets import read_mark_image
    row = conn.execute(
        "SELECT file, image_format, image_size FROM mark_images WHERE serial_no = '71165547'"
    ).fetchone()
    assert row[0] == "marks/71165547.png"
    assert row[1] == "PNG"
    assert row[2] == len(_PNG_BYTES)
    assert read_mark_image(conn, "71165547")[:4] == b"\x89PNG"
    conn.close()


def test_store_mark_image_skips_if_already_stored():
    conn   = _in_memory_db()
    client = MagicMock()
    client.fetch_mark_image.return_value = _PNG_BYTES

    store_mark_image("71165547", client, conn)
    result = store_mark_image("71165547", client, conn)

    assert result is False
    assert client.fetch_mark_image.call_count == 1
    conn.close()


def test_store_mark_image_force_refetches():
    conn   = _in_memory_db()
    client = MagicMock()
    client.fetch_mark_image.return_value = _PNG_BYTES

    store_mark_image("71165547", client, conn)
    result = store_mark_image("71165547", client, conn, force=True)

    assert result is True
    assert client.fetch_mark_image.call_count == 2
    conn.close()


def test_store_mark_image_returns_false_when_no_image():
    conn   = _in_memory_db()
    client = MagicMock()
    client.fetch_mark_image.return_value = None

    result = store_mark_image("99999999", client, conn)
    assert result is False
    row = conn.execute(
        "SELECT 1 FROM mark_images WHERE serial_no = '99999999'"
    ).fetchone()
    assert row is None
    conn.close()


def test_store_mark_image_updates_existing_row_without_data():
    conn = _in_memory_db()
    conn.execute(
        "INSERT INTO mark_images (serial_no) VALUES ('71165547')"
    )
    conn.commit()

    client = MagicMock()
    client.fetch_mark_image.return_value = _PNG_BYTES

    result = store_mark_image("71165547", client, conn)
    assert result is True

    from markery.common.assets import read_mark_image
    assert read_mark_image(conn, "71165547")[:4] == b"\x89PNG"
    conn.close()


# ---------------------------------------------------------------------------
# store_case_status
# ---------------------------------------------------------------------------

def test_store_case_status_inserts_new():
    conn   = _in_memory_db()
    client = MagicMock()
    client.fetch_case_status.return_value = _PARSED_STATUS

    result = store_case_status("71165547", client, conn)
    assert result is True

    row = conn.execute(
        "SELECT mark_text, status_cd FROM extended_marks WHERE serial_no = '71165547'"
    ).fetchone()
    assert row[0] == "VI-DEX"
    assert row[1] == "700"
    conn.close()


def test_store_case_status_skips_if_already_stored():
    conn   = _in_memory_db()
    client = MagicMock()
    client.fetch_case_status.return_value = _PARSED_STATUS

    store_case_status("71165547", client, conn)
    result = store_case_status("71165547", client, conn)

    assert result is False
    assert client.fetch_case_status.call_count == 1
    conn.close()


def test_store_case_status_returns_false_when_not_found():
    conn   = _in_memory_db()
    client = MagicMock()
    client.fetch_case_status.return_value = None

    result = store_case_status("99999999", client, conn)
    assert result is False
    conn.close()


def test_store_case_status_force_refetches():
    conn   = _in_memory_db()
    client = MagicMock()
    client.fetch_case_status.return_value = _PARSED_STATUS

    store_case_status("71165547", client, conn)
    result = store_case_status("71165547", client, conn, force=True)

    assert result is True
    assert client.fetch_case_status.call_count == 2
    conn.close()


# ---------------------------------------------------------------------------
# _collect_serial_nos
# ---------------------------------------------------------------------------

def test_collect_serial_nos_from_confirmed(tmp_path: Path):
    confirmed = tmp_path / "projects" / "test-proj" / "matches" / "confirmed.jsonl"
    confirmed.parent.mkdir(parents=True)
    confirmed.write_text(
        json.dumps({"patent_no": "US123A", "trademark_serial": "71111111"}) + "\n" +
        json.dumps({"patent_no": "US456A", "trademark_serial": "71222222"}) + "\n" +
        json.dumps({"patent_no": "US789A", "trademark_serial": "71111111"}) + "\n"
    )

    with _patch_root(tmp_path):
        proj = Project("test-proj")
        serial_nos = _collect_serial_nos(proj, "confirmed", 0.0)

    # Deduplicated, order preserved
    assert serial_nos == ["71111111", "71222222"]


def test_collect_serial_nos_filters_by_min_score(tmp_path: Path):
    candidates = tmp_path / "projects" / "test-proj" / "matches" / "candidates.jsonl"
    candidates.parent.mkdir(parents=True)
    candidates.write_text(
        json.dumps({"trademark_serial": "71111111", "score": 0.80}) + "\n" +
        json.dumps({"trademark_serial": "71222222", "score": 0.50}) + "\n"
    )

    with _patch_root(tmp_path):
        proj = Project("test-proj")
        serial_nos = _collect_serial_nos(proj, "candidates", 0.70)

    assert serial_nos == ["71111111"]
    assert "71222222" not in serial_nos


# ---------------------------------------------------------------------------
# enrich_project integration
# ---------------------------------------------------------------------------

def test_enrich_project_stores_marks(tmp_path: Path):
    confirmed = tmp_path / "projects" / "test-proj" / "matches" / "confirmed.jsonl"
    confirmed.parent.mkdir(parents=True)
    confirmed.write_text(
        json.dumps({"patent_no": "US123A", "trademark_serial": "71165547"}) + "\n"
    )

    client = MagicMock()
    client.fetch_mark_image.return_value  = _PNG_BYTES
    client.fetch_case_status.return_value = _PARSED_STATUS

    conn = _in_memory_db()

    with _patch_root(tmp_path):
        result = enrich_project("test-proj", client, conn)
    conn.close()

    assert result["images"] == 1
    assert result["status"] == 1


# ---------------------------------------------------------------------------
# backfill_structured_fields (D038)
# ---------------------------------------------------------------------------

_NEW_FORMAT_RAW_JSON = json.dumps({
    "trademarks": [{
        "status": {
            "markElement":          "DOUBLE EAGLE",
            "filingDate":           "1926-08-28",
            "usRegistrationNumber": "216932",
            "usRegistrationDate":   "1927-02-01",
            "status":               900,
        },
        "gsList": [{
            "description": "PNEUMATIC TIRES AND TUBES",
            "internationalClasses": [{"code": "012", "description": "Vehicles"}],
        }],
        "parties": {
            "ownerGroups": {
                "30": [{"name": "GOODYEAR TIRE & RUBBER COMPANY, THE"}],
            }
        },
    }]
})


def test_backfill_structured_fields_populates_null_rows():
    conn = _in_memory_db()
    # Insert a row with raw_json but NULL structured fields
    conn.execute(
        "INSERT INTO extended_marks (serial_no, raw_json, fetched_dt) VALUES (?, ?, '2026-01-01')",
        ["71273695", _NEW_FORMAT_RAW_JSON],
    )
    conn.commit()

    n = backfill_structured_fields(conn)
    assert n == 1

    row = conn.execute(
        "SELECT mark_text, status_cd, goods_desc, owner_name FROM extended_marks "
        "WHERE serial_no = '71273695'"
    ).fetchone()
    assert row[0] == "DOUBLE EAGLE"
    assert row[1] == "900"
    assert row[2] == "PNEUMATIC TIRES AND TUBES"
    assert row[3] == "GOODYEAR TIRE & RUBBER COMPANY, THE"
    conn.close()


def test_backfill_skips_already_populated_rows():
    conn = _in_memory_db()
    # Row already has mark_text set
    client = MagicMock()
    client.fetch_case_status.return_value = {**_PARSED_STATUS, "raw_json": _NEW_FORMAT_RAW_JSON}
    store_case_status("71165547", client, conn)
    conn.commit()

    n = backfill_structured_fields(conn)
    assert n == 0
    conn.close()


# ---------------------------------------------------------------------------
# _collect_serials_from_variants (D046)
# ---------------------------------------------------------------------------

def _tm_conn_with_owner_table():
    """In-memory trademark DB with a minimal owner table."""
    conn = _in_memory_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS owner "
        "(serial_no BIGINT, own_name VARCHAR, own_seq BIGINT)"
    )
    conn.execute("INSERT INTO owner VALUES (71246709, 'Rand Kardex Bureau, Inc.', 1)")
    conn.execute("INSERT INTO owner VALUES (71164631, 'COLT S PT F A MFG CO', 1)")
    conn.execute("INSERT INTO owner VALUES (71299042, 'Chicago Pneumatic Tool Co', 1)")
    return conn


def _write_variants_csv(path: Path, rows: list[dict]) -> None:
    import csv
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["entity_id", "variant_name", "source"])
        w.writeheader()
        w.writerows(rows)


def test_collect_serials_from_variants_returns_matching_serials(tmp_path):
    conn = _tm_conn_with_owner_table()
    variants_path = tmp_path / "variants.csv"
    _write_variants_csv(variants_path, [
        {"entity_id": 1, "variant_name": "Rand Kardex Bureau, Inc.", "source": "trademark_owner"},
        {"entity_id": 2, "variant_name": "COLT S PT F A MFG CO",     "source": "trademark_owner"},
    ])
    serials = _collect_serials_from_variants(variants_path, conn)
    assert set(serials) == {"71246709", "71164631"}
    conn.close()


def test_collect_serials_from_variants_case_insensitive(tmp_path):
    conn = _tm_conn_with_owner_table()
    variants_path = tmp_path / "variants.csv"
    _write_variants_csv(variants_path, [
        {"entity_id": 1, "variant_name": "rand kardex bureau, inc.", "source": "trademark_owner"},
    ])
    serials = _collect_serials_from_variants(variants_path, conn)
    assert "71246709" in serials
    conn.close()


def test_collect_serials_from_variants_ignores_patent_assignee_source(tmp_path):
    conn = _tm_conn_with_owner_table()
    variants_path = tmp_path / "variants.csv"
    _write_variants_csv(variants_path, [
        {"entity_id": 1, "variant_name": "Rand Kardex Bureau, Inc.", "source": "patent_assignee"},
    ])
    serials = _collect_serials_from_variants(variants_path, conn)
    assert serials == []
    conn.close()


def test_collect_serials_from_variants_empty_when_file_missing(tmp_path):
    conn = _tm_conn_with_owner_table()
    serials = _collect_serials_from_variants(tmp_path / "nonexistent.csv", conn)
    assert serials == []
    conn.close()


def test_collect_serials_from_variants_no_candidates_file_needed(tmp_path):
    """Verify serials are found even when candidates.jsonl does not exist."""
    conn = _tm_conn_with_owner_table()
    variants_path = tmp_path / "variants.csv"
    _write_variants_csv(variants_path, [
        {"entity_id": 1, "variant_name": "Chicago Pneumatic Tool Co", "source": "trademark_search"},
    ])
    # No candidates.jsonl in tmp_path — it must not be needed
    assert not (tmp_path / "candidates.jsonl").exists()
    serials = _collect_serials_from_variants(variants_path, conn)
    assert "71299042" in serials
    conn.close()
