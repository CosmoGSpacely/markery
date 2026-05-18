"""Orchestrate full site build for a project."""

from __future__ import annotations

from pathlib import Path

from markery.common.config import Project
from markery.specialist.publisher import queries as q
from markery.specialist.publisher import render as r


def build_site(project: str, out_dir: Path | None = None) -> list[Path]:
    """Render all pages for a project; return list of written paths."""
    proj = Project(project)
    out  = out_dir if out_dir is not None else proj.site
    out.mkdir(parents=True, exist_ok=True)
    (out / "entities").mkdir(exist_ok=True)
    (out / "matches").mkdir(exist_ok=True)

    print(f"Building site for '{project}' → {out}/")

    entity_ids = q.get_project_entity_ids(project)
    entities   = q.get_entities(entity_ids)
    trademarks = q.get_trademarks_for_project(entity_ids)
    patents    = q.get_patents_for_project(entity_ids)
    matches    = q.get_confirmed_matches(project)
    stats      = q.get_entity_stats(entity_ids, trademarks, patents, matches)
    colors     = r._entity_color_map(entity_ids)

    pages: list[Path] = []

    pages.append(r.render_landing(project, entities, trademarks, patents, matches, stats, out))
    print(f"  landing          → {pages[-1].name}")

    pages.append(r.render_trademark_gallery(project, entities, trademarks, matches, colors, out))
    print(f"  trademark gallery → {pages[-1].name}")

    pages.append(r.render_patent_gallery(project, entities, patents, matches, colors, out))
    print(f"  patent gallery   → {pages[-1].name}")

    for entity in entities:
        ent_tms   = [t for t in trademarks if t["entity_id"] == entity["entity_id"]]
        ent_pats  = [p for p in patents    if p["entity_id"] == entity["entity_id"]]
        ent_mats  = [m for m in matches    if m["entity_id"] == entity["entity_id"]]
        ent_stats = stats.get(entity["entity_id"], {})
        p = r.render_entity_page(project, entity, entities, ent_tms, ent_pats, ent_mats, ent_stats, out)
        pages.append(p)
        print(f"  entity           → entities/{p.name}")

    seen: set[str] = set()
    for match in matches:
        slug = match.get("slug", "")
        if slug in seen:
            continue
        seen.add(slug)
        p = r.render_match_essay(project, match, entities, out)
        pages.append(p)
        print(f"  match essay      → matches/{p.name}")

    print(f"\n{len(pages)} pages written to {out}/")
    return pages
