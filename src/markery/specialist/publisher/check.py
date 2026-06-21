"""Validate a built site: resolve internal links, report broken links and orphans.

`markery site check <project>` walks every built HTML page, resolves each internal
`href`/`src` against files on disk, and reports:

  - broken links   — a relative target that does not exist on disk
  - orphaned files  — an emitted file no page links to (and which is not an entry point)

Exits non-zero on any broken link so the command can gate a build. Orphans are
reported as warnings and do not by themselves fail the check (an orphan is dead
weight, not breakage); pass ``--strict`` to also fail on orphans.

This reads only build artifacts (HTML on disk), not project DB/CSV/JSONL state,
so it does not bypass the CLI-first rule for project state.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from markery.common.project import Project, load_project

# Files that legitimately have no inbound link from another page.
_ENTRY_POINTS = {"index.html", "search.html", "search.json", "sitemap.xml", "robots.txt"}
# Directory prefixes whose contents are managed externally (search index, etc.).
_IGNORED_DIRS = ("pagefind/",)


class _LinkExtractor(HTMLParser):
    """Collect href/src attribute values from a page."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.links.append(value)


def _is_internal(link: str) -> bool:
    """True if the link points at a local file (not http, mailto, anchor, data)."""
    parsed = urlparse(link)
    if parsed.scheme or parsed.netloc:        # http://, https://, mailto:, data:
        return False
    if not parsed.path:                       # pure anchor (#section) or empty
        return False
    return True


def _resolve(page: Path, link: str, out: Path) -> Path:
    """Resolve a relative link found in `page` to an absolute path under `out`."""
    path = unquote(urlparse(link).path)
    return (page.parent / path).resolve()


def check_site(project: str, out_dir: Path | None = None) -> dict:
    """Walk every built page and return a report dict.

    Returns ``{pages, links_checked, broken, orphans, referenced, out}`` where
    ``broken`` is a list of ``(page_rel, link)`` and ``orphans`` is a sorted list
    of file paths (relative to ``out``) that no page references.
    """
    proj = load_project(Project(project).root)
    out  = (out_dir if out_dir is not None else proj.site).resolve()

    if not out.exists():
        return {"pages": 0, "links_checked": 0, "broken": [], "orphans": [],
                "referenced": set(), "out": out, "missing_dir": True}

    html_pages = sorted(p for p in out.rglob("*.html"))
    referenced: set[Path] = set()
    broken: list[tuple[str, str]] = []
    links_checked = 0

    for page in html_pages:
        extractor = _LinkExtractor()
        extractor.feed(page.read_text(encoding="utf-8"))
        for link in extractor.links:
            if not _is_internal(link):
                continue
            links_checked += 1
            target = _resolve(page, link, out)
            referenced.add(target)
            if not target.exists():
                broken.append((str(page.relative_to(out)), link))

    # Orphans: emitted files no page references and which aren't entry points.
    orphans: list[str] = []
    for f in sorted(out.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(out)
        rel_str = rel.as_posix()
        if rel.name in _ENTRY_POINTS:
            continue
        if any(rel_str.startswith(prefix) for prefix in _IGNORED_DIRS):
            continue
        if f.resolve() not in referenced:
            orphans.append(rel_str)

    return {
        "pages":         len(html_pages),
        "links_checked": links_checked,
        "broken":        broken,
        "orphans":       orphans,
        "referenced":    referenced,
        "out":           out,
        "missing_dir":   False,
    }


def run_check(project: str, out_dir: Path | None = None, strict: bool = False) -> int:
    """Print the report and return a process exit code (0 ok, 1 on breakage)."""
    report = check_site(project, out_dir)
    out = report["out"]

    if report.get("missing_dir"):
        print(f"No built site at {out}. Run 'markery site build {project}' first.")
        return 1

    print(f"Site check: {project} → {out}/")
    print(f"  pages checked : {report['pages']}")
    print(f"  links checked : {report['links_checked']}")

    broken  = report["broken"]
    orphans = report["orphans"]

    if broken:
        print(f"\n  {len(broken)} broken link(s):")
        for page_rel, link in broken:
            print(f"    {page_rel}  →  {link}")
    else:
        print("  broken links  : 0")

    if orphans:
        print(f"\n  {len(orphans)} orphaned file(s) (no page links here):")
        for o in orphans:
            print(f"    {o}")
    else:
        print("  orphaned files: 0")

    if broken:
        print(f"\nFAIL: {len(broken)} broken link(s).")
        return 1
    if strict and orphans:
        print(f"\nFAIL (--strict): {len(orphans)} orphaned file(s).")
        return 1
    print("\nAll internal links resolve.")
    return 0
