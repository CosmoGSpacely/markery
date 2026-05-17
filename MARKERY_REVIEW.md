# Markery Project Review and Restructuring Plan

## Executive Summary
The Markery project has grown beyond its original scope as a research tool for USPTO trademark-patent cross-referencing. Current issues include mission creep, disorganized file structure, and incoherent workflows. This document proposes a comprehensive restructuring to restore focus and improve maintainability.

## Identified Problems

### Mission Creep
- The project has expanded beyond its core research tool purpose to include:
  - Image enhancement pipeline (Real-ESRGAN upscaling)
  - Patent document fetching and processing
  - AI historian specialist agent (`commerce-and-technology-historian/`)
  - Multiple research projects with different scopes
- This dilutes the focus on USPTO trademark-patent cross-referencing

### Disorganized Structure
- Flat module layout at root level (`image_tools/`, `match/`, `patent_docs/`)
- Mixed concerns: research tools, data processing, AI agents, project outputs
- Scripts directory contains operational scripts but no clear categorization
- Projects directory mixes research content with generated outputs

### Workflow Issues
- No single entry point or clear user journey
- Operations scattered across multiple scripts and modules
- Phase 1 completion blocked by lack of documented workflow checklist
- Dependencies between components not clearly defined

## Proposed Restructuring Plan

### 1. Separate Core Research Tool from Extensions
**Create two distinct packages:**
- `markery-core/`: Core USPTO data processing (databases, matching, basic queries)
- `markery-tools/`: Extended functionality (image enhancement, patent docs, AI agents)

**Benefits:** Allows users to install only what they need, reduces complexity for core research workflows.

### 2. Reorganize Directory Structure
```
markery/
├── src/markery/          # Core package
│   ├── db/               # Database builders and schemas
│   ├── matching/         # Candidate generation and scoring
│   └── cli.py            # Main CLI entry point
├── tools/                # Extended tools (optional install)
│   ├── image_enhancement/
│   ├── patent_docs/
│   ├── trademark_docs/
│   └── historian/
├── projects/             # Research projects only
│   ├── monthly-survey/
│   └── information-systems/
├── scripts/              # Operational scripts (minimize)
├── data/                 # DuckDB files and raw data
├── docs/                 # All documentation
└── tests/                # Comprehensive test suite
```

### 3. Define Clear Workflows
**Primary Research Workflow:**
1. `markery init` - Set up databases and environment
2. `markery entities add <company>` - Add new entity
3. `markery match <project>` - Generate candidates
4. `markery review <project>` - Interactive candidate review
5. `markery confirm <project> <patent> <trademark>` - Add confirmed pair
6. `markery export <project>` - Generate research outputs

**Secondary Workflows:**
- Image enhancement: `markery-tools enhance`
- Patent docs: `markery-tools fetch-patents`
- Trademark docs: `markery-tools fetch-trademarks`
- AI assistance: `markery-tools historian`

### 4. Consolidate Entry Points
- Single `markery` command with subcommands
- Remove scattered scripts in favor of subcommands
- Clear help system and command discovery

### 5. Documentation Overhaul
- Create `docs/workflows/` with step-by-step guides
- Move all reference docs to `docs/reference/`
- Add `docs/contributing/` for extension development
- Include workflow diagrams and decision trees

### 6. Project Scope Refinement
**Core Markery (v1.0):**
- USPTO and EPO data ingestion and cross-referencing
- Candidate generation and scoring
- Basic research project management
- Confirmed pair curation

**Extensions (separate packages):**
- Image processing tools
- Patent document handling
- AI research assistance

### 7. Implementation Phases
**Phase 1:** Restructure core package and migrate existing code
**Phase 2:** Create extension packages and migration guides
**Phase 3:** Update documentation and workflows
**Phase 4:** Deprecate old structure with clear migration path

## Next Steps
1. Create the new directory structure
2. Migrate core functionality to `src/markery/`
3. Move extensions to `tools/` subdirectories
4. Update import statements and dependencies
5. Create unified CLI interface
6. Update documentation to reflect new structure
7. Add deprecation warnings for old entry points

This restructuring will restore Markery's focus on its core research mission while making the codebase more maintainable and user-friendly.