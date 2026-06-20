"""Wikipedia tooling CLI.

Commands:
    markery wikipedia draft  <project> <slug>   — generate wikitext draft
    markery wikipedia submit <project> <slug>   — show diff and POST to Wikipedia
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

from markery.common.config import ROOT
from markery.common.project import Project


def _record_submission(
    project_name: str,
    revision_id: int | None,
    article: str,
    description: str,
    submitted_at: str,
    serial_no: str | None = None,
    status: str = "live",
) -> None:
    """Append one submission record to projects/<project>/wikipedia/submissions.jsonl."""
    wiki_dir = ROOT / "projects" / project_name / "wikipedia"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "revision_id": revision_id,
        "article": article,
        "description": description,
        "serial_no": serial_no,
        "submitted_at": submitted_at,
        "status": status,
        "diff_url": (
            f"https://en.wikipedia.org/w/index.php?diff={revision_id}"
            if revision_id else None
        ),
    }
    path = wiki_dir / "submissions.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    print(f"  Recorded → {path}")


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


def _candidate_slug(record: dict) -> str:
    """Derive the canonical slug for a confirmed-pair record (matches historian)."""
    tm = record.get("trademark") or "figurative"
    tm_slug = re.sub(r"[^a-z0-9]+", "-", tm.lower()).strip("-")
    return f"{tm_slug}-{record['patent_no'].lower()}"


def cmd_candidates(project: str) -> None:
    """List a project's confirmed pairs as Wikipedia-edit candidates.

    Deterministic (no API). Replaces reading confirmed.jsonl by hand: shows the
    derived slug, normal-cased mark, patent, whether a finalized essay exists, and
    whether the mark's serial has already been submitted to Wikipedia.
    """
    proj = Project(project)
    if not proj.confirmed.exists():
        print(f"No confirmed.jsonl for {project}.", file=sys.stderr)
        sys.exit(1)

    submitted: set[str] = set()
    sub_path = proj.root / "wikipedia" / "submissions.jsonl"
    if sub_path.exists():
        for line in sub_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("serial_no"):
                    submitted.add(str(r["serial_no"]))

    rows: list[dict] = []
    for line in proj.confirmed.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        slug = _candidate_slug(m)
        essay = proj.content / f"{slug}.md"
        serial = str(m.get("trademark_serial", ""))
        rows.append({
            "slug": slug,
            "mark": m.get("trademark") or "(figurative)",
            "patent": m.get("patent_no", ""),
            "entity": m.get("entity", ""),
            "essay": "yes" if essay.exists() else "NO",
            "wp": "✓" if serial in submitted else "",
        })

    if not rows:
        print(f"No confirmed pairs in {project}.")
        return

    print(f"Confirmed pairs in {project}  ({len(rows)} total; ✓ = already on Wikipedia)\n")
    print(f"  {'slug':<34}{'mark':<26}{'patent':<11}{'essay':<6}{'wp':<4}entity")
    for r in rows:
        print(f"  {r['slug']:<34}{r['mark'][:24]:<26}{r['patent']:<11}{r['essay']:<6}{r['wp']:<4}{r['entity']}")


_PROPOSE_SYSTEM = """You draft a single neutral, encyclopedic Wikipedia sentence that adds a primary-source trademark citation to an existing article, based on a Markery research essay.

Output format:
- Output WIKITEXT only for the sentence(s) to insert, then a final line beginning "SUMMARY: " with a short edit summary. No preamble, no markdown fences, no commentary.

Hard rules:
- Render the trademark name in NORMAL CASE (e.g. "John Deere Moline, Ill."), NEVER in all capitals. Wikipedia's MOS:TM forbids all-caps and its abuse filter rejects "shouting".
- State ONLY what the essay's facts and "Primary Sources" support: the mark, its USPTO serial number, filing date, registration date, owner, and goods. Use the EXACT serial number and dates from the essay frontmatter.
- Cite the trademark with exactly this template, substituting the serial, a normal-case MARK, and the given ACCESS-DATE:
  <ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=SERIAL&caseType=SERIAL_NO&searchType=statusSearch|title=Trademark Serial No. SERIAL — MARK|publisher=USPTO Trademark Status and Document Retrieval|access-date=ACCESS-DATE}}</ref>
- Do NOT assert that any patent is embodied in, underlies, or is the technology behind the trademarked product UNLESS the essay's "The Connection" explicitly establishes documented goods-correspondence. Owner-and-era pairings get a trademark-only sentence with no patent claim.
- One sentence (two only if necessary). Neutral tone; no marketing language.
"""


def cmd_propose_edit(project: str, slug: str, article: str, model_override: str | None) -> None:
    """Draft a citation sentence for an existing article via the project's model.

    Reads the human-gated match essay (the honest source of record), has the
    configured model (the free model when project.json sets it) distill a neutral,
    sourced Wikipedia sentence, and saves it for human review + anchor selection.
    The human still picks the insertion point and runs `wikipedia replace`.
    """
    import time
    from datetime import date

    from markery.common.llm import call as llm_call
    from markery.common.project import load_project
    from markery.common.tokens import TokenRecord, emit as emit_tokens

    proj = Project(project)
    essay_path = proj.content / f"{slug}.md"
    if not essay_path.exists():
        print(f"No essay at {essay_path}.\n"
              f"Run `markery wikipedia candidates {project}` to list slugs with essays.",
              file=sys.stderr)
        sys.exit(1)

    model = model_override or load_project(proj.root).model
    if not model:
        print("No model set: project.json has no 'model' and no --model was given.",
              file=sys.stderr)
        sys.exit(1)

    essay_text = essay_path.read_text(encoding="utf-8")
    access = date.today().isoformat()
    user = (f"TARGET ARTICLE: {article}\nACCESS-DATE: {access}\n\n"
            f"--- MARKERY ESSAY ---\n{essay_text}")

    print(f"Drafting Wikipedia citation for '{slug}' → article '{article}' with {model}…",
          flush=True)
    t0 = time.monotonic()
    try:
        text, ptok, ctok, cache_read, cache_create = llm_call(
            model, _PROPOSE_SYSTEM, user, 600)
    except RuntimeError as exc:
        print(f"Inference error: {exc}", file=sys.stderr)
        sys.exit(1)

    rec = TokenRecord(
        model=model, prompt_tokens=ptok, completion_tokens=ctok,
        cache_read_tokens=cache_read, cache_creation_tokens=cache_create,
        wall_ms=int((time.monotonic() - t0) * 1000),
    )
    emit_tokens(rec, specialist="publisher", command="wikipedia-propose", tokens_flag=True)

    out = proj.root / "wikipedia" / f"{slug}-propose.wiki"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text.strip() + "\n", encoding="utf-8")

    print(f"\nProposed insertion → {out}\n")
    print(text.strip())
    print("\n— Review for honesty (esp. no unsupported patent-embodiment claim), then")
    print("  choose a unique existing sentence in the article as the anchor and run:")
    print(f"    markery wikipedia replace \"{article}\" --project {project} \\")
    print("      --find '<exact existing sentence>' \\")
    print("      --replace '<that sentence> <proposed wikitext>' --summary '<summary>'")


def cmd_check_revision(project: str) -> None:
    """Check MediaWiki API status for every revision_id in submissions.jsonl.

    Prints a per-entry table and updates the `status` field in-place for any
    entry that has changed (live → reverted). Exits 1 if any revision is reverted.
    """
    from markery.specialist.publisher.wikipedia.api import WikipediaClient

    submissions_path = ROOT / "projects" / project / "wikipedia" / "submissions.jsonl"
    if not submissions_path.exists():
        print(f"No submissions.jsonl found at {submissions_path}.", file=sys.stderr)
        sys.exit(1)

    rows: list[dict] = []
    with submissions_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    checkable = [r for r in rows if r.get("revision_id")]
    if not checkable:
        print("No revision IDs to check (all entries have null revision_id).")
        return

    client = WikipediaClient()
    any_reverted = False
    updated = False

    col_w = 42
    print(f"\n{'revision_id':<14}  {'article':<{col_w}}  {'submitted_at':<12}  status")
    print("-" * (14 + 2 + col_w + 2 + 12 + 2 + 12))

    for row in rows:
        revid = row.get("revision_id")
        if not revid:
            print(f"{'(none)':<14}  {row.get('article',''):<{col_w}}  "
                  f"{row.get('submitted_at',''):<12}  skipped (no revision_id)")
            continue

        api_status = client.get_revision_status(revid)
        if not api_status["exists"]:
            label = "unknown"
        elif api_status["reverted"]:
            label = "REVERTED"
            any_reverted = True
        else:
            label = "live"

        print(f"{revid:<14}  {row.get('article',''):<{col_w}}  "
              f"{row.get('submitted_at',''):<12}  {label}")

        # Update status field when it has changed
        prev = row.get("status", "live")
        if api_status["exists"] and api_status["reverted"] and prev != "reverted":
            row["status"] = "reverted"
            updated = True

    if updated:
        with submissions_path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        print(f"\nUpdated {submissions_path.name} with new status.")

    print()
    if any_reverted:
        print("FAIL — one or more revisions have been reverted.")
        sys.exit(1)
    else:
        print("All checked revisions are live.")


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


def cmd_verify_credentials() -> None:
    """Authenticate with Wikipedia and report success or failure."""
    from markery.specialist.publisher.wikipedia.api import WikipediaClient
    client = WikipediaClient()
    try:
        client.login()
        print(f"Authenticated as: {client._username}")
    except RuntimeError as e:
        print(f"Authentication failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_add_external_link(
    page_title: str,
    url: str,
    label: str,
    summary: str,
    yes: bool = False,
    project: str | None = None,
) -> None:
    """Append one external link to a page's External links section."""
    from markery.specialist.publisher.wikipedia.api import WikipediaClient

    client = WikipediaClient()
    current = client.get_page(page_title)
    if current is None:
        print(f"Page '{page_title}' not found on Wikipedia.", file=sys.stderr)
        sys.exit(1)

    if url in current:
        print(f"URL already present in '{page_title}'. No edit needed.")
        return

    lines = current.splitlines(keepends=True)
    ext_links_idx = next(
        (i for i, ln in enumerate(lines) if ln.strip() == "== External links =="),
        None,
    )
    if ext_links_idx is None:
        print(
            f"No '== External links ==' section found in '{page_title}'.\n"
            "Add the section manually before using this command.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Insert just before the next top-level section, navbox template, category block, or EOF
    insert_idx = len(lines)
    for i in range(ext_links_idx + 1, len(lines)):
        ln = lines[i]
        if (
            (ln.startswith("==") and not ln.startswith("==="))
            or ln.startswith("[[Category:")
            or ln.startswith("{{")
        ):
            insert_idx = i
            break

    new_line_text = f"* [{url} {label}]\n"
    # Ensure the preceding line ends with a newline so the link starts on its own line
    if insert_idx > 0 and lines[insert_idx - 1].rstrip("\n") and not lines[insert_idx - 1].endswith("\n"):
        new_lines = lines[:insert_idx] + ["\n", new_line_text] + lines[insert_idx:]
    else:
        new_lines = lines[:insert_idx] + [new_line_text] + lines[insert_idx:]
    new_text = "".join(new_lines)

    diff_lines = list(difflib.unified_diff(
        current.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile=f"{page_title} (current)",
        tofile=f"{page_title} (proposed)",
        lineterm="",
    ))
    print("".join(diff_lines))
    print(f"\nPage:    https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}")
    print(f"Summary: {summary}")
    if not yes:
        answer = input("\nSubmit to Wikipedia? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return

    result = client.edit_page(page_title, new_text, summary)
    if result.get("edit", {}).get("result") == "Success":
        revid = result["edit"].get("newrevid")
        print(f"Submitted. Revision: {revid}")
        print(f"View: https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}")
        if project:
            from datetime import datetime, timezone
            _record_submission(
                project_name=project,
                revision_id=revid,
                article=page_title,
                description=summary,
                submitted_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )
    else:
        print(f"Unexpected API response: {result}", file=sys.stderr)
        sys.exit(1)


def cmd_from_essay(
    essay_path: Path,
    out_path: Path,
    title: str,
    serial: str,
    categories: list[str],
) -> None:
    """Generate wikitext from any essay file without a confirmed match record."""
    from markery.specialist.publisher.wikipedia.wikitext import build_standalone_wikitext

    if not essay_path.exists():
        print(f"Essay not found: {essay_path}", file=sys.stderr)
        sys.exit(1)

    wikitext = build_standalone_wikitext(
        essay_text=essay_path.read_text(encoding="utf-8"),
        title=title,
        serial=serial,
        categories=categories,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(wikitext, encoding="utf-8")
    print(f"Draft written → {out_path}")
    print("Review and edit the draft before submitting.")


def cmd_replace(
    page_title: str,
    find: str,
    replace: str,
    summary: str,
    yes: bool = False,
    project: str | None = None,
) -> None:
    """Targeted find-and-replace on a Wikipedia article, with diff and confirmation."""
    from markery.specialist.publisher.wikipedia.api import WikipediaClient

    client = WikipediaClient()
    current = client.get_page(page_title)
    if current is None:
        print(f"Page '{page_title}' not found on Wikipedia.", file=sys.stderr)
        sys.exit(1)

    if find not in current:
        print(f"Target text not found in '{page_title}'.", file=sys.stderr)
        print(f"Looking for: {find!r}", file=sys.stderr)
        sys.exit(1)

    count = current.count(find)
    if count > 1:
        print(
            f"Target text appears {count} times — cannot safely replace. "
            "Expand the search string to make it unique.",
            file=sys.stderr,
        )
        sys.exit(1)

    new_text = current.replace(find, replace, 1)

    diff_lines = list(difflib.unified_diff(
        current.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile=f"{page_title} (current)",
        tofile=f"{page_title} (proposed)",
        lineterm="",
    ))
    print("".join(diff_lines))
    print(f"\nPage:    https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}")
    print(f"Summary: {summary}")
    if not yes:
        answer = input("\nSubmit to Wikipedia? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return

    result = client.edit_page(page_title, new_text, summary)
    if result.get("edit", {}).get("result") == "Success":
        revid = result["edit"].get("newrevid")
        print(f"Submitted. Revision: {revid}")
        print(f"View: https://en.wikipedia.org/w/index.php?diff={revid}")
        if project:
            from datetime import datetime, timezone
            _record_submission(
                project_name=project,
                revision_id=revid,
                article=page_title,
                description=summary,
                submitted_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )
    else:
        print(f"Unexpected API response: {result}", file=sys.stderr)
        sys.exit(1)


def cmd_submit(project: str, slug: str, page_title: str | None, summary: str, yes: bool = False) -> None:
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
    if not yes:
        answer = input("\nSubmit to Wikipedia? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return

    result = client.edit_page(title, new_text, summary)
    if result.get("edit", {}).get("result") == "Success":
        revid = result["edit"].get("newrevid")
        print(f"Submitted. New revision: {revid}")
        from datetime import datetime, timezone
        _record_submission(
            project_name=project,
            revision_id=revid,
            article=title,
            description=summary,
            submitted_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
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

    cand = sub.add_parser("candidates",
                          help="List confirmed pairs as Wikipedia-edit candidates (no API)")
    cand.add_argument("project", help="Project name")

    pe = sub.add_parser("propose-edit",
                        help="Free-model draft of a citation sentence for an existing article")
    pe.add_argument("project", help="Project name")
    pe.add_argument("slug",    help="Confirmed pair slug (see `wikipedia candidates`)")
    pe.add_argument("--article", required=True, metavar="TITLE",
                    help="Target Wikipedia article title")
    pe.add_argument("--model", default=None, metavar="MODEL",
                    help="Override the project.json model for this draft")

    submit = sub.add_parser("submit", help="Show diff and POST to Wikipedia")
    submit.add_argument("project", help="Project name")
    submit.add_argument("slug",    help="Match essay slug")
    submit.add_argument("--title", metavar="TITLE",
                        help="Wikipedia article title (default: trademark name)")
    submit.add_argument("--summary", metavar="MSG",
                        default="Add primary source citations from USPTO filing record",
                        help="Edit summary")
    submit.add_argument("--yes", "-y", action="store_true",
                        help="Submit without interactive confirmation")

    fe = sub.add_parser("from-essay", help="Generate wikitext from any essay file")
    fe.add_argument("essay_path", type=Path, help="Path to markdown essay file")
    fe.add_argument("--out", required=True, metavar="PATH", type=Path,
                    help="Output wikitext file path")
    fe.add_argument("--title", default="", metavar="TITLE",
                    help="Article title (informational)")
    fe.add_argument("--serial", default="", metavar="SERIAL",
                    help="USPTO trademark serial number — adds TSDR sources section")
    fe.add_argument("--category", dest="categories", action="append", default=[],
                    metavar="CAT", help="Wikipedia category tag (repeatable)")

    sub.add_parser("verify-credentials", help="Test Wikipedia authentication")

    cr = sub.add_parser("check-revision",
                        help="Check MediaWiki API status for all project submissions")
    cr.add_argument("project", help="Project name")

    ael = sub.add_parser("add-external-link",
                         help="Append one link to the External links section")
    ael.add_argument("page_title", help="Wikipedia article title")
    ael.add_argument("url",        help="URL to add")
    ael.add_argument("label",      help="Link label text")
    ael.add_argument("--summary", metavar="MSG",
                     default="Add external link",
                     help="Edit summary")
    ael.add_argument("--yes", "-y", action="store_true",
                     help="Submit without interactive confirmation")
    ael.add_argument("--project", metavar="NAME", default=None,
                     help="Project name — records submission in wikipedia/submissions.jsonl")

    rep = sub.add_parser("replace",
                         help="Targeted find-and-replace with diff and confirmation")
    rep.add_argument("page_title", help="Wikipedia article title")
    rep.add_argument("--find",    required=True, metavar="TEXT",
                     help="Exact wikitext string to find (must be unique in article)")
    rep.add_argument("--replace", required=True, dest="replace_text", metavar="TEXT",
                     help="Replacement wikitext string")
    rep.add_argument("--summary", required=True, metavar="MSG", help="Edit summary")
    rep.add_argument("--yes", "-y", action="store_true",
                     help="Submit without interactive confirmation")
    rep.add_argument("--project", metavar="NAME", default=None,
                     help="Project name — records submission in wikipedia/submissions.jsonl")

    args = parser.parse_args()

    if args.action == "draft":
        cmd_draft(args.project, args.slug)
    elif args.action == "candidates":
        cmd_candidates(args.project)
    elif args.action == "propose-edit":
        cmd_propose_edit(args.project, args.slug, args.article, args.model)
    elif args.action == "submit":
        cmd_submit(args.project, args.slug, args.title, args.summary, args.yes)
    elif args.action == "from-essay":
        cmd_from_essay(args.essay_path, args.out, args.title, args.serial, args.categories)
    elif args.action == "verify-credentials":
        cmd_verify_credentials()
    elif args.action == "add-external-link":
        cmd_add_external_link(
            args.page_title, args.url, args.label, args.summary, args.yes,
            project=args.project,
        )
    elif args.action == "replace":
        cmd_replace(
            args.page_title, args.find, args.replace_text, args.summary, args.yes,
            project=args.project,
        )
    elif args.action == "check-revision":
        cmd_check_revision(args.project)
