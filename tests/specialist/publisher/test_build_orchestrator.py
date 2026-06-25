"""Hermetic end-to-end coverage for the publisher build orchestrator.

Synthesises a tiny project (one entity, three marks/patents, two confirmed
pairs, one with an essay) in temp corpus DBs and runs the real
build_site / build_all / check_site against it — the integration the old
real-data tests stood in for, now hermetic.
"""

from __future__ import annotations

import importlib

import pytest

from tests.fixtures.synthetic import build_synthetic_repo


@pytest.fixture
def site(tmp_path, monkeypatch):
    """Build the full Markery portal from a synthetic repo; yield (repo, site_root)."""
    repo = build_synthetic_repo(tmp_path)

    import markery.common.config as cfg
    import markery.common.project as pm

    monkeypatch.setattr(cfg, "ROOT", repo.root)
    monkeypatch.setattr(cfg, "SITE_ROOT", repo.root / "site")
    monkeypatch.setattr(cfg, "ASSETS_DIR", repo.assets_dir)
    monkeypatch.setattr(pm, "ROOT", repo.root)
    for key in ("patents", "trademarks", "entities"):
        monkeypatch.setitem(cfg.DB, key, repo.data_dir / f"{key}.duckdb")

    from markery.specialist.publisher import build
    importlib.reload(build)  # rebind module-level config references under the patch

    site_root = repo.root / "site"
    build.build_all(site_root)
    yield repo, site_root
    importlib.reload(build)


# ---------------------------------------------------------------------------
# discovery
# ---------------------------------------------------------------------------

def test_discover_projects_finds_synthetic(site):
    repo, _ = site
    from markery.specialist.publisher import build
    assert build.discover_projects() == [repo.project]


# ---------------------------------------------------------------------------
# build_site / build_all page emission
# ---------------------------------------------------------------------------

def test_core_pages_exist(site):
    repo, root = site
    proj = root / repo.project
    for rel in (
        "index.html",
        "trademarks.html",
        "patents.html",
        "entities/index.html",
        "matches/index.html",
    ):
        assert (proj / rel).exists(), f"missing page: {rel}"


def test_detail_pages_per_record(site):
    repo, root = site
    proj = root / repo.project
    # One detail page per mark and per patent (3 each in the fixture).
    assert (proj / "trademarks" / f"{repo.cand_serial}.html").exists()
    assert (proj / "patents" / f"{repo.cand_patent}.html").exists()
    # One detail page per record; the galleries live at trademarks.html/patents.html.
    assert len(list((proj / "trademarks").glob("*.html"))) == 3
    assert len(list((proj / "patents").glob("*.html"))) == 3


def test_entity_page_rendered(site):
    repo, root = site
    proj = root / repo.project
    assert (proj / "entities" / "synthex-manufacturing-company.html").exists()


def test_match_essay_with_and_without_content(site):
    repo, root = site
    proj = root / repo.project
    # gaugex has a finished essay; measurex is a confirmed pair without one.
    assert (proj / "matches" / f"{repo.conf_slug}.html").exists()
    assert (proj / "matches" / "measurex-us1999003a.html").exists()


def test_mark_image_written_to_disk(site):
    repo, root = site
    proj = root / repo.project
    img = proj / "images" / "marks" / f"{repo.cand_serial}.png"
    assert img.exists() and img.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_patent_figure_written_to_disk(site):
    repo, root = site
    proj = root / repo.project
    fig = proj / "images" / "patents" / f"{repo.cand_patent}.png"
    assert fig.exists() and fig.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# portal (build_all)
# ---------------------------------------------------------------------------

def test_portal_index_lists_project(site):
    repo, root = site
    portal = root / "index.html"
    assert portal.exists()
    assert repo.project in portal.read_text(encoding="utf-8")


def test_site_search_emitted(site):
    _, root = site
    assert (root / "search.json").exists()
    assert (root / "search.html").exists()


def test_referenced_library_media_copied_into_site(site):
    repo, root = site
    # The match-review project references one global library media item (P2);
    # the build resolves the ref against the catalog and copies the file in.
    media_file = root / repo.project / "media" / f"{repo.media_id}.png"
    assert media_file.exists()
    assert media_file.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_media_embed_renders_with_attribution(site):
    repo, root = site
    # The confirmed essay embeds [[media:<id>]]; the rendered match essay must show
    # the figure with its catalog attribution (Phase 29 gate).
    essay = (root / repo.project / "matches" / f"{repo.conf_slug}.html").read_text()
    assert f"media/{repo.media_id}.png" in essay
    assert "public domain" in essay.lower()   # attribution_text from the catalog


# ---------------------------------------------------------------------------
# annual-review project (build_all review branch)
# ---------------------------------------------------------------------------

def test_discover_annual_reviews(site):
    repo, _ = site
    from markery.specialist.publisher import build
    names = [p.name for p in build.discover_annual_reviews()]
    assert repo.review_project in names


def test_annual_review_pages_rendered(site):
    repo, root = site
    year_dir = root / repo.review_project / str(repo.review_year)
    assert (year_dir / "index.html").exists(), "year landing missing"
    # 12 monthly galleries.
    months = sorted(p.name for p in year_dir.glob("[0-1][0-9].html"))
    assert len(months) == 12, f"expected 12 monthly pages, got {months}"


def test_annual_review_design_mark_present(site):
    repo, root = site
    # The design mark (STARBURST) was filed in June of the review year.
    june = (root / repo.review_project / str(repo.review_year) / "06.html").read_text()
    assert "STARBURST" in june


def test_portal_lists_review(site):
    repo, root = site
    portal = (root / "index.html").read_text(encoding="utf-8")
    assert str(repo.review_year) in portal


def test_review_pages_indexed_in_search(site):
    repo, root = site
    import json
    records = json.loads((root / "search.json").read_text())
    titles = [r["title"] for r in records]
    # The year landing + 12 months of the annual review are searchable.
    assert f"{repo.review_year} Design-Mark Review" in titles
    assert sum(1 for t in titles if f"{repo.review_year}-" in t) == 12


# ---------------------------------------------------------------------------
# check_site — no broken internal links
# ---------------------------------------------------------------------------

def test_check_site_no_broken_links(site):
    repo, root = site
    from markery.specialist.publisher import check
    report = check.check_site(repo.project, root / repo.project)
    assert report["broken"] == [], f"broken links: {report['broken']}"
    assert report["pages"] > 0


def test_check_site_missing_dir_reports_cleanly(site):
    repo, root = site
    from markery.specialist.publisher import check
    report = check.check_site(repo.project, root / "does-not-exist")
    assert report.get("missing_dir") is True


def test_run_check_exit_code_zero(site, capsys):
    repo, root = site
    from markery.specialist.publisher.check import run_check
    rc = run_check(repo.project, root / repo.project)
    out = capsys.readouterr().out
    assert rc == 0
    assert "All internal links resolve." in out
    assert "broken links  : 0" in out


# ---------------------------------------------------------------------------
# base_url → sitemap.xml + canonical
# ---------------------------------------------------------------------------

def test_build_all_with_base_url_emits_sitemap(site):
    repo, root = site
    from markery.specialist.publisher import build
    bu_root = repo.root / "site-bu"
    build.build_all(bu_root, base_url="https://example.com")
    sitemap = bu_root / "sitemap.xml"
    assert sitemap.exists()
    text = sitemap.read_text()
    assert "https://example.com/" in text
    assert f"{repo.project}/index.html" in text
