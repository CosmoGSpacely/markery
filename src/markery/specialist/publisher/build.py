"""Orchestrate full site build for a project."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from markery.common.project import Project, load_project
from markery.specialist.publisher import queries as q
from markery.specialist.publisher import render as r


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


def build_site(project: str, out_dir: Path | None = None, base_url: str | None = None) -> list[Path]:
    """Render all pages for a project; return list of written paths."""
    proj = load_project(Project(project).root)
    out  = out_dir if out_dir is not None else proj.site
    out.mkdir(parents=True, exist_ok=True)
    (out / "entities").mkdir(exist_ok=True)
    (out / "matches").mkdir(exist_ok=True)
    (out / "themes").mkdir(exist_ok=True)

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

    for tm in trademarks:
        if tm.get("image_available"):
            data = q.get_mark_image_bytes(tm["serial_no"])
            if data:
                (images_dir / "marks" / f"{tm['serial_no']}.png").write_bytes(data)

    figure_index: dict[str, str] = {}
    for pat in patents:
        if pat.get("figure_available"):
            data = q.get_patent_figure_bytes(pat["patent_no"])
            if data:
                dest = images_dir / "patents" / f"{pat['patent_no']}.png"
                dest.write_bytes(data)
                figure_index[pat["patent_no"]] = f"images/patents/{pat['patent_no']}.png"

    pages: list[Path] = []
    search_records: list[dict] = []

    pages.append(r.render_landing(
        project, entities, trademarks, patents, matches, stats, out,
        base_url=base_url, link_index=link_index, extra_nav=extra_nav,
        images_dir=images_dir, research_question=research_question,
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
    ))
    print(f"  trademark gallery → {pages[-1].name}")

    pages.append(r.render_patent_gallery(
        project, entities, patents, matches, colors, out,
        base_url=base_url, link_index=link_index, extra_nav=extra_nav,
        images_dir=images_dir,
    ))
    print(f"  patent gallery   → {pages[-1].name}")

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

    _run_pagefind(out)

    print(f"\n{len(pages)} pages written to {out}/")
    return pages
