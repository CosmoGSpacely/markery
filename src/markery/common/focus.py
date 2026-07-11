"""Focus areas — the unit of the reconfigured Markery (Phase 34, STRUCTURE_REVIEW §2–3).

Markery is one cross-linked website: a web of *documented subjects* ("focus areas")
of five types (mark, patent, technology, entity, person), each an essay + media +
library references. A focus **references** shared corpus/registry data by id/slug; it
never re-declares entities.

This module owns:
  * the ``focus.json`` manifest schema (one schema for all five types, Decision 3);
  * ``[[type:slug]]`` cross-link resolution with **alias redirects** (Decision 2) —
    an unresolved link is a build failure, the same integrity discipline as ``site check``.

The registry (DuckDB) supplies identity + alias redirects via
``registry_link_maps``; the resolver itself is layout-agnostic (it takes an explicit
``url_for`` map) so it is testable without a site build. Render-time wiring lands in
Phase 37.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# The five focus types. Ordered for stable listing; membership is what matters.
FOCUS_TYPES: tuple[str, ...] = ("mark", "patent", "technology", "entity", "person")

# Namespaces the cross-link resolver owns. CPC is a browse *facet*, not a focus, but it
# is a first-class link namespace (Decision 2). Namespaces outside this set (media,
# figure) are handled by other render passes and pass through the resolver untouched.
LINK_NAMESPACES: frozenset[str] = frozenset(FOCUS_TYPES) | {"cpc"}

# [[type:slug]] — slug is everything up to the closing bracket (slugs never contain ]).
CROSS_LINK_RE = re.compile(r"\[\[([a-z]+):([^\]]+)\]\]")


class UnresolvedLink(Exception):
    """A [[type:slug]] cross-link in an owned namespace did not resolve. Fails the build."""


# ---------------------------------------------------------------------------
# focus.json manifest
# ---------------------------------------------------------------------------

@dataclass
class Focus:
    """A focus manifest (``focus.json``). One schema for all five types.

    ``subject`` is the identity (USPTO serial, patent no, or internal registry id);
    ``slug`` is stored and immutable (never re-derived at render). ``selector`` is
    used only by technology foci, whose CPC selector over-includes and is narrowed by
    a curated ``members.jsonl``.
    """
    type: str
    subject: str
    slug: str
    title: str
    selector: dict | None = None

    def __post_init__(self) -> None:
        if self.type not in FOCUS_TYPES:
            raise ValueError(
                f"focus type {self.type!r} not one of {FOCUS_TYPES}"
            )
        if self.selector is not None and self.type != "technology":
            raise ValueError(
                f"selector is only valid on technology foci, not {self.type!r}"
            )

    def to_dict(self) -> dict:
        d: dict = {
            "type": self.type,
            "subject": self.subject,
            "slug": self.slug,
            "title": self.title,
        }
        if self.selector is not None:
            d["selector"] = self.selector
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Focus":
        missing = {"type", "subject", "slug", "title"} - d.keys()
        if missing:
            raise ValueError(f"focus.json missing required key(s): {sorted(missing)}")
        return cls(
            type=d["type"],
            subject=str(d["subject"]),
            slug=d["slug"],
            title=d["title"],
            selector=d.get("selector"),
        )

    # -- filesystem layout: focus/<type>/<slug>/ ----------------------------

    @staticmethod
    def dir(root: Path, type: str, slug: str) -> Path:
        return Path(root) / "focus" / type / slug

    @property
    def link_key(self) -> tuple[str, str]:
        return (self.type, self.slug)

    def write(self, root: Path) -> Path:
        """Write focus.json under focus/<type>/<slug>/. Returns the focus directory."""
        d = Focus.dir(root, self.type, self.slug)
        d.mkdir(parents=True, exist_ok=True)
        (d / "focus.json").write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n"
        )
        return d

    @classmethod
    def load(cls, focus_json: Path) -> "Focus":
        return cls.from_dict(json.loads(Path(focus_json).read_text()))


def load_all_foci(root: Path) -> list[Focus]:
    """Load every focus/<type>/<slug>/focus.json under root, ordered by (type, slug)."""
    base = Path(root) / "focus"
    if not base.exists():
        return []
    foci = [Focus.load(p) for p in sorted(base.glob("*/*/focus.json"))]
    return sorted(foci, key=lambda f: (FOCUS_TYPES.index(f.type), f.slug))


# ---------------------------------------------------------------------------
# Default URL layout (Phase 37 may override by passing its own url_for map)
# ---------------------------------------------------------------------------

def default_focus_url(type: str, slug: str) -> str:
    """Root-relative URL for a focus of the given type/slug."""
    if type == "cpc":
        return f"cpc/{slug}/"
    return f"focus/{type}/{slug}/"


# ---------------------------------------------------------------------------
# Cross-link resolver — [[type:slug]] with alias redirects
# ---------------------------------------------------------------------------

@dataclass
class LinkResolver:
    """Resolve [[type:slug]] cross-links, following alias redirects.

    ``url_for`` maps (type, slug) → root-relative URL for every known target.
    ``aliases`` maps (type, retired_slug) → survivor_slug (dedup redirects); a chain
    is followed to its survivor. A link in an owned namespace (LINK_NAMESPACES) that
    resolves to neither raises UnresolvedLink — a build failure. Links outside the
    owned namespaces pass through untouched (media/figure are other passes' concern).
    """
    url_for: dict[tuple[str, str], str] = field(default_factory=dict)
    aliases: dict[tuple[str, str], str] = field(default_factory=dict)

    def resolve(self, type: str, slug: str) -> str:
        """Return the URL for (type, slug), following aliases. Raises UnresolvedLink."""
        seen: set[str] = set()
        cur = slug
        while (type, cur) not in self.url_for:
            redirect = self.aliases.get((type, cur))
            if redirect is None or redirect in seen:
                raise UnresolvedLink(f"[[{type}:{slug}]] does not resolve")
            seen.add(cur)
            cur = redirect
        return self.url_for[(type, cur)]

    def resolve_html(self, text: str, label_for: dict[tuple[str, str], str] | None = None) -> str:
        """Replace every owned [[type:slug]] in text with an <a> tag.

        Unowned namespaces are left verbatim. Raises UnresolvedLink on the first owned
        link that fails to resolve. ``label_for`` supplies anchor text; the slug is used
        when absent.
        """
        label_for = label_for or {}

        def _sub(m: re.Match) -> str:
            ns, slug = m.group(1), m.group(2)
            if ns not in LINK_NAMESPACES:
                return m.group(0)
            url = self.resolve(ns, slug)  # raises on unresolved
            label = label_for.get((ns, slug), slug)
            return f'<a href="{url}">{label}</a>'

        return CROSS_LINK_RE.sub(_sub, text)

    def unresolved(self, text: str) -> list[tuple[str, str]]:
        """Return owned (type, slug) links in text that do not resolve. For site check."""
        out: list[tuple[str, str]] = []
        for ns, slug in CROSS_LINK_RE.findall(text):
            if ns not in LINK_NAMESPACES:
                continue
            try:
                self.resolve(ns, slug)
            except UnresolvedLink:
                out.append((ns, slug))
        return out


def registry_link_maps(conn) -> tuple[dict, dict]:
    """Derive (url_for, aliases) for entity + person foci from the registry connection.

    Entities/persons contribute (type, slug) → focus URL for every registered subject;
    entity_alias / person_alias contribute (type, retired_slug) → survivor_slug so
    merged/retired slugs redirect rather than 404. Mark/patent/technology/cpc targets
    are added by the caller (they come from foci + the corpus, not the registry).
    """
    url_for: dict[tuple[str, str], str] = {}
    aliases: dict[tuple[str, str], str] = {}

    for slug, in conn.execute(
        "SELECT slug FROM company_entity WHERE slug IS NOT NULL AND slug <> ''"
    ).fetchall():
        url_for[("entity", slug)] = default_focus_url("entity", slug)
    for slug, in conn.execute(
        "SELECT slug FROM person_entity WHERE slug IS NOT NULL AND slug <> ''"
    ).fetchall():
        url_for[("person", slug)] = default_focus_url("person", slug)

    # Alias redirects: retired_slug → survivor's stored slug.
    for retired_slug, surv_slug in conn.execute(
        "SELECT a.retired_slug, e.slug FROM entity_alias a "
        "JOIN company_entity e ON e.entity_id = a.survivor_id "
        "WHERE a.retired_slug IS NOT NULL AND a.retired_slug <> ''"
    ).fetchall():
        aliases[("entity", retired_slug)] = surv_slug
    for retired_slug, surv_slug in conn.execute(
        "SELECT a.retired_slug, p.slug FROM person_alias a "
        "JOIN person_entity p ON p.person_id = a.survivor_id "
        "WHERE a.retired_slug IS NOT NULL AND a.retired_slug <> ''"
    ).fetchall():
        aliases[("person", retired_slug)] = surv_slug

    return url_for, aliases
