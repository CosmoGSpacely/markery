"""
fetch.py — download patent grant PDFs from Google Patents and extract page-1 figures.

For each patent_no, attempts:
  1. https://patents.google.com/patent/{patent_no}/PDF   (follows redirect)

Saves:
  projects/<project>/output/patent-docs/<patent_no>.pdf
  projects/<project>/output/patent-figures/<patent_no>/fig_001.png

Updates patent_documents and patent_figures tables in patents.duckdb.
"""

from __future__ import annotations

import io
import json
import time
from datetime import datetime
from pathlib import Path

import duckdb
import requests
from PIL import Image

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader  # older name fallback

ROOT = Path(__file__).parent.parent

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
RATE_SLEEP = 2.0  # seconds between requests


# ── PDF download ──────────────────────────────────────────────────────────────

def _google_pdf_url(patent_no: str) -> str:
    return f"https://patents.google.com/patent/{patent_no}/PDF"


def download_pdf(patent_no: str, dest: Path) -> bool:
    """Download grant PDF to dest. Returns True on success."""
    url = _google_pdf_url(patent_no)
    try:
        resp = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=30)
        time.sleep(RATE_SLEEP)
    except requests.RequestException as e:
        print(f"  {patent_no}: network error — {e}")
        return False

    if resp.status_code != 200:
        print(f"  {patent_no}: HTTP {resp.status_code}")
        return False

    content_type = resp.headers.get("Content-Type", "")
    if "pdf" not in content_type.lower() and not resp.url.endswith(".pdf"):
        print(f"  {patent_no}: unexpected content-type: {content_type!r}")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(resp.content)
    return True


# ── Figure extraction ─────────────────────────────────────────────────────────

def extract_page1_figure(pdf_path: Path, fig_path: Path) -> bool:
    """Extract the first embedded image from page 1 of the PDF. Returns True on success."""
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        print(f"  could not open PDF: {e}")
        return False

    if not reader.pages:
        return False

    page = reader.pages[0]

    # Try to extract embedded raster images (scanned PDFs embed each page as an image)
    try:
        images = page.images
    except Exception as e:
        print(f"  could not read page images: {e}")
        return False

    if not images:
        print(f"  no embedded images on page 1")
        return False

    fig_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        img = Image.open(io.BytesIO(images[0].data))
        img.save(str(fig_path))
        return True
    except Exception as e:
        print(f"  could not save figure: {e}")
        return False


def _page_count(pdf_path: Path) -> int:
    try:
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return 0


# ── Database helpers ──────────────────────────────────────────────────────────

def _upsert_document(conn: duckdb.DuckDBPyConnection, patent_no: str,
                     pdf_path: str, page_count: int, figure_count: int) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO patent_documents
           (patent_no, pdf_path, pdf_fetched_at, page_count, figure_count)
           VALUES (?, ?, ?, ?, ?)""",
        [patent_no, pdf_path, datetime.now(), page_count, figure_count],
    )


def _upsert_figure(conn: duckdb.DuckDBPyConnection, patent_no: str,
                   figure_no: int, figure_path: str, is_representative: bool) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO patent_figures
           (patent_no, figure_no, figure_path, is_representative)
           VALUES (?, ?, ?, ?)""",
        [patent_no, figure_no, figure_path, is_representative],
    )


# ── Main entry point ──────────────────────────────────────────────────────────

def fetch_patents(
    patent_nos: list[str],
    project_dir: Path,
    patents_db: Path,
    force: bool = False,
) -> None:
    docs_dir    = project_dir / "output" / "patent-docs"
    figures_dir = project_dir / "output" / "patent-figures"

    conn = duckdb.connect(str(patents_db))

    for patent_no in patent_nos:
        pdf_path = docs_dir / f"{patent_no}.pdf"
        fig_path = figures_dir / patent_no / "fig_001.png"

        # Skip if already fetched
        if not force and pdf_path.exists():
            row = conn.execute(
                "SELECT 1 FROM patent_documents WHERE patent_no = ?", [patent_no]
            ).fetchone()
            if row:
                print(f"  {patent_no}: already fetched, skipping")
                continue

        print(f"  {patent_no}: downloading PDF ...", end="", flush=True)
        ok = download_pdf(patent_no, pdf_path)
        if not ok:
            print(f"  {patent_no}: download failed")
            continue
        print(f" {pdf_path.stat().st_size // 1024} KB")

        pages = _page_count(pdf_path)

        print(f"  {patent_no}: extracting page-1 figure ...", end="", flush=True)
        fig_ok = extract_page1_figure(pdf_path, fig_path)
        if fig_ok:
            print(f" saved → {fig_path.relative_to(ROOT)}")
        else:
            print(" (no figure)")

        # Paths stored relative to project root for portability
        rel_pdf = str(pdf_path.relative_to(ROOT))
        rel_fig = str(fig_path.relative_to(ROOT)) if fig_ok else None

        _upsert_document(conn, patent_no, rel_pdf, pages, 1 if fig_ok else 0)
        if fig_ok:
            _upsert_figure(conn, patent_no, 1, rel_fig, True)

        conn.commit()

    conn.close()


def patents_from_confirmed(confirmed_path: Path) -> list[str]:
    if not confirmed_path.exists():
        return []
    nos = []
    seen = set()
    for line in confirmed_path.read_text().splitlines():
        if line.strip():
            no = json.loads(line)["patent_no"]
            if no not in seen:
                seen.add(no)
                nos.append(no)
    return nos


def patents_from_candidates(candidates_path: Path, min_score: float) -> list[str]:
    if not candidates_path.exists():
        return []
    nos = []
    seen = set()
    for line in candidates_path.read_text().splitlines():
        if line.strip():
            c = json.loads(line)
            if c["score"] >= min_score:
                no = c["patent_no"]
                if no not in seen:
                    seen.add(no)
                    nos.append(no)
    return nos
