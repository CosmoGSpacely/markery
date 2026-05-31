"""CLI for the LIBRARIAN specialist.

Registered as: markery librarian <subcommand>

P2 subcommands (source adapters and acquisition):
  search-sources  Search IA and/or Gutenberg without downloading
  discover        Resolve Wikipedia article citations to acquirable sources
  wants           List the ILL/wants queue
  wants-update    Update a wants-entry status
  acquire         Fetch metadata + full text; register in library/works/
  enter           Manually register a work (ILL arrival, physical copy)
  raw-text        Print path to raw_text.txt for a slug

Later phases add: extract, review, index, search, list, card
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from markery.common.config import ROOT

_LIBRARY = ROOT / "library"
_WANTS = _LIBRARY / "wants.jsonl"


# ---------------------------------------------------------------------------
# library/ path helpers
# ---------------------------------------------------------------------------

def _works_dir(slug: str) -> Path:
    return _LIBRARY / "works" / slug


def _ensure_library() -> None:
    _LIBRARY.mkdir(parents=True, exist_ok=True)
    (_LIBRARY / "works").mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# wants.jsonl helpers
# ---------------------------------------------------------------------------

def _read_wants() -> list[dict]:
    if not _WANTS.exists():
        return []
    return [json.loads(ln) for ln in _WANTS.read_text().splitlines() if ln.strip()]


def _write_wants(entries: list[dict]) -> None:
    _ensure_library()
    _WANTS.write_text("\n".join(json.dumps(e) for e in entries) + ("\n" if entries else ""))


def _find_wants_entry(entries: list[dict], slug: str) -> int:
    """Return index of the entry whose title slug matches, or -1."""
    from markery.specialist.librarian.sources.common import make_slug
    for i, e in enumerate(entries):
        e_slug = make_slug(e.get("title", ""), e.get("author", ""))
        if e_slug == slug or e.get("slug") == slug:
            return i
    return -1


# ---------------------------------------------------------------------------
# search-sources
# ---------------------------------------------------------------------------

def cmd_search_sources(args: argparse.Namespace) -> None:
    from markery.specialist.librarian.sources import ia as _ia
    from markery.specialist.librarian.sources import gutenberg as _gut
    from markery.specialist.librarian.sources.common import make_slug

    sources = args.source or "all"
    results = []

    if sources in ("ia", "all"):
        try:
            for r in _ia.search(args.query, max_results=args.top):
                results.append(("IA", r.identifier, r.title, r.author,
                                 r.year, r.access))
        except Exception as exc:
            print(f"[IA search error: {exc}]", file=sys.stderr)

    if sources in ("gutenberg", "all"):
        try:
            for r in _gut.search(args.query, max_results=args.top):
                results.append(("GUT", r.book_id, r.title, r.author,
                                 r.year, None))
        except Exception as exc:
            print(f"[Gutenberg search error: {exc}]", file=sys.stderr)

    if not results:
        print("No results.")
        return

    # Header
    print(f"{'SRC':<5} {'IDENTIFIER':<35} {'YEAR':<6} {'ACCESS':<7} TITLE / AUTHOR")
    print("-" * 90)
    for src, ident, title, author, year, access in results[:args.top]:
        yr = str(year) if year else "?"
        acc = access or "-"
        slug = make_slug(title, author)
        print(f"{src:<5} {ident:<35} {yr:<6} {acc:<7} {title}")
        if author:
            print(f"{'':5} {'slug: ' + slug:<35}")


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------

def cmd_discover(args: argparse.Namespace) -> None:
    from markery.specialist.librarian.sources import wikipedia as _wp
    from markery.specialist.librarian.sources.common import make_slug, WantsEntry

    try:
        citations = _wp.fetch_citations(args.wikipedia)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not citations:
        print(f"No cite book / cite journal templates found in '{args.wikipedia}'.")
        return

    wants_to_add: list[dict] = []

    print(f"{'STATUS':<14} {'SLUG':<35} TITLE, AUTHOR YEAR")
    print("-" * 90)

    for cit in citations:
        result = _wp.resolve_to_source(cit)
        label = f"{cit.title}, {cit.author} {cit.year or '?'}"
        if result:
            tag = f"FOUND ({result.source.upper()})"
            access_note = f" [{result.access}]" if result.access else ""
            print(f"{tag:<14} {result.slug:<35} {label}{access_note}")
        else:
            print(f"{'NOT FOUND':<14} {'—':<35} {label}")
            if args.add_wants:
                wants_to_add.append({
                    "title": cit.title,
                    "author": cit.author,
                    "year": cit.year,
                    "isbn": cit.isbn,
                    "source_article": args.wikipedia,
                    "added_at": datetime.now(timezone.utc).isoformat(),
                    "status": "wanted",
                })

    if wants_to_add:
        existing = _read_wants()
        existing_titles = {e["title"].lower() for e in existing}
        added = 0
        for entry in wants_to_add:
            if entry["title"].lower() not in existing_titles:
                existing.append(entry)
                added += 1
        _write_wants(existing)
        print(f"\nAdded {added} item(s) to library/wants.jsonl.")


# ---------------------------------------------------------------------------
# wants
# ---------------------------------------------------------------------------

def cmd_wants(args: argparse.Namespace) -> None:
    entries = _read_wants()
    status_filter = args.status  # None = show wanted + in-progress; else exact match

    shown = 0
    for e in entries:
        s = e.get("status", "wanted")
        if status_filter:
            if s != status_filter:
                continue
        else:
            if s == "acquired":
                continue
        shown += 1
        yr = e.get("year") or "?"
        author = e.get("author") or "?"
        article = e.get("source_article") or "—"
        note = e.get("note") or ""
        print(f"[{s}]  {e.get('title', '?')} — {author} {yr}")
        print(f"         source article: {article}")
        if note:
            print(f"         note: {note}")

    if shown == 0:
        filter_desc = f"status={status_filter}" if status_filter else "wanted/in-progress"
        print(f"No wants entries ({filter_desc}).")


# ---------------------------------------------------------------------------
# wants-update
# ---------------------------------------------------------------------------

def cmd_wants_update(args: argparse.Namespace) -> None:
    entries = _read_wants()
    idx = _find_wants_entry(entries, args.slug)
    if idx == -1:
        # Try exact title match as fallback
        for i, e in enumerate(entries):
            if args.slug.lower() in e.get("title", "").lower():
                idx = i
                break
    if idx == -1:
        print(f"No wants entry matching '{args.slug}'.", file=sys.stderr)
        sys.exit(1)

    entries[idx]["status"] = args.status
    if args.note:
        entries[idx]["note"] = args.note
    _write_wants(entries)
    title = entries[idx].get("title", args.slug)
    print(f"Updated '{title}' → status={args.status}")


# ---------------------------------------------------------------------------
# acquire
# ---------------------------------------------------------------------------

def cmd_acquire(args: argparse.Namespace) -> None:
    from markery.specialist.librarian.sources import ia as _ia
    from markery.specialist.librarian.sources import gutenberg as _gut
    from markery.specialist.librarian.sources.common import normalize_metadata, make_slug

    identifier = args.identifier
    source = args.source  # "ia", "gutenberg", or None (auto-detect)

    # Auto-detect source
    if not source:
        source = "gutenberg" if identifier.isdigit() else "ia"

    _ensure_library()

    if source == "ia":
        meta = _ia.fetch_metadata(identifier)
        if not meta.get("metadata", {}).get("title"):
            print(f"IA identifier '{identifier}' not found.", file=sys.stderr)
            sys.exit(1)
        ia_meta = meta["metadata"]
        author = ia_meta.get("creator", "") or ""
        if isinstance(author, list):
            author = author[0] if author else ""
        slug = make_slug(ia_meta.get("title", identifier), author)
        norm = normalize_metadata(meta, "ia", slug)

        work_dir = _works_dir(slug)
        if (work_dir / "metadata.json").exists():
            print(f"Already acquired: {slug}")
            print(f"  {work_dir}")
            sys.exit(0)

        work_dir.mkdir(parents=True, exist_ok=True)
        norm["acquired_at"] = datetime.now(timezone.utc).isoformat()
        (work_dir / "metadata.json").write_text(json.dumps(norm, indent=2) + "\n")

        try:
            txt_path = _ia.download_text(identifier, work_dir)
            print(f"Acquired (IA): {slug}")
            print(f"  metadata: {work_dir / 'metadata.json'}")
            print(f"  raw text: {txt_path}")
        except (PermissionError, FileNotFoundError) as exc:
            print(f"Warning: {exc}", file=sys.stderr)
            print(f"Registered metadata only (no raw text): {slug}")

    elif source == "gutenberg":
        book = _gut.fetch_metadata(identifier)
        if not book.get("title"):
            print(f"Gutenberg book {identifier!r} not found.", file=sys.stderr)
            sys.exit(1)
        authors = book.get("authors", [])
        author = authors[0].get("name", "") if authors else ""
        slug = make_slug(book.get("title", identifier), author)
        norm = normalize_metadata(book, "gutenberg", slug)

        work_dir = _works_dir(slug)
        if (work_dir / "metadata.json").exists():
            print(f"Already acquired: {slug}")
            print(f"  {work_dir}")
            sys.exit(0)

        work_dir.mkdir(parents=True, exist_ok=True)
        norm["acquired_at"] = datetime.now(timezone.utc).isoformat()
        (work_dir / "metadata.json").write_text(json.dumps(norm, indent=2) + "\n")

        try:
            txt_path = _gut.download_text(identifier, work_dir)
            print(f"Acquired (Gutenberg): {slug}")
            print(f"  metadata: {work_dir / 'metadata.json'}")
            print(f"  raw text: {txt_path}")
        except FileNotFoundError as exc:
            print(f"Warning: {exc}", file=sys.stderr)
            print(f"Registered metadata only (no raw text): {slug}")
    else:
        print(f"Unknown source: {source!r}", file=sys.stderr)
        sys.exit(1)

    # Update wants.jsonl if entry exists
    entries = _read_wants()
    idx = _find_wants_entry(entries, slug)
    if idx != -1 and entries[idx].get("status") != "acquired":
        entries[idx]["status"] = "acquired"
        _write_wants(entries)
        print(f"  wants.jsonl updated → acquired")


# ---------------------------------------------------------------------------
# enter (manual ILL/physical acquisition)
# ---------------------------------------------------------------------------

def cmd_enter(args: argparse.Namespace) -> None:
    _ensure_library()
    slug = args.slug
    work_dir = _works_dir(slug)

    if (work_dir / "metadata.json").exists():
        print(f"Already registered: {slug}", file=sys.stderr)
        sys.exit(1)

    work_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "source": "manual",
        "slug": slug,
        "title": args.title,
        "author": args.author,
        "year": args.year,
        "isbn": args.isbn or None,
        "ia_identifier": None,
        "ia_access": None,
        "gutenberg_id": None,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
    }
    (work_dir / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    # Empty excerpts.md for hand-entry
    (work_dir / "excerpts.md").write_text(
        f"# Excerpts — {args.title}\n\n"
        f"*Source: manual (ILL/physical copy)*\n\n"
        f"## Relevant passages\n\n"
        f"<!-- Add verbatim passages with page numbers here -->\n"
    )
    print(f"Registered: {slug}")
    print(f"  {work_dir / 'metadata.json'}")
    print(f"  {work_dir / 'excerpts.md'}  ← add passages by hand")

    # Update wants.jsonl
    entries = _read_wants()
    idx = _find_wants_entry(entries, slug)
    if idx == -1:
        # Try matching by title
        for i, e in enumerate(entries):
            if args.title.lower() in e.get("title", "").lower():
                idx = i
                break
    if idx != -1 and entries[idx].get("status") != "acquired":
        entries[idx]["status"] = "acquired"
        _write_wants(entries)
        print(f"  wants.jsonl updated → acquired")


# ---------------------------------------------------------------------------
# raw-text
# ---------------------------------------------------------------------------

def cmd_raw_text(args: argparse.Namespace) -> None:
    work_dir = _works_dir(args.slug)
    if not work_dir.exists():
        print(f"No library entry for slug '{args.slug}'.", file=sys.stderr)
        sys.exit(1)
    raw = work_dir / "raw_text.txt"
    if not raw.exists():
        print(f"No raw_text.txt in {work_dir}.\n"
              f"Run: markery librarian acquire <identifier> --source ia", file=sys.stderr)
        sys.exit(1)
    print(raw)


# ---------------------------------------------------------------------------
# extract / review
# ---------------------------------------------------------------------------

def cmd_extract(args: argparse.Namespace) -> None:
    from markery.specialist.librarian.extract import extract
    extract(
        slug=args.slug,
        topics=args.topics,
        max_passages=args.max_passages,
        auto_accept=args.auto_accept,
        tokens_flag=args.tokens,
    )


def cmd_review(args: argparse.Namespace) -> None:
    from markery.specialist.librarian.extract import review
    review(slug=args.slug)


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def librarian_main() -> None:
    parser = argparse.ArgumentParser(
        prog="markery librarian",
        description="LIBRARIAN specialist: acquire, index, and search secondary literature.",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    # search-sources
    p_ss = sub.add_parser("search-sources", help="Search IA and/or Gutenberg (no download)")
    p_ss.add_argument("query", help="Search query")
    p_ss.add_argument("--source", choices=["ia", "gutenberg", "all"], default="all")
    p_ss.add_argument("--top", type=int, default=10, metavar="N")

    # discover
    p_disc = sub.add_parser("discover",
                             help="Resolve Wikipedia article citations to acquirable sources")
    p_disc.add_argument("--wikipedia", required=True, metavar="ARTICLE_TITLE",
                        help="Wikipedia article title (e.g. 'Remington Rand')")
    p_disc.add_argument("--add-wants", action="store_true",
                        help="Append NOT FOUND entries to library/wants.jsonl")

    # wants
    p_wants = sub.add_parser("wants", help="List the ILL/wants queue")
    p_wants.add_argument("--status", choices=["wanted", "in-progress", "acquired"],
                         default=None,
                         help="Filter by status (default: wanted + in-progress)")

    # wants-update
    p_wu = sub.add_parser("wants-update", help="Update a wants entry status")
    p_wu.add_argument("slug", help="Title slug or partial title to match")
    p_wu.add_argument("--status", required=True,
                      choices=["wanted", "in-progress", "acquired"])
    p_wu.add_argument("--note", metavar="TEXT", default=None)

    # acquire
    p_acq = sub.add_parser("acquire",
                            help="Fetch metadata + full text; register in library/works/")
    p_acq.add_argument("identifier",
                       help="IA identifier or Gutenberg book ID")
    p_acq.add_argument("--source", choices=["ia", "gutenberg"], default=None,
                       help="Source (auto-detected from identifier if omitted)")

    # enter
    p_enter = sub.add_parser("enter",
                              help="Manually register a work (ILL arrival, physical copy)")
    p_enter.add_argument("slug", help="Slug for library/works/<slug>/")
    p_enter.add_argument("--title", required=True)
    p_enter.add_argument("--author", required=True)
    p_enter.add_argument("--year", type=int, default=None)
    p_enter.add_argument("--isbn", default=None)

    # raw-text
    p_rt = sub.add_parser("raw-text", help="Print path to raw_text.txt for a slug")
    p_rt.add_argument("slug")

    # extract
    p_ext = sub.add_parser(
        "extract",
        help="Extract passages from raw_text.txt using Claude (writes candidates.md)",
    )
    p_ext.add_argument("slug", help="Library slug (library/works/<slug>)")
    p_ext.add_argument("--topics", nargs="+", required=True, metavar="TOPIC",
                       help="Research topics to guide extraction")
    p_ext.add_argument("--max-passages", type=int, default=10, metavar="N",
                       help="Maximum candidates to retain after deduplication (default 10)")
    p_ext.add_argument("--auto-accept", action="store_true",
                       help="Skip review; append directly to excerpts.md")
    p_ext.add_argument("--tokens", action="store_true",
                       help="Print token usage to stderr after extraction")

    # review
    p_rev = sub.add_parser(
        "review",
        help="Interactively accept/reject candidates from candidates.md",
    )
    p_rev.add_argument("slug", help="Library slug")

    args = parser.parse_args()

    dispatch = {
        "search-sources": cmd_search_sources,
        "discover":       cmd_discover,
        "wants":          cmd_wants,
        "wants-update":   cmd_wants_update,
        "acquire":        cmd_acquire,
        "enter":          cmd_enter,
        "raw-text":       cmd_raw_text,
        "extract":        cmd_extract,
        "review":         cmd_review,
    }
    dispatch[args.action](args)
