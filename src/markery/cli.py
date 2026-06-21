"""
markery — unified CLI for the Markery research tool.

Usage:
  markery match <project>
  markery match --list-entities
  markery review <project> --min-score 0.65
  markery status
  markery enhance enhance <serial_no> --out-dir projects/<project>/output/<slug>
  markery enhance batch "<sql_where>" --out-dir projects/<project>/output/batch
  markery enhance gallery projects/<project>/output/<slug> --title "<title>"
  markery patent build --classes B42F --year-start 1900 --year-end 1939
  markery patent build --resume
  markery patent fetch <project> --confirmed
  markery patent figures <patent_no>
  markery patent verify-credentials
  markery patent signals <project>
  markery site build <project>
  markery publisher build <project>
"""

from __future__ import annotations

import sys


def _try_inject_project_model(rest: list[str]) -> None:
    """Set MARKERY_MODEL from project.json if the project specifies one and env doesn't."""
    import json
    import os
    from pathlib import Path

    if "MARKERY_MODEL" in os.environ:
        return
    from markery.common.config import ROOT
    projects_dir = ROOT / "projects"
    for arg in rest:
        if arg.startswith("-"):
            continue
        pjson = projects_dir / arg / "project.json"
        if pjson.exists():
            try:
                data = json.loads(pjson.read_text(encoding="utf-8"))
                m = data.get("model")
                if m:
                    os.environ["MARKERY_MODEL"] = m
            except Exception:
                pass
            return

_SUBCOMMANDS = {
    "match":       "Generate patent-trademark candidate pairs",
    "review":      "Interactive candidate pair review",
    "status":      "Show database row counts and project metrics",
    "enhance":     "Enhance mark images  (enhance|batch|gallery)",
    "patent":      "Patent specialist  (build|fetch|figures|signals|…)",
    "trademark":   "Trademark specialist  (build|enrich|status|…)",
    "matchmaker":  "Entity registry management  (build|list|status)",
    "historian":   "Historian specialist  (prepare <project>)",
    "librarian":   "Librarian specialist  (acquire|search-sources|discover|…)",
    "site":        "Build static research site  (build <project>)",
    "publisher":   "Publisher specialist  (build <project>)",
    "wikipedia":   "Wikipedia tooling  (draft|submit <project> <slug>)",
    "project":     "Project management  (init|adopt)",
    "tokens":      "Token-cost reporting  (report [--by specialist|command|model])",
    "model":       "Provider/model setup  (status|mint|test — OpenRouter)",
}


def _print_help() -> None:
    print("usage: markery <subcommand> [args]\n")
    print("USPTO trademark-patent cross-reference research tool\n")
    print("subcommands:")
    for name, desc in _SUBCOMMANDS.items():
        print(f"  {name:<16}  {desc}")
    print("\nRun 'markery <subcommand> --help' for subcommand options.")
    print("All commands must be run from the project root with the venv active.")


def cmd_match(rest: list[str]) -> None:
    from markery.specialist.matchmaker.cli import match_main
    sys.argv = ["markery match"] + rest
    match_main()


def cmd_matchmaker(rest: list[str]) -> None:
    from markery.specialist.matchmaker.cli import matchmaker_main
    sys.argv = ["markery matchmaker"] + rest
    matchmaker_main()


def cmd_review(rest: list[str]) -> None:
    from markery.specialist.historian.review import main
    sys.argv = ["markery review"] + rest
    main()


def cmd_status() -> None:
    from markery.specialist.historian.status import main
    main()


def cmd_enhance(rest: list[str]) -> None:
    from markery.specialist.publisher.image_enhancement.cli import main
    sys.argv = ["markery enhance"] + rest
    main()


def cmd_patent(rest: list[str]) -> None:
    from markery.specialist.patent.cli import main
    sys.argv = ["markery patent"] + rest
    main()


def cmd_trademark(rest: list[str]) -> None:
    from markery.specialist.trademark.cli import main
    sys.argv = ["markery trademark"] + rest
    main()


def cmd_historian(rest: list[str]) -> None:
    from markery.specialist.historian.cli import historian_main
    sys.argv = ["markery historian"] + rest
    historian_main()


def cmd_librarian(rest: list[str]) -> None:
    from markery.specialist.librarian.cli import librarian_main
    sys.argv = ["markery librarian"] + rest
    librarian_main()


def cmd_publisher(rest: list[str]) -> None:
    from markery.specialist.publisher.cli import publisher_main
    sys.argv = ["markery publisher"] + rest
    publisher_main()


def cmd_wikipedia(rest: list[str]) -> None:
    from markery.specialist.publisher.wikipedia.cli import wikipedia_main
    sys.argv = ["markery wikipedia"] + rest
    wikipedia_main()


def cmd_project(rest: list[str]) -> None:
    from markery.common.project_cli import project_main
    sys.argv = ["markery project"] + rest
    project_main()


def cmd_tokens(rest: list[str]) -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="markery tokens")
    sub = parser.add_subparsers(dest="action", required=True)
    rep = sub.add_parser("report", help="Aggregate a token log into a cost summary")
    rep.add_argument("--log", metavar="PATH", default=None,
                     help="Token log path (default: $MARKERY_TOKEN_LOG)")
    rep.add_argument("--by", metavar="FIELD", default=None,
                     choices=["specialist", "command", "model"],
                     help="Group the breakdown by specialist, command, or model")
    args, _ = parser.parse_known_args(rest)
    if args.action == "report":
        from markery.common.tokens_report import report_main
        report_main(rest[1:])  # drop the "report" token


def cmd_site(rest: list[str]) -> None:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(prog="markery site")
    sub = parser.add_subparsers(dest="action", required=True)

    build = sub.add_parser("build", help="Render project to HTML")
    build.add_argument("project", help="Project name (directory under projects/)")
    build.add_argument("--out", metavar="DIR",
                       help="Output directory (default: site/<project>)")
    build.add_argument("--base-url", metavar="URL", default=None,
                       help="Absolute base URL for Open Graph og:url tags")
    build.add_argument("--no-prune", action="store_true",
                       help="Keep stale files from previous builds (default: prune)")

    build_all = sub.add_parser("build-all",
                               help="Build every project + the Markery portal into site/")
    build_all.add_argument("--out", metavar="DIR",
                           help="Site root (default: site/)")
    build_all.add_argument("--base-url", metavar="URL", default=None,
                           help="Absolute base URL for canonical/sitemap/OG tags")
    build_all.add_argument("--no-prune", action="store_true",
                           help="Keep stale files from previous builds (default: prune)")

    check = sub.add_parser("check", help="Validate built site links; exit non-zero on breakage")
    check.add_argument("project", help="Project name (directory under projects/)")
    check.add_argument("--out", metavar="DIR",
                       help="Site directory to check (default: projects/<project>/site)")
    check.add_argument("--strict", action="store_true",
                       help="Also fail on orphaned (unlinked) files")

    args = parser.parse_args(rest)

    from markery.common import config

    if args.action == "build":
        from markery.specialist.publisher.build import build_site
        out = Path(args.out) if args.out else config.SITE_ROOT / args.project
        build_site(args.project, out,
                   base_url=args.base_url, prune=not args.no_prune)
    elif args.action == "build-all":
        from markery.specialist.publisher.build import build_all
        build_all(Path(args.out) if args.out else None,
                  base_url=args.base_url, prune=not args.no_prune)
    elif args.action == "check":
        from markery.specialist.publisher.check import run_check
        out = Path(args.out) if args.out else config.SITE_ROOT / args.project
        sys.exit(run_check(args.project, out, strict=args.strict))


def cmd_model(rest: list[str]) -> None:
    """Provider/model setup — currently the OpenRouter runtime-key lifecycle."""
    import argparse
    import os

    from markery.common import openrouter as orr

    parser = argparse.ArgumentParser(prog="markery model")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("status", help="Show provider key state and default test model")

    p_mint = sub.add_parser("mint", help="Mint an OpenRouter runtime key from the provisioning key")
    p_mint.add_argument("--name", default="markery-runtime", help="Key label (default: markery-runtime)")
    p_mint.add_argument("--limit", type=float, default=None, metavar="USD",
                        help="Optional spend cap in USD (omit for free models)")

    p_test = sub.add_parser("test", help="Make one live call to verify provider wiring")
    p_test.add_argument("--model", default=orr.DEFAULT_TEST_MODEL,
                        help=f"Model id for any provider — OpenRouter slug, gpt-*, "
                             f"openai:<model>, grok-*, xai:<model>, or claude-* "
                             f"(default: {orr.DEFAULT_TEST_MODEL})")

    args = parser.parse_args(rest)

    def _mask(secret: str) -> str:
        return f"{secret[:12]}…{secret[-4:]}" if len(secret) > 20 else "set"

    if args.action == "status":
        from markery.common import providers as prv
        prov = bool(orr._provisioning_key())
        explicit = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())
        cache = orr._cache_path()
        print("OpenRouter:")
        print(f"  provisioning key   : {'present' if prov else 'MISSING (set OPENROUTER_PROVISIONING_KEY in .env)'}")
        print(f"  OPENROUTER_API_KEY : {'set' if explicit else 'not set'}")
        print(f"  cached runtime key : {'present (' + str(cache) + ')' if cache.exists() else 'none'}")
        rk = orr.runtime_key(allow_mint=False)
        print(f"  resolved runtime   : {'yes' if rk else 'no — run: markery model mint'}")
        print(f"  default test model : {orr.DEFAULT_TEST_MODEL}")
        keys = prv.key_status()
        print("\nDirect providers:")
        print(f"  OPENAI_API_KEY     : {'set' if keys['openai'] else 'not set'}  (models: gpt-*, openai:<model>)")
        print(f"  XAI_API_KEY        : {'set' if keys['xai'] else 'not set'}  (models: grok-*, xai:<model>)")
        return

    if args.action == "mint":
        secret = orr.mint_runtime_key(name=args.name, limit=args.limit)
        cache = orr._cache_path()
        try:
            cache.write_text(secret + "\n", encoding="utf-8")
            cache.chmod(0o600)
        except OSError as exc:
            print(f"Minted key but could not cache it: {exc}", file=sys.stderr)
        print(f"Minted runtime key {_mask(secret)} → cached at {cache}")
        print("It is gitignored. OpenRouter calls will now use it automatically.")
        return

    if args.action == "test":
        from markery.common.llm import call
        import time as _time
        t0 = _time.monotonic()
        text, ptok, ctok, _, _ = call(
            args.model,
            system="You are a terse assistant. Answer in one short sentence.",
            user="In one sentence, what is a trademark?",
            max_tokens=128,
        )
        ms = int((_time.monotonic() - t0) * 1000)
        print(f"Model: {args.model}  ({ms}ms, prompt={ptok}, completion={ctok})")
        print(f"Response: {text}")
        return


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        _print_help()
        return

    if sys.argv[1] in ("-V", "--version"):
        from markery import __version__
        print(f"markery {__version__}")
        return

    cmd  = sys.argv[1]
    rest = sys.argv[2:]

    _try_inject_project_model(rest)

    if cmd not in _SUBCOMMANDS:
        print(f"markery: unknown subcommand '{cmd}'")
        print("Run 'markery --help' for available subcommands.")
        sys.exit(1)

    {
        "match":      lambda: cmd_match(rest),
        "review":     lambda: cmd_review(rest),
        "status":     lambda: cmd_status(),
        "enhance":    lambda: cmd_enhance(rest),
        "patent":     lambda: cmd_patent(rest),
        "trademark":  lambda: cmd_trademark(rest),
        "matchmaker": lambda: cmd_matchmaker(rest),
        "historian":  lambda: cmd_historian(rest),
        "librarian":  lambda: cmd_librarian(rest),
        "site":       lambda: cmd_site(rest),
        "publisher":  lambda: cmd_publisher(rest),
        "wikipedia":  lambda: cmd_wikipedia(rest),
        "project":    lambda: cmd_project(rest),
        "tokens":     lambda: cmd_tokens(rest),
        "model":      lambda: cmd_model(rest),
    }[cmd]()


if __name__ == "__main__":
    main()
