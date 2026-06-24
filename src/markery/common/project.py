"""Project type definitions and project directory contracts.

ProjectType — enum of known project kinds
Project     — path contract for a research project directory
load_project(path)         — read project.json and return a typed Project
detect_project_type(path)  — heuristic inference when project.json is absent
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from markery.common.config import ROOT

_PATENT_RE  = re.compile(r'^[A-Z]{2}\d+[A-Z]\d*$', re.IGNORECASE)
_SERIAL_RE  = re.compile(r'^\d{5,9}$')


def validate_patent_no(patent_no: str) -> str:
    """Return the uppercased patent_no, or exit with an error if malformed.

    Expected format: country-code (2 letters) + digits + kind code (letter[s]).
    Examples: US1261167A, EP0123456B1.
    """
    if not _PATENT_RE.match(patent_no):
        print(
            f"Invalid patent number '{patent_no}'. "
            "Expected format: <CC><digits><kind>, e.g. US1261167A.",
            file=sys.stderr,
        )
        sys.exit(1)
    return patent_no.upper()


def validate_serial_no(serial_no: str) -> str:
    """Return the serial_no as-is, or exit with an error if malformed.

    USPTO trademark serial numbers are 7–9 digits.
    """
    if not _SERIAL_RE.match(serial_no.strip()):
        print(
            f"Invalid serial number '{serial_no}'. "
            "Expected 5–9 digits (USPTO trademark serial number).",
            file=sys.stderr,
        )
        sys.exit(1)
    return serial_no.strip()


class ProjectType(str, Enum):
    MATCH_REVIEW_ESSAY = "match-review-essay"
    GALLERY_EXPLORATION = "gallery-exploration"
    ANNUAL_REVIEW = "annual-review"


@dataclass
class Project:
    """Path contract for a research project directory.

    Construct directly with Project(name=...) for legacy callers or
    intermediate states. Use load_project() to get a type-annotated
    instance read from project.json.

    Type-specific path properties raise TypeError if the project type is
    set and does not match. When type is None (legacy construction), all
    paths are accessible for backward compatibility during the transition
    to project.json-declared types.
    """

    name: str
    type: ProjectType | None = field(default=None)
    focus_serials: list[int] = field(default_factory=list)
    class_hints: list[str] = field(default_factory=list)
    model: str | None = field(default=None)
    prior_brand_serials: list[str] = field(default_factory=list)
    review_years: list[int] = field(default_factory=list)

    def _require_type(self, required: ProjectType, attr: str) -> None:
        if self.type is not None and self.type != required:
            raise TypeError(
                f"'{attr}' is only available for {required.value} projects; "
                f"this project type is {self.type.value}. "
                f"Check {self.root / 'project.json'}."
            )

    # ------------------------------------------------------------------
    # Universal paths
    # ------------------------------------------------------------------

    @property
    def root(self) -> Path:
        return ROOT / "projects" / self.name

    def exists(self) -> bool:
        return self.root.is_dir()

    # ------------------------------------------------------------------
    # Match-review-essay paths
    # ------------------------------------------------------------------

    @property
    def candidates(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "candidates")
        return self.root / "matches" / "candidates.jsonl"

    @property
    def confirmed(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "confirmed")
        return self.root / "matches" / "confirmed.jsonl"

    @property
    def rejected(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "rejected")
        return self.root / "matches" / "rejected.jsonl"

    @property
    def pipeline_state(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "pipeline_state")
        return self.root / "matches" / "pipeline_state.json"

    @property
    def entities_file(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "entities_file")
        return self.root / "entities.txt"

    @property
    def objectives(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "objectives")
        return self.root / "OBJECTIVES.md"

    @property
    def brief(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "brief")
        return self.root / "BRIEF.md"

    @property
    def references(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "references")
        return self.root / "references"

    @property
    def content(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "content")
        return self.root / "content"

    @property
    def site(self) -> Path:
        self._require_type(ProjectType.MATCH_REVIEW_ESSAY, "site")
        return self.root / "site"


def load_project(path: Path) -> Project:
    """Read project.json from path and return a typed Project.

    Raises FileNotFoundError if project.json is absent — run
    'markery project adopt <name>' to declare the project type.
    Raises ValueError if project.json contains an unrecognised type.
    """
    json_path = path / "project.json"
    if not json_path.exists():
        raise FileNotFoundError(
            f"No project.json found at {json_path}.\n"
            f"Run 'markery project adopt {path.name}' to declare the project type."
        )
    data = json.loads(json_path.read_text(encoding="utf-8"))
    try:
        project_type = ProjectType(data["type"])
    except KeyError:
        raise ValueError(f"project.json at {json_path} is missing the 'type' field.")
    except ValueError:
        known = [t.value for t in ProjectType]
        raise ValueError(
            f"Unknown project type '{data['type']}' in {json_path}. "
            f"Known types: {known}"
        )
    focus_serials = [int(s) for s in data.get("focus_serials", [])]
    class_hints = [str(c) for c in data.get("class_hints", [])]
    model = data.get("model") or None
    prior_brand_serials = [str(s) for s in data.get("prior_brand_serials", [])]
    review_years = [int(y) for y in data.get("review_years", [])]
    return Project(name=path.name, type=project_type, focus_serials=focus_serials,
                   class_hints=class_hints, model=model,
                   prior_brand_serials=prior_brand_serials, review_years=review_years)


def scaffold_project(root: Path, project_type: ProjectType) -> list[Path]:
    """Create the canonical directory structure for a new project.

    Creates directories and empty placeholder files. Returns the list of
    paths created (directories and files). Does not overwrite existing files.
    Raises FileExistsError if root already contains a project.json.
    """
    project_json = root / "project.json"
    if project_json.exists():
        raise FileExistsError(
            f"{project_json} already exists. "
            "Use 'markery project adopt' to update the type of an existing project."
        )

    created: list[Path] = []

    def _mkdir(p: Path) -> None:
        p.mkdir(parents=True, exist_ok=True)
        created.append(p)

    def _touch(p: Path, content: str = "") -> None:
        if not p.exists():
            p.write_text(content, encoding="utf-8")
            created.append(p)

    _mkdir(root)

    if project_type == ProjectType.MATCH_REVIEW_ESSAY:
        _mkdir(root / "matches")
        _touch(root / "matches" / "candidates.jsonl")
        _touch(root / "matches" / "confirmed.jsonl")
        _touch(root / "matches" / "rejected.jsonl")
        _touch(root / "entities.csv", "entity_id,canonical_name,entity_type,industry\n")
        _touch(root / "variants.csv", "entity_id,variant_name,source\n")
        _mkdir(root / "references")
        _mkdir(root / "content")
        _touch(root / "OBJECTIVES.md", f"# Objectives — {root.name}\n\n")
        _touch(root / "BRIEF.md", f"# Brief — {root.name}\n\n")

    elif project_type == ProjectType.GALLERY_EXPLORATION:
        _mkdir(root / "output")
        _mkdir(root / "essays")
        _mkdir(root / "wikipedia")

    _touch(root / "README.md", f"# {root.name}\n\n")
    _touch(root / "project.json",
           json.dumps({"type": project_type.value}, indent=2) + "\n")

    return created


def require_project(name: str | None) -> Project:
    """Return a typed Project for name, or exit with a clear error.

    Checks that the project directory exists and contains project.json.
    Call this at CLI entry points before any DB or file access.
    """
    import sys
    if not name:
        print("Project name required. Usage: markery <command> <project>", file=sys.stderr)
        sys.exit(1)
    proj = Project(name=name)
    if not proj.root.is_dir():
        print(
            f"Project '{name}' not found at {proj.root}.\n"
            f"Run 'markery project init {name}' to create it, or check the name.",
            file=sys.stderr,
        )
        sys.exit(1)
    pjson = proj.root / "project.json"
    if not pjson.exists():
        print(
            f"Project '{name}' has no project.json at {pjson}.\n"
            f"Run 'markery project adopt {name}' to declare the project type.",
            file=sys.stderr,
        )
        sys.exit(1)
    return load_project(proj.root)


def detect_project_type(path: Path) -> ProjectType | None:
    """Infer project type from directory structure.

    Returns None when signals are absent or ambiguous.
    Signals for MATCH_REVIEW_ESSAY (any one is sufficient):
      - entities.txt present
      - matches/confirmed.jsonl present
      - matches/candidates.jsonl present
    Signals for GALLERY_EXPLORATION (any one, and no MRE signals):
      - essays/ directory present
      - output/ directory present (without match pipeline files)
    """
    has_entities   = (path / "entities.txt").exists()
    has_confirmed  = (path / "matches" / "confirmed.jsonl").exists()
    has_candidates = (path / "matches" / "candidates.jsonl").exists()

    if has_entities or has_confirmed or has_candidates:
        return ProjectType.MATCH_REVIEW_ESSAY

    has_essays = (path / "essays").is_dir()
    has_output = (path / "output").is_dir()

    if has_essays or has_output:
        return ProjectType.GALLERY_EXPLORATION

    return None
