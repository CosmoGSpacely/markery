# Common Layer Review — Project Types

**Date:** 2026-05-21  
**Status:** Concept — not yet promoted to ROADMAP or DEFERRED  
**Scope:** A framework for defining, declaring, and introspecting project types as a first-class concept in Markery, hosted in the shared common layer.

---

## Problem Statement

Project type is currently a documentation concept only. CONTEXT.md describes two project types — match-review-essay and gallery/exploration — but there is no code that knows what type a project is. Any specialist or command that needs to behave differently based on project type guesses by checking for the presence of files (`entities.txt`, `confirmed.jsonl`, etc.). There is no `project_type()` function, no declaration in the project directory, and no registry of what types exist or what structure they require.

The absence of a clear home for project type creates three compounding problems:

1. **No introspection** — Code cannot ask "what kind of project is this?" without heuristics that break when projects are partially built or evolving.
2. **No validation** — No command can check whether a project directory conforms to its type's expected structure.
3. **No scaffold** — New projects of a given type must be created by convention, with no programmatic scaffold to enforce or guide the structure.

---

## Architecture

### Where type definitions live: `markery/common/project.py`

Type definitions belong in the shared common layer, not in any specialist. Specialist code imports from common without triggering cross-specialist dependencies. The orchestrator imports from common when it needs type information to make routing decisions. This keeps definition, policy, and declaration as separate concerns.

`common/project.py` provides:

- A `ProjectType` enum: `MATCH_REVIEW_ESSAY`, `GALLERY_EXPLORATION` (extensible as new types emerge)
- A `Project` dataclass: `type: ProjectType`, `path: Path`, and derived properties for expected paths within the project directory
- A `load_project(path: Path) -> Project` reader that reads `project.json` from the project root and returns a typed `Project` instance
- A `detect_project_type(path: Path) -> ProjectType | None` heuristic for use when `project.json` does not yet exist (see Human Entry Points below)

### Where type is used as policy: `orchestrator.py`

The orchestrator is the single auditable place for cross-specialist policy (G5). Project type is the highest-level cross-specialist policy: it determines which specialists are involved, in what order, and what operations are valid. The orchestrator gains:

- A `project_type(path: Path) -> ProjectType` function that delegates to `common/project.py`
- Type-aware validation for cross-specialist calls: operations that require a `MATCH_REVIEW_ESSAY` project will surface a clear error if invoked on a `GALLERY_EXPLORATION` project, rather than failing silently downstream

The orchestrator does not own type definitions — it uses them. This keeps specialists importable from common without pulling in orchestrator's deferred imports.

### Where type is declared: `project.json` in each project root

A minimal JSON file at the project root declares the type:

```json
{
  "type": "match-review-essay"
}
```

This file is the authoritative source. It is human-editable — if a project's type evolves (a gallery project grows into a match-review-essay project as leads are followed up), the human edits one field. `load_project()` reads it; specialists read it through `load_project()`. The file is committed to the project directory alongside `README.md`.

---

## Human Entry Points

### New projects: `markery project init <name>`

A new top-level command owned by the common layer (or a thin `markery/project_cli.py` that routes through it). The command:

1. Prompts the human to select a project type from the defined options
2. Creates the project directory under `projects/<name>/`
3. Scaffolds the appropriate structure for the selected type (see Structure by Type below)
4. Writes `project.json` with the confirmed type
5. Writes a starter `README.md` with the type's standard workflow description

The human confirms type at project creation — the right moment, since type is a founding decision that shapes which specialists will be involved and what files will be created.

### Existing projects: `markery project adopt <name>`

Existing projects (`information-systems`, `monthly-image-review`) have no `project.json`. A `markery project adopt` command handles retroactive declaration:

1. Runs `detect_project_type()` — the heuristic examines the project directory for structural signals:
   - Presence of `entities.txt`, `entities.csv`, `confirmed.jsonl`, or `RESEARCH-AGENDA.md` → suggests `MATCH_REVIEW_ESSAY`
   - Absence of the above, presence of `output/` galleries or `essays/` without a match pipeline → suggests `GALLERY_EXPLORATION`
2. Shows the inferred type to the human: `"Detected: match-review-essay — confirm? [Y/n]"`
3. Offers a numbered list of alternatives if the inference is wrong
4. Writes `project.json` with the confirmed type

The human confirms an inference rather than making a blank choice. For ambiguous projects, the heuristic is transparent — it lists which signals it found — so the human understands the basis for the suggestion.

### Type evolution

Project type is not permanent. A gallery project may grow into a match-review-essay project. The human edits `project.json` directly (one field, one line), and the new type takes effect immediately. No migration command is required. The `adopt` command can also be re-run on an existing project to interactively change the declared type.

---

## Structure by Type

`common/project.py` encodes the expected structure for each type. This is what `init` scaffolds and what a future `validate` command would check.

**`MATCH_REVIEW_ESSAY`**

```
projects/<name>/
  project.json
  README.md
  STATUS.md
  RESEARCH-AGENDA.md
  RESEARCH.md
  OBJECTIVES.md
  entities.txt
  entities.csv
  variants.csv
  matches/
    candidates.jsonl      (generated)
    confirmed.jsonl       (curated)
    rejected.jsonl        (curated)
    pipeline_state.json   (generated)
  content/
  references/             (optional)
  output/                 (gitignored)
  site/                   (gitignored)
```

**`GALLERY_EXPLORATION`**

```
projects/<name>/
  project.json
  README.md
  STATUS.md
  essays/                 (optional)
  wikipedia/              (optional)
  output/                 (gitignored)
```

New types are added by extending the `ProjectType` enum and adding a structure definition to `common/project.py`. No specialist code changes.

---

## Current State Gap Analysis

Analysis of `src/markery/common/` and `src/markery/specialist/orchestrator.py` against the design above. Note: orchestrator changes are downstream of the common layer work and touch `specialist/orchestrator.py`, but are analyzed here because they are part of the same coherent change.

### What is solid and should not change

- **ROOT detection** (`config.py`) — `pyproject.toml` walk is clean and reliable
- **DB dict** (`config.py`) — right pattern; stays in `config.py` after `Project` moves out
- **`Project.exists()`** (`config.py`) — correct method; survives the refactor unchanged
- **Orchestrator deferred imports** (`orchestrator.py`) — all five functions use lazy imports correctly
- **`cli.py` dispatch table** — extensible; adding a `project` subcommand is one dict entry and one `cmd_project()` function

### Gaps

**Critical — load-bearing for everything else:**

`Project` in `config.py` has no `type` field. It is entirely unaware of project type. Every downstream gap follows from this one.

All path properties on `Project` — `candidates`, `confirmed`, `rejected`, `pipeline_state`, `entities_file`, `objectives`, `brief`, `content`, `site` — are match-review-essay specific. Instantiating `Project("monthly-image-review")` silently exposes `.candidates` pointing to a path that doesn't exist and makes no sense for a gallery project. The class lies about its callers' projects without error.

No `load_project()` reader exists. `Project` is always constructed as `Project(name="...")` with no filesystem read, no `project.json` lookup, and no type resolution. The heuristic detection and human confirmation loop has no code counterpart anywhere.

No `project.json` file exists in any project directory. There is no convention, no schema, no writer, and no reader.

**High — blocked on the critical gaps:**

No `detect_project_type()` heuristic exists. Needed by `markery project adopt` to infer type from directory structure before prompting the human to confirm.

No `markery project` subcommand exists. `cli.py` has no `project` entry in `_SUBCOMMANDS`. `markery project init` and `markery project adopt` have no dispatch path.

**Medium — additive once the critical gaps are resolved:**

Orchestrator functions take raw `Path` args instead of `Project` objects. `enrich_signal_fields(candidates_path: Path)` — the caller must know to pass the correct subpath. With a typed `Project`, the orchestrator could accept a `Project`, validate its type before dispatching, and derive the path internally. Nothing currently prevents a `GALLERY_EXPLORATION` project from being passed to a `MATCH_REVIEW_ESSAY`-only operation.

`Project` lives in `config.py` alongside ROOT and DB path resolution. These are different concerns. `config.py` should own infrastructure paths only; `Project` and related types should move to `project.py`.

**Low:**

`common/__init__.py` is empty. Callers must import from specific modules (`markery.common.config`, `markery.common.auth`). When `project.py` is added, this is a natural moment to decide whether `from markery.common import Project, ProjectType` should work as a published API.

### Gap table

| Gap | Severity | Location |
|---|---|---|
| `Project` has no `type` field | Critical | `common/config.py` |
| All path properties assume match-review-essay | Critical | `common/config.py` |
| No `load_project()` reader | Critical | missing from `common/` |
| No `project.json` convention | Critical | missing from all project dirs |
| No `detect_project_type()` heuristic | High | missing from `common/` |
| No `markery project` subcommand | High | `cli.py` |
| Orchestrator takes `Path` not `Project`, no type validation | Medium | `specialist/orchestrator.py` |
| `Project` lives in `config.py` not `project.py` | Medium | `common/config.py` |
| `common/__init__.py` publishes nothing | Low | `common/__init__.py` |

---

## Convergence with Other Proposals

The `preflight`, `card`, `scaffold`, and `auto-disposition` tools proposed in `SPECIALIST_REVIEW.md` are all invoked in the context of a specific project. Each of those tools will need to know what type of project they are operating on — `preflight` only makes sense for `MATCH_REVIEW_ESSAY` projects, `card` requires a `confirmed.jsonl` that does not exist in `GALLERY_EXPLORATION` projects. The project type framework described here is the prerequisite for those tools to fail cleanly when invoked on the wrong project type rather than failing deep in the stack.

---

## Summary

| Concern | Home |
|---|---|
| Type definitions (enum, structure) | `markery/common/project.py` |
| Type declaration per project | `project.json` at project root |
| Type policy for cross-specialist routing | `orchestrator.py` |
| Human entry point — new project | `markery project init <name>` |
| Human entry point — existing project | `markery project adopt <name>` (heuristic + confirm) |
| Type evolution | Human edits `project.json` directly |

The three concerns — definition, declaration, and policy — are separate files with separate owners. No specialist owns project type knowledge; specialists read it through the common layer's `load_project()`.
