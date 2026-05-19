"""Wikipedia tooling CLI.

Commands:
    markery wikipedia draft  <project> <slug>   — generate wikitext draft
    markery wikipedia submit <project> <slug>   — show diff and POST to Wikipedia
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

from markery.common.config import Project


def _load_match(project: str, slug: str) -> dict:
    """Load confirmed match record for slug from confirmed.jsonl."""
    proj = Project(project)
    if not proj.confirmed.exists():
        raise FileNotFoundError(f"confirmed.jsonl not found at {proj.confirmed}")
    for line in proj.confirmed.read_text().splitlines():
        m = json.loads(line)
        if m.get("slug") == slug:
            return m
    raise KeyError(f"No confirmed match with slug '{slug}' in {project}")


def _draft_path(project: str, slug: str) -> Path:
    proj = Project(project)
    wiki_dir = proj.root / "wikipedia"
    wiki_dir.mkdir(exist_ok=True)
    return wiki_dir / f"{slug}.wiki"


def cmd_draft(project: str, slug: str) -> None:
    """Generate a wikitext draft from the match essay and save it."""
    from markery.specialist.publisher.wikipedia.wikitext import build_draft_wikitext

    match = _load_match(project, slug)
    proj  = Project(project)

    essay_path = Path(match["essay_path"]) if match.get("essay_path") else None
    if not essay_path or not essay_path.exists():
        print(f"No essay found for '{slug}'. Write the match essay first.", file=sys.stderr)
        sys.exit(1)

    # Try to get goods description from confirmed match record or leave blank
    goods_desc = match.get("goods_desc", "")

    wikitext = build_draft_wikitext(
        essay_text=essay_path.read_text(),
        trademark=match["trademark"],
        patent_no=match["patent_no"],
        trademark_serial=str(match["trademark_serial"]),
        entity=match.get("entity", ""),
        filing_dt=str(match.get("filing_dt", "")),
        grant_dt=str(match.get("grant_dt", "")),
        goods_desc=goods_desc,
    )

    out = _draft_path(project, slug)
    out.write_text(wikitext, encoding="utf-8")
    print(f"Draft written → {out}")
    print("Review and edit the draft before submitting.")
    print(f"  markery wikipedia submit {project} {slug}")


def cmd_submit(project: str, slug: str, page_title: str | None, summary: str) -> None:
    """Show diff against current Wikipedia article and prompt before submitting."""
    from markery.specialist.publisher.wikipedia.api import WikipediaClient

    match = _load_match(project, slug)
    title = page_title or match.get("wikipedia_title") or match["trademark"]

    draft_file = _draft_path(project, slug)
    if not draft_file.exists():
        print(f"No draft found at {draft_file}. Run 'markery wikipedia draft' first.", file=sys.stderr)
        sys.exit(1)

    new_text = draft_file.read_text(encoding="utf-8")

    client = WikipediaClient()
    current = client.get_page(title)

    if current is None:
        print(f"Page '{title}' does not exist on Wikipedia. Creating a new article.")
        diff_lines = list(difflib.unified_diff(
            [], new_text.splitlines(keepends=True),
            fromfile="(new page)", tofile=title, lineterm="",
        ))
    else:
        diff_lines = list(difflib.unified_diff(
            current.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"{title} (current)",
            tofile=f"{title} (draft)",
            lineterm="",
        ))

    if not diff_lines:
        print("No changes detected between draft and current Wikipedia page.")
        return

    print("\n".join(diff_lines[:80]))
    if len(diff_lines) > 80:
        print(f"  … {len(diff_lines) - 80} more lines …")

    print(f"\nPage:    https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")
    print(f"Summary: {summary}")
    answer = input("\nSubmit to Wikipedia? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    result = client.edit_page(title, new_text, summary)
    if result.get("edit", {}).get("result") == "Success":
        print(f"Submitted. New revision: {result['edit'].get('newrevid')}")
    else:
        print(f"Unexpected response: {result}", file=sys.stderr)
        sys.exit(1)


def wikipedia_main() -> None:
    parser = argparse.ArgumentParser(
        prog="markery wikipedia",
        description="Wikipedia tooling for Markery research projects",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    draft = sub.add_parser("draft", help="Generate wikitext draft from match essay")
    draft.add_argument("project", help="Project name")
    draft.add_argument("slug",    help="Match essay slug")

    submit = sub.add_parser("submit", help="Show diff and POST to Wikipedia")
    submit.add_argument("project", help="Project name")
    submit.add_argument("slug",    help="Match essay slug")
    submit.add_argument("--title", metavar="TITLE",
                        help="Wikipedia article title (default: trademark name)")
    submit.add_argument("--summary", metavar="MSG",
                        default="Add primary source citations from USPTO filing record",
                        help="Edit summary")

    args = parser.parse_args()

    if args.action == "draft":
        cmd_draft(args.project, args.slug)
    elif args.action == "submit":
        cmd_submit(args.project, args.slug, args.title, args.summary)
