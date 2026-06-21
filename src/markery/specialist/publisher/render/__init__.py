"""HTML page generators for the Markery research site.

This package was decomposed from a single 1560-line module. Submodules:
  css        — the shared CSS block
  components — escaping, page chrome, Markdown parser, timeline, helpers
  landing    — landing page + Entities/Matches section index pages
  galleries  — trademark and patent galleries
  entity     — entity profile page
  essays     — match essays and thematic essays
  aux        — sources, timeline, and search pages

The names below are re-exported so existing imports
(`from markery.specialist.publisher.render import X`) keep working.
"""

from markery.specialist.publisher.render.components import (
    _STATUS_LABELS,
    _MARKERY_REPO,
    _esc,
    _img_src,
    _page,
    _nav_links,
    _render_markdown,
    _read_narrative,
    _narrative_block,
    _page_title,
    _breadcrumb,
    _strip_frontmatter,
    _parse_site_mode,
    _text_excerpt,
    _year_from_dt,
    build_link_index,
    _timeline_range,
    _timeline_svg,
    _entity_color_map,
)
from markery.specialist.publisher.render.landing import (
    render_landing,
    render_entities_index,
    render_matches_index,
)
from markery.specialist.publisher.render.galleries import (
    render_trademark_gallery,
    render_patent_gallery,
)
from markery.specialist.publisher.render.entity import render_entity_page
from markery.specialist.publisher.render.detail import (
    render_trademark_detail,
    render_patent_detail,
)
from markery.specialist.publisher.render.essays import (
    render_match_essay,
    render_thematic_essay,
)
from markery.specialist.publisher.render.aux import (
    render_sources_page,
    render_timeline_page,
    render_search_page,
)
from markery.specialist.publisher.render.portal import (
    render_portal,
    render_root_search,
)

__all__ = [
    "render_landing",
    "render_entities_index",
    "render_matches_index",
    "render_trademark_gallery",
    "render_patent_gallery",
    "render_entity_page",
    "render_trademark_detail",
    "render_patent_detail",
    "render_match_essay",
    "render_thematic_essay",
    "render_sources_page",
    "render_timeline_page",
    "render_search_page",
    "render_portal",
    "render_root_search",
    "build_link_index",
]
