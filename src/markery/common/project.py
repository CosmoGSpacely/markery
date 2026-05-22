"""Project type definitions and project directory contracts.

ProjectType — enum of known project kinds
Project     — path contract for a research project directory
load_project(path)         — read project.json and return a typed Project
detect_project_type(path)  — heuristic inference when project.json is absent
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from markery.common.config import ROOT


class ProjectType(str, Enum):
    MATCH_REVIEW_ESSAY = "match-review-essay"
    GALLERY_EXPLORATION = "gallery-exploration"


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
    return Project(name=path.name, type=project_type)


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
