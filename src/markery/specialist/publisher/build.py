"""Orchestrate full site build for a project."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from markery.common import config
from markery.common.project import Project, ProjectType, load_project
from markery.specialist.publisher import queries as q
from markery.specialist.publisher import render as r

# Years to build annual design-mark reviews for (Phase 24 P4).
REVIEW_YEARS = [1929, 1930]


def _collect_theme_slugs(proj: Project) -> list[str]:
    """Return slugs for all content/theme-<slug>.md files."""
    return [
        p.stem[len("theme-"):]
        for p in sorted(proj.content.glob("theme-*.md"))
        if p.stem.startswith("theme-")
    ]


def _build_extra_nav(proj: Project, theme_slugs: list[str]) -> dict[str, str]:
    """Build the extra nav entries for optional pages that exist."""
    extra: dict[str, str] = {}
    for slug in theme_slugs:
        label = slug.replace("-", " ").title()
        extra[label] = f"themes/{slug}.html"
    if (proj.content / "timeline.md").exists():
        extra["Timeline"] = "timeline.html"
    if (proj.content / "sources.md").exists():
        extra["Sources"] = "sources.html"
    extra["Search"] = "search.html"
    return extra


def _build_search_record(
    title: str,
    page_type: str,
    url: str,
    src_path: Path | None,
) -> dict:
    excerpt = r._text_excerpt(src_path) if src_path else ""
    return {"title": title, "type": page_type, "url": url, "excerpt": excerpt}


def _run_pagefind(out_dir: Path) -> None:
    """Run pagefind against the output directory if the binary is available."""
    binary = shutil.which("pagefind")
    if binary is None:
        return
    try:
        subprocess.run(
            [binary, "--site", str(out_dir)],
            check=True,
            capture_output=True,
        )
        print(f"  pagefind index  → {out_dir}/pagefind/")
    except subprocess.CalledProcessError as exc:
        print(f"  pagefind failed: {exc.stderr.decode()[:200]}")


def _prune_stale(out: Path, written: set[Path]) -> list[Path]:
    """Remove HTML, image, and media files under `out` not written this run.

    Only `.html` pages and files under `images/` and `media/` are pruned — these
    are the outputs whose names track project state (match slugs, mark serials,
    media slugs) and so go stale when that state changes. The pagefind index and
    `search.json` are rewritten every build and left alone.
    """
    removed: list[Path] = []
    candidates = list(out.rglob("*.html"))
    for sub in ("images", "media"):
        d = out / sub
        if d.exists():
            candidates += [p for p in d.rglob("*") if p.is_file()]
    for f in candidates:
        if f.resolve() not in written:
            f.unlink()
            removed.append(f)
    return removed


def _display_title(project: str) -> str:
    return project.replace("-", " ").title()


def discover_projects() -> list[str]:
    """Return slugs of all match-review-essay projects under projects/, sorted."""
    base = config.ROOT / "projects"
    out: list[str] = []
    for d in sorted(base.iterdir()) if base.exists() else []:
        if not (d / "project.json").is_file():
            continue
        try:
            proj = load_project(d)
        except (ValueError, FileNotFoundError):
            continue
        if proj.type == ProjectType.MATCH_REVIEW_ESSAY:
            out.append(d.name)
    return out


def _project_overrides(proj: Project) -> dict:
    pj = proj.root / "project.json"
    if not pj.exists():
        return {}
    try:
        return json.loads(pj.read_text())
    except (ValueError, OSError):
        return {}


def _auto_summary(proj: Project) -> str:
    """First real paragraph of OBJECTIVES.md (heading + frontmatter stripped)."""
    path = proj.objectives
    if not path.exists():
        return ""
    text = r._strip_frontmatter(path.read_text())
    for para in text.split("\n\n"):
        block = " ".join(
            ln.strip() for ln in para.splitlines() if not ln.lstrip().startswith("#")
        ).strip()
        if block:
            return (block[:277] + "…") if len(block) > 280 else block
    return ""


def _representative_mark(project: str, tms: list[dict], pair_serials: set[str],
                         override) -> tuple[str | None, str]:
    mark = None
    if override is not None:
        mark = next((t for t in tms if str(t["serial_no"]) == str(override)), None)
    if mark is None:
        mark = next((t for t in tms if t.get("image_available")
                     and str(t["serial_no"]) in pair_serials), None)
    if mark is None:
        mark = next((t for t in tms if t.get("image_available")), None)
    if mark is None:
        mark = tms[0] if tms else None
    if mark is None:
        return None, "No marks"
    src = (f"{project}/images/marks/{mark['serial_no']}.png"
           if mark.get("image_available") else None)
    return src, (mark.get("mark_name") or "(design mark)")


def _representative_figure(project: str, pats: list[dict], pair_patents: set[str],
                           override) -> tuple[str | None, str]:
    pat = None
    if override is not None:
        pat = next((p for p in pats if p["patent_no"] == override), None)
    if pat is None:
        pat = next((p for p in pats if p.get("figure_available")
                    and p["patent_no"] in pair_patents), None)
    if pat is None:
        pat = next((p for p in pats if p.get("figure_available")), None)
    if pat is None:
        pat = pats[0] if pats else None
    if pat is None:
        return None, "No patents"
    src = (f"{project}/images/patents/{pat['patent_no']}.png"
           if pat.get("figure_available") else None)
    return src, (pat.get("title") or pat["patent_no"])


def build_all(out_dir: Path | None = None, base_url: str | None = None,
              prune: bool = True) -> list[Path]:
    """Build every project into the unified site root plus the Markery portal.

    Produces site/index.html (portal), site/<project>/... (each project),
    site/search.html + site/search.json (site-wide search), and site/sitemap.xml
    (when base_url is given).
    """
    site_root = out_dir if out_dir is not None else config.SITE_ROOT
    site_root.mkdir(parents=True, exist_ok=True)

    projects = discover_projects()
    print(f"Building Markery portal for {len(projects)} project(s) → {site_root}/")

    portal_projects: list[dict] = []
    portal_matches: list[dict] = []
    combined_search: list[dict] = []

    for project in projects:
        proj_out = site_root / project
        proj_base = f"{base_url.rstrip('/')}/{project}" if base_url else None
        build_site(project, proj_out, base_url=proj_base, prune=prune)

        proj = load_project(Project(project).root)
        ids = q.get_project_entity_ids(project)
        entities = q.get_entities(ids)
        tms = q.get_trademarks_for_project(ids)
        pats = q.get_patents_for_project(ids)
        matches = q.get_confirmed_matches(project)
        overrides = _project_overrides(proj)

        pair_serials = {str(m["trademark_serial"]) for m in matches}
        pair_patents = {m["patent_no"] for m in matches}
        mark_src, mark_label = _representative_mark(
            project, tms, pair_serials, overrides.get("feature_serial"))
        fig_src, fig_label = _representative_figure(
            project, pats, pair_patents, overrides.get("feature_patent"))
        # image_available can be set without bytes on disk — only link a file
        # the project build actually wrote.
        if mark_src and not (site_root / mark_src).exists():
            mark_src = None
        if fig_src and not (site_root / fig_src).exists():
            fig_src = None

        confirmed = [m for m in matches if m.get("essay_path")]
        portal_projects.append({
            "slug": project,
            "title": _display_title(project),
            "summary": overrides.get("summary") or _auto_summary(proj),
            "counts": {
                "companies": len(entities), "marks": len(tms),
                "patents": len(pats), "pairs": len(confirmed),
            },
            "mark_src": mark_src, "mark_label": mark_label,
            "fig_src": fig_src, "fig_label": fig_label,
        })

        seen: set[str] = set()
        for m in confirmed:
            slug = m.get("slug", "")
            if not slug or slug in seen:
                continue
            seen.add(slug)
            thumb_src = (f"{project}/images/marks/{m['trademark_serial']}.png"
                         if m.get("has_image") else None)
            if thumb_src and not (site_root / thumb_src).exists():
                thumb_src = None
            portal_matches.append({
                "url": f"{project}/matches/{slug}.html",
                "label": m.get("trademark") or "(figurative)",
                "patent_no": m["patent_no"],
                "project_title": _display_title(project),
                "entity": m.get("entity", ""),
                "note": m.get("note", ""),
                "thumb_src": thumb_src,
            })

        sj = proj_out / "search.json"
        if sj.exists():
            for rec in json.loads(sj.read_text()):
                rec = dict(rec)
                rec["url"] = f"{project}/{rec['url']}"
                rec["title"] = f"{rec['title']} · {_display_title(project)}"
                combined_search.append(rec)

    # Annual design-mark reviews (Phase 24 P4): one year landing + 12 monthly
    # galleries each, surfaced as portal cards.
    pages: list[Path] = []
    review_summaries: list[dict] = []
    for year in REVIEW_YEARS:
        y_path, y_summary, _ = r.render_review_year(year, site_root, base_url=base_url)
        review_summaries.append(y_summary)
        pages.append(y_path)
        for mm in range(1, 13):
            pages.append(site_root / "reviews" / str(year) / f"{mm:02d}.html")
        print(f"  review {year}      → reviews/{year}/ (12 months, {y_summary['count']} marks)")

    pages.insert(0, r.render_portal(site_root, portal_projects, portal_matches,
                                    base_url=base_url, reviews=review_summaries))
    print(f"  portal           → index.html ({len(portal_projects)} projects, {len(review_summaries)} reviews)")
    pages.append(r.render_root_search(site_root))
    print("  root search      → search.html")

    (site_root / "search.json").write_text(
        json.dumps(combined_search, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  search.json      → {len(combined_search)} records")

    if base_url:
        base = base_url.rstrip("/")
        locs = sorted(
            f"{base}/{p.relative_to(site_root).as_posix()}"
            for p in site_root.rglob("*.html")
        )
        urls = "".join(f"  <url><loc>{loc}</loc></url>\n" for loc in locs)
        (site_root / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{urls}</urlset>\n", encoding="utf-8")
        print(f"  sitemap.xml      → {len(locs)} urls")

    _run_pagefind(site_root)
    print(f"\nMarkery portal built at {site_root}/")
    return pages


def build_site(project: str, out_dir: Path | None = None, base_url: str | None = None,
               prune: bool = True) -> list[Path]:
    """Render all pages for a project; return list of written paths.

    When ``prune`` is true (the default), stale `.html` and `images/` files from
    a previous build that are not re-written this run are removed, so renamed or
    deleted pages do not linger as orphans on disk.
    """
    proj = load_project(Project(project).root)
    # The CLI and build_all pass an explicit out_dir under the unified site root
    # (site/<project>/); proj.site remains the fallback for direct callers.
    out  = out_dir if out_dir is not None else proj.site
    out.mkdir(parents=True, exist_ok=True)
    (out / "entities").mkdir(exist_ok=True)
    (out / "matches").mkdir(exist_ok=True)
    (out / "themes").mkdir(exist_ok=True)
    (out / "trademarks").mkdir(exist_ok=True)
    (out / "patents").mkdir(exist_ok=True)

    focus_serials: set[int] | None = set(proj.focus_serials) if proj.focus_serials else None
    rq_path = proj.content / "research-question.md"
    research_question: str | None = rq_path.read_text(encoding="utf-8").strip() if rq_path.exists() else None

    print(f"Building site for '{project}' → {out}/")
    if focus_serials:
        print(f"  focus_serials: {len(focus_serials)} project marks")
    if research_question:
        print(f"  research-question.md: {len(research_question)} chars")

    entity_ids = q.get_project_entity_ids(project)
    entities   = q.get_entities(entity_ids)
    trademarks = q.get_trademarks_for_project(entity_ids)
    patents    = q.get_patents_for_project(entity_ids)
    matches    = q.get_confirmed_matches(project)
    stats      = q.get_entity_stats(entity_ids, trademarks, patents, matches)
    colors     = r._entity_color_map(entity_ids)

    theme_slugs = _collect_theme_slugs(proj)
    link_index  = r.build_link_index(entities, matches, theme_slugs)
    extra_nav   = _build_extra_nav(proj, theme_slugs)

    # Write image files to disk and build figure_index for [[figure:]] cross-links.
    images_dir = out / "images"
    (images_dir / "marks").mkdir(parents=True, exist_ok=True)
    (images_dir / "patents").mkdir(parents=True, exist_ok=True)

    written_images: set[Path] = set()
    for tm in trademarks:
        if tm.get("image_available"):
            data = q.get_mark_image_bytes(tm["serial_no"])
            if data:
                dest = images_dir / "marks" / f"{tm['serial_no']}.png"
                dest.write_bytes(data)
                written_images.add(dest.resolve())

    figure_index: dict[str, str] = {}
    for pat in patents:
        if pat.get("figure_available"):
            data = q.get_patent_figure_bytes(pat["patent_no"])
            if data:
                dest = images_dir / "patents" / f"{pat['patent_no']}.png"
                dest.write_bytes(data)
                figure_index[pat["patent_no"]] = f"images/patents/{pat['patent_no']}.png"
                written_images.add(dest.resolve())

    # Copy acquired public-domain/free media and build media_index for [[media:]] embeds.
    media_index: dict[str, dict] = {}
    media_src = proj.root / "library" / "media"
    media_idx_file = media_src / "index.jsonl"
    if media_idx_file.exists():
        out_media = out / "media"
        for line in media_idx_file.read_text().splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            srcfile = media_src / item["slug"] / item["file"]
            if not srcfile.exists():
                continue
            dest = out_media / item["file"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(srcfile.read_bytes())
            written_images.add(dest.resolve())
            media_index[item["slug"]] = {
                "file": f"media/{item['file']}",
                "title": item.get("title", ""),
                "attribution_text": item.get("attribution_text", ""),
                "license": item.get("license", ""),
                "source_url": item.get("source_url", ""),
            }

    pages: list[Path] = []
    search_records: list[dict] = []

    pages.append(r.render_landing(
        project, entities, trademarks, patents, matches, stats, out,
        base_url=base_url, link_index=link_index, extra_nav=extra_nav,
        images_dir=images_dir, research_question=research_question,
        media_index=media_index,
    ))
    print(f"  landing          → {pages[-1].name}")
    search_records.append(_build_search_record(
        project.replace("-", " ").title(), "landing", "index.html",
        proj.content / "index-narrative.md",
    ))

    pages.append(r.render_trademark_gallery(
        project, entities, trademarks, matches, colors, out,
        base_url=base_url, link_index=link_index, extra_nav=extra_nav,
        images_dir=images_dir, focus_serials=focus_serials,
        media_index=media_index,
    ))
    print(f"  trademark gallery → {pages[-1].name}")

    pages.append(r.render_patent_gallery(
        project, entities, patents, matches, colors, out,
        base_url=base_url, link_index=link_index, extra_nav=extra_nav,
        images_dir=images_dir, media_index=media_index,
    ))
    print(f"  patent gallery   → {pages[-1].name}")

    for tm in trademarks:
        p = r.render_trademark_detail(
            project, tm, entities, matches, out,
            base_url=base_url, link_index=link_index, extra_nav=extra_nav,
            images_dir=images_dir,
        )
        pages.append(p)
        search_records.append(_build_search_record(
            tm["mark_name"] or "(design mark)", "trademark",
            f"trademarks/{tm['serial_no']}.html", None,
        ))
    print(f"  trademark detail → {len(trademarks)} page(s)")

    for pat in patents:
        p = r.render_patent_detail(
            project, pat, entities, matches, out,
            base_url=base_url, link_index=link_index, extra_nav=extra_nav,
            images_dir=images_dir,
        )
        pages.append(p)
        search_records.append(_build_search_record(
            pat.get("title") or pat["patent_no"], "patent",
            f"patents/{pat['patent_no']}.html", None,
        ))
    print(f"  patent detail    → {len(patents)} page(s)")

    pages.append(r.render_entities_index(
        project, entities, stats, out,
        base_url=base_url, link_index=link_index, extra_nav=extra_nav,
    ))
    print(f"  entities index   → entities/{pages[-1].name}")
    search_records.append(_build_search_record(
        "Entities", "entities_index", "entities/index.html", None,
    ))

    for entity in entities:
        ent_tms   = [t for t in trademarks if t["entity_id"] == entity["entity_id"]]
        ent_pats  = [p for p in patents    if p["entity_id"] == entity["entity_id"]]
        ent_mats  = [m for m in matches    if m["entity_id"] == entity["entity_id"]]
        ent_stats = stats.get(entity["entity_id"], {})
        p = r.render_entity_page(
            project, entity, entities, ent_tms, ent_pats, ent_mats, ent_stats, out,
            base_url=base_url, link_index=link_index, extra_nav=extra_nav,
            media_index=media_index,
        )
        pages.append(p)
        print(f"  entity           → entities/{p.name}")
        search_records.append(_build_search_record(
            entity["canonical_name"], "entity",
            f"entities/{entity['slug']}.html",
            proj.content / f"entity-{entity['slug']}.md",
        ))

    pages.append(r.render_matches_index(
        project, matches, entities, out,
        base_url=base_url, link_index=link_index, extra_nav=extra_nav,
        images_dir=images_dir,
    ))
    print(f"  matches index    → matches/{pages[-1].name}")
    search_records.append(_build_search_record(
        "Confirmed Pairs", "matches_index", "matches/index.html", None,
    ))

    seen: set[str] = set()
    for match in matches:
        slug = match.get("slug", "")
        if slug in seen:
            continue
        seen.add(slug)
        p = r.render_match_essay(
            project, match, entities, out,
            base_url=base_url, link_index=link_index, extra_nav=extra_nav,
            images_dir=images_dir, figure_index=figure_index,
            media_index=media_index,
        )
        pages.append(p)
        print(f"  match essay      → matches/{p.name}")
        essay_path = Path(match["essay_path"]) if match.get("essay_path") else None
        search_records.append(_build_search_record(
            f"{match['trademark'] or '(figurative)'} ↔ {match['patent_no']}",
            "match_essay",
            f"matches/{slug}.html",
            essay_path,
        ))

    for slug in theme_slugs:
        p = r.render_thematic_essay(
            project, slug, out, entities,
            base_url=base_url, link_index=link_index, extra_nav=extra_nav,
            media_index=media_index,
        )
        pages.append(p)
        print(f"  thematic essay   → themes/{p.name}")
        search_records.append(_build_search_record(
            slug.replace("-", " ").title(), "thematic_essay",
            f"themes/{slug}.html",
            proj.content / f"theme-{slug}.md",
        ))

    if (proj.content / "sources.md").exists():
        p = r.render_sources_page(
            project, out, entities,
            base_url=base_url, link_index=link_index, extra_nav=extra_nav,
        )
        pages.append(p)
        print(f"  sources          → {p.name}")
        search_records.append(_build_search_record(
            "Sources", "sources", "sources.html", proj.content / "sources.md",
        ))

    if (proj.content / "timeline.md").exists():
        p = r.render_timeline_page(
            project, out, entities, patents, trademarks, colors,
            base_url=base_url, link_index=link_index, extra_nav=extra_nav,
        )
        pages.append(p)
        print(f"  timeline         → {p.name}")
        search_records.append(_build_search_record(
            "Timeline", "timeline", "timeline.html", proj.content / "timeline.md",
        ))

    search_page = r.render_search_page(project, out, entities, extra_nav)
    pages.append(search_page)
    print(f"  search           → {search_page.name}")

    (out / "search.json").write_text(
        json.dumps(search_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  search.json      → {len(search_records)} records")

    if base_url:
        base = base_url.rstrip("/")
        locs = [
            f"{base}/{project}/{p.relative_to(out).as_posix()}"
            for p in pages
        ]
        urls = "".join(f"  <url><loc>{loc}</loc></url>\n" for loc in sorted(locs))
        (out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{urls}"
            "</urlset>\n",
            encoding="utf-8",
        )
        print(f"  sitemap.xml      → {len(locs)} urls")

    if prune:
        written = {p.resolve() for p in pages} | written_images
        removed = _prune_stale(out, written)
        if removed:
            print(f"  pruned           → {len(removed)} stale file(s)")

    _run_pagefind(out)

    print(f"\n{len(pages)} pages written to {out}/")
    return pages
