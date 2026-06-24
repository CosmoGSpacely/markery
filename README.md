# Markery

[![CI](https://github.com/CosmoGSpacely/markery/actions/workflows/ci.yml/badge.svg)](https://github.com/CosmoGSpacely/markery/actions/workflows/ci.yml)

Markery is a command-line research tool for historical patent and trademark scholarship. It finds correspondences between US patents and USPTO trademark registrations — the moment when an invention became a product — and builds a documented, human-reviewed record of those pairings. The output is a static research site with sourced essays, figures, and timelines.

Active research projects include the pre-computer information systems industry (filing appliances, card-index equipment, tabulating machines), early American radio manufacturers (1920–1940), and animal imagery in technology company trademarks (pre-1931).

[![CI](https://github.com/CosmoGSpacely/markery/actions/workflows/ci.yml/badge.svg)](https://github.com/CosmoGSpacely/markery/actions/workflows/ci.yml) · 647 tests · `historian validate` 8/8 on every essay · cross-model MVO benchmark 6/6 ([Haiku & Sonnet](DESIGN.md#empirical-verification-phase-22-p3))

---

## See the output

`markery site build-all` renders the Markery portal into `site/` (the root landing plus each project under `site/<project>/`); open `site/index.html`. Each page is static HTML (no JavaScript framework), with breadcrumb navigation, a Primary Sources block linking the USPTO serial and patent numbers, and sourced essays scaffolded from DB records and human-finalized; essay frontmatter is checked against the live databases by `markery historian validate` before it publishes. Built sites are regenerable artifacts and are not committed.

---

## Quickstart

```bash
git clone https://github.com/CosmoGSpacely/markery.git
cd markery
python -m venv .venv && source .venv/bin/activate
pip install -e "."
markery --version        # confirm install
markery status           # inspect committed databases
markery project init my-project   # scaffold a new research project
```

The three databases (`patents.duckdb`, `trademarks.duckdb`, `entities.duckdb`) are committed to the repository. No rebuild is required to start working with the existing `information-systems` project.

Full setup, credential configuration, and rebuild instructions: [**SETUP.md**](SETUP.md)

---

## How it works

Markery is structured as six specialist agents, each owning one data domain:

| Specialist | Owns | Role |
|---|---|---|
| PATENT | `data/patents.duckdb` | Fetches patent records from EPO OPS by CPC class and year range |
| TRADEMARK | `data/trademarks.duckdb` | Loads USPTO bulk data; enriches marks via the TSDR API |
| MATCHMAKER | `data/entities.duckdb` | Manages the entity registry; scores patent-trademark candidate pairs |
| HISTORIAN | `confirmed.jsonl` per project | Guides human review; scaffolds and validates research essays |
| PUBLISHER | `site/` per project | Renders confirmed pairs and essays into a static research site |
| LIBRARIAN | `library/` at repo root | Acquires secondary literature; indexes passages for historian context |

**Candidate generation** — The MATCHMAKER scores every patent-trademark pair for each entity in a project: how closely the trademark filing follows the patent grant date (max 0.5), whether the CPC class falls in the product signal set (0.3 binary). Maximum score: 0.80. The ceiling is intentional — a 1.0 would claim a certainty no automated process can deliver.

**Human confirmation** — A high score identifies a pair worth examining; it does not confirm a historical correspondence. Confirmation is a human act. The HISTORIAN presents each candidate and records the human's decision. `confirmed.jsonl` is curated by hand. `candidates.jsonl` is generated automatically and never edited.

**Publishing** — Once pairs are confirmed, the HISTORIAN scaffolds research essays from a defined scholar persona; the PUBLISHER renders them as a static site with mark images, patent figures, timelines, and cross-linked entity pages.

Cross-specialist calls route through `orchestrator.py`. No specialist imports directly from another.

---

## CLI reference

```bash
# Start a project
markery project init <project>
markery status

# Patent corpus
markery patent build --classes B42F B42D --year-start 1900 --year-end 1939
markery patent build --resume              # resume after quota interruption
markery patent pull <patent_no>            # fetch a single patent on demand
markery patent coverage-check --classes B42F --year-start 1900 --year-end 1939
markery patent verify-credentials

# Trademark corpus
markery trademark build --csv-dir csv/ --date-start 1900-01-01 --date-end 1939-12-31
markery trademark fetch <serial_no>
markery trademark enrich-project <project> --source confirmed
markery trademark verify-credentials

# Entity registry
markery matchmaker build --data-dir projects/<project>
markery matchmaker list
markery matchmaker suggest-variants "<entity name>"   # rank name variants from DB
markery matchmaker validate-variants --data-dir projects/<project>

# Match pipeline
markery match <project>                    # generate candidates (focus_serials-scoped if set)
markery match <project> --all-serials      # generate from all entity trademarks
markery match <project> --full             # generate + signals + rescore
markery match auto-disposition <project> --reject-below 0.25  # batch-reject low scorers
markery match preflight <project>          # pre-session signal and image audit
markery match rescore <project>
markery review <project>                   # interactive review (Y / N / Q)

# Historian tools
markery historian prepare <project>        # generate session brief
markery historian digest <project>         # compact project state summary (~800–1200 tokens)
markery historian card <project> <slug>    # compact candidate card (~250 tokens)
markery historian scaffold <project> <slug>  # generate essay skeleton
markery historian validate <project> <slug>  # validate essay against DB

# Secondary literature (LIBRARIAN)
markery librarian discover --wikipedia "<Article Name>" --add-wants
markery librarian search-sources "<query>" --source ia
markery librarian acquire <ia-identifier>
markery librarian extract <slug> --topics "topic1" "topic2"
markery librarian index --embed
markery librarian card "<query>" --mode semantic
markery librarian search "<query>"

# Publish
markery site build <project>
markery enhance enhance <serial_no> --out-dir projects/<project>/output/<slug>
markery wikipedia draft <project> <slug>

# Diagnostics
markery status
markery <subcommand> --help
```

---

## Current corpus

| Database | Contents |
|---|---|
| `trademarks.duckdb` | 25,473 case files, 1900–1939 (USPTO bulk) · 96+ mark images · enriched records via TSDR |
| `patents.duckdb` | ~40,000+ US patents across B42F, B42D, B41J, B41L, G06C, G06K, G09F, H04B, H01J, H03F, B60C, A01B, F02B and others |
| `entities.duckdb` | 30 entities across three projects (information-systems, radio-pioneers, animal-marks-1930) |
| `library/` | Shared secondary literature corpus (Internet Archive / Gutenberg) — full text, indexed passages, embedding index |

---

## Published contributions

The research output is not only a static site — confirmed pairs have been used to add primary-source citations to live Wikipedia articles. Each edit is a real, reverted-checked revision:

| Article | Contribution | Revision |
|---|---|---|
| [Soundex](https://en.wikipedia.org/wiki/Soundex) | SOUNDEX trademark citation (USPTO Serial 71246709, Rand Kardex, 1927) | [1358151441](https://en.wikipedia.org/w/index.php?diff=1358151441) |
| [Rolodex](https://en.wikipedia.org/wiki/Rolodex) | Wheeldex trademark citation (USPTO Serial 71321669) | [1357918452](https://en.wikipedia.org/w/index.php?diff=1357918452) |
| [Remington Rand](https://en.wikipedia.org/wiki/Remington_Rand) | Filing-systems section from primary sources | [1358111560](https://en.wikipedia.org/w/index.php?diff=1358111560) |
| [Library Bureau](https://en.wikipedia.org/wiki/Library_Bureau) | Resolved `{{Citation needed}}` (1921 catalog) | [1357391696](https://en.wikipedia.org/w/index.php?diff=1357391696) |
| [Library Bureau](https://en.wikipedia.org/wiki/Library_Bureau) | Absorption citation (LA Times, 1927) | [1357570204](https://en.wikipedia.org/w/index.php?diff=1357570204) |
| [Chicago Pneumatic](https://en.wikipedia.org/wiki/Chicago_Pneumatic) | CP monogram trademark citation (USPTO Serial 71299042, 1930) | [1358151236](https://en.wikipedia.org/w/index.php?diff=1358151236) |

---

## How this was built

Markery is an AI-orchestrated research tool, and that is a design stance, not a disclaimer. The architecture is built to put a stronger model (or a human) only where judgment is irreducible, and to make everything else checkable by code:

- **Three-tier work classification.** Every change belongs to exactly one of *Markery* (shared infrastructure), *Specialist* (one agent's domain), or *Project* (one research project's artifacts). The boundaries are enforced per session by `CLAUDE.md` and each specialist's `identity.md` scope — so an agent cannot write outside its lane without halting.
- **Human judgment at the right altitude.** Automated scoring caps at 0.80 by design: a high score identifies a pair *worth examining*, never a confirmed correspondence. Confirmation is a human act recorded in `confirmed.jsonl`; `candidates.jsonl` is machine-generated and never hand-edited. The model drafts prose from a scholar persona; a human finalizes it.
- **Checkable outputs (MVO).** Each command defines a *minimum viable output* that code can validate — `historian validate` checks an essay's facts against the live databases (serial resolves, patent resolves, grant date matches, no cross-pair contamination). This converts "is this essay accurate?" from a model-sensitive judgment into a deterministic check.
- **Model-agnosticism, measured.** Because the model-agnostic tier is defined by checkable outputs, model choice there is a *cost* decision, not a *correctness* one — and this is proven, not asserted: the [cross-model MVO benchmark](DESIGN.md#empirical-verification-phase-22-p3) runs the inference tasks under Haiku 4.5 and Sonnet 4.6 and both pass every validator (6/6).
- **CLI as the test harness.** The CLI is the product under test: every read and write goes through it, so exercising a command validates the same path a user hits. There is no privileged back door for the tool's own scripts.

See [DESIGN.md](DESIGN.md) for the full rationale and [CONTEXT.md](CONTEXT.md) for the specialist/project model.

---

## Engineering discipline

The internal process is deliberate and visible, not buried:

- **Phase-gated roadmap.** [ROADMAP.md](ROADMAP.md) carries explicit, checkable phase gates (`PASSED when: …`) and dated results paragraphs — work is not "done" until its gate criteria are met and recorded.
- **Contract-versioned subprocess interface.** The `markery-langgraph` orchestration repo calls Markery through a versioned contract declared in [`MANIFEST.json`](MANIFEST.json) (`contract_version`); a signature or output-format change bumps the version and a `check_contract()` assertion catches drift.
- **Reopen-triggered deferral register.** [DEFERRED.md](DEFERRED.md) records known-but-not-now work, and every entry carries an explicit *reopen trigger* — no item is deferred without the condition that should bring it back.

---

## Links

| | |
|---|---|
| [SETUP.md](SETUP.md) | Installation, credentials, database rebuild |
| [CONTEXT.md](CONTEXT.md) | Project constitution — specialists, project model, workflow |
| [DESIGN.md](DESIGN.md) | Engineering rationale — DuckDB, scoring, scope neutrality |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [ROADMAP.md](ROADMAP.md) | Active development phases |
| [DEFERRED.md](DEFERRED.md) | Known deferred work with reopen triggers |
