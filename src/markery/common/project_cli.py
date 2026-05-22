"""CLI for project management commands.

Commands:
    markery project init [name]   — scaffold a new project directory
    markery project adopt <name>  — declare the type of an existing project
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markery.common.config import ROOT
from markery.common.project import ProjectType, detect_project_type, scaffold_project


_TYPE_CHOICES = list(ProjectType)


def _prompt_name() -> str:
    name = input("Project name (directory under projects/): ").strip()
    if not name:
        print("Project name cannot be empty.", file=sys.stderr)
        sys.exit(1)
    return name


def _prompt_type() -> ProjectType:
    print("\nProject type:")
    for i, pt in enumerate(_TYPE_CHOICES, 1):
        print(f"  {i}) {pt.value}")
    raw = input("Select [1]: ").strip() or "1"
    try:
        idx = int(raw) - 1
        if not (0 <= idx < len(_TYPE_CHOICES)):
            raise ValueError
    except ValueError:
        print(f"Invalid selection '{raw}'.", file=sys.stderr)
        sys.exit(1)
    return _TYPE_CHOICES[idx]


def cmd_init(name: str | None) -> None:
    if not name:
        name = _prompt_name()

    project_root = ROOT / "projects" / name

    if (project_root / "project.json").exists():
        print(
            f"Project '{name}' already has a project.json at {project_root}.\n"
            "Use 'markery project adopt' to update an existing project's type.",
            file=sys.stderr,
        )
        sys.exit(1)

    project_type = _prompt_type()

    try:
        created = scaffold_project(project_root, project_type)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    print(f"\nScaffolded '{name}' ({project_type.value}):")
    for p in created:
        rel = p.relative_to(ROOT)
        suffix = "/" if p.is_dir() else ""
        print(f"  {rel}{suffix}")
    print(f"\nNext: cd into projects/{name} and start filling in the files.")


def cmd_adopt(name: str) -> None:
    project_root = ROOT / "projects" / name

    if not project_root.is_dir():
        print(f"No directory found at {project_root}.", file=sys.stderr)
        sys.exit(1)

    detected = detect_project_type(project_root)
    if detected is not None:
        print(f"Detected type: {detected.value}")
        confirm = input(f"Write project.json with type '{detected.value}'? [Y/n] ").strip().lower()
        if confirm not in ("", "y"):
            project_type = _prompt_type()
        else:
            project_type = detected
    else:
        print("Could not detect project type from directory structure.")
        project_type = _prompt_type()

    json_path = project_root / "project.json"
    import json
    json_path.write_text(json.dumps({"type": project_type.value}, indent=2) + "\n", encoding="utf-8")
    print(f"Written: {json_path.relative_to(ROOT)}")


def project_main() -> None:
    parser = argparse.ArgumentParser(
        prog="markery project",
        description="Project management for Markery research projects",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    init_p = sub.add_parser("init", help="Scaffold a new project directory")
    init_p.add_argument("name", nargs="?", default=None, help="Project name (prompted if omitted)")

    adopt_p = sub.add_parser("adopt", help="Declare the type of an existing project")
    adopt_p.add_argument("name", help="Project name (directory under projects/)")

    args = parser.parse_args()

    if args.action == "init":
        cmd_init(args.name)
    elif args.action == "adopt":
        cmd_adopt(args.name)
